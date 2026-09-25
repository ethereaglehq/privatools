"""PDFs whose pages are referenced from every place a PDF can point at a page.

Shared by the page-removal tests (Delete Pages and every tool that keeps a
subset of pages). A page leaves the page tree easily; what keeps it in the file
is everything else that still points at it: bookmarks, links, named
destinations, the structure tree, form fields, article threads, the open
action. qpdf writes every object reachable from the trailer, so one surviving
reference carries the page, its content stream and its images into the output.

Markers
-------
Every object that belongs to page n, or exists only to reach page n, carries
the text ``PRIVA-P<n>-``: the page's own content stream, its image, its
annotations and form fields, its structure elements, the bookmark and named
destination that point at it. An object that depends on two pages (a link on
page 1 to page 2) carries both markers. So one check covers every tool: in any
output, each marker must name a page that is in that output.

The check reads every object in the output file, not only the objects
reachable from the trailer, and decodes streams first. A marker in a
compressed content stream would be invisible to a byte search.
"""

from __future__ import annotations

import io
import re
from collections.abc import Iterable

import pikepdf
from pikepdf import Array, Dictionary, Name, String

PAGE_COUNT = 4

# Reference kinds the builder can add. Each one alone is enough to keep a
# removed page in the file if a tool forgets about it.
KINDS = (
    "outline_dest",     # bookmark per page: /Dest [page /Fit]
    "outline_goto",     # bookmark per page: /A << /S /GoTo /D [page ...] >>
    "outline_nested",   # bookmark for page 2 whose children point at 3, 4, 1
    "link_dest",        # link on page n to page n+1: /Dest [page /Fit]
    "link_goto",        # link on page n to page n+1: /A GoTo
    "named_dests",      # /Names /Dests name tree (two leaves, /Limits) + links
    "legacy_dests",     # catalog /Dests dictionary (PDF 1.1) + bookmarks
    "struct_tree",      # tagged content: /Pg, MCIDs, MCRs, OBJRs, ParentTree
    "acroform",         # a text field per page, one field on pages 1 and 2
    "open_action",      # /OpenAction [page 2 /Fit]
    "threads",          # an article across every page, one only on page 2
    "annotations",      # /IRT reply, /Popup, page /AA, action /Next chain
    "named_pages",      # /Names /Pages name tree
    "piece_info",       # private application data on page 1 naming page 2
)

_MARKER = re.compile(rb"PRIVA-P(\d+)-")
_PAGE_TEXT = re.compile(rb"PRIVA-P(\d+)-TEXT")


def marker(page: int, what: str) -> str:
    return f"PRIVA-P{page}-{what}"


def _next(page: int, pages: int) -> int:
    return page % pages + 1


# ── building ────────────────────────────────────────────────────────────────


def build_reference_pdf(
    kinds: Iterable[str] = KINDS,
    *,
    pages: int = PAGE_COUNT,
    blank: Iterable[int] = (),
) -> bytes:
    """Return a PDF with `pages` pages and the requested reference kinds.

    Pages in `blank` have no text layer and render almost white (a small image
    and a content-stream comment carrying the page marker), so Remove Blank
    Pages removes them while their annotations, fields and tags stay attached.
    """
    kinds = set(kinds)
    unknown = kinds - set(KINDS)
    if unknown:
        raise ValueError(f"unknown reference kinds: {sorted(unknown)}")
    blank = set(blank)
    tagged = "struct_tree" in kinds

    pdf = pikepdf.new()
    font = pdf.make_indirect(Dictionary(
        Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica,
        Encoding=Name.WinAnsiEncoding,
    ))
    page_objs: list[Dictionary] = []
    for n in range(1, pages + 1):
        image = pdf.make_stream(
            bytes([(40 * n) % 200]) * 4,
            Type=Name.XObject, Subtype=Name.Image, Width=2, Height=2,
            ColorSpace=Name.DeviceGray, BitsPerComponent=8,
            PrivaFixture=String(marker(n, "IMAGE")),
        )
        pdf.pages.append(pikepdf.Page(Dictionary(
            Type=Name.Page,
            MediaBox=Array([0, 0, 612, 792]),
            Resources=Dictionary(
                Font=Dictionary(F1=font),
                XObject=Dictionary(Im1=image),
            ),
            Contents=pdf.make_stream(_content(n, tagged, n in blank)),
        )))
        # pikepdf copies a page it is handed, so take the object that is
        # actually in the page tree.
        page_objs.append(pdf.pages[-1].obj)

    annots: dict[int, list] = {n: [] for n in range(1, pages + 1)}

    if "link_dest" in kinds or "link_goto" in kinds or "named_dests" in kinds:
        for n in range(1, pages + 1):
            to = _next(n, pages)
            if "link_dest" in kinds:
                link = _link(pdf, 100, marker(n, "LINK"), marker(to, "DEST"))
                link.Dest = Array([page_objs[to - 1], Name.Fit])
                annots[n].append(link)
            if "link_goto" in kinds:
                link = _link(pdf, 130, marker(n, "GOTO"), marker(to, "GOTO"))
                link.A = Dictionary(S=Name.GoTo, D=Array(
                    [page_objs[to - 1], Name.XYZ, None, None, None]))
                annots[n].append(link)
            if "named_dests" in kinds:
                link = _link(pdf, 160, marker(n, "NAMEDLINK"), marker(to, "NAMEDLINK"))
                link.Dest = String(marker(to, "NAMED"))
                annots[n].append(link)

    if "named_dests" in kinds:
        _named_dests(pdf, page_objs)
    if "legacy_dests" in kinds:
        pdf.Root.Dests = pdf.make_indirect(Dictionary({
            f"/{marker(n, 'LEGACY')}": Array([page_objs[n - 1], Name.Fit])
            for n in range(1, pages + 1)
        }))

    if "acroform" in kinds:
        _acroform(pdf, page_objs, annots, font, blank)
    if "annotations" in kinds and pages >= 3:
        _misc_annotations(pdf, page_objs, annots)
    if "piece_info" in kinds and pages >= 2:
        # Nothing in this library knows this dictionary; only a generic
        # sweep can find the page reference inside it.
        page_objs[0].PieceInfo = Dictionary(PrivaFixture=Dictionary(
            LastModified=String("D:20260924000000Z"),
            Private=Dictionary(Page=page_objs[1]),
        ))
    if tagged:
        _struct_tree(pdf, page_objs, annots)

    for n, items in annots.items():
        if items:
            page_objs[n - 1].Annots = Array(items)
    if "threads" in kinds:
        _threads(pdf, page_objs)
    if "open_action" in kinds and pages >= 2:
        pdf.Root.OpenAction = Array([page_objs[1], Name.Fit])
    if "named_pages" in kinds:
        names = pdf.Root.get("/Names")
        if names is None:
            names = pdf.Root.Names = Dictionary()
        flat = []
        for n in range(1, pages + 1):
            flat.extend([String(marker(n, "NAMEDPAGE")), page_objs[n - 1]])
        names.Pages = pdf.make_indirect(Dictionary(Names=Array(flat)))

    outline_items = _outline_items(kinds, pages)
    if outline_items:
        _write_outline(pdf, page_objs, outline_items)

    buf = io.BytesIO()
    pdf.save(buf)
    return buf.getvalue()


def _content(n: int, tagged: bool, blank: bool) -> bytes:
    text = (
        f"% {marker(n, 'TEXT')}\n" if blank
        else f"BT /F1 18 Tf 72 720 Td ({marker(n, 'TEXT')}) Tj ET\n"
    )
    image = "q 30 0 0 30 72 600 cm /Im1 Do Q\n"
    if not tagged:
        return (text + image).encode()
    span = "" if blank else "BT /F1 10 Tf 72 560 Td (continued) Tj ET "
    return (
        f"/P <</MCID 0>> BDC\n{text}EMC\n"
        f"/Figure <</MCID 1>> BDC\n{image}EMC\n"
        f"/Span <</MCID 2>> BDC {span}EMC\n"
    ).encode()


def _link(pdf: pikepdf.Pdf, y: int, own: str, target: str) -> Dictionary:
    return pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Link,
        Rect=Array([72, y, 300, y + 20]), Border=Array([0, 0, 0]),
        Contents=String(f"{own} to {target}"),
    ))


