"""Pages a tool removes must be gone from the file, and what stays must work.

Delete Pages took a page out of the page tree and saved, but qpdf writes every
object reachable from the trailer. A bookmark, a link, a named destination,
the structure tree, a form field, an article thread or the open action that
still pointed at the page kept it in the output, with its text and images.
Measured on main before the fix, with the fixtures in page_reference_pdfs.py:
every one of the 14 reference kinds kept a deleted page in the file.

The tools that copy some pages into a new document (Organize, Extract, Split
in every mode, Merge with page ranges) never carried a left-out page itself,
because qpdf replaces references to pages it was not asked to copy with null.
They did carry what belonged to it: its widget of a form field spanning pages,
the comment a reply on a kept page answers, its bead of an article thread, and
for Extract and Merge its structure elements with their /ActualText and /Alt.
Links to it stayed too, leading nowhere. Remove Blank Pages, which copied the
kept pages into a new PyMuPDF document, pulled a removed page back in whole
through a form field.
"""

from __future__ import annotations

import io
import json
import logging
import re
import time
import zipfile
from pathlib import Path

import pikepdf
import pytest

from backend.tests.page_reference_pdfs import (
    CATALOG_LISTED,
    CRAFTED,
    DAMAGED_TREES,
    KINDS,
    MALFORMED,
    MISPLACED_TREES,
    PROTECTED,
    build_catalog_listed_pdf,
    build_crafted_pdf,
    build_damaged_tree_pdf,
    build_dense_tagged_pdf,
    build_direct_page_tree_pdf,
    build_malformed_pdf,
    build_protected_pdf,
    build_reference_pdf,
    build_shared_chain_pages_pdf,
    build_shared_objects_pdf,
    build_tagged_link_pdf,
    page_texts,
    form_fields,
    leaked_pages,
    links,
    named_destinations,
    outline,
    page_numbers,
    qpdf_check_passes,
    structure_problems,
    threads,
    tree_items,
)

# The copying tools have never carried /AcroForm, so pikepdf warns on save that
# the copied widgets are unreachable from it. True on main too; not this change.
pytestmark = pytest.mark.filterwarnings("ignore::pikepdf.PageCopyWarning")

EVERY_KIND = "every kind"

# tool: (route, form, kinds it needs, blank pages, source pages of each output)
TOOLS = {
    "delete-pages": ("/api/delete-pages", {"pages": "2"}, (), (), [[1, 3, 4]]),
    "organize-pages": ("/api/organize-pages", {"page_order": "[4,1,3]"}, (), (), [[4, 1, 3]]),
    "extract-pages": ("/api/extract-pages", {"pages": "1,3-4"}, (), (), [[1, 3, 4]]),
    "split-pages": ("/api/split", {"mode": "pages", "pages": "1,3-4"}, (), (), [[1, 3, 4]]),
    "split-individual": ("/api/split", {"mode": "individual"}, (), (), [[1], [2], [3], [4]]),
    "split-every-n": ("/api/split", {"mode": "every_n", "n": "3"}, (), (), [[1, 2, 3], [4]]),
    "split-by-bookmarks": (
        "/api/split-by-bookmarks", {}, ("outline_dest",), (), [[1], [2], [3], [4]]),
    # One-byte parts: the chunking decides the split, the pages cover 1-4.
    "split-by-size": ("/api/split-by-size", {"max_size_mb": "0.000001"}, (), (), None),
    "split-by-text": ("/api/split-by-text", {"search": "PRIVA-P3-"}, (), (), [[1, 2], [3, 4]]),
    "merge-with-ranges": ("/api/merge", {"page_ranges": json.dumps(["1,3-4", "1"])}, (), (),
                          [[1, 3, 4, 1]]),
    "remove-blank-pages": ("/api/remove-blank-pages", {"sensitivity": "85"}, (), (2,), [[1, 3, 4]]),
    # Removes nothing: every page comes out twice, halved. Checked all the same.
    "split-in-half": ("/api/split-in-half", {"direction": "vertical"}, (), (),
                      [[1, 1, 2, 2, 3, 3, 4, 4]]),
}


@pytest.fixture(scope="module")
def reference_pdf():
    cache: dict = {}

    def build(kinds, blank=()):
        key = (tuple(sorted(kinds)), tuple(blank))
        if key not in cache:
            cache[key] = build_reference_pdf(kinds, blank=blank)
        return cache[key]

    return build


def _upload(data: bytes, name: str = "in.pdf"):
    return (name, data, "application/pdf")


def _outputs(resp) -> list[bytes]:
    assert resp.status_code == 200, resp.text[:300]
    if resp.content[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(resp.content)) as zf:
            return [zf.read(name) for name in sorted(zf.namelist()) if name.endswith(".pdf")]
    return [resp.content]


def _run(client, reference_pdf, tool: str, kinds) -> list[bytes]:
    route, form, needs, blank, _ = TOOLS[tool]
    data = reference_pdf(set(kinds) | set(needs), blank)
    if tool == "merge-with-ranges":
        files = [("files", _upload(data, "a.pdf")), ("files", _upload(data, "b.pdf"))]
    else:
        files = {"file": _upload(data)}
    return _outputs(client.post(route, files=files, data=form))


def _numbers(data: bytes) -> list[int]:
    with pikepdf.open(io.BytesIO(data)) as pdf:
        return page_numbers(pdf)


# ── nothing of a removed page may stay ──────────────────────────────────────


@pytest.mark.parametrize("kind", [EVERY_KIND, *KINDS])
@pytest.mark.parametrize("tool", list(TOOLS))
def test_nothing_of_a_removed_page_stays_in_the_file(client, reference_pdf, tool, kind):
    outputs = _run(client, reference_pdf, tool, KINDS if kind == EVERY_KIND else [kind])

    expected = TOOLS[tool][4]
    pages = [_numbers(data) for data in outputs]
    if expected is None:
        assert [n for part in pages for n in part] == [1, 2, 3, 4]
        assert len(pages) > 1
    else:
        assert pages == expected
    for part, data in zip(pages, outputs):
        leaked = leaked_pages(data)
        assert not leaked, (
            f"{tool} output with pages {part} still holds objects of removed "
            f"pages {sorted(leaked)} through {kind}"
        )


