"""nginx's own error answers on the API host are readable cross-origin.

The page on privatools.me reads api.privatools.me cross-origin. The app puts
CORS headers on its answers, but some answers come from nginx itself: 413 when
an upload passes client_max_body_size, 502 when the app is down, 504 when it
says nothing for proxy_read_timeout, and 503 from limit_req and limit_conn.
Those carried no CORS headers, so the page could read neither their status nor
their text, reported a network failure and sent the upload again.

Config-level like test_nginx_country_boundary.py: this does not run nginx.
The PR that added it ran the same file in nginx 1.18 against a stub upstream
(deploy/api-subdomain-split.md records how).
"""

from __future__ import annotations

import json
import re

from .test_nginx_country_boundary import ORACLE, ROOT, direct, named, parse_config, walk

NGINX_ERRORS = {"413", "502", "503", "504"}


def _nodes():
    return parse_config(ORACLE)


def _api_server(nodes):
    return next(
        server for server in named(nodes, "server")
        if ["443", "ssl", "http2"] in direct(server, "listen")
        and ["api.privatools.me"] in direct(server, "server_name")
    )


def _maps(nodes) -> dict:
    return {item.args[1]: item for item in named(nodes, "map")}


def _add_headers(node) -> dict[str, list[str]]:
    return {args[0]: args[1:] for args in direct(node, "add_header")}


def _allowed_origins() -> list[str]:
    compose = (ROOT / "docker-compose.yml").read_text()
    return re.search(r"ALLOWED_ORIGINS=(\S+)", compose).group(1).split(",")


def test_the_origin_map_names_exactly_the_origins_the_app_allows():
    maps = _maps(_nodes())
    origin = maps["$pt_cors_origin"]
    assert origin.args[0] == "$http_origin"
    entries = {item.name: item.args for item in origin.children}
    assert entries.pop("default") == [""], "an origin not listed gets no CORS header"
    # Each allowed origin maps to itself as written here, never to the
    # request's own Origin header echoed back.
    assert entries == {site: [site] for site in _allowed_origins()}
    vary = maps["$pt_cors_vary"]
    assert vary.args[0] == "$pt_cors_origin"
    assert {item.name: item.args for item in vary.children} == {"": [""], "default": ["Origin"]}


def test_nginx_error_answers_on_the_api_host_carry_cors_for_allowed_origins():
    server = _api_server(_nodes())
    api = next(location for location in named(server.children, "location") if location.args == ["/api/"])
    pages = {args[0]: args[1] for args in direct(api, "error_page")}
    assert set(pages) == NGINX_ERRORS
    answers = {location.args[0]: location for location in named(server.children, "location")
               if location.args[0].startswith("@")}
    server_headers = _add_headers(server)
    assert "Strict-Transport-Security" in server_headers
    limit = direct(server, "client_max_body_size")[0][0]
    assert limit == "500M"
    for status, target in pages.items():
        answer = answers[target]
        headers = _add_headers(answer)
        assert headers["Access-Control-Allow-Origin"] == ["$pt_cors_origin", "always"]
        assert headers["Vary"] == ["$pt_cors_vary", "always"]
        # A location with its own add_header inherits none of the server's,
        # so each of those must be declared here again.
        for name, value in server_headers.items():
            assert headers.get(name) == value, f"{target} drops the server's {name}"
        assert direct(answer, "default_type") == [["application/json"]]
        (answer_return,) = direct(answer, "return")
        assert answer_return[0] == status
        detail = json.loads(answer_return[1])["detail"]
        assert detail.endswith(".") and len(detail) > 20
        if status == "413":
            assert "500 MB" in detail


def test_answers_from_the_app_pass_through_with_its_own_cors_headers():
    # The app already sends Access-Control-Allow-Origin. nginx adding one too
    # would give an answer two, and a browser refuses that answer outright.
    nodes = _nodes()
    for server in named(nodes, "server"):
        assert not [name for name in _add_headers(server) if name.lower().startswith("access-control-")]
        for location in named(server.children, "location"):
            if not direct(location, "proxy_pass"):
                continue
            assert not [name for name in _add_headers(location) if name.lower().startswith("access-control-")]
    # error_page applies to the app's own 413/502/503/504 only if nginx
    # intercepts them; it must not, or their JSON and CORS headers would be lost.
    assert not [item for item in walk(nodes) if item.name == "proxy_intercept_errors" and item.args != ["off"]]