def _named_dests(pdf: pikepdf.Pdf, page_objs: list) -> None:
    pages = len(page_objs)
    names = sorted(
        (marker(n, "NAMED"), n) for n in range(1, pages + 1)
    )
    half = max(1, len(names) // 2)
    kids = []
    for chunk_no, chunk in enumerate((names[:half], names[half:])):
        if not chunk:
            continue
        flat = []
        for name, n in chunk:
            dest = Array([page_objs[n - 1], Name.Fit])
            # Both value forms the spec allows: a bare array and a /D dict.
            flat.extend([String(name), dest if chunk_no == 0 else Dictionary(D=dest)])
        kids.append(pdf.make_indirect(Dictionary(
            Names=Array(flat),
            Limits=Array([String(chunk[0][0]), String(chunk[-1][0])]),
        )))
    root = pdf.make_indirect(Dictionary(Kids=Array(kids)))
    names_dict = pdf.Root.get("/Names")
    if names_dict is None:
        names_dict = pdf.Root.Names = Dictionary()
    names_dict.Dests = root


def _acroform(
    pdf: pikepdf.Pdf, page_objs: list, annots: dict, font, blank: set,
) -> None:
    fields = []

    def appearance(text: str, page: int):
        # A blank page must stay text-free for Remove Blank Pages, which reads
        # widget appearances too; there the marker rides in a comment.
        body = (
            f"% {text}\n0 0 m 1 1 l S" if page in blank
            else f"/Tx BMC BT /Helv 10 Tf 2 6 Td ({text}) Tj ET EMC"
        )
        return pdf.make_stream(
            body.encode(),
            Type=Name.XObject, Subtype=Name.Form, BBox=Array([0, 0, 200, 20]),
            Resources=Dictionary(Font=Dictionary(Helv=font)),
        )

    for n, page in enumerate(page_objs, start=1):
        value = marker(n, "VALUE")
        field = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Widget, FT=Name.Tx,
            T=String(marker(n, "FIELD")), V=String(value), DA=String("/Helv 10 Tf 0 g"),
            Rect=Array([300, 700, 500, 720]), F=4, P=page,
            AP=Dictionary(N=appearance(value, n)),
        ))
        annots[n].append(field)
        fields.append(field)

    if len(page_objs) >= 2:
        # One field, two widgets on two pages. Removing page 2 must keep the
        # field and its page-1 widget and drop only the page-2 widget.
        shared = pdf.make_indirect(Dictionary(
            FT=Name.Tx, T=String("shared"), V=String("same on both pages"),
            DA=String("/Helv 10 Tf 0 g"),
        ))
        kids = []
        for n in (1, 2):
            widget = pdf.make_indirect(Dictionary(
                Type=Name.Annot, Subtype=Name.Widget, Parent=shared,
                Rect=Array([300, 660, 500, 680]), F=4, P=page_objs[n - 1],
                AP=Dictionary(N=appearance(marker(n, "WIDGET"), n)),
            ))
            annots[n].append(widget)
            kids.append(widget)
        shared.Kids = Array(kids)
        fields.append(shared)

    pdf.Root.AcroForm = pdf.make_indirect(Dictionary(
        Fields=Array(fields),
        CO=Array(fields[:2]),
        DA=String("/Helv 0 Tf 0 g"),
        DR=Dictionary(Font=Dictionary(Helv=font)),
    ))


def _misc_annotations(pdf: pikepdf.Pdf, page_objs: list, annots: dict) -> None:
    p1, p2, p3 = page_objs[0], page_objs[1], page_objs[2]
    # A note on page 2 with its popup, and a reply to it on page 1.
    note = pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Text, Rect=Array([400, 500, 420, 520]),
        Contents=String(marker(2, "NOTE")), P=p2, NM=String(marker(2, "NOTE-ID")),
    ))
    popup = pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Popup, Rect=Array([420, 400, 560, 500]),
        Parent=note, P=p2,
    ))
    note.Popup = popup
    annots[2].extend([note, popup])
    annots[1].append(pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Text, Rect=Array([400, 500, 420, 520]),
        Contents=String(marker(1, "REPLY")), IRT=note, RT=Name.R, P=p1,
    )))
    # Page 1 jumps to page 2 when opened.
    p1.AA = Dictionary(O=Dictionary(S=Name.GoTo, D=Array([p2, Name.Fit])))
    # A web link on page 3 whose action chain also jumps to page 2.
    annots[3].append(pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Link, Rect=Array([72, 300, 300, 320]),
        Border=Array([0, 0, 0]), Contents=String(marker(3, "WEBLINK")),
        A=Dictionary(
            S=Name.URI, URI=String("https://example.com/"),
            Next=Dictionary(S=Name.GoTo, D=Array([p2, Name.Fit])),
        ),
    )))


def _struct_tree(pdf: pikepdf.Pdf, page_objs: list, annots: dict) -> None:
    """Tag every page: a P (MCID 0), a Figure through an MCR (MCID 1), a Link
    element whose OBJR is a link annotation on the page, and a Span that starts
    on page 2 and continues on page 3 (MCID 2 on both)."""
    pages = len(page_objs)
    root = pdf.make_indirect(Dictionary(Type=Name.StructTreeRoot))
    document = pdf.make_indirect(Dictionary(
        Type=Name.StructElem, S=Name.Document, P=root))
    nums: list = []
    link_nums: list = []
    ids: list = []
    sections = []
    per_page: dict[int, list] = {}
    for n, page in enumerate(page_objs, start=1):
        sect = pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name.Sect, P=document))
        para = pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name.P, P=sect, Pg=page, K=0,
            ActualText=String(marker(n, "STRUCT")), ID=String(marker(n, "ID")),
        ))
        figure = pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name.Figure, P=sect, Pg=page,
            Alt=String(marker(n, "ALT")),
            K=Array([Dictionary(Type=Name.MCR, Pg=page, MCID=1)]),
        ))
        # "Back to top" link on the page itself, tagged through an OBJR.
        link = _link(pdf, 40, marker(n, "SELFLINK"), marker(n, "SELFLINK"))
        link.Dest = Array([page, Name.Fit])
        link.StructParent = 1000 + n
        annots[n].append(link)
        link_elem = pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name.Link, P=sect, Pg=page,
            Alt=String(marker(n, "LINKELEM")),
            K=Array([Dictionary(Type=Name.OBJR, Obj=link, Pg=page)]),
        ))
        link_nums.extend([1000 + n, link_elem])
        sect.K = Array([para, figure, link_elem])
        sections.append(sect)
        per_page[n] = [para, figure, None]
        page.StructParents = n - 1
        ids.append((marker(n, "ID"), para))

    if pages >= 3:
        # Starts on page 2, continues on page 3. Without page 2 it must keep
        # its page-3 half and stop claiming page 2.
        span = pdf.make_indirect(Dictionary(
            Type=Name.StructElem, S=Name.Span, P=document, Pg=page_objs[1],
            K=Array([2, Dictionary(Type=Name.MCR, Pg=page_objs[2], MCID=2)]),
        ))
        per_page[2][2] = span
        per_page[3][2] = span
        # PDF 2.0 /Ref from page 3's paragraph to page 2's.
        per_page[3][0].Ref = Array([per_page[2][0]])
        document.K = Array(sections + [span])
    else:
        document.K = Array(sections)

    for n in range(1, pages + 1):
        nums.extend([n - 1, Array(per_page[n])])
    nums.extend(link_nums)
    root.K = Array([document])
    root.ParentTree = pdf.make_indirect(Dictionary(Nums=Array(nums)))
    root.ParentTreeNextKey = 1000 + pages + 1
    flat = []
    for key, elem in sorted(ids, key=lambda item: item[0]):
        flat.extend([String(key), elem])
    root.IDTree = pdf.make_indirect(Dictionary(Names=Array(flat)))
    pdf.Root.StructTreeRoot = root
    pdf.Root.MarkInfo = Dictionary(Marked=True)


def _threads(pdf: pikepdf.Pdf, page_objs: list) -> None:
    article = pdf.make_indirect(Dictionary(
        Type=Name.Thread, I=Dictionary(Title=String("Article"))))
    beads = []
    for n, page in enumerate(page_objs, start=1):
        bead = pdf.make_indirect(Dictionary(
            Type=Name.Bead, T=article, P=page, R=Array([72, 72, 540, 400]),
            PrivaFixture=String(marker(n, "BEAD")),
        ))
        beads.append(bead)
        page.B = Array([bead])
    for i, bead in enumerate(beads):
        bead.N = beads[(i + 1) % len(beads)]
        bead.V = beads[i - 1]
    article.F = beads[0]
    threads = [article]
    if len(page_objs) >= 2:
        # A second article that lives only on page 2.
        lonely = pdf.make_indirect(Dictionary(
            Type=Name.Thread, I=Dictionary(Title=String(marker(2, "THREAD")))))
        bead = pdf.make_indirect(Dictionary(
            Type=Name.Bead, T=lonely, P=page_objs[1], R=Array([72, 420, 540, 700])))
        bead.N = bead
        bead.V = bead
        lonely.F = bead
        page_objs[1].B = Array([page_objs[1].B[0], bead])
        threads.append(lonely)
    pdf.Root.Threads = Array(threads)