@pytest.mark.parametrize("tool", list(TOOLS))
def test_every_output_passes_qpdf_check(client, reference_pdf, tool, tmp_path):
    for i, data in enumerate(_run(client, reference_pdf, tool, KINDS)):
        path = tmp_path / f"{tool}-{i}.pdf"
        path.write_bytes(data)
        assert qpdf_check_passes(path), f"qpdf --check failed on {tool} output {i}"


# ── what stays keeps working ────────────────────────────────────────────────


def _delete(client, reference_pdf, pages: str, kinds=KINDS) -> pikepdf.Pdf:
    resp = client.post(
        "/api/delete-pages", files={"file": _upload(reference_pdf(kinds))}, data={"pages": pages},
    )
    return pikepdf.open(io.BytesIO(_outputs(resp)[0]))


def test_bookmarks_to_remaining_pages_stay_and_children_move_up(client, reference_pdf):
    with _delete(client, reference_pdf, "2") as pdf:
        assert page_numbers(pdf) == [1, 3, 4]
        per_page = [
            (0, f"PRIVA-P{n}-{what}", n)
            for n in (1, 3, 4)
            for what in ("OUTLINE", "OUTLINE-GOTO", "OUTLINE-LEGACY", "OUTLINE-NAMED")
        ]
        assert outline(pdf) == per_page + [
            # The chapter on page 2 went; its sections took its place.
            (0, "PRIVA-P3-CHILD", 3),
            (1, "PRIVA-P4-GRANDCHILD", 4),
            (0, "PRIVA-P1-CHILD", 1),
            # The heading over page 2 alone went with it; the closed bookmark
            # lost its only child and its /Count.
            (0, "PRIVA-P3-CLOSED", 3),
        ]


def test_bookmarks_keep_counts_when_their_children_are_removed(client, reference_pdf):
    with _delete(client, reference_pdf, "1,4") as pdf:
        assert page_numbers(pdf) == [2, 3]
        nested = [entry for entry in outline(pdf) if "OUTLINE" not in entry[1]]
        assert nested == [
            (0, "PRIVA-P2-PARENT", 2),
            (1, "PRIVA-P3-CHILD", 3),
            (0, "PRIVA-P2-HEADING", None),
            (1, "PRIVA-P2-HEADING-CHILD", 2),
            (0, "PRIVA-P3-CLOSED", 3),
            (1, "PRIVA-P2-HIDDEN", 2),
        ]
        closed = [i for i in _items(pdf.Root.Outlines) if str(i.Title) == "PRIVA-P3-CLOSED"]
        assert closed[0].Count == -1, "a closed bookmark must stay closed"


def _items(root):
    item = root.get("/First")
    while item is not None:
        yield item
        item = item.get("/Next")


def test_links_and_named_destinations_to_remaining_pages_still_resolve(client, reference_pdf):
    with _delete(client, reference_pdf, "2") as pdf:
        # Page 1's three links to page 2 are gone; its "back to top" link stays.
        assert links(pdf) == [
            (1, 1),
            (3, 4), (3, 4), (3, 4), (3, None), (3, 3),
            (4, 1), (4, 1), (4, 1), (4, 4),
        ]
        assert named_destinations(pdf) == {
            "PRIVA-P1-NAMED": 1, "PRIVA-P3-NAMED": 3, "PRIVA-P4-NAMED": 4,
            "/PRIVA-P1-LEGACY": 1, "/PRIVA-P3-LEGACY": 3, "/PRIVA-P4-LEGACY": 4,
        }
        assert "/OpenAction" not in pdf.Root  # it opened the deleted page
        web_link = [
            a for a in pdf.pages[1].obj.Annots if str(a.get("/Contents")) == "PRIVA-P3-WEBLINK"
        ]
        assert web_link[0].A.URI == "https://example.com/", "the web link must stay"
        assert "/Next" not in web_link[0].A, "its jump to the deleted page must not"
        reply = [a for a in pdf.pages[0].obj.Annots if str(a.get("/Contents")) == "PRIVA-P1-REPLY"]
        assert reply and "/IRT" not in reply[0], "a reply stays, without its deleted parent"


def test_form_fields_keep_their_widgets_on_remaining_pages(client, reference_pdf):
    with _delete(client, reference_pdf, "2") as pdf:
        assert form_fields(pdf) == {
            "PRIVA-P1-FIELD": [1], "PRIVA-P3-FIELD": [3], "PRIVA-P4-FIELD": [4],
            "shared": [1],
        }
        assert [str(f.T) for f in pdf.Root.AcroForm.CO] == ["PRIVA-P1-FIELD"]


def test_article_threads_keep_their_remaining_beads(client, reference_pdf):
    with _delete(client, reference_pdf, "2") as pdf:
        assert threads(pdf) == [[1, 3, 4]]  # the article only on page 2 went


def test_a_tagged_pdf_stays_tagged_with_a_consistent_tree(client, reference_pdf):
    with _delete(client, reference_pdf, "2") as pdf:
        assert structure_problems(pdf) == []
        root = pdf.Root.StructTreeRoot
        texts = sorted(str(label) for _, label in _walk_elements(root) if label is not None)
        assert texts == sorted(
            [f"PRIVA-P{n}-{w}" for n in (1, 3, 4) for w in ("STRUCT", "ALT", "LINKELEM")]
        )
        span = [e for e, _ in _walk_elements(root) if e.S == "/Span"]
        assert len(span) == 1, "the span continuing on page 3 must survive"
        assert "/Pg" not in span[0], "without claiming the deleted page"


def _walk_elements(node, depth=0):
    kids = node.get("/K")
    for kid in (kids if isinstance(kids, pikepdf.Array) else [kids] if kids is not None else []):
        if isinstance(kid, pikepdf.Dictionary) and "/S" in kid:
            yield kid, kid.get("/ActualText", kid.get("/Alt"))
            if depth < 32:
                yield from _walk_elements(kid, depth + 1)


