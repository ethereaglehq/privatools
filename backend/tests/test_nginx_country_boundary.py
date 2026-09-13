"""Config-level country trust contract. These do not claim a live nginx -t.

Parse the shipped directives, exercise their CIDRs and map expression, and
verify every proxy location overrides the internal/raw headers explicitly.
"""
from dataclasses import dataclass, field
from ipaddress import ip_address, ip_network
import json
from pathlib import Path
import re
import shlex

import pytest

ROOT = Path(__file__).resolve().parents[2]
ORACLE = ROOT / "deploy/oracle-vm/nginx-privatools.conf"
LEGACY = ROOT / "deploy/nginx.conf"
POLICY = "/api/analytics/policy"


@dataclass
class Directive:
    name: str
    args: list[str]
    children: list["Directive"] = field(default_factory=list)


def parse_config(path: Path) -> list[Directive]:
    lexer = shlex.shlex(path.read_text(), posix=True, punctuation_chars="{};")
    lexer.whitespace_split = True
    lexer.commenters = "#"
    tokens = []
    for token in lexer:
        tokens.extend(list(token) if token and set(token) <= set("{};") else [token])
    position = 0

    def parse(inside=False):
        nonlocal position
        nodes = []
        while position < len(tokens):
            if tokens[position] == "}":
                assert inside, "Unmatched nginx closing brace"
                position += 1
                return nodes
            words = []
            while position < len(tokens) and tokens[position] not in (";", "{", "}"):
                words.append(tokens[position])
                position += 1
            assert words and position < len(tokens), "Unterminated nginx directive"
            ending = tokens[position]
            position += 1
            assert ending != "}", "Missing nginx semicolon"
            nodes.append(Directive(words[0], words[1:], parse(True) if ending == "{" else []))
        assert not inside, "Unclosed nginx block"
        return nodes

    return parse()


def named(nodes, name):
    return [node for node in nodes if node.name == name]


def walk(nodes):
    for node in nodes:
        yield node
        yield from walk(node.children)


def direct(node, name):
    return [item.args for item in node.children if item.name == name]


def header(node, name):
    values = [args[1] for args in direct(node, "proxy_set_header") if args[0].lower() == name.lower()]
    assert len(values) == 1, f"{node.name} {node.args}: {name} must be overwritten exactly once"
    return values[0]


def country_from_shipped_map(peer, country, worker=""):
    nodes = parse_config(ORACLE)
    geo = named(nodes, "geo")[0]
    assert geo.args == ["$realip_remote_addr", "$pt_cloudflare_ingress"]
    networks = [ip_network(item.name) for item in geo.children if item.name != "default"]
    try:
        address = ip_address(peer)
        trusted = any(address in network for network in networks)
    except ValueError:
        trusted = False
    country_map = named(nodes, "map")[0]
    assert country_map.args == ["$pt_cloudflare_ingress:$http_cf_worker:$http_cf_ipcountry", "$pt_analytics_country"]
    value = f"{int(trusted)}:{worker}:{country}"
    for item in country_map.children:
        if item.name == "default":
            continue
        if item.name.startswith("~"):
            regex = item.name[1:].replace("(?<", "(?P<")
            match = re.fullmatch(regex, value)
            if match:
                return match.group(item.args[0][1:])
        elif item.name.lower() == value.lower():
            return item.args[0]
    return next(item.args[0] for item in country_map.children if item.name == "default")


def test_ranges_match_verified_official_snapshot_and_do_not_trust_private_or_all_networks():
    snapshot = json.loads((ROOT / "deploy/cloudflare-country-ranges.json").read_text())
    geo = named(parse_config(ORACLE), "geo")[0]
    configured = [item.name for item in geo.children if item.name != "default"]
    assert configured == snapshot["ipv4"] + snapshot["ipv6"]
    assert snapshot["sources"] == ["https://www.cloudflare.com/ips-v4", "https://www.cloudflare.com/ips-v6"]
    assert snapshot["verifiedAt"] == "2026-09-14"
    assert len(configured) == len(set(configured)) == 22
    assert direct(geo, "default") == [["0"]]
    for item in geo.children:
        if item.name == "default":
            continue
        network = ip_network(item.name, strict=True)
        assert network.is_global and network.prefixlen > 0
        assert item.args == ["1"]
        assert country_from_shipped_map(str(network.network_address + 1), "IN") == "IN"