def _outline_items(kinds: set, pages: int) -> list:
    """Return outline items as (title, target, children, closed) tuples.

    `target` is ("dest", page), ("goto", page), ("legacy", page) or None.
    """
    items: list = []
    for n in range(1, pages + 1):
        if "outline_dest" in kinds:
            items.append((marker(n, "OUTLINE"), ("dest", n), [], False))
        if "outline_goto" in kinds:
            items.append((marker(n, "OUTLINE-GOTO"), ("goto", n), [], False))
        if "legacy_dests" in kinds:
            items.append((marker(n, "OUTLINE-LEGACY"), ("legacy", n), [], False))
        if "named_dests" in kinds:
            items.append((marker(n, "OUTLINE-NAMED"), ("named", n), [], False))
    if "outline_nested" in kinds and pages >= 4:
        items.extend([
            # Chapter on page 2 whose sections are on pages 3, 4 and 1.
            (marker(2, "PARENT"), ("dest", 2), [
                (marker(3, "CHILD"), ("dest", 3), [
                    (marker(4, "GRANDCHILD"), ("dest", 4), [], False),
                ], False),
                (marker(1, "CHILD"), ("dest", 1), [], False),
            ], False),
            # A heading with no target of its own, over page 2 only.
            (marker(2, "HEADING"), None, [
                (marker(2, "HEADING-CHILD"), ("dest", 2), [], False),
            ], False),
            # A closed bookmark on page 3 with one hidden child on page 2.
            (marker(3, "CLOSED"), ("dest", 3), [
                (marker(2, "HIDDEN"), ("dest", 2), [], False),
            ], True),
        ])
    return items


def _write_outline(pdf: pikepdf.Pdf, page_objs: list, items: list) -> None:
    root = pdf.make_indirect(Dictionary(Type=Name.Outlines))

    def target(obj: Dictionary, spec) -> None:
        if spec is None:
            return
        kind, n = spec
        page = page_objs[n - 1]
        if kind == "dest":
            obj.Dest = Array([page, Name.Fit])
        elif kind == "goto":
            obj.A = Dictionary(S=Name.GoTo, D=Array([page, Name.FitH, 700]))
        elif kind == "legacy":
            obj.Dest = Name(f"/{marker(n, 'LEGACY')}")
        elif kind == "named":
            obj.Dest = String(marker(n, "NAMED"))

    def build(parent: Dictionary, specs: list) -> int:
        """Link `specs` under `parent`; return the visible descendant count."""
        objs = []
        visible = 0
        for title, spec, children, closed in specs:
            obj = pdf.make_indirect(Dictionary(Title=String(title), Parent=parent))
            target(obj, spec)
            if children:
                below = build(obj, children)
                obj.Count = -len(children) if closed else below
                if not closed:
                    visible += below
            objs.append(obj)
            visible += 1
        for prev, nxt in zip(objs, objs[1:]):
            prev.Next = nxt
            nxt.Prev = prev
        parent.First = objs[0]
        parent.Last = objs[-1]
        return visible

    root.Count = build(root, items)
    pdf.Root.Outlines = root


# ── hostile, damaged, malformed and crafted input ───────────────────────────


def _open(data: bytes) -> pikepdf.Pdf:
    return pikepdf.open(io.BytesIO(data))


def _saved(pdf: pikepdf.Pdf) -> bytes:
    buf = io.BytesIO()
    pdf.save(buf, object_stream_mode=pikepdf.ObjectStreamMode.disable)
    pdf.close()
    return buf.getvalue()


def _stream(pdf: pikepdf.Pdf, **entries):
    stream = pdf.make_stream(b"")
    for key, value in entries.items():
        stream[f"/{key}"] = value
    return stream


def _outline_of(pdf: pikepdf.Pdf, items: list) -> None:
    root = pdf.make_indirect(Dictionary(Type=Name.Outlines))
    for item in items:
        item["/Parent"] = root
    for prev, nxt in zip(items, items[1:]):
        prev["/Next"] = nxt
        nxt["/Prev"] = prev
    root.First, root.Last, root.Count = items[0], items[-1], len(items)
    pdf.Root.Outlines = root


SHARED_KINDS = (
    "shared_action", "shared_outline", "shared_ring", "stray_headings", "stray_list",
    "shared_annots", "shared_beads", "shared_kids", "shared_field_kids",
    "shared_hide_list", "shared_field_list", "shared_next_list", "shared_next_dead",
    "shared_triggers", "long_named_view",
)