@pytest.mark.parametrize("pages", ["1", "2", "3", "4", "1,4", "2-3", "1-3"])
def test_what_remains_is_consistent_whatever_is_deleted(client, reference_pdf, pages):
    with _delete(client, reference_pdf, pages) as pdf:
        present = set(page_numbers(pdf))
        outline(pdf)  # asserts the outline is well formed
        assert all(target is None or target in present for _, _, target in outline(pdf))
        assert all(target is None or target in present for _, target in links(pdf))
        assert all(page in present for page in named_destinations(pdf).values())
        assert all(set(pages_) <= present for pages_ in form_fields(pdf).values())
        assert all(set(ring) <= present for ring in threads(pdf))
        assert structure_problems(pdf) == []


# ── the copying tools ───────────────────────────────────────────────────────


def test_extract_keeps_a_consistent_structure_tree_and_working_links(client, reference_pdf):
    [data] = _run(client, reference_pdf, "extract-pages", KINDS)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert page_numbers(pdf) == [1, 3, 4]
        assert structure_problems(pdf) == []
        # Named destinations stay in the source; the links that used them
        # now point straight at their page, or are gone with it.
        assert links(pdf) == [
            (1, 1),
            (3, 4), (3, 4), (3, 4), (3, None), (3, 3),
            (4, 1), (4, 1), (4, 1), (4, 4),
        ]


def test_organize_keeps_links_pointing_at_the_right_pages(client, reference_pdf):
    [data] = _run(client, reference_pdf, "organize-pages", KINDS)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert page_numbers(pdf) == [4, 1, 3]
        assert links(pdf) == [
            (4, 1), (4, 1), (4, 1), (4, 4),
            (1, 1),
            (3, 4), (3, 4), (3, 4), (3, None), (3, 3),
        ]


def test_merge_with_ranges_prunes_the_structure_of_pages_left_out(client, reference_pdf):
    [data] = _run(client, reference_pdf, "merge-with-ranges", KINDS)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert page_numbers(pdf) == [1, 3, 4, 1]
        root = pdf.Root.StructTreeRoot
        keys = [int(key) for key, _ in tree_items(root.ParentTree, "/Nums")]
        # First file: pages 1, 3, 4 and their links. Second file, its keys
        # shifted by 1005: page 1 and its link. Nothing of any page left out.
        assert keys == [0, 2, 3, 1001, 1003, 1004, 1005, 2006]
        # StructureTreeMerger shifts the second file's page keys but not its
        # annotations' /StructParent, so that link still says 1001 and 2006
        # is unused. That predates this change and happens without ranges
        # too; everything else about the tree must hold.
        problems = [
            p for p in structure_problems(pdf)
            if p not in ("annotation key 1001 does not lead to its element",
                         "ParentTree key 2006 belongs to nothing in the output")
        ]
        assert problems == []


def test_remove_blank_pages_keeps_bookmarks_and_fields_of_the_other_pages(client, reference_pdf):
    [data] = _run(client, reference_pdf, "remove-blank-pages", KINDS)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert page_numbers(pdf) == [1, 3, 4]
        assert {title for _, title, _ in outline(pdf)} >= {"PRIVA-P1-OUTLINE", "PRIVA-P4-OUTLINE"}
        assert form_fields(pdf)["shared"] == [1]
        assert structure_problems(pdf) == []


# ── the utility on its own ──────────────────────────────────────────────────


def _open(data: bytes) -> pikepdf.Pdf:
    return pikepdf.open(io.BytesIO(data))


def _save(pdf: pikepdf.Pdf) -> bytes:
    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def _budget(size: int = 0):
    """A request's work budget for ``size`` bytes uploaded: the floor alone
    covers the small fixtures."""
    from backend.app.utils.page_removal import WorkBudget

    return WorkBudget("test", size)


def test_removing_nothing_changes_nothing(client, reference_pdf):
    from backend.app.utils.page_removal import remove_pages

    data = reference_pdf(KINDS)
    with _open(data) as before, _open(data) as pdf:
        remove_pages(pdf, [], budget=_budget())
        after = _open(_save(pdf))
        for view in (outline, links, named_destinations, form_fields, threads):
            assert view(after) == view(before), view.__name__
        assert structure_problems(after) == []
        # Copying every page prunes too; nothing may break there either.
        resp = client.post(
            "/api/extract-pages", files={"file": _upload(data)}, data={"pages": "1-4"},
        )
        [copied] = _outputs(resp)
        with _open(copied) as out:
            assert links(out) == links(before)
            assert structure_problems(out) == []


def test_a_file_an_earlier_version_left_pages_in_is_cleaned(reference_pdf):
    """Outputs of the old Delete Pages still hold their deleted pages; the
    next tool that removes pages from such a file must not pass them on."""
    from backend.app.utils.page_removal import remove_pages

    with _open(reference_pdf(["link_dest", "outline_dest"])) as pdf:
        del pdf.pages[1]  # what Delete Pages used to do
        damaged = _save(pdf)
    assert leaked_pages(damaged) == {2}
    with _open(damaged) as pdf:
        remove_pages(pdf, [2], budget=_budget())  # now remove source page 4
        cleaned = _save(pdf)
    assert _numbers(cleaned) == [1, 3]
    assert leaked_pages(cleaned) == set()


def test_everything_tagged_on_removed_pages_leaves_an_honest_untagged_file():
    from backend.app.utils.page_removal import remove_pages

    data = build_reference_pdf(["struct_tree"], pages=2)
    with _open(data) as pdf:
        # Keep only page 1's section in the tree, so every element is on the
        # page removed next.
        root = pdf.Root.StructTreeRoot
        document = root.K[0]
        document.K = pikepdf.Array([document.K[0]])
        remove_pages(pdf, [0], budget=_budget())
        out = _open(_save(pdf))
    assert "/StructTreeRoot" not in out.Root
    mark = out.Root.get("/MarkInfo")
    assert not (mark is not None and mark.get("/Marked")), "must not claim to be tagged"