@pytest.mark.parametrize("peer,country,worker,expected", [
    ("173.245.48.12", "IN", "", "IN"),
    ("2606:4700::1", "DE", "", "DE"),
    ("8.8.8.8", "IN", "", ""),
    ("198.51.100.24", "US", "", ""),
    ("127.0.0.1", "US", "", ""),
    ("192.168.0.2", "US", "", ""),
    ("::1", "US", "", ""),
    ("not-an-ip", "US", "", ""),
    ("173.245.48.12", "XX", "", ""),
    ("173.245.48.12", "T1", "", ""),
    ("173.245.48.12", "", "", ""),
    ("173.245.48.12", "in", "", ""),
    ("173.245.48.12", "IND", "", ""),
    ("173.245.48.12", "IN, DE", "", ""),
    ("173.245.48.12", " US", "", ""),
    ("173.245.48.12", "US", "example.workers.dev", ""),
])
def test_ingress_and_country_fail_closed(peer, country, worker, expected):
    assert country_from_shipped_map(peer, country, worker) == expected


def test_original_socket_peer_is_the_only_ingress_input():
    nodes = parse_config(ORACLE)
    geo = named(nodes, "geo")[0]
    assert geo.args[0] == "$realip_remote_addr"
    assert not named(geo.children, "proxy")
    assert not named(geo.children, "proxy_recursive")
    # A visitor address restored by real_ip or an XFF chain is never the test
    # input. An attacker cannot create a trusted ingress by adding a header.
    assert not any("$http_" in arg or "$remote_addr" == arg for arg in geo.args)


@pytest.mark.parametrize("path", [ORACLE, LEGACY])
def test_every_proxied_location_drops_user_country_headers_unless_exact_policy(path):
    nodes = parse_config(path)
    count = 0
    for server in named(nodes, "server"):
        hosts = sum(direct(server, "server_name"), [])
        for location in named(server.children, "location"):
            if not direct(location, "proxy_pass"):
                continue
            count += 1
            expected = "$pt_analytics_country" if path == ORACLE and hosts == ["privatools.me"] and location.args == ["=", POLICY] else ""
            assert header(location, "X-PrivaTools-Country") == expected
            assert header(location, "CF-IPCountry") == ""
    assert count >= 4
    assert not any(item.name == "proxy_pass_request_headers" and item.args == ["off"] for item in walk(nodes)), "Do not remove unrelated request headers"


def test_only_apex_policy_can_receive_computed_country():
    nodes = parse_config(ORACLE)
    computed = [item for item in walk(nodes) if item.name == "proxy_set_header" and item.args == ["X-PrivaTools-Country", "$pt_analytics_country"]]
    assert len(computed) == 1
    api_server = next(server for server in named(nodes, "server") if ["443", "ssl", "http2"] in direct(server, "listen") and ["api.privatools.me"] in direct(server, "server_name"))
    for location in named(api_server.children, "location"):
        if direct(location, "proxy_pass"):
            assert header(location, "X-PrivaTools-Country") == ""


@pytest.mark.parametrize("path,expected_count", [(ORACLE, 2), (LEGACY, 1)])
def test_policy_endpoint_cannot_use_proxy_cache_or_override_backend_no_store(path, expected_count):
    locations = [item for item in walk(parse_config(path)) if item.name == "location" and item.args == ["=", POLICY]]
    assert len(locations) == expected_count
    for location in locations:
        assert direct(location, "proxy_pass") == [["http://127.0.0.1:8000"]], "Preserve the full /api path"
        assert direct(location, "proxy_cache") == [["off"]]
        assert direct(location, "proxy_cache_bypass") == [["1"]]
        assert direct(location, "proxy_no_cache") == [["1"]]
        assert not named(location.children, "proxy_ignore_headers")
        assert not any("cache-control" in [arg.lower() for arg in item.args] for item in location.children if item.name in {"proxy_hide_header", "add_header"})
        assert not named(location.children, "add_header"), "Keep the existing server security-header inheritance"