def build_shared_objects_pdf(kind: str, n: int) -> bytes:
    """A PDF whose many owners share one object, as hostile files do.

    A walk that starts afresh for each owner costs n*n, or 2**n when owners
    nest. On 4 pages unless said otherwise:

    - ``shared_action``: n links on page 1 share one action whose /Next lists
      n more; ``shared_outline``: n bookmarks share such an action;
    - ``shared_ring``: n article threads start in one ring of n beads;
    - ``stray_headings``: n levels of two headings without a target that share
      their list of children, the deepest going to page 2, reached only from
      page 1's /PieceInfo (so the outline pass never sees them, the sweep
      does); ``stray_list``: n such headings share one list of n bookmarks to
      page 2;
    - ``shared_annots``: n pages share one /Annots array of n links, every
      other one to page 2; ``shared_beads``: n pages share one /B array, a
      ring of n beads on page 1;
    - ``shared_kids``: n structure elements on page 1 share one /K array of n
      elements on page 2; ``shared_field_kids``: n fields share one /Kids
      array of n widgets on page 2;
    - ``shared_hide_list``: n links on page 1, each with its own Hide action,
      name one list of n notes on page 3 and one on page 2;
      ``shared_field_list``: the same with ResetForm actions and fields;
    - ``shared_next_list``: n links on page 1, each with its own action, share
      one /Next list of n actions; ``shared_next_dead``: the same, each own
      action going to page 2, so the list takes its place;
    - ``shared_triggers``: n links on page 1 share one /AA dictionary of n
      actions, the first going to page 2;
    - ``long_named_view``: n links on page 1 name one destination on page 3
      whose view holds n numbers.
    """
    pages = n if kind in ("shared_annots", "shared_beads") else PAGE_COUNT
    pdf = _open(build_reference_pdf((), pages=pages))
    p = [page.obj for page in pdf.pages]
    if kind in ("shared_action", "shared_outline"):
        subs = [
            pdf.make_indirect(Dictionary(S=Name.URI, URI=String(f"https://example.com/{k}")))
            for k in range(n)
        ]
        shared = pdf.make_indirect(Dictionary(
            S=Name.GoTo, D=Array([p[0], Name.Fit]), Next=Array(subs)))
    if kind == "shared_action":
        p[0].Annots = Array([
            pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link,
                                         Rect=Array([0, 0, 10, 10]), A=shared))
            for _ in range(n)
        ])
        p[2].Annots = Array([pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 10, 10]),
            Dest=Array([p[1], Name.Fit])))])
    elif kind == "shared_outline":
        _outline_of(pdf, [
            pdf.make_indirect(Dictionary(Title=String(f"b{k}"), A=shared)) for k in range(n)
        ])
    elif kind == "shared_ring":
        beads = [pdf.make_indirect(Dictionary(Type=Name.Bead, P=p[0], R=Array([0, 0, 1, 1])))
                 for _ in range(n)]
        threads = [pdf.make_indirect(Dictionary(Type=Name.Thread, F=beads[0])) for _ in range(n)]
        for k, bead in enumerate(beads):
            bead.N = beads[(k + 1) % n]
            bead.V = beads[k - 1]
            bead.T = threads[0]
        p[0].B = Array(beads)
        pdf.Root.Threads = Array(threads)
    elif kind == "stray_headings":
        holder = pdf.make_indirect(Dictionary(Title=String("root")))
        level = None
        for k in range(n, 0, -1):
            a = pdf.make_indirect(Dictionary(Title=String(f"a{k}"), Parent=holder))
            b = pdf.make_indirect(Dictionary(Title=String(f"b{k}"), Parent=holder, Prev=a))
            a.Next = b
            if level is None:
                a.Title = String(marker(2, "STRAY"))
                a.Dest = Array([p[1], Name.Fit])
                b.Dest = Array([p[1], Name.Fit])
            else:
                a.First = level
                b.First = level
            level = a
        top = pdf.make_indirect(Dictionary(Title=String("top"), Parent=holder, First=level))
        _private(p[0], top)
    elif kind == "stray_list":
        holder = pdf.make_indirect(Dictionary(Title=String("root")))
        items = [pdf.make_indirect(Dictionary(
            Title=String(marker(2, "STRAY")), Parent=holder, Dest=Array([p[1], Name.Fit])))
            for _ in range(n)]
        for a, b in zip(items, items[1:]):
            a.Next = b
        _private(p[0], Array([
            pdf.make_indirect(Dictionary(Title=String(f"heading {k}"), Parent=holder, First=items[0]))
            for k in range(n)
        ]))
    elif kind == "shared_annots":
        shared = pdf.make_indirect(Array([
            _link(pdf, 10, marker(2 if k % 2 else 1, "SHARED"), "")
            for k in range(n)
        ]))
        for k, link in enumerate(shared):
            link.Dest = Array([p[1] if k % 2 else p[0], Name.Fit])
        for page in p:
            page.Annots = shared
    elif kind == "shared_beads":
        thread = pdf.make_indirect(Dictionary(Type=Name.Thread))
        beads = [pdf.make_indirect(Dictionary(Type=Name.Bead, T=thread, P=p[0], R=Array([0, 0, 1, 1])))
                 for _ in range(n)]
        for k, bead in enumerate(beads):
            bead.N = beads[(k + 1) % n]
            bead.V = beads[k - 1]
        thread.F = beads[0]
        shared = pdf.make_indirect(Array(beads))
        for page in p:
            page.B = shared
        pdf.Root.Threads = Array([thread])
    elif kind == "shared_kids":
        root = pdf.make_indirect(Dictionary(Type=Name.StructTreeRoot))
        document = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Document, P=root))
        shared = pdf.make_indirect(Array([
            pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Span, P=document, Pg=p[1],
                                         Alt=String(marker(2, "SHARED-KID")), K=0))
            for _ in range(n)
        ]))
        document.K = Array([
            pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.P, P=document, Pg=p[0], K=shared))
            for _ in range(n)
        ])
        root.K = Array([document])
        pdf.Root.StructTreeRoot = root
        pdf.Root.MarkInfo = Dictionary(Marked=True)
    elif kind == "shared_field_kids":
        shared = pdf.make_indirect(Array([
            pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Widget, Rect=Array([0, 0, 10, 10]),
                                         P=p[1], TU=String(marker(2, "SHARED-WIDGET"))))
            for _ in range(n)
        ]))
        p[1].Annots = shared
        pdf.Root.AcroForm = Dictionary(Fields=Array([
            pdf.make_indirect(Dictionary(FT=Name.Tx, T=String(f"field {k}"), Kids=shared))
            for k in range(n)
        ]))
    elif kind in ("shared_hide_list", "shared_field_list"):
        fields = kind == "shared_field_list"

        def target(page: int):
            entries = dict(Type=Name.Annot, Rect=Array([0, 0, 5, 5]), P=p[page - 1],
                           Contents=String(marker(page, "LISTED")))
            if fields:
                entries.update(Subtype=Name.Widget, FT=Name.Tx, T=String(marker(page, "LISTED")))
            else:
                entries.update(Subtype=Name.Text)
            return pdf.make_indirect(Dictionary(**entries))

        listed = [target(3) for _ in range(n)]
        gone = target(2)
        p[2].Annots = Array(listed)
        p[1].Annots = Array([gone])
        shared = pdf.make_indirect(Array([*listed, gone]))
        if fields:
            pdf.Root.AcroForm = Dictionary(Fields=Array([*listed, gone]))
        p[0].Annots = Array([
            pdf.make_indirect(Dictionary(
                Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 5, 5]),
                A=Dictionary(S=Name.ResetForm, Fields=shared) if fields
                else Dictionary(S=Name.Hide, T=shared)))
            for _ in range(n)
        ])
    elif kind in ("shared_next_list", "shared_next_dead"):
        shared = pdf.make_indirect(Array([
            pdf.make_indirect(Dictionary(S=Name.URI, URI=String(f"https://example.com/{k}")))
            for k in range(n)
        ]))

        def action():
            if kind == "shared_next_dead":
                return Dictionary(S=Name.GoTo, D=Array([p[1], Name.Fit]), Next=shared)
            return Dictionary(S=Name.URI, URI=String("https://example.com/"), Next=shared)

        p[0].Annots = Array([
            pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link,
                                         Rect=Array([0, 0, 5, 5]), A=action()))
            for _ in range(n)
        ])
        p[2].Annots = Array([pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 5, 5]),
            Dest=Array([p[1], Name.Fit])))])
    elif kind == "shared_triggers":
        triggers = {
            f"/K{k}": pdf.make_indirect(Dictionary(S=Name.URI, URI=String(f"https://example.com/{k}")))
            for k in range(1, n)
        }
        triggers["/K0"] = pdf.make_indirect(Dictionary(S=Name.GoTo, D=Array([p[1], Name.Fit])))
        shared = pdf.make_indirect(Dictionary(triggers))
        p[0].Annots = Array([
            pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link,
                                         Rect=Array([0, 0, 5, 5]), AA=shared))
            for _ in range(n)
        ])
    elif kind == "long_named_view":
        pdf.Root.Names = Dictionary(Dests=pdf.make_indirect(Dictionary(
            Names=Array([String("far"), Array([p[2], Name.XYZ, *([0] * n)])]))))
        p[0].Annots = Array([
            pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link,
                                         Rect=Array([0, 0, 5, 5]), Dest=String("far")))
            for _ in range(n)
        ])
    else:
        raise ValueError(kind)
    return _saved(pdf)


def _private(page, value) -> None:
    """Hang ``value`` off ``page``'s /PieceInfo, where only the sweep looks."""
    page.PieceInfo = Dictionary(PrivaApp=Dictionary(
        LastModified=String("D:20260924"), Private=Dictionary(Data=value)))


DAMAGED_TREES = ("count_small", "count_large", "junk_kid", "dangling_kid")


def build_damaged_tree_pdf(damage: str) -> bytes:
    """Pages reading PAGE-1, PAGE-2, (blank), PAGE-4, in a damaged page tree.

    ``count_small`` and ``count_large``: the root /Count says 3 or 6.
    ``junk_kid``: a string sits in /Kids between pages 1 and 2.
    ``dangling_kid``: a /Kids entry points at an object that does not exist.
    MuPDF trusts /Count and reads a junk entry as a page; qpdf does neither.
    """
    pdf = pikepdf.new()
    font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica))
    for i in range(1, 5):
        text = b"" if i == 3 else f"BT /F1 24 Tf 72 700 Td (PAGE-{i}) Tj ET".encode()
        pdf.pages.append(pikepdf.Page(Dictionary(
            Type=Name.Page, MediaBox=Array([0, 0, 612, 792]),
            Resources=Dictionary(Font=Dictionary(F1=font)),
            Contents=pdf.make_stream(text))))
    if damage in ("junk_kid", "dangling_kid"):
        kids = list(pdf.Root.Pages.Kids)
        pdf.Root.Pages.Kids = Array(kids[:1] + [String("junk")] + kids[1:])
    data = _saved(pdf)
    patch = {
        "count_small": (b"/Count 4", b"/Count 3"),
        "count_large": (b"/Count 4", b"/Count 6"),
        "junk_kid": None,
        "dangling_kid": (b"(junk)", b"999 0 R"),
    }[damage]
    if patch:
        assert patch[0] in data, damage
        data = data.replace(patch[0], patch[1])
    return data


def page_texts(data: bytes) -> list[str]:
    """PAGE-n, or "blank", for each page in qpdf's page list."""
    found = []
    with _open(data) as pdf:
        for page in pdf.pages:
            match = re.search(rb"PAGE-\d", _content_bytes(page.obj))
            found.append(match.group(0).decode() if match else "blank")
    return found