def test_a_nested_parent_tree_is_pruned_and_its_limits_fixed(reference_pdf):
    from backend.app.utils.page_removal import remove_pages

    with _open(reference_pdf(["struct_tree"])) as pdf:
        root = pdf.Root.StructTreeRoot
        nums = [x for x in root.ParentTree.Nums]
        pairs = [nums[i:i + 2] for i in range(0, len(nums), 2)]
        kids = []
        for chunk in (pairs[:2], pairs[2:]):
            flat = [x for pair in chunk for x in pair]
            kids.append(pdf.make_indirect(pikepdf.Dictionary(
                Nums=pikepdf.Array(flat), Limits=pikepdf.Array([chunk[0][0], chunk[-1][0]]))))
        root.ParentTree = pdf.make_indirect(pikepdf.Dictionary(Kids=pikepdf.Array(kids)))
        remove_pages(pdf, [1], budget=_budget())
        data = _save(pdf)
    assert leaked_pages(data) == set()
    with _open(data) as out:
        assert structure_problems(out) == []
        first = out.Root.StructTreeRoot.ParentTree.Kids[0]
        keys = [int(x) for i, x in enumerate(first.Nums) if i % 2 == 0]
        assert keys == [0], "page 2's entry must go from the first leaf"
        assert [int(x) for x in first.Limits] == [0, 0]


def test_a_looping_outline_does_not_hang(reference_pdf):
    from backend.app.utils.page_removal import remove_pages

    with _open(reference_pdf(["outline_dest"])) as pdf:
        last = pdf.Root.Outlines.Last
        last.Next = pdf.Root.Outlines.First  # malformed: the list loops
        remove_pages(pdf, [1], budget=_budget())
        data = _save(pdf)
    assert leaked_pages(data) == set()


def test_xfa_goes_when_fields_are_removed_and_stays_otherwise(reference_pdf):
    from backend.app.utils.page_removal import remove_pages

    data = reference_pdf(["acroform"])
    with _open(data) as pdf:
        pdf.Root.AcroForm.XFA = pdf.make_stream(b"<xdp:xdp>PRIVA-P2-XFA</xdp:xdp>")
        with_xfa = _save(pdf)
    with _open(with_xfa) as pdf:
        remove_pages(pdf, [1], budget=_budget())
        assert "/XFA" not in pdf.Root.AcroForm, "XFA holds the removed fields' values"
        assert leaked_pages(_save(pdf)) == set()
    with _open(with_xfa) as pdf:
        remove_pages(pdf, [], budget=_budget())
        assert "/XFA" in pdf.Root.AcroForm


def test_template_pages_are_left_alone(reference_pdf):
    from backend.app.utils.page_removal import remove_pages

    with _open(reference_pdf(["outline_dest"])) as pdf:
        template = pdf.make_indirect(pikepdf.Dictionary(
            Type=pikepdf.Name.Page, MediaBox=pikepdf.Array([0, 0, 10, 10]),
            Contents=pdf.make_stream(b"% template"),
        ))
        pdf.Root.Names = pikepdf.Dictionary(Templates=pikepdf.Dictionary(
            Names=pikepdf.Array([pikepdf.String("form-page"), template])))
        remove_pages(pdf, [1], budget=_budget())
        out = _open(_save(pdf))
    names = out.Root.Names.Templates.Names
    assert str(names[0]) == "form-page" and names[1].get("/Type") == "/Page"


# ── review round 1: hostile, damaged, malformed and crafted input ───────────


def _service(tool: str, path) -> list[bytes]:
    """Run a page service on ``path``; return each output PDF's bytes."""
    from backend.app.services import (
        delete_pages_service,
        extract_pages_service,
        merge_service,
        organize_pages_service,
        split_service,
    )

    run = {
        "delete": lambda: delete_pages_service.delete_pages(str(path), "2"),
        "extract": lambda: extract_pages_service.extract_pages(str(path), "1,3-end"),
        "organize": lambda: organize_pages_service.reorder_pages(str(path), [1, 3, 4]),
        "split": lambda: split_service.split_pdf(str(path), mode="individual"),
        "merge": lambda: merge_service.merge_pdfs([str(path), str(path)], ["1,3-4", "1"]),
    }[tool]
    out = Path(run())
    data = out.read_bytes()
    out.unlink()
    if data[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(data)) as zf:
            return [zf.read(name) for name in sorted(zf.namelist()) if name.endswith(".pdf")]
    return [data]


def _stray_pages(data: bytes) -> int:
    with pikepdf.open(io.BytesIO(data)) as pdf:
        listed = {page.obj.objgen for page in pdf.pages}
        return sum(
            1 for obj in pdf.objects
            if isinstance(obj, (pikepdf.Dictionary, pikepdf.Stream))
            and obj.get("/Type") == pikepdf.Name.Page and obj.objgen not in listed
        )


@pytest.mark.parametrize("kind, tool, n", [
    ("shared_action", "delete", 3000),
    ("shared_action", "extract", 3000),
    ("shared_outline", "delete", 3000),
    ("shared_ring", "delete", 4000),
    ("stray_headings", "delete", 40),
    ("stray_headings", "extract", 40),
    ("stray_list", "delete", 3000),
    ("shared_annots", "extract", 2000),
    ("shared_beads", "delete", 3000),
    ("shared_kids", "delete", 2000),
    ("shared_field_kids", "delete", 3000),
    ("shared_hide_list", "delete", 2000),
    ("shared_field_list", "delete", 2000),
    ("shared_next_list", "delete", 2000),
    ("shared_next_list", "extract", 2000),
    ("shared_next_dead", "delete", 2000),
    ("shared_triggers", "delete", 2000),
    ("shared_triggers", "extract", 2000),
    ("long_named_view", "extract", 4000),
])
def test_an_object_shared_by_many_owners_is_read_once(kind, tool, n, tmp_path):
    """One action chain shared by every link, one bead ring shared by every
    thread, one array shared by every page, element, field or action, one
    /AA dictionary shared by every link, one list of bookmarks shared by
    every heading, one named view named by every link: each was read, and
    often copied, again for each owner, n*n (n**3 for dead actions sharing
    their successors), and nested headings once per path, 2**n. At these
    sizes the pruning took from 8 s to hours of CPU, and the copies made
    outputs about 70 times the input; read once, it takes under 0.5 s. Only
    the pruning is timed: saving is qpdf's and pikepdf's work, and pikepdf's
    own save is slow on fields that share their kids. The bound is loose on
    purpose, so a loaded CI runner cannot flake it."""
    from backend.app.utils.page_removal import copy_pages, prune_to_page_tree, remove_pages

    out = tmp_path / "out.pdf"
    source = build_shared_objects_pdf(kind, n)
    budget = _budget(len(source))
    with pikepdf.open(io.BytesIO(source)) as pdf:
        start = time.process_time()
        if tool == "delete":
            removal = remove_pages(pdf, [1], budget=budget)
        else:  # Extract every page but page 2
            copy = pikepdf.new()
            copy_pages(copy, pdf, [i for i in range(len(pdf.pages)) if i != 1], budget=budget)
            removal = prune_to_page_tree(copy, budget=budget)
        cpu = time.process_time() - start
        assert cpu < 3, f"{kind} with {n} owners took {cpu:.1f} s of CPU"
        removal.save(out)
    assert out.stat().st_size < 2 * len(source), "the output grew with the owners"
    assert not leaked_pages(out.read_bytes())