def test_default_html_and_static_responses_do_not_receive_country():
    for path in [ORACLE, LEGACY]:
        for node in walk(parse_config(path)):
            if node.name == "location" and direct(node, "proxy_pass") and node.args != ["=", POLICY]:
                assert header(node, "X-PrivaTools-Country") == ""


def test_real_ip_restoration_trusts_only_verified_edges_and_preserves_country_peer():
    nodes = parse_config(ORACLE)
    snapshot = json.loads((ROOT / "deploy/cloudflare-country-ranges.json").read_text())
    assert [n.args[0] for n in named(nodes, "set_real_ip_from")] == snapshot["ipv4"] + snapshot["ipv6"]
    assert [n.args for n in named(nodes, "real_ip_header")] == [["CF-Connecting-IP"]]
    assert [n.args for n in named(nodes, "real_ip_recursive")] == [["off"]]
    assert named(nodes, "geo")[0].args[0] == "$realip_remote_addr"


def tls_server(host):
    return next(
        server for server in named(parse_config(ORACLE), "server")
        if ["443", "ssl", "http2"] in direct(server, "listen")
        and [host] in direct(server, "server_name")
    )


def test_api_document_exact_match_prevents_nginx_automatic_slash_redirect():
    server = tls_server("privatools.me")
    locations = named(server.children, "location")
    # A proxied /api/ prefix makes nginx redirect /api to /api/ before the
    # default SPA location can run. Only an EXACT /api location prevents this;
    # merely retaining location / (or adding an /api prefix) is insufficient.
    api_prefix = next(location for location in locations if location.args == ["/api/"])
    assert direct(api_prefix, "proxy_pass"), "Keep the existing API endpoint upstream"
    exact = [location for location in locations if location.args == ["=", "/api"]]
    assert len(exact) == 1, "Without exact /api, nginx's proxied /api/ prefix returns automatic 301"
    document = exact[0]
    default = next(location for location in locations if location.args == ["/"])
    for directive in ("proxy_pass", "proxy_set_header", "proxy_read_timeout", "proxy_connect_timeout"):
        assert direct(document, directive) == direct(default, directive)
    assert direct(document, "proxy_pass") == [["http://127.0.0.1:8000"]], "Do not rewrite /api to /api/ upstream"
    assert not direct(document, "return")
    assert not direct(document, "rewrite")
    assert not direct(document, "add_header"), "Inherit all apex security headers"
    assert not direct(document, "proxy_hide_header"), "Preserve the backend's per-request CSP"


def test_api_document_trailing_slash_redirect_is_exact_and_preserves_query():
    locations = named(tls_server("privatools.me").children, "location")
    exact = [location for location in locations if location.args == ["=", "/api/"]]
    assert len(exact) == 1
    assert direct(exact[0], "return") == [["308", "/api$is_args$args"]]
    assert not direct(exact[0], "proxy_pass")
    assert not direct(exact[0], "add_header"), "Redirects retain inherited apex security headers"


@pytest.mark.parametrize("route", ["/api/health", "/api/tools/merge-pdf", "/api/analytics/policy"])
def test_api_document_locations_do_not_capture_real_api_endpoints(route):
    locations = named(tls_server("privatools.me").children, "location")
    exact = next((location for location in locations if location.args == ["=", route]), None)
    # These non-static API routes use an exact endpoint when present, otherwise
    # the longest prefix. The document redirects must match neither case.
    selected = exact or max(
        (location for location in locations if len(location.args) == 1 and route.startswith(location.args[0])),
        key=lambda location: len(location.args[0]),
    )
    assert direct(selected, "proxy_pass") == [["http://127.0.0.1:8000"]]
    assert not direct(selected, "return")
    if route != POLICY:
        assert selected.args == ["/api/"]
        assert direct(selected, "limit_req") == [["zone=api", "burst=20", "nodelay"]]
        assert direct(selected, "limit_conn") == [["apiconn", "24"]]
        assert direct(selected, "proxy_read_timeout") == [["300s"]]


def test_api_document_locations_are_not_added_to_the_direct_api_host():
    locations = named(tls_server("api.privatools.me").children, "location")
    assert not any(location.args in (["=", "/api"], ["=", "/api/"]) for location in locations)
    default = next(location for location in locations if location.args == ["/"])
    assert direct(default, "return") == [["404"]]