MALFORMED = (
    "structparents_array", "structparents_page", "structparent_stream",
    "aa_names_a_page", "aa_is_array", "count_is_name", "first_is_integer",
    "odd_parent_tree", "kid_is_string", "pg_is_array", "annots_is_dictionary",
    "fields_is_name", "bead_ring_is_broken", "dest_array_empty",
    "element_kid_is_name", "element_is_its_own_kid", "pg_is_the_catalog",
    "section_kids_are_junk", "thread_first_is_junk", "bookmark_list_is_broken",
    "thread_first_is_a_stream", "heading_child_is_a_removed_page", "bead_type_is_junk",
)
# Something other than a tree where a name tree belongs. The pages must stay
# as they are; what the tree held cannot be read, so a named link to page 2
# keeps its name.
MISPLACED_TREES = ("names_is_the_catalog", "named_pages_is_the_page_tree")


def build_malformed_pdf(name: str) -> bytes:
    """The all-kinds fixture with one value of a type the spec does not allow."""
    pdf = _open(build_reference_pdf(KINDS))
    p = [page.obj for page in pdf.pages]
    root = pdf.Root.StructTreeRoot
    if name == "structparents_array":
        p[2].StructParents = Array([])
    elif name == "structparents_page":
        p[2].StructParents = p[1]
    elif name == "structparent_stream":
        link = [a for a in p[1].Annots if "/StructParent" in a][0]
        link.StructParent = pdf.make_stream(b"x")
    elif name == "aa_names_a_page":
        p[0].AA = Dictionary(O=p[1])
    elif name == "aa_is_array":
        p[0].AA = Array([p[1]])
    elif name == "count_is_name":
        pdf.Root.Outlines.Count = Name.Bogus
    elif name == "first_is_integer":
        pdf.Root.Outlines.First.First = 7
    elif name == "odd_parent_tree":
        nums = [x for x in root.ParentTree.Nums]
        root.ParentTree.Nums = Array(nums + [99])
    elif name == "kid_is_string":
        section = root.K[0].K[1]
        section.K = Array([x for x in section.K] + [String("junk")])
    elif name == "pg_is_array":
        root.K[0].K[1].K[0].Pg = Array([])
    elif name == "annots_is_dictionary":
        p[0].Annots = Dictionary(Bogus=1)
    elif name == "fields_is_name":
        pdf.Root.AcroForm.Fields = Name.Bogus
    elif name == "bead_ring_is_broken":
        p[1].B[0].N = 7
    elif name == "dest_array_empty":
        pdf.Root.Outlines.First.Dest = Array([])
    elif name == "element_kid_is_name":
        # Page 2's Link element: no valid kid says where it is, its /Pg does.
        root.K[0].K[1].K[2].K = Name.Bogus
    elif name == "element_is_its_own_kid":
        element = root.K[0].K[1].K[2]
        element.K = Array([element])
    elif name == "names_is_the_catalog":
        pdf.Root.Names = pdf.Root
    elif name == "named_pages_is_the_page_tree":
        pdf.Root.Names.Pages = pdf.Root.Pages
    elif name == "pg_is_the_catalog":
        root.K[0].K[1].K[0].Pg = pdf.Root  # page 2's paragraph
    elif name == "section_kids_are_junk":
        # Page 2's elements drop out of the tree; page 3's /Ref still names one.
        root.K[0].K[1].K = 7
    elif name == "thread_first_is_junk":
        pdf.Root.Threads[0].F = 7  # the ring can no longer be walked
    elif name == "bookmark_list_is_broken":
        # The bookmarks after the first are reached only through /Last and /Prev.
        pdf.Root.Outlines.First.Next = 7
    elif name == "thread_first_is_a_stream":
        pdf.Root.Threads[1].F = pdf.make_stream(b"x")  # the article only on page 2
    elif name == "heading_child_is_a_removed_page":
        item = pdf.Root.Outlines.First
        while str(item.get("/Title", "")) != marker(2, "HEADING"):
            item = item.Next
        item.First = p[1]
    elif name == "bead_type_is_junk":
        # In a copy, this bead's /P is null too: only its shape says it is one.
        p[1].B[0].Type = 7
    else:
        raise ValueError(name)
    return _saved(pdf)


# A crafted file puts the catalog, the page tree or a kept page where a pass
# expects something it removes with page 2. Nothing of those may go.
PROTECTED = (
    "removed_annots_list_a_kept_page", "removed_beads_list_a_kept_page",
    "kept_page_as_a_dead_link", "kept_page_as_a_dead_element",
    "removed_annots_list_the_catalog", "removed_annots_list_the_page_tree",
    "tagged_removed_annots_list_a_kept_page",
)


def build_protected_pdf(name: str) -> bytes:
    """Page 2's annotations or beads, or a dead link or structure element,
    that are really page 3, the catalog or the page tree."""
    tagged = name in ("kept_page_as_a_dead_element", "tagged_removed_annots_list_a_kept_page")
    pdf = _open(build_reference_pdf(("struct_tree",) if tagged else ()))
    p = [page.obj for page in pdf.pages]
    if name == "removed_annots_list_a_kept_page":
        p[1].Annots = Array([p[2]])
    elif name == "removed_beads_list_a_kept_page":
        p[1].B = Array([p[2]])
    elif name == "kept_page_as_a_dead_link":
        p[2].Subtype = Name.Link
        p[2].Rect = Array([0, 0, 10, 10])
        p[2].Dest = Array([p[1], Name.Fit])
        p[0].Annots = Array([p[2]])
    elif name == "kept_page_as_a_dead_element":
        p[2].S = Name.P
        p[2].Pg = p[1]
        document = pdf.Root.StructTreeRoot.K[0]
        document.K = Array([x for x in document.K] + [p[2]])
    elif name == "removed_annots_list_the_catalog":
        p[1].Annots = Array([pdf.Root])
    elif name == "removed_annots_list_the_page_tree":
        p[1].Annots = Array([pdf.Root.Pages])
    elif name == "tagged_removed_annots_list_a_kept_page":
        p[1].Annots = Array([x for x in p[1].get("/Annots", [])] + [p[2]])
    else:
        raise ValueError(name)
    return _saved(pdf)


# Each removes page 2's markers only if a pass reads it the way PDFium does.
CRAFTED = (
    "private_numbers_key", "template_is_removed_page", "stream_action",
    "stream_bookmark", "stream_field", "stream_note", "stream_element",
    "stream_dest", "widget_not_in_annots", "reply_to_unlisted_note",
    "structure_destination", "spanning_actualtext", "font_bbox_page",
    "catalog_under_a_kept_page", "catalog_as_a_thread", "page_tree_in_the_bookmarks",
    "catalog_under_an_element", "catalog_is_an_element_kid", "page_written_in_place",
    "text_element_shares_kids_read_second", "alt_element_shares_kids_read_second",
    "inherited_page_element_shares_kids", "text_element_shares_kids_read_first",
    "form_is_a_note_of_the_removed_page",
)