@pytest.mark.parametrize("damage", DAMAGED_TREES)
def test_remove_blank_pages_on_a_damaged_page_tree_keeps_every_page_with_content(client, damage):
    """MuPDF finds the blank pages and qpdf removes them, and on a damaged page
    tree the two list different pages. Matched by position, content pages went
    and the blank one stayed; matched by object, only the blank page goes."""
    resp = client.post(
        "/api/remove-blank-pages", files={"file": _upload(build_damaged_tree_pdf(damage))},
        data={"sensitivity": "85"},
    )
    assert resp.status_code == 200, resp.text
    assert page_texts(resp.content) == ["PAGE-1", "PAGE-2", "PAGE-4"]


def test_delete_pages_accepts_a_page_tree_whose_count_is_wrong(client):
    """qpdf refuses to remove a page when the root /Count disagrees with /Kids."""
    resp = client.post(
        "/api/delete-pages", files={"file": _upload(build_damaged_tree_pdf("count_small"))},
        data={"pages": "3"},
    )
    assert resp.status_code == 200, resp.text
    assert page_texts(resp.content) == ["PAGE-1", "PAGE-2", "PAGE-4"]


@pytest.mark.parametrize("tool", ["delete", "extract", "organize"])
@pytest.mark.parametrize("name", MALFORMED)
def test_a_malformed_value_neither_fails_the_tool_nor_keeps_a_removed_page(name, tool, tmp_path):
    path = tmp_path / "malformed.pdf"
    path.write_bytes(build_malformed_pdf(name))
    for data in _service(tool, path):
        assert not leaked_pages(data), f"{tool} kept page 2 of {name}"


@pytest.mark.parametrize("tool", ["delete", "extract", "organize"])
@pytest.mark.parametrize("name", MISPLACED_TREES)
def test_a_page_tree_where_a_name_tree_belongs_keeps_its_pages(name, tool, tmp_path):
    """The name tree pass must not prune the page tree, or the catalog, as
    if it were a name tree: that emptied the page tree's /Kids."""
    path = tmp_path / "misplaced.pdf"
    path.write_bytes(build_malformed_pdf(name))
    [data] = _service(tool, path)
    assert _numbers(data) == [1, 3, 4]
    assert _stray_pages(data) == 0


@pytest.mark.parametrize("tool", ["delete", "extract", "organize", "split", "merge"])
@pytest.mark.parametrize("name", CRAFTED)
def test_a_crafted_reference_to_a_removed_page_does_not_keep_it(name, tool, tmp_path):
    path = tmp_path / "crafted.pdf"
    path.write_bytes(build_crafted_pdf(name))
    for data in _service(tool, path):
        assert not leaked_pages(data), f"{tool} kept objects of page 2 through {name}"
        assert _stray_pages(data) == 0


@pytest.mark.parametrize("tool", ["delete", "extract", "organize"])
@pytest.mark.parametrize("name", PROTECTED)
def test_the_catalog_the_page_tree_and_kept_pages_are_never_cut(name, tool, tmp_path):
    """Listed among page 2's annotations or beads, or dressed up as a dead link
    or an element of page 2, page 3, the page tree or the catalog was cut:
    Delete Pages lost page 3, or wrote a file without a page tree or catalog,
    and Extract and Organize lost page 3 when it posed as a dead link."""
    path = tmp_path / "protected.pdf"
    path.write_bytes(build_protected_pdf(name))
    [data] = _service(tool, path)
    assert _numbers(data) == [1, 3, 4]
    assert _stray_pages(data) == 0
    assert not leaked_pages(data)
    checked = tmp_path / "out.pdf"
    checked.write_bytes(data)
    assert qpdf_check_passes(checked)


@pytest.mark.parametrize("name", CATALOG_LISTED)
def test_the_outline_or_form_listed_among_a_removed_pages_annotations_stays(name, tmp_path):
    """Listed among page 2's annotations, the outline root or the form went
    as page 2's annotation, and every bookmark or field with it. Neither
    looks like an annotation, so Delete Pages keeps what it keeps without
    the listing. (A form that does look like one goes: see CRAFTED.)"""
    listed, plain = tmp_path / "listed.pdf", tmp_path / "plain.pdf"
    listed.write_bytes(build_catalog_listed_pdf(name))
    plain.write_bytes(build_catalog_listed_pdf(name, listed=False))
    [data] = _service("delete", listed)
    [expected] = _service("delete", plain)
    with _open(data) as pdf, _open(expected) as want:
        kept = (outline(pdf), form_fields(pdf))
        assert kept == (outline(want), form_fields(want))
        assert kept[0] or kept[1]
    assert not leaked_pages(data)