def build_crafted_pdf(name: str) -> bytes:
    """Page 2 reached in a way the reference kinds do not cover.

    Removing page 2 (Delete Pages "2", or any copy without it) must leave no
    PRIVA-P2- marker. ``stream_*`` put a stream where a dictionary belongs,
    which PDFium accepts. ``font_bbox_page`` hides page 2 in a font's number
    array, where the sweep once did not look. ``catalog_under_a_kept_page``
    makes a copied page carry the whole source catalog, bookmarks and tags of
    page 2 included. ``*_shares_kids_*`` give an element of a kept page the
    /K array of an element of page 2, and a text that describes page 2's
    content; the tree pass reads the later sections first, so the element
    with the text is read second, or first.
    """
    base = {
        "catalog_under_a_kept_page": ("outline_dest", "struct_tree"),
        "catalog_as_a_thread": ("threads",),
        "page_tree_in_the_bookmarks": ("outline_dest",),
        "catalog_under_an_element": ("outline_dest", "struct_tree"),
        "catalog_is_an_element_kid": ("outline_dest", "struct_tree"),
        "template_is_removed_page": ("outline_dest",),
        "widget_not_in_annots": ("acroform",),
        "structure_destination": ("struct_tree",),
        "spanning_actualtext": ("struct_tree",),
        "stream_element": ("struct_tree",),
        "text_element_shares_kids_read_second": ("struct_tree",),
        "alt_element_shares_kids_read_second": ("struct_tree",),
        "inherited_page_element_shares_kids": ("struct_tree",),
        "text_element_shares_kids_read_first": ("struct_tree",),
        "form_is_a_note_of_the_removed_page": ("acroform",),
    }.get(name, ())
    pdf = _open(build_reference_pdf(base))
    p = [page.obj for page in pdf.pages]
    if name == "private_numbers_key":
        p[0].PieceInfo = Dictionary(PrivaApp=Dictionary(
            LastModified=String("D:20260924"), Private=Dictionary(BBox=Array([p[1]]))))
    elif name == "template_is_removed_page":
        pdf.Root.Names = Dictionary(Templates=Dictionary(Names=Array([String("tpl"), p[1]])))
    elif name == "stream_action":
        _outline_of(pdf, [pdf.make_indirect(Dictionary(
            Title=String(marker(2, "BOOKMARK")),
            A=_stream(pdf, S=Name.GoTo, D=Array([p[1], Name.Fit]))))])
    elif name == "stream_bookmark":
        _outline_of(pdf, [
            pdf.make_indirect(Dictionary(Title=String("one"), Dest=Array([p[0], Name.Fit]))),
            _stream(pdf, Title=String("two"), Dest=Array([p[2], Name.Fit])),
            pdf.make_indirect(Dictionary(Title=String(marker(2, "BOOKMARK")),
                                         Dest=Array([p[1], Name.Fit]))),
        ])
    elif name == "stream_field":
        field = _stream(pdf, FT=Name.Tx, T=String("ssn"), V=String(marker(2, "TYPED")))
        widget = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Widget, Rect=Array([300, 600, 500, 620]),
            Parent=field, P=p[1], F=4))
        field.Kids = Array([widget])
        p[1].Annots = Array([widget])
        pdf.Root.AcroForm = pdf.make_indirect(Dictionary(Fields=Array([field])))
    elif name == "stream_note":
        note = _stream(pdf, Type=Name.Annot, Subtype=Name.Text, Rect=Array([0, 0, 20, 20]),
                       Contents=String(marker(2, "NOTE")), P=p[1])
        reply = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Text, Rect=Array([0, 0, 20, 20]),
            Contents=String("reply"), IRT=note, P=p[0]))
        p[1].Annots = Array([note])
        p[0].Annots = Array([reply])
    elif name == "stream_element":
        section = pdf.Root.StructTreeRoot.K[0].K[1]
        element = _stream(pdf, Type=Name.StructElem, S=Name.P, P=section, Pg=p[1],
                          ActualText=String(marker(2, "STREAM-ELEM")), K=0)
        section.K = Array([x for x in section.K] + [element])
    elif name == "stream_dest":
        _outline_of(pdf, [pdf.make_indirect(Dictionary(
            Title=String(marker(2, "BOOKMARK")),
            Dest=_stream(pdf, D=Array([p[1], Name.Fit]))))])
    elif name == "widget_not_in_annots":
        widget = [a for a in p[1].Annots if str(a.get("/T", "")) == marker(2, "FIELD")][0]
        p[1].Annots = Array([a for a in p[1].Annots if a.objgen != widget.objgen])
    elif name == "reply_to_unlisted_note":
        note = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Text, Rect=Array([0, 0, 20, 20]),
            Contents=String(marker(2, "UNLISTED-NOTE")), P=p[1]))
        p[0].Annots = Array([pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Text, Rect=Array([0, 0, 20, 20]),
            Contents=String("reply"), IRT=note, P=p[0]))])
    elif name == "structure_destination":
        tree = pdf.Root.StructTreeRoot
        paragraph = tree.K[0].K[0].K[0]  # page 1's P
        link = pdf.make_indirect(Dictionary(
            Type=Name.Annot, Subtype=Name.Link, Rect=Array([72, 10, 200, 30]),
            A=Dictionary(S=Name.GoTo, D=Array([p[0], Name.Fit]),
                         SD=Array([paragraph, Name.Fit]))))
        p[0].Annots = Array([x for x in p[0].Annots] + [link])
    elif name == "spanning_actualtext":
        for element in pdf.Root.StructTreeRoot.K[0].K:
            if element.get("/S") == Name.Span:
                element.ActualText = String(marker(2, "SPAN") + " continued on page 3")
    elif name == "font_bbox_page":
        font = p[0].Resources.Font.F1
        font.FontBBox = Array([p[1]])
    elif name == "catalog_under_a_kept_page":
        p[0].PieceInfo = Dictionary(PrivaApp=Dictionary(
            LastModified=String("D:20260924"), Private=Dictionary(Doc=pdf.Root)))
    elif name == "catalog_as_a_thread":
        p[0].B[0].T = pdf.Root  # page 1's bead
    elif name == "page_tree_in_the_bookmarks":
        pdf.Root.Outlines.First.Next = pdf.Root.Pages
    elif name == "catalog_under_an_element":
        pdf.Root.StructTreeRoot.K[0].K[0].PrivaDoc = pdf.Root  # page 1's section
    elif name == "catalog_is_an_element_kid":
        section = pdf.Root.StructTreeRoot.K[0].K[0]
        section.K = Array([x for x in section.K] + [pdf.Root])
    elif name == "page_written_in_place":
        # A copy of page 2's dictionary, not an object: no page tree can list it.
        p[0].PieceInfo = Dictionary(PrivaApp=Dictionary(
            LastModified=String("D:20260924"), Private=Dictionary(Page=Dictionary(dict(p[1].items())))))
    elif name.endswith("_shares_kids") or "_shares_kids_" in name:
        _share_kids(pdf, p, name)
    elif name == "form_is_a_note_of_the_removed_page":
        form = pdf.Root.AcroForm
        form.Subtype = Name.Text
        form.Rect = Array([0, 0, 10, 10])
        form.Contents = String(marker(2, "NOTE-IN-FORM"))
        p[1].Annots = Array([*p[1].Annots, form])
    else:
        raise ValueError(name)
    return _saved(pdf)


def _share_kids(pdf: pikepdf.Pdf, p: list, name: str) -> None:
    """An element of page 2 and one of page 3 (its own, or its section's)
    share one /K array holding page 2's content; the second has the text."""
    sections = [s for s in pdf.Root.StructTreeRoot.K[0].K if s.get("/S") == Name.Sect]
    keep_under, gone_under = (3, 0) if name.endswith("_read_first") else (0, 3)
    shared = pdf.make_indirect(Array([Dictionary(Type=Name.MCR, Pg=p[1], MCID=0)]))
    gone = pdf.make_indirect(Dictionary(
        Type=Name.StructElem, S=Name.P, Pg=p[1], K=shared, P=sections[gone_under]))
    kept = pdf.make_indirect(Dictionary(
        Type=Name.StructElem, S=Name.Span, K=shared, P=sections[keep_under]))
    if name.startswith("inherited_page"):
        sections[keep_under].Pg = p[2]
    else:
        kept.Pg = p[2]
    key = "/Alt" if name.startswith("alt_") else "/ActualText"
    kept[key] = String(marker(2, "SHARED-K"))
    sections[gone_under].K = Array([*sections[gone_under].K, gone])
    sections[keep_under].K = Array([*sections[keep_under].K, kept])


# The outline root or the form, listed among page 2's annotations as if it
# were one. They are no annotations: nothing of them may go.
CATALOG_LISTED = ("outline_listed_on_removed_page", "form_listed_on_removed_page")


def build_catalog_listed_pdf(name: str, *, listed: bool = True) -> bytes:
    """With ``listed=False``, the same file without the listing."""
    kind = "outline_dest" if name.startswith("outline") else "acroform"
    pdf = _open(build_reference_pdf((kind,)))
    if listed:
        page = pdf.pages[1].obj
        held = pdf.Root.Outlines if kind == "outline_dest" else pdf.Root.AcroForm
        page.Annots = Array([*page.get("/Annots", []), held])
    return _saved(pdf)


def build_direct_page_tree_pdf() -> bytes:
    """The reference PDF with its page tree root written into the catalog.

    The specification wants the root indirect; some writers do not, and qpdf
    reads it all the same.
    """
    pdf = _open(build_reference_pdf(()))
    buf = io.BytesIO()
    pdf.save(buf, qdf=True, object_stream_mode=pikepdf.ObjectStreamMode.disable)
    pdf.close()
    raw = buf.getvalue()
    number = re.search(rb"/Pages (\d+) 0 R", raw).group(1)
    body = re.search(rb"\n" + number + rb" 0 obj\n(<<.*?>>)\nendobj", raw, re.S).group(1)
    return raw.replace(b"/Pages " + number + b" 0 R", b"/Pages " + body, 1)