@pytest.mark.parametrize("tool, pages", [
    ("delete", [[1, 3, 4]]), ("extract", [[1, 3, 4]]), ("organize", [[1, 3, 4]]),
    ("split", [[1], [2], [3], [4]]), ("merge", [[1, 3, 4, 1]]),
])
def test_a_page_tree_root_written_into_the_catalog_is_read(tool, pages, tmp_path):
    """The specification wants the page tree's root indirect, but qpdf reads
    one written into the catalog, and the check after saving refused it."""
    path = tmp_path / "direct.pdf"
    path.write_bytes(build_direct_page_tree_pdf())
    with pikepdf.open(path) as pdf:
        assert not pdf.Root.Pages.is_indirect
    outputs = _service(tool, path)
    assert [_numbers(data) for data in outputs] == pages
    assert not any(leaked_pages(data) for data in outputs)


def _cutting_sweep(monkeypatch, cut):
    """Make the sweep damage the page tree after doing its work, as a bug would."""
    from backend.app.utils import page_removal

    sweep = page_removal._Pruner.sweep

    def cutting(self, exhaustive=False):
        sweep(self, exhaustive)
        cut(self.pdf)

    monkeypatch.setattr(page_removal._Pruner, "sweep", cutting)


def _cut_the_page_tree(pdf):
    del pdf.Root["/Pages"]


def _cut_a_kept_page(pdf):
    kids = pdf.Root.Pages.Kids
    page = kids[1]
    pdf.Root.Pages.Kids = pikepdf.Array([kids[0], kids[2]])
    pdf.Root.Pages.Count = 2
    pdf.pages[0].obj.PieceInfo = pikepdf.Dictionary(PrivaApp=pikepdf.Dictionary(
        LastModified=pikepdf.String("D:20260924"),
        Private=pikepdf.Dictionary(Page=page)))  # still written


@pytest.mark.parametrize("cut, reason", [
    (_cut_the_page_tree, "the output has no page tree"),
    (_cut_a_kept_page, "the page tree lists 2 pages, 3 expected"),
])
def test_an_output_whose_page_tree_is_not_the_one_kept_is_refused(client, monkeypatch, caplog, cut, reason):
    """The check reads the pages from the tree the save wrote, not from qpdf's
    list of pages, which a cut in /Kids or in the catalog does not change: an
    output that no reader could open, or that lost a kept page, was returned
    as a success. It is refused, and the refusal is logged with the tool and
    the reason, and no document text."""
    from backend.app.utils import cleanup

    _cutting_sweep(monkeypatch, cut)
    before = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    with caplog.at_level(logging.ERROR, logger="backend.app.utils.page_removal"):
        resp = client.post(
            "/api/delete-pages", files={"file": _upload(build_reference_pdf(["piece_info"]))},
            data={"pages": "2"},
        )
    assert resp.status_code == 422
    assert "could not be removed completely" in resp.json()["detail"]
    refusals = [r.getMessage() for r in caplog.records if "refused the output" in r.getMessage()]
    assert refusals == [f"page removal refused the output of delete-pages: {reason}"]
    after = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    assert after <= before, f"left behind: {sorted(str(p) for p in after - before)}"


def test_an_element_the_tree_pass_leaves_to_the_sweep_is_swept(tmp_path, caplog):
    """A section reached only through elements the tree pass read in full is
    still read by the sweep, so the check after saving has nothing to find."""
    pdf = pikepdf.open(io.BytesIO(build_reference_pdf(("struct_tree",))))
    pdf.Root.StructTreeRoot.K[0].K[0].PrivaData = pdf.pages[1].obj  # page 1's section
    path = tmp_path / "element.pdf"
    pdf.save(path)
    with caplog.at_level(logging.WARNING, logger="backend.app.utils.page_removal"):
        [data] = _service("delete", path)
    assert not any("sweeping again" in record.getMessage() for record in caplog.records)
    assert _numbers(data) == [1, 3, 4]
    assert not leaked_pages(data)
    assert _stray_pages(data) == 0


def test_a_page_the_sweep_missed_is_caught_after_saving(tmp_path, caplog, monkeypatch):
    """If the sweep misses a reference, the check after saving finds the page
    it keeps, and a second sweep that skips nothing cuts it."""
    from backend.app.utils import page_removal

    sweep = page_removal._Pruner.sweep
    monkeypatch.setattr(
        page_removal._Pruner, "sweep",
        lambda self, exhaustive=False: sweep(self, exhaustive) if exhaustive else None,
    )
    path = tmp_path / "hidden.pdf"
    path.write_bytes(build_crafted_pdf("font_bbox_page"))
    with caplog.at_level(logging.WARNING, logger="backend.app.utils.page_removal"):
        [data] = _service("delete", path)
    assert any("sweeping again" in record.getMessage() for record in caplog.records)
    assert _numbers(data) == [1, 3, 4]
    assert not leaked_pages(data)
    assert _stray_pages(data) == 0


def test_an_output_that_would_keep_a_removed_page_is_refused(client, monkeypatch, caplog):
    """If even the second sweep cannot cut a removed page, no file is returned,
    and the refusal is logged with the tool and the reason."""
    from backend.app.utils import cleanup, page_removal

    monkeypatch.setattr(page_removal._Pruner, "sweep", lambda self, exhaustive=False: None)
    before = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    with caplog.at_level(logging.ERROR, logger="backend.app.utils.page_removal"):
        resp = client.post(
            "/api/delete-pages", files={"file": _upload(build_reference_pdf(["piece_info"]))},
            data={"pages": "2"},
        )
    assert resp.status_code == 422, resp.text
    assert "could not be removed completely" in resp.json()["detail"]
    refusals = [r.getMessage() for r in caplog.records if "refused the output" in r.getMessage()]
    assert refusals == [
        "page removal refused the output of delete-pages: "
        "1 page object(s) outside the page tree after a second sweep"
    ]
    after = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    assert after <= before, f"left behind: {sorted(str(p) for p in after - before)}"


# ── the work budget ─────────────────────────────────────────────────────────


def _budgets(monkeypatch) -> list:
    """Every work budget made from now on."""
    from backend.app.utils import page_removal

    made: list = []
    init = page_removal.WorkBudget.__init__

    def recording(self, tool, size):
        init(self, tool, size)
        made.append(self)

    monkeypatch.setattr(page_removal.WorkBudget, "__init__", recording)
    return made


@pytest.mark.parametrize("tool", sorted(set(TOOLS) - {"split-in-half"}))
def test_every_tool_stays_far_below_its_work_budget(client, reference_pdf, monkeypatch, tool):
    """A request has one budget, whatever the parts it writes, and may take
    _STEPS_PER_BYTE for each byte uploaded, or _STEPS_PER_OBJECT for each
    object it copies, if that is more. With every kind of reference in the
    file, no request takes a quarter of that: the limit is for files that
    make a pass read one object once per owner, not for any file a tool
    meets. (On real files, at most 0.08 steps per byte.)"""
    from backend.app.utils import page_removal

    made = _budgets(monkeypatch)
    _run(client, reference_pdf, tool, KINDS)
    assert len(made) == 1, "one budget per request"
    [budget] = made
    assert budget.used * 4 <= budget.limit - page_removal._STEPS_FLOOR, budget.tool


@pytest.mark.parametrize("route, form", [
    ("/api/delete-pages", {"pages": "2"}),
    ("/api/extract-pages", {"pages": "1,3-4"}),
    ("/api/split", {"mode": "individual"}),
])
def test_a_request_past_its_work_budget_is_refused(client, reference_pdf, monkeypatch, caplog, route, form):
    """Past its budget, a request stops wherever it is, and is refused like a
    leak: a 422 that says why, no file, and a log line with the tool and the
    budget, and no document text."""
    from backend.app.utils import cleanup, page_removal

    monkeypatch.setattr(page_removal, "_STEPS_FLOOR", 100)
    monkeypatch.setattr(page_removal, "_STEPS_PER_BYTE", 0)
    monkeypatch.setattr(page_removal, "_STEPS_PER_OBJECT", 0)
    before = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    with caplog.at_level(logging.ERROR, logger="backend.app.utils.page_removal"):
        resp = client.post(route, files={"file": _upload(reference_pdf(KINDS))}, data=form)
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"] == page_removal.PageWorkError.default_detail
    refusals = [r.getMessage() for r in caplog.records if "refused the output" in r.getMessage()]
    tool = {"/api/delete-pages": "delete-pages", "/api/extract-pages": "extract-pages"}.get(route, "split")
    assert len(refusals) == 1
    assert re.fullmatch(
        rf"page removal refused the output of {tool}: its work passed \d+ steps, "
        r"allowed for \d+ bytes uploaded and \d+ objects copied",
        refusals[0],
    ), refusals
    after = set(cleanup.TEMP_DIR.iterdir()) if cleanup.TEMP_DIR.exists() else set()
    assert after <= before, f"left behind: {sorted(str(p) for p in after - before)}"


def test_a_shape_read_once_per_owner_is_stopped_by_the_work_budget(monkeypatch, tmp_path):
    """Each review of this module found another shape of shared objects that
    a pass read, or copied, once per owner. As if one were still unknown, the
    pruner here decides a shared list again for each owner: 2,000 links whose
    Hide actions name one list of 2,000 notes took 10 s and made a 35 MB file
    that way. The budget stops the job after linear work, and refuses it.
    The allowance per byte is lowered to 2, so the test is quick: with the
    real 25, this 540 KB file fits in it (12 million steps, about 10 s), and
    the same shape is refused from about 2,500 owners."""
    from backend.app.utils import page_removal
    from backend.app.utils.page_removal import PageWorkError, remove_pages

    decide = page_removal._Pruner._shared_array

    def for_each_owner(self, array, keep):
        self._arrays.clear()
        return decide(self, array, keep)

    monkeypatch.setattr(page_removal._Pruner, "_shared_array", for_each_owner)
    monkeypatch.setattr(page_removal, "_STEPS_PER_BYTE", 2)
    out = tmp_path / "out.pdf"
    source = build_shared_objects_pdf("shared_hide_list", 2000)
    with pikepdf.open(io.BytesIO(source)) as pdf:
        start = time.process_time()
        with pytest.raises(PageWorkError):
            remove_pages(pdf, [1], budget=_budget(len(source))).save(out)
        cpu = time.process_time() - start
    assert not out.exists()
    assert cpu < 10, f"the budget stopped the job after {cpu:.1f} s of CPU"


def _walks_afresh(monkeypatch) -> None:
    """A walk nobody has found yet, as the backstop tests simulate one: every
    owner of a shared action walks its chain afresh, in the pruner and in
    the copier."""
    from backend.app.utils import page_removal

    prune = page_removal._Pruner.prune_action

    def prune_afresh(self, action, depth=0):
        if depth == 0:
            self._actions.clear()
            self._arrays.clear()
        return prune(self, action, depth)

    chain = page_removal._action_chain

    def chain_afresh(action, seen, depth=0):
        return chain(action, set() if depth == 0 else seen, depth)

    monkeypatch.setattr(page_removal._Pruner, "prune_action", prune_afresh)
    monkeypatch.setattr(page_removal, "_action_chain", chain_afresh)


@pytest.mark.parametrize("tool", ["split", "merge"])
def test_the_parts_of_a_request_share_one_work_budget(monkeypatch, tmp_path, tool):
    """Split prunes and saves a document per part, and Merge copies each
    source. With a budget per part, each got a floor of its own, and a walk
    that goes wrong once per owner ran 4 minutes on a 106 KB file without a
    refusal. A request's parts share one budget, whose floor counts once:
    here the floor alone, lowered so the test is quick. One job over the
    whole file fits in it; Split's 20 parts and Merge's 10 sources, each
    about as much work, do not together."""
    from backend.app.services import delete_pages_service, merge_service, split_service
    from backend.app.utils import page_removal

    _walks_afresh(monkeypatch)
    monkeypatch.setattr(page_removal, "_STEPS_FLOOR", 40_000)
    monkeypatch.setattr(page_removal, "_STEPS_PER_BYTE", 0)
    monkeypatch.setattr(page_removal, "_STEPS_PER_OBJECT", 0)
    path = tmp_path / "chain.pdf"
    path.write_bytes(build_shared_chain_pages_pdf(pages=20, links=60))
    made = _budgets(monkeypatch)
    Path(delete_pages_service.delete_pages(str(path), "2")).unlink()
    assert made[0].used * 3 < page_removal._STEPS_FLOOR, "one job fits in the floor"
    with pytest.raises(page_removal.PageWorkError):
        if tool == "split":
            split_service.split_pdf(str(path), mode="individual")
        else:
            merge_service.merge_pdfs([str(path)] * 10)
    assert len(made) == 2, "one budget per request"