def build_dense_tagged_pdf(pages: int, elements: int, mcids: int) -> bytes:
    """A valid tagged PDF with word-level marked content.

    Some OCR and tagging pipelines write it this way: each page has
    ``elements`` paragraph elements, each owning ``mcids`` marked-content ids,
    and the ParentTree maps every id to its paragraph. So the file holds far
    more entries to read than objects.
    """
    pdf = pikepdf.new()
    font = pdf.make_indirect(Dictionary(Type=Name.Font, Subtype=Name.Type1, BaseFont=Name.Helvetica))
    root = pdf.make_indirect(Dictionary(Type=Name.StructTreeRoot))
    document = pdf.make_indirect(Dictionary(Type=Name.StructElem, S=Name.Document, P=root))
    paragraphs, nums = [], []
    for n in range(pages):
        words = b"BT /F1 6 Tf 20 786 Td (PRIVA-P%d-TEXT) Tj ET\n" % (n + 1) + b"".join(
            b"/Span <</MCID %d>> BDC BT /F1 6 Tf %d %d Td (PRIVA-P%d-w%d) Tj ET EMC\n"
            % (m, 20 + (m % 20) * 28, 778 - (m // 20) * 8, n + 1, m)
            for m in range(elements * mcids)
        )
        pdf.pages.append(pikepdf.Page(Dictionary(
            Type=Name.Page, MediaBox=Array([0, 0, 612, 792]), Contents=pdf.make_stream(words),
            Resources=Dictionary(Font=Dictionary(F1=font)), StructParents=n)))
        page = pdf.pages[-1].obj
        owners = []
        for e in range(elements):
            paragraph = pdf.make_indirect(Dictionary(
                Type=Name.StructElem, S=Name.P, P=document, Pg=page,
                K=Array(list(range(e * mcids, (e + 1) * mcids)))))
            paragraphs.append(paragraph)
            owners.extend([paragraph] * mcids)
        nums.extend([n, pdf.make_indirect(Array(owners))])
    document.K = Array(paragraphs)
    root.K = Array([document])
    root.ParentTree = pdf.make_indirect(Dictionary(Nums=Array(nums)))
    root.ParentTreeNextKey = pages
    pdf.Root.StructTreeRoot = root
    pdf.Root.MarkInfo = Dictionary(Marked=True)
    buf = io.BytesIO()
    pdf.save(buf, object_stream_mode=pikepdf.ObjectStreamMode.generate)
    pdf.close()
    return buf.getvalue()


def build_shared_chain_pages_pdf(pages: int, links: int) -> bytes:
    """Every page lists the same ``links`` links, which share one action whose
    /Next lists ``links`` more: a pass that walked each link's chain afresh
    would read links * links actions for every document it prunes."""
    pdf = _open(build_reference_pdf((), pages=pages))
    chain = pdf.make_indirect(Array([
        pdf.make_indirect(Dictionary(S=Name.URI, URI=String(f"https://example.com/{k}")))
        for k in range(links)
    ]))
    action = pdf.make_indirect(Dictionary(S=Name.URI, URI=String("https://example.com/"), Next=chain))
    shared = pdf.make_indirect(Array([
        pdf.make_indirect(Dictionary(Type=Name.Annot, Subtype=Name.Link, Rect=Array([0, 0, 5, 5]), A=action))
        for _ in range(links)
    ]))
    for page in pdf.pages:
        page.obj.Annots = shared
    return _saved(pdf)


def build_tagged_link_pdf() -> bytes:
    """A tagged link on page 1 to page 2 whose element also owns link text.

    Page 1's third marked-content sequence (MCID 2) becomes the link's text,
    owned by a Link element with an OBJR to the annotation and /Alt naming
    page 2. Removing page 2 removes the link; the element survives through its
    text, and the link's ParentTree key must go with the link.
    """
    pdf = _open(build_reference_pdf(("struct_tree",)))
    p = [page.obj for page in pdf.pages]
    tree = pdf.Root.StructTreeRoot
    section = tree.K[0].K[0]
    link = pdf.make_indirect(Dictionary(
        Type=Name.Annot, Subtype=Name.Link, Rect=Array([72, 60, 300, 80]),
        Dest=Array([p[1], Name.Fit]), StructParent=2000))
    element = pdf.make_indirect(Dictionary(
        Type=Name.StructElem, S=Name.Link, P=section, Pg=p[0],
        Alt=String(marker(2, "LINK-ALT")),
        K=Array([2, Dictionary(Type=Name.OBJR, Obj=link, Pg=p[0])])))
    section.K = Array([x for x in section.K] + [element])
    p[0].Annots = Array([x for x in p[0].Annots] + [link])
    nums = [x for x in tree.ParentTree.Nums]
    page1_key = int(p[0].StructParents)
    at = nums.index(page1_key) + 1
    parents = [x for x in nums[at]]
    parents[2] = element
    nums[at] = Array(parents)
    tree.ParentTree.Nums = Array(nums + [2000, element])
    return _saved(pdf)


# ── checking ────────────────────────────────────────────────────────────────


def page_numbers(pdf: pikepdf.Pdf) -> list[int]:
    """Source page number of each page in the output's page tree, in order."""
    numbers = []
    for page in pdf.pages:
        found = _PAGE_TEXT.search(_content_bytes(page.obj))
        numbers.append(int(found.group(1)) if found else 0)
    return numbers


def markers_in_file(pdf: pikepdf.Pdf) -> set[int]:
    """Page numbers named by any marker in any object in the file.

    Reads every object the file contains, reachable from the trailer or not,
    with streams decoded.
    """
    found: set[int] = set()
    for obj in pdf.objects:
        _scan(obj, found, 0)
    return found


def leaked_pages(data: bytes) -> set[int]:
    """Pages whose markers are in the file although the page is not."""
    with pikepdf.open(io.BytesIO(data)) as pdf:
        return markers_in_file(pdf) - set(page_numbers(pdf))


def qpdf_check_passes(path) -> bool:
    """`qpdf --check`: exit code 0 and no warnings."""
    job = pikepdf.Job(["pikepdf", "--check", str(path)])
    job.run()
    return job.exit_code == 0 and not job.has_warnings


class Resolver:
    """Resolves an output's page references to source page numbers.

    A page in the output's page tree resolves to its source number, a page
    object outside the tree to 0, and null or nothing to None.
    """

    def __init__(self, pdf: pikepdf.Pdf):
        self.pdf = pdf
        self.number = {
            page.obj.objgen: n for page, n in zip(pdf.pages, page_numbers(pdf))
        }
        names = pdf.Root.get("/Names")
        tree = names.get("/Dests") if isinstance(names, Dictionary) else None
        self.named = {bytes(k): v for k, v in tree_items(tree, "/Names")}
        legacy = pdf.Root.get("/Dests")
        self.legacy = dict(legacy.items()) if isinstance(legacy, Dictionary) else {}

    def page(self, obj):
        if not isinstance(obj, Dictionary):
            return None
        return self.number.get(obj.objgen, 0)

    def dest(self, dest):
        if isinstance(dest, String):
            dest = self.named.get(bytes(dest))
        elif isinstance(dest, Name):
            dest = self.legacy.get(str(dest))
        if isinstance(dest, Dictionary):
            dest = dest.get("/D")
        if isinstance(dest, Array) and len(dest):
            return self.page(dest[0])
        return None

    def target(self, owner):
        """Where a bookmark or link leads: its /Dest or its GoTo action's /D."""
        if "/Dest" in owner:
            return self.dest(owner.Dest)
        action = owner.get("/A")
        if isinstance(action, Dictionary) and action.get("/S") == Name.GoTo:
            return self.dest(action.get("/D"))
        return None


def tree_items(node, leaf_key: str, depth: int = 0):
    """(key, value) pairs of a name or number tree, in order."""
    if not isinstance(node, Dictionary) or depth > 32:
        return
    entries = node.get(leaf_key)
    if isinstance(entries, Array):
        for i in range(0, len(entries) - 1, 2):
            yield entries[i], entries[i + 1]
    for kid in node.get("/Kids", []):
        yield from tree_items(kid, leaf_key, depth + 1)


def outline(pdf: pikepdf.Pdf) -> list[tuple[int, str, int | None]]:
    """(depth, title, target page) of every bookmark in reading order.

    Also asserts the outline is well formed: /Parent, /Prev, /Next, /First and
    /Last agree, and every /Count is what PDF 12.3.3 says it must be.
    """
    resolver = Resolver(pdf)
    found: list = []
    root = pdf.Root.get("/Outlines")
    if not isinstance(root, Dictionary):
        return found

    def walk(parent, depth) -> int:
        visible = 0
        item, prev = parent.get("/First"), None
        while item is not None:
            assert len(found) < 1000, "outline loops"
            assert item.Parent.objgen == parent.objgen, f"{item.Title}: wrong /Parent"
            if prev is None:
                assert "/Prev" not in item, f"{item.Title}: /Prev on a first child"
            else:
                assert item.Prev.objgen == prev.objgen, f"{item.Title}: wrong /Prev"
            found.append((depth, str(item.Title), resolver.target(item)))
            count = item.get("/Count")
            if "/First" in item:
                below = walk(item, depth + 1)
                assert count is not None and abs(count) == below, (
                    f"{item.Title}: /Count {count}, {below} descendants")
                visible += 1 + (below if count > 0 else 0)
            else:
                assert not count, f"{item.Title}: /Count without children"
                visible += 1
            prev, item = item, item.get("/Next")
        if prev is not None:
            assert parent.Last.objgen == prev.objgen, "wrong /Last"
        else:
            assert "/Last" not in parent, "/Last without children"
        return visible

    total = walk(root, 0)
    if found:
        assert root.Count == total, f"outline /Count {root.get('/Count')}, {total} visible"
    return found


def links(pdf: pikepdf.Pdf) -> list[tuple[int, int | None]]:
    """(page it is on, page it leads to) for every link annotation, in order."""
    resolver = Resolver(pdf)
    found = []
    for page, n in zip(pdf.pages, page_numbers(pdf)):
        for annot in page.obj.get("/Annots", []):
            if annot.get("/Subtype") == Name.Link:
                found.append((n, resolver.target(annot)))
    return found


def named_destinations(pdf: pikepdf.Pdf) -> dict[str, int | None]:
    """Every named destination, name tree and /Dests dictionary, with its page."""
    resolver = Resolver(pdf)
    found = {bytes(k).decode(): resolver.dest(v) for k, v in resolver.named.items()}
    found.update({k: resolver.dest(v) for k, v in resolver.legacy.items()})
    return found


def form_fields(pdf: pikepdf.Pdf) -> dict[str, list[int]]:
    """Each /AcroForm field with the pages of its widgets (0: on no page)."""
    on_page = {}
    for page, n in zip(pdf.pages, page_numbers(pdf)):
        for annot in page.obj.get("/Annots", []):
            on_page[annot.objgen] = n
    acroform = pdf.Root.get("/AcroForm")
    found = {}
    for field in (acroform.get("/Fields", []) if acroform is not None else []):
        widgets = field.Kids if "/Kids" in field else [field]
        found[str(field.T)] = [on_page.get(w.objgen, 0) for w in widgets]
    return found


def threads(pdf: pikepdf.Pdf) -> list[list[int]]:
    """Pages of each article thread's beads, in reading order.

    Also asserts every ring is consistent: /N and /V agree, /T is the thread,
    and each bead is in its page's /B.
    """
    resolver = Resolver(pdf)
    found = []
    for thread in pdf.Root.get("/Threads", []):
        ring, bead = [], thread.F
        while True:
            assert len(ring) < 100, "bead ring loops"
            assert bead.N.V.objgen == bead.objgen, "/N and /V disagree"
            assert bead.T.objgen == thread.objgen, "bead of another thread"
            assert any(b.objgen == bead.objgen for b in bead.P.get("/B", [])), (
                "bead not in its page's /B")
            ring.append(resolver.page(bead.P))
            bead = bead.N
            if bead.objgen == thread.F.objgen:
                break
        found.append(ring)
    return found


def structure_problems(pdf: pikepdf.Pdf) -> list[str]:
    """What is wrong with the structure tree, judged against the page tree.

    Every /Pg must be a page of the output, every OBJR an annotation on one,
    every element's /P its parent; each page's ParentTree entry must map its
    marked-content ids to the elements that own them, each tagged
    annotation's entry to the element holding its OBJR; and nothing in the
    ParentTree or IDTree may name an element outside the tree.
    """
    root = pdf.Root.get("/StructTreeRoot")
    if not isinstance(root, Dictionary):
        return ["no structure tree"]
    problems: list[str] = []
    mark = pdf.Root.get("/MarkInfo")
    if not (isinstance(mark, Dictionary) and mark.get("/Marked")):
        problems.append("/MarkInfo does not say /Marked true")
    live = {page.obj.objgen for page in pdf.pages}
    on_page = {
        annot.objgen for page in pdf.pages for annot in page.obj.get("/Annots", [])
    }
    owners: dict = {}
    objr_owner: dict = {}
    elements: set = set()

    def walk(node, page, depth):
        kids = node.get("/K")
        items = list(kids) if isinstance(kids, Array) else ([] if kids is None else [kids])
        for kid in items:
            if isinstance(kid, int):
                if page is None:
                    problems.append(f"{node.S}: MCID {kid} without a page")
                else:
                    owners[(page.objgen, kid)] = node.objgen
            elif isinstance(kid, Dictionary) and "/MCID" in kid:
                pg = kid.get("/Pg") or page
                if pg is None or pg.objgen not in live:
                    problems.append(f"{node.S}: MCR on a page not in the output")
                else:
                    owners[(pg.objgen, int(kid.MCID))] = node.objgen
            elif isinstance(kid, Dictionary) and "/Obj" in kid:
                obj = kid.get("/Obj")
                if obj is None or obj.objgen not in on_page:
                    problems.append(f"{node.S}: OBJR to an annotation on no page")
                else:
                    objr_owner[obj.objgen] = node.objgen
            elif isinstance(kid, Dictionary):
                elements.add(kid.objgen)
                if kid.get("/P") is None or kid.P.objgen != node.objgen:
                    problems.append(f"{kid.get('/S')}: /P is not its parent")
                pg = kid.get("/Pg")
                if pg is not None and pg.objgen not in live:
                    problems.append(f"{kid.get('/S')}: /Pg is a page not in the output")
                if depth < 64:
                    walk(kid, pg if pg is not None else page, depth + 1)

    walk(root, None, 0)
    entries = {int(k): v for k, v in tree_items(root.get("/ParentTree"), "/Nums")}
    used = set()
    for page in pdf.pages:
        key = page.obj.get("/StructParents")
        if key is not None:
            used.add(key)
            value = entries.get(key)
            if not isinstance(value, Array):
                problems.append(f"page key {key} has no ParentTree entry")
            else:
                for mcid, elem in enumerate(value):
                    if elem is not None and owners.get((page.obj.objgen, mcid)) != elem.objgen:
                        problems.append(f"ParentTree {key}[{mcid}] is not the owner of that content")
        for annot in page.obj.get("/Annots", []):
            key = annot.get("/StructParent")
            if key is not None:
                used.add(key)
                elem = entries.get(key)
                if not isinstance(elem, Dictionary) or objr_owner.get(annot.objgen) != elem.objgen:
                    problems.append(f"annotation key {key} does not lead to its element")
    for key, value in entries.items():
        if key not in used:
            problems.append(f"ParentTree key {key} belongs to nothing in the output")
        for elem in (value if isinstance(value, Array) else [value]):
            if isinstance(elem, Dictionary) and elem.objgen not in elements:
                problems.append(f"ParentTree {key} names an element outside the tree")
    for key, elem in tree_items(root.get("/IDTree"), "/Names"):
        if isinstance(elem, Dictionary) and elem.objgen not in elements:
            problems.append(f"IDTree {key} names an element outside the tree")
    return problems


def _content_bytes(page: Dictionary) -> bytes:
    contents = page.get("/Contents")
    if contents is None:
        return b""
    streams = contents if isinstance(contents, Array) else [contents]
    out = b""
    for stream in streams:
        if isinstance(stream, pikepdf.Stream):
            out += stream.read_bytes()
    return out


def _scan(obj, found: set[int], depth: int) -> None:
    if depth > 50:
        return
    if isinstance(obj, pikepdf.Stream):
        try:
            data = obj.read_bytes()
        except pikepdf.PdfError:
            data = obj.read_raw_bytes()
        found.update(int(m) for m in _MARKER.findall(data))
        obj = obj.stream_dict
    if isinstance(obj, Dictionary):
        for key in obj.keys():
            found.update(int(m) for m in _MARKER.findall(key.encode()))
            value = obj.get(key)
            if value is not None and not getattr(value, "is_indirect", False):
                _scan(value, found, depth + 1)
    elif isinstance(obj, Array):
        for value in obj:
            if not getattr(value, "is_indirect", False):
                _scan(value, found, depth + 1)
    elif isinstance(obj, (String, Name)):
        raw = bytes(obj) if isinstance(obj, String) else str(obj).encode()
        found.update(int(m) for m in _MARKER.findall(raw))