def test_a_valid_file_dense_with_tags_is_not_refused(monkeypatch, tmp_path):
    """Word-level tags, as some OCR and tagging pipelines write them: 100
    marked-content ids to each paragraph, 10 paragraphs to a page. Pruning
    reads every id, about 230 steps per object of the file, so a budget
    sized by objects refused such a file from about 560 pages, where main
    returned one. Each id takes room in the file, and the budget is sized by
    the bytes uploaded: here 0.5 steps per byte. The floor is taken away, so
    20 pages stand for the 700 the review built."""
    from backend.app.utils import page_removal

    monkeypatch.setattr(page_removal, "_STEPS_FLOOR", 0)
    path = tmp_path / "dense.pdf"
    path.write_bytes(build_dense_tagged_pdf(pages=20, elements=10, mcids=100))
    made = _budgets(monkeypatch)
    for tool in ("delete", "extract", "merge"):
        for data in _service(tool, path):
            with pikepdf.open(io.BytesIO(data)) as pdf:
                assert "/StructTreeRoot" in pdf.Root, tool
            assert not leaked_pages(data), tool
    assert len(made) == 3
    for budget in made:
        assert budget.used * 10 < budget.limit, budget.tool


@pytest.mark.parametrize("tool", ["delete", "extract"])
def test_an_output_with_far_more_objects_than_its_input_is_refused(client, monkeypatch, caplog, tool):
    """Pruning removes objects, and the few it makes replace others. An
    output with more than twice its input's objects, and 10,000 more, is
    what a pass that makes objects by mistake would write: refused. A copy's
    objects are counted before it is pruned; a file pruned in place stands
    for no more objects than a quarter of its bytes."""
    from backend.app.utils import page_removal

    data = build_reference_pdf(["piece_info"])
    extra = 12_000 + len(data) // 2

    def add_objects(pdf):
        pdf.Root.PrivaJunk = pikepdf.Array([pdf.make_indirect(pikepdf.Dictionary()) for _ in range(extra)])

    _cutting_sweep(monkeypatch, add_objects)
    route, form, name = {
        "delete": ("/api/delete-pages", {"pages": "2"}, "delete-pages"),
        "extract": ("/api/extract-pages", {"pages": "1,3-4"}, "extract-pages"),
    }[tool]
    with caplog.at_level(logging.ERROR, logger="backend.app.utils.page_removal"):
        resp = client.post(route, files={"file": _upload(data)}, data=form)
    assert resp.status_code == 422, resp.text
    assert resp.json()["detail"] == page_removal.PageLeakError.default_detail
    refusals = [r.getMessage() for r in caplog.records if "refused the output" in r.getMessage()]
    assert len(refusals) == 1
    assert re.fullmatch(
        rf"page removal refused the output of {name}: "
        r"it holds \d+ objects, \d+ allowed for \d+ in its input",
        refusals[0],
    ), refusals


def test_a_request_budget_is_sized_by_the_upload_not_by_what_it_claims(monkeypatch, tmp_path):
    """The budget is the floor plus _STEPS_PER_BYTE for each byte uploaded,
    or _STEPS_PER_OBJECT for each object a copy holds before pruning, if
    that is more. A cross-reference table that claims 99,999,999 objects
    changes nothing: nothing counts the objects a file says it has."""
    from backend.app.utils import page_removal

    data = build_reference_pdf(())
    declared = re.search(rb"/Size (\d+)", data).group(0)
    claims = tmp_path / "claims.pdf"
    claims.write_bytes(data.replace(declared, b"/Size 99999999"))
    size = claims.stat().st_size
    made = _budgets(monkeypatch)
    _service("delete", claims)
    _service("extract", claims)
    delete, extract = made
    assert delete.limit == page_removal._STEPS_FLOOR + page_removal._STEPS_PER_BYTE * size
    assert extract.objects > 0
    assert extract.limit == page_removal._STEPS_FLOOR + max(
        page_removal._STEPS_PER_BYTE * size, page_removal._STEPS_PER_OBJECT * extract.objects,
    )


def test_a_tagged_link_to_a_removed_page_leaves_no_parent_tree_key(client):
    """The link goes with its target; its element stays for the link text, so
    the link's own ParentTree key has to be dropped explicitly, and the
    element's /Alt, which described the link to page 2, goes too."""
    resp = client.post(
        "/api/delete-pages", files={"file": _upload(build_tagged_link_pdf())},
        data={"pages": "2"},
    )
    [data] = _outputs(resp)
    assert not leaked_pages(data)
    with pikepdf.open(io.BytesIO(data)) as pdf:
        assert structure_problems(pdf) == []
        tree = pdf.Root.StructTreeRoot
        keys = [int(key) for key, _ in tree_items(tree.ParentTree, "/Nums")]
        assert 2000 not in keys
        text_links = [
            e for e, _ in _walk_elements(tree)
            if e.S == "/Link" and isinstance(e.get("/K"), pikepdf.Array) and list(e.K) == [2]
        ]
        assert len(text_links) == 1, "the link's element keeps its text and loses its OBJR"
        assert "/Alt" not in text_links[0]


def test_validation_errors_of_page_services_reach_the_user_as_400(client):
    """The page routes turned every service error into a bare 500."""
    data = build_reference_pdf(())
    resp = client.post("/api/delete-pages", files={"file": _upload(data)}, data={"pages": "1-4"})
    assert resp.status_code == 400, resp.text
    resp = client.post(
        "/api/split-by-text", files={"file": _upload(data)}, data={"search": "not in this file"},
    )
    assert resp.status_code == 400, resp.text
