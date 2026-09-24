"""Remove pages from a PDF without leaving them in the file.

Deleting a page from the page tree does not delete it from the PDF. qpdf, and
so pikepdf, writes every object reachable from the trailer, and a document
points at its pages from many places besides the page tree: bookmarks, links,
named destinations, the structure tree, form fields, article threads, the open
action. One reference that survives carries the whole page into the output,
with its content streams, images and fonts. Before this module existed, every
one of those references kept a page removed by Delete Pages in the file.

Pages disappear in two ways here, and one pruner serves both:

* In place. Delete Pages and Remove Blank Pages delete pages from the document
  they opened (:func:`remove_pages`). The removed page objects are still in
  memory, so whatever belonged to them, their annotations and article beads,
  is known exactly.

* By copying. Extract, Organize, Split and Merge build a new document out of
  some of the pages (:class:`PageCopier`). qpdf copies each page's object graph
  but replaces references to pages it was not asked to copy with null, so a
  page left behind never arrives itself. Objects that belong to it still do:
  its widget of a form field that spans pages, a comment that a reply on a kept
  page answers, its bead of an article thread. And links to it stay, leading
  nowhere.

The pruner then makes the document agree with its page tree. Destinations,
links, bookmarks, named destinations, form fields, threads and the structure
tree lose whatever points at a page that is not in it, and a final sweep over
everything reachable from the trailer drops any reference to a removed object
that is left. The sweep is the guarantee. The passes before it are what keep
the rest of the document working: a bookmark whose page went is removed but its
children are kept, a field keeps its widgets on the remaining pages, and a
tagged document stays tagged.

Not handled, because none of it points at a page: document-level objects that
only a removed page used, such as an optional-content layer or a named
JavaScript, stay in the file.

pikepdf reads an object from the file the first time it is touched, and each
key lookup costs about a microsecond, so the passes read every object they
visit once, through ``items()``.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Iterable

import pikepdf
from pikepdf import Array, Dictionary, Name, ObjectType, String

logger = logging.getLogger(__name__)

# Guards against malformed or hostile input: the nesting depth of trees and
# action chains, and the length of linked lists (outline siblings, bead rings).
_MAX_DEPTH = 64
_MAX_CHAIN = 1_000_000

_DICT = ObjectType.dictionary
_ARRAY = ObjectType.array
_STREAM = ObjectType.stream
_STRING = ObjectType.string
_NAME = ObjectType.name_

# Keys of bookmarks and structure elements whose values the passes below
# check themselves. A vetted object's other containers go to the sweep.
_OUTLINE_KEYS = frozenset((
    "/Type", "/Title", "/Parent", "/Prev", "/Next", "/First", "/Last",
    "/Count", "/Dest", "/A", "/SE", "/C", "/F",
))
_ELEMENT_KEYS = frozenset((
    "/Type", "/S", "/P", "/K", "/Pg", "/Ref", "/ID", "/C", "/R", "/T",
    "/Lang", "/Alt", "/E", "/ActualText", "/PhoneticAlphabet", "/Phoneme",
))

# Keys whose values the PDF specification limits to numbers and names: a
# font's widths, boxes, matrices, function domains. The sweep does not walk
# them; a font's /W alone can hold thousands of numbers, copied into every part
# a split writes.
_NUMBERS_ONLY = frozenset((
    "/W", "/W2", "/Widths", "/DW2", "/FontBBox", "/FontMatrix", "/Differences",
    "/MediaBox", "/CropBox", "/BleedBox", "/TrimBox", "/ArtBox", "/BBox",
    "/Matrix", "/Rect", "/QuadPoints", "/Vertices", "/InkList", "/Decode",
    "/Domain", "/Range", "/Encode", "/Bounds", "/Size", "/Coords",
))

_LIVE = "live"
_DEAD = "dead"
_UNKNOWN = "unknown"


def remove_pages(pdf: pikepdf.Pdf, indices: Iterable[int]) -> None:
    """Delete the pages at the 0-based ``indices`` and everything pointing at them."""
    doomed = sorted(set(indices), reverse=True)
    pages = _page_objs(pdf)
    removed = [pages[i] for i in doomed]
    for i in doomed:
        del pdf.pages[i]
    _Pruner(pdf, removed=removed).run()


def prune_to_page_tree(pdf: pikepdf.Pdf) -> None:
    """Drop every reference to a page that is not in ``pdf``'s page tree.

    For a document built by copying pages in (:class:`PageCopier`), right
    before it is saved. Anything that belongs to no page of ``pdf``, such as an
    annotation in no page's /Annots or a bead in no page's /B, came from a page
    that was left behind and is dropped with it.
    """
    _Pruner(pdf, removed=None).run()


def prune_structure_tree_to_pages(pdf: pikepdf.Pdf, indices: Iterable[int]) -> None:
    """Prune ``pdf``'s structure tree, in memory, to the pages at ``indices``.

    For tools that copy a structure tree into a new document. qpdf turns the
    /Pg of an element whose page was not copied into null, and a null /Pg reads
    exactly like no /Pg at all, so the elements of the pages left behind cannot
    be told apart afterwards. The tree has to be pruned in the source, while
    every page reference is intact, and copied after. Nothing else changes,
    and ``pdf`` must not be saved afterwards.
    """
    keep = set(indices)
    pages = _page_objs(pdf)
    if keep >= set(range(len(pages))):
        return
    pruner = _Pruner(
        pdf,
        removed=[page for i, page in enumerate(pages) if i not in keep],
        live_pages={pages[i].objgen for i in keep},
    )
    pruner.prune_structure_tree(pdf.Root)


class PageCopier:
    """Copies pages out of one document into new ones.

    Named destinations stay behind with the source's catalog, so a link on a
    copied page that names its target would lead nowhere in the copy. Each
    such name is replaced by an explicit destination when its target page is
    copied too, and by a null one when it is not, which
    :func:`prune_to_page_tree` then removes. Build one copier per source and
    reuse it across the documents made from it, so the name tree is read once.
    """

    def __init__(self, src: pikepdf.Pdf):
        self.src = src
        self._pages: list | None = None
        self._string_dests: dict[bytes, object] | None = None
        self._name_dests: dict[str, object] | None = None

    def copy(self, dst: pikepdf.Pdf, indices: Iterable[int]) -> None:
        """Append ``src.pages[i]`` for each index to ``dst``, in order."""
        indices = list(indices)
        if self._pages is None:
            # One pass: `pages[i]` costs a copy of the whole page list.
            self._pages = [page for page in self.src.pages]
        start = len(dst.pages)
        for i in indices:
            dst.pages.append(self._pages[i])
        copied = _page_objs(dst)[start:]
        page_map: dict[tuple[int, int], Dictionary] = {}
        for i, page in zip(indices, copied):
            page_map.setdefault(self._pages[i].obj.objgen, page)
        for page in copied:
            for owner, key, value in _destination_slots(page):
                if _type(value) in (_STRING, _NAME):
                    self._resolve(owner, key, value, page_map)

    def _resolve(self, owner, key: str, value, page_map: dict) -> None:
        if _type(value) == _STRING:
            dest = self._lookup_string(bytes(value))
        else:
            dest = self._lookup_name(str(value))
        if dest is None:
            return  # not a name the source defines either; nothing to resolve
        view = _items(dest)
        target = view.pop(0) if view else None
        page = page_map.get(target.objgen) if _is_indirect_dict(target) else None
        if page is None or any(getattr(v, "is_indirect", False) for v in view):
            view = [Name.Fit]
        owner[key] = Array([page, *view])

    def _lookup_string(self, name: bytes):
        if self._string_dests is None:
            self._string_dests = {}
            names = self.src.Root.get("/Names")
            tree = names.get("/Dests") if _type(names) == _DICT else None
            for key, value in _tree_entries(tree, "/Names"):
                if _type(key) == _STRING:
                    self._string_dests.setdefault(bytes(key), value)
        return _explicit(self._string_dests.get(name))

    def _lookup_name(self, name: str):
        if self._name_dests is None:
            self._name_dests = {}
            dests = self.src.Root.get("/Dests")
            if _type(dests) == _DICT:
                self._name_dests.update(dests.items())
        return _explicit(self._name_dests.get(name))


def copy_pages(dst: pikepdf.Pdf, src: pikepdf.Pdf, indices: Iterable[int]) -> None:
    """Append ``src``'s pages at ``indices`` to ``dst``; see :class:`PageCopier`."""
    PageCopier(src).copy(dst, indices)


# ── helpers ─────────────────────────────────────────────────────────────────


def _type(obj):
    return getattr(obj, "_type_code", None)


def _is_indirect_dict(obj) -> bool:
    return _type(obj) == _DICT and obj.is_indirect


def _items(array) -> list:
    return [item for item in array]


def _array(obj) -> list:
    return _items(obj) if _type(obj) == _ARRAY else []


def _first(array):
    for item in array:
        return item
    return None


def _page_objs(pdf: pikepdf.Pdf) -> list:
    # Iterate: `pdf.pages[i]` copies qpdf's whole page list on every call.
    return [page.obj for page in pdf.pages]


def _explicit(dest):
    """The explicit destination array behind a named-destination value."""
    if _type(dest) == _DICT:
        dest = dest.get("/D")
    return dest if _type(dest) == _ARRAY else None


def _is_annotation(fields: dict) -> bool:
    return fields.get("/Type") == Name.Annot or ("/Rect" in fields and "/Subtype" in fields)


def _destination_slots(page: Dictionary):
    """(owner, key, value) for each destination on a page and its annotations."""
    for annot in _array(page.get("/Annots")):
        if _type(annot) != _DICT:
            continue
        fields = dict(annot.items())
        if "/Dest" in fields:
            yield annot, "/Dest", fields["/Dest"]
        yield from _action_slots(fields.get("/A"), set(), 0)
        aa = fields.get("/AA")
        if _type(aa) == _DICT:
            for _, action in aa.items():
                yield from _action_slots(action, set(), 0)
    aa = page.get("/AA")
    if _type(aa) == _DICT:
        for _, action in aa.items():
            yield from _action_slots(action, set(), 0)


def _action_slots(action, seen: set, depth: int):
    if depth > _MAX_DEPTH or _type(action) != _DICT:
        return
    if action.is_indirect:
        if action.objgen in seen:
            return
        seen.add(action.objgen)
    fields = dict(action.items())
    if fields.get("/S") == Name.GoTo and "/D" in fields:
        yield action, "/D", fields["/D"]
    nxt = fields.get("/Next")
    for sub in (_items(nxt) if _type(nxt) == _ARRAY else [nxt]):
        yield from _action_slots(sub, seen, depth + 1)


def _tree_entries(node, leaf_key: str, depth: int = 0, seen: set | None = None):
    """Yield (key, value) pairs of a name or number tree, in order."""
    if seen is None:
        seen = set()
    if depth > _MAX_DEPTH or _type(node) != _DICT:
        return
    if node.is_indirect:
        if node.objgen in seen:
            return
        seen.add(node.objgen)
    fields = dict(node.items())
    entries = fields.get(leaf_key)
    if _type(entries) == _ARRAY:
        items = _items(entries)
        for i in range(0, len(items) - 1, 2):
            yield items[i], items[i + 1]
    for kid in _array(fields.get("/Kids")):
        yield from _tree_entries(kid, leaf_key, depth + 1, seen)


def _prune_tree(node, leaf_key: str, keep: Callable, depth: int = 0, seen: set | None = None):
    """Filter a name or number tree in place, fixing /Limits and empty nodes.

    ``keep(key, value)`` decides each entry and may modify ``value`` in place.
    Returns ``(first_key, last_key)`` of what is left, or None when nothing is.
    """
    if seen is None:
        seen = set()
    if depth > _MAX_DEPTH or _type(node) != _DICT:
        return None
    if node.is_indirect:
        if node.objgen in seen:
            return None
        seen.add(node.objgen)
    fields = dict(node.items())
    first = last = None
    changed = False
    entries = fields.get(leaf_key)
    if _type(entries) == _ARRAY:
        items = _items(entries)
        kept = []
        for i in range(0, len(items) - 1, 2):
            if keep(items[i], items[i + 1]):
                kept.extend(items[i:i + 2])
        if len(kept) != len(items):
            node[leaf_key] = Array(kept)
            changed = True
        if kept:
            first, last = kept[0], kept[-2]
    kids = fields.get("/Kids")
    if _type(kids) == _ARRAY:
        items = _items(kids)
        kept_kids = []
        for kid in items:
            limits = _prune_tree(kid, leaf_key, keep, depth + 1, seen)
            if limits is None:
                continue
            kept_kids.append(kid)
            if first is None:
                first = limits[0]
            last = limits[1]
        if len(kept_kids) != len(items):
            node.Kids = Array(kept_kids)
            changed = True
    if first is None:
        return None
    if changed and "/Limits" in fields:
        node.Limits = Array([first, last])
    return first, last


# ── the pruner ──────────────────────────────────────────────────────────────


class _Pruner:
    """Removes what points at pages outside the live set; see the module docstring.

    ``removed`` lists the page objects deleted in place; None means the pages
    left behind are unknown (a copied document), so anything that is on no live
    page counts as belonging to one of them.
    """

    def __init__(self, pdf: pikepdf.Pdf, removed: list | None, live_pages: set | None = None):
        self.pdf = pdf
        self.exact = removed is not None
        self.removed = removed or []
        pages = _page_objs(pdf)
        self.live_pages = live_pages if live_pages is not None else {p.objgen for p in pages}
        self.pages = [page for page in pages if page.objgen in self.live_pages]
        self.removed_pages = {page.objgen for page in self.removed}
        self.template_pages: set = set()
        self.dead_names: set[bytes] = set()
        self.dead_legacy: set[str] = set()
        self.dead_elements: set = set()
        self.alive_elements: set = set()

        # Each live page's annotations, read once and shared by the passes.
        self.annots_of: dict = {}
        self.live_annots: set = set()
        self.live_beads: set = set()
        for page in self.pages:
            annots = _array(page.get("/Annots"))
            self.annots_of[page.objgen] = annots
            for annot in annots:
                if _is_indirect_dict(annot):
                    self.live_annots.add(annot.objgen)
            for bead in _array(page.get("/B")):
                if _is_indirect_dict(bead):
                    self.live_beads.add(bead.objgen)
        self.dead_annots: set = set()
        self.dead_beads: set = set()
        for page in self.removed:
            for annot in _array(page.get("/Annots")):
                if _is_indirect_dict(annot) and annot.objgen not in self.live_annots:
                    self.dead_annots.add(annot.objgen)
            for bead in _array(page.get("/B")):
                if _is_indirect_dict(bead) and bead.objgen not in self.live_beads:
                    self.dead_beads.add(bead.objgen)
        # Everything removed by any pass; the sweep cuts references to these.
        self.dead: set = set(self.removed_pages)
        self.dead.update(self.dead_annots)
        self.dead.update(self.dead_beads)
        # Objects a pass has fully checked, and containers it left to the sweep.
        self.vetted: set = set()
        self.pending: list = []

    # ── predicates ──────────────────────────────────────────────────────────

    def page_dead(self, obj) -> bool:
        """True for a page reference that does not lead to a page in the output."""
        if obj is None:
            return True  # qpdf's stand-in for a page that was not copied
        if _type(obj) != _DICT:
            return False  # a page number or something else: not ours to judge
        if not obj.is_indirect:
            return obj.get("/Type") == Name.Page
        og = obj.objgen
        if og in self.live_pages or og in self.template_pages:
            return False
        return og in self.removed_pages or obj.get("/Type") == Name.Page

    def annot_dead(self, obj) -> bool:
        if not _is_indirect_dict(obj):
            return False
        og = obj.objgen
        if og in self.dead:
            return True
        if og in self.live_annots:
            return False
        if self.exact:
            return og in self.dead_annots
        return _is_annotation(dict(obj.items()))

    def bead_dead(self, obj) -> bool:
        if not _is_indirect_dict(obj):
            return False
        og = obj.objgen
        if og in self.dead:
            return True
        if og in self.live_beads:
            return False
        return og in self.dead_beads if self.exact else True

    def dest_state(self, dest) -> str:
        kind = _type(dest)
        if kind == _DICT:  # a named destination's << /D [...] >> form
            dest = dest.get("/D")
            kind = _type(dest)
        if kind == _ARRAY:
            target = _first(dest)
            if target is None or _type(target) == _DICT:
                if target is None and len(dest) == 0:
                    return _UNKNOWN
                return _DEAD if self.page_dead(target) else _LIVE
            return _UNKNOWN
        if kind == _STRING:
            return _DEAD if bytes(dest) in self.dead_names else _UNKNOWN
        if kind == _NAME:
            return _DEAD if str(dest) in self.dead_legacy else _UNKNOWN
        return _UNKNOWN

    def kill(self, obj) -> None:
        if getattr(obj, "is_indirect", False):
            self.dead.add(obj.objgen)

    def _field_dead(self, obj) -> bool:
        return _is_indirect_dict(obj) and obj.objgen in self.dead

    # ── actions ─────────────────────────────────────────────────────────────

    def prune_action(self, action, seen: set | None = None, depth: int = 0):
        """Return the action chain without actions that reach removed pages.

        Returns ``action`` itself (possibly edited), a replacement when the
        head of the chain had to go, or None when nothing is left.
        """
        if seen is None:
            seen = set()
        if depth > _MAX_DEPTH or _type(action) != _DICT:
            return action
        if action.is_indirect:
            if action.objgen in seen:
                return action
            seen.add(action.objgen)
        fields = dict(action.items())

        nxt = fields.get("/Next")
        if nxt is not None:
            if _type(nxt) == _ARRAY:
                subs = _items(nxt)
                kept = [s for s in (self.prune_action(s, seen, depth + 1) for s in subs) if s is not None]
                if not kept:
                    del action["/Next"]
                elif len(kept) != len(subs) or any(a is not b for a, b in zip(kept, subs)):
                    action.Next = Array(kept)
            else:
                pruned = self.prune_action(nxt, seen, depth + 1)
                if pruned is None:
                    del action["/Next"]
                elif pruned is not nxt:
                    action.Next = pruned

        if not self._action_dead(action, fields):
            return action
        self.kill(action)
        rest = action.get("/Next")
        if rest is None:
            return None
        if _type(rest) != _ARRAY:
            return rest
        # The head goes; its successors run in the same order without it.
        subs = _items(rest)
        head, tail = subs[0], subs[1:]
        if tail and _type(head) == _DICT:
            own = head.get("/Next")
            own_list = [] if own is None else (_items(own) if _type(own) == _ARRAY else [own])
            head.Next = Array(own_list + tail)
        return head

    def _action_dead(self, action: Dictionary, fields: dict) -> bool:
        kind = fields.get("/S")
        if kind == Name.GoTo:
            return self.dest_state(fields.get("/D")) == _DEAD
        if kind == Name.Thread:
            thread, bead = fields.get("/D"), fields.get("/B")
            return (
                (_is_indirect_dict(thread) and thread.objgen in self.dead)
                or self.bead_dead(bead)
            )
        if kind == Name.Rendition:
            return self.annot_dead(fields.get("/AN"))
        if kind == Name.GoTo3DView:
            return self.annot_dead(fields.get("/TA"))
        if kind == Name.Movie:
            return self.annot_dead(fields.get("/Annotation"))
        if kind == Name.Hide:
            targets = fields.get("/T")
            if _type(targets) != _ARRAY:
                return self.annot_dead(targets) or self._field_dead(targets)
            items = _items(targets)
            kept = [t for t in items if not self.annot_dead(t) and not self._field_dead(t)]
            if len(kept) != len(items):
                if not kept:
                    return True
                action.T = Array(kept)
            return False
        if kind in (Name.SubmitForm, Name.ResetForm):
            fields_ = fields.get("/Fields")
            if _type(fields_) == _ARRAY:
                items = _items(fields_)
                kept = [f for f in items if not self._field_dead(f) and not self.annot_dead(f)]
                if len(kept) != len(items):
                    # An empty list would mean "every field", the opposite.
                    if not kept:
                        return True
                    action.Fields = Array(kept)
        return False

    def prune_additional_actions(self, owner, aa) -> None:
        if _type(aa) != _DICT:
            return
        for trigger, action in list(aa.items()):
            pruned = self.prune_action(action)
            if pruned is None:
                del aa[trigger]
            elif pruned is not action:
                aa[trigger] = pruned
        if not aa.keys():
            del owner["/AA"]

    # ── passes ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        root = self.pdf.Root
        catalog = dict(root.items())
        self._collect_templates(catalog)
        self.prune_named_destinations(catalog)
        # Fields and threads first: actions that name fields (reset, submit,
        # hide) or threads are pruned with the annotations and need to know
        # which of them went.
        self.prune_fields(catalog)
        self.prune_threads(root, catalog)
        self.prune_page_annotations()
        self.prune_structure_tree(root)
        self.prune_outline(catalog)
        self.prune_catalog(root)
        self.sweep()

    def _collect_templates(self, catalog: dict) -> None:
        # Template pages live outside the page tree on purpose (PDF 12.7.6).
        names = catalog.get("/Names")
        if _type(names) == _DICT:
            for _, page in _tree_entries(names.get("/Templates"), "/Names"):
                if _is_indirect_dict(page):
                    self.template_pages.add(page.objgen)

    def prune_named_destinations(self, catalog: dict) -> None:
        names = catalog.get("/Names")
        tree = names.get("/Dests") if _type(names) == _DICT else None
        if tree is not None:
            def keep(key, value):
                if self.dest_state(value) != _DEAD:
                    return True
                if _type(key) == _STRING:
                    self.dead_names.add(bytes(key))
                self.kill(value)
                return False

            if _prune_tree(tree, "/Names", keep) is None:
                del names["/Dests"]
        dests = catalog.get("/Dests")
        if _type(dests) == _DICT:
            for key, value in list(dests.items()):
                if self.dest_state(value) == _DEAD:
                    self.dead_legacy.add(key)
                    self.kill(value)
                    del dests[key]

    def prune_fields(self, catalog: dict) -> None:
        acroform = catalog.get("/AcroForm")
        acroform = acroform if _type(acroform) == _DICT else None
        seen: set = set()
        removed_any = False

        def alive(field, depth: int) -> bool:
            nonlocal removed_any
            if depth > _MAX_DEPTH or _type(field) != _DICT:
                return True
            if field.is_indirect:
                if field.objgen in seen:
                    return field.objgen not in self.dead
                seen.add(field.objgen)
            fields = dict(field.items())
            kids = fields.get("/Kids")
            if _type(kids) == _ARRAY and len(kids):
                items = _items(kids)
                kept = [kid for kid in items if alive(kid, depth + 1)]
                if len(kept) != len(items):
                    removed_any = True
                    if not kept:
                        self.kill(field)
                        return False
                    field.Kids = Array(kept)
                return True
            if _is_annotation(fields) and self.annot_dead(field):
                self.kill(field)
                removed_any = True
                return False
            return True

        if acroform is not None:
            fields = acroform.get("/Fields")
            if _type(fields) == _ARRAY:
                items = _items(fields)
                kept = [field for field in items if alive(field, 0)]
                if len(kept) != len(items):
                    acroform.Fields = Array(kept)
        # A copied document has no /AcroForm, but a widget's field still
        # reaches its sibling widgets on the pages left behind.
        for annots in self.annots_of.values():
            for annot in annots:
                if _type(annot) != _DICT:
                    continue
                parent = annot.get("/Parent")
                if _type(parent) != _DICT or annot.get("/Subtype") != Name.Widget:
                    continue
                top, steps = parent, 0
                while steps < _MAX_DEPTH:
                    up = top.get("/Parent")
                    if _type(up) != _DICT:
                        break
                    top, steps = up, steps + 1
                alive(top, 0)
        if acroform is None:
            return
        order = acroform.get("/CO")
        if _type(order) == _ARRAY:
            items = _items(order)
            kept = [f for f in items if not self._field_dead(f)]
            if len(kept) != len(items):
                acroform.CO = Array(kept)
        if removed_any and "/XFA" in acroform:
            # XFA keeps every field's value in its own XML, so the values of
            # the fields that went would stay in the file. Without it the
            # remaining fields still work from the AcroForm.
            del acroform["/XFA"]

    def prune_page_annotations(self) -> None:
        remaining = []  # (page, annotation, its entries) for what stays
        for page in self.pages:
            annots = self.annots_of[page.objgen]
            if annots:
                kept, removed = [], []
                for annot in annots:
                    fields = dict(annot.items()) if _type(annot) == _DICT else {}
                    if self._annotation_goes(annot, fields):
                        removed.append(annot)
                    else:
                        kept.append(annot)
                        remaining.append((page, annot, fields))
                for annot in removed:
                    if _is_indirect_dict(annot):
                        self.live_annots.discard(annot.objgen)
                        self.dead.add(annot.objgen)
                if removed:
                    if kept:
                        page.Annots = Array(kept)
                    else:
                        del page["/Annots"]
                    self.annots_of[page.objgen] = kept
            aa = page.get("/AA")
            if aa is not None:
                self.prune_additional_actions(page, aa)
        # Replies and popups can point at annotations of removed pages and at
        # links removed above, on any page.
        for page, annot, fields in remaining:
            for key in ("/IRT", "/Popup"):
                if key in fields and self.annot_dead(fields[key]):
                    del annot[key]
            if "/P" in fields and self.page_dead(fields["/P"]):
                annot.P = page

    def _annotation_goes(self, annot, fields: dict) -> bool:
        """Decide one annotation on a live page; edits what stays in place."""
        if not fields:
            return False
        if annot.is_indirect and annot.objgen in self.dead:
            return True
        subtype = fields.get("/Subtype")
        if subtype == Name.Popup and self.annot_dead(fields.get("/Parent")):
            return True  # the popup of a comment that was on a removed page
        dest_dead = "/Dest" in fields and self.dest_state(fields["/Dest"]) == _DEAD
        action = fields.get("/A")
        action_dead = False
        if action is not None:
            pruned = self.prune_action(action)
            if pruned is None:
                action_dead = True
            elif pruned is not action:
                annot.A = pruned
        if "/AA" in fields:
            self.prune_additional_actions(annot, fields["/AA"])
        if subtype == Name.Link:
            has_dest, has_action = "/Dest" in fields, action is not None
            if (has_dest or has_action) and (dest_dead or not has_dest) and (action_dead or not has_action):
                return True
        if dest_dead:
            del annot["/Dest"]
        if action_dead:
            del annot["/A"]
        return False

    def prune_threads(self, root, catalog: dict) -> None:
        threads = catalog.get("/Threads")
        candidates = _array(threads)
        listed = {t.objgen for t in candidates if _is_indirect_dict(t)}
        for page in self.pages:
            for bead in _array(page.get("/B")):
                thread = bead.get("/T") if _type(bead) == _DICT else None
                if _is_indirect_dict(thread) and thread.objgen not in listed:
                    listed.add(thread.objgen)
                    candidates.append(thread)
        dead_threads = set()
        for thread in candidates:
            if _type(thread) != _DICT:
                continue
            ring, seen, bead = [], set(), thread.get("/F")
            while _is_indirect_dict(bead) and bead.objgen not in seen and len(ring) < _MAX_CHAIN:
                seen.add(bead.objgen)
                ring.append(bead)
                bead = bead.get("/N")
            live = [b for b in ring if not self.bead_dead(b)]
            if len(live) == len(ring):
                continue
            for b in ring:
                if self.bead_dead(b):
                    self.kill(b)
            if not live:
                self.kill(thread)
                if thread.is_indirect:
                    dead_threads.add(thread.objgen)
                continue
            for i, b in enumerate(live):
                b.N = live[(i + 1) % len(live)]
                b.V = live[i - 1]
            thread.F = live[0]
        if dead_threads and _type(threads) == _ARRAY:
            kept = [t for t in _items(threads) if not (_is_indirect_dict(t) and t.objgen in dead_threads)]
            if kept:
                root.Threads = Array(kept)
            else:
                del root["/Threads"]

    # ── structure tree ──────────────────────────────────────────────────────

    def prune_structure_tree(self, root) -> None:
        tree = root.get("/StructTreeRoot")
        if _type(tree) != _DICT:
            return
        tree_fields = dict(tree.items())
        kids = tree_fields.get("/K")
        if kids is None:
            return
        records = self._walk_structure(tree, kids)
        top = records[0]
        if top.had_kids and not top.kept:
            # Nothing tagged is left: say so rather than claim a tree.
            del root["/StructTreeRoot"]
            mark = root.get("/MarkInfo")
            if _type(mark) == _DICT and "/Marked" in mark:
                del mark["/Marked"]
                if not mark.keys():
                    del root["/MarkInfo"]
            for page in self.pages:
                if "/StructParents" in page:
                    del page["/StructParents"]
            return

        dead_keys = self._dead_struct_keys()

        def keep_parent_entry(key, value):
            if key in dead_keys:
                return False  # the key of a removed page or annotation
            if _type(value) == _ARRAY:
                items = _items(value)
                cleared = [
                    i for i, item in enumerate(items)
                    if _is_indirect_dict(item) and item.objgen not in self.alive_elements
                ]
                if len(cleared) + sum(item is None for item in items) == len(items):
                    return False
                for i in cleared:
                    value[i] = None
                return True
            if _is_indirect_dict(value):
                return value.objgen in self.alive_elements
            return value is not None

        parent_tree = tree_fields.get("/ParentTree")
        if parent_tree is not None and _prune_tree(parent_tree, "/Nums", keep_parent_entry) is None:
            del tree["/ParentTree"]

        def keep_id(_key, value):
            return not (_is_indirect_dict(value) and value.objgen not in self.alive_elements)

        id_tree = tree_fields.get("/IDTree")
        if id_tree is not None and _prune_tree(id_tree, "/Names", keep_id) is None:
            del tree["/IDTree"]

        for record in records[1:]:
            if not record.alive:
                continue
            refs = record.fields.get("/Ref")
            if _type(refs) == _ARRAY:
                items = _items(refs)
                kept = [r for r in items if not (_is_indirect_dict(r) and r.objgen in self.dead_elements)]
                if len(kept) != len(items):
                    if kept:
                        record.obj.Ref = Array(kept)
                    else:
                        del record.obj["/Ref"]
            parent = record.fields.get("/P")
            if _is_indirect_dict(parent) and parent.objgen in self.dead_elements:
                record.obj.P = record.parent.obj
        self.dead.update(self.dead_elements)

    def _dead_struct_keys(self) -> set:
        """ParentTree keys that belonged to removed pages and annotations."""
        dead, live = set(), set()
        for page in self.removed:
            dead.add(page.get("/StructParents"))
            for annot in _array(page.get("/Annots")):
                if _is_indirect_dict(annot) and annot.objgen in self.dead:
                    dead.add(annot.get("/StructParent"))
        if not dead:
            return dead
        for page in self.pages:
            live.add(page.get("/StructParents"))
            for annot in self.annots_of.get(page.objgen, []):
                if _type(annot) == _DICT:
                    live.add(annot.get("/StructParent"))
        dead -= live
        dead.discard(None)
        return dead

    def _walk_structure(self, tree, kids):
        """Prune the element tree below ``tree``; return its records, root first.

        Iterative, so a deep tree cannot exhaust the interpreter stack.
        """
        top = _Record(tree, {"/K": kids}, None, None)
        records = [top]
        pending = [top]
        seen: set = set()
        while pending:
            record = pending.pop()
            raw = record.fields.get("/K")
            items = _items(raw) if _type(raw) == _ARRAY else ([] if raw is None else [raw])
            record.single = _type(raw) != _ARRAY
            record.had_kids = bool(items)
            page = record.page
            for item in items:
                if _type(item) != _DICT:
                    record.kids.append((item, self._mcid_alive(item, page)))
                    continue
                fields = dict(item.items())
                if "/MCID" in fields or "/Obj" in fields or "/S" not in fields:
                    alive = self._content_alive(fields, page)
                    record.kids.append((item, alive))
                    if alive:
                        self.pending.append(item)  # /Stm, /StmOwn: the sweep's
                    continue
                if item.is_indirect:
                    if item.objgen in seen:
                        continue  # a second parent or a loop: keep the first
                    seen.add(item.objgen)
                own = fields.get("/Pg")
                child = _Record(item, fields, record, own if own is not None else page)
                records.append(child)
                record.kids.append(child)
                pending.append(child)
        for record in reversed(records):
            kept = []
            for kid in record.kids:
                if isinstance(kid, _Record):
                    if kid.alive:
                        kept.append(kid.obj)
                elif kid[1]:
                    kept.append(kid[0])
            record.kept = kept
            if record is top:
                if len(kept) != len(record.kids) and kept:
                    tree.K = Array(kept)
                continue
            elem = record.obj
            if record.had_kids:
                record.alive = bool(kept)
            else:
                record.alive = record.page is None or not self.page_dead(record.page)
            if not record.alive:
                if elem.is_indirect:
                    self.dead_elements.add(elem.objgen)
                continue
            if elem.is_indirect:
                self.alive_elements.add(elem.objgen)
            self._vet(elem, record.fields, _ELEMENT_KEYS)
            if len(kept) != len(record.kids):
                elem.K = kept[0] if record.single and len(kept) == 1 else Array(kept)
            own = record.fields.get("/Pg")
            if own is not None and self.page_dead(own):
                del elem["/Pg"]
        return records

    def _mcid_alive(self, item, page) -> bool:
        """A marked-content id: it lives on the element's page."""
        return page is None or not self.page_dead(page)

    def _content_alive(self, fields: dict, page) -> bool:
        """A marked-content reference or an object reference."""
        own = fields.get("/Pg")
        page = own if own is not None else page
        if "/Obj" in fields or fields.get("/Type") == Name.OBJR:
            target = fields.get("/Obj")
            if target is None or self.annot_dead(target):
                return False
            if _is_indirect_dict(target) and target.objgen in self.dead:
                return False
        return page is None or not self.page_dead(page)

    # ── outline ─────────────────────────────────────────────────────────────

    def prune_outline(self, catalog: dict) -> None:
        outlines = catalog.get("/Outlines")
        if _type(outlines) != _DICT:
            return
        first = outlines.get("/First")
        if first is not None:
            self._prune_outline_level(outlines, first, None, 0, set())

    def _prune_outline_level(self, parent, first, parent_open, depth: int, seen: set):
        """Prune the bookmarks under ``parent`` and relink what stays.

        A bookmark whose target was on a removed page goes, and its surviving
        children take its place. So does a heading without a target of its own
        once all its children are gone. ``parent_open`` is None for the
        outline root. Returns ``(kept, changed)``: the kept children as
        ``(item, descendants visible when it is open, is open)``, and whether
        anything at or below this level changed.
        """
        items = []
        item = first
        while _is_indirect_dict(item) and item.objgen not in seen and len(seen) < _MAX_CHAIN:
            seen.add(item.objgen)
            fields = dict(item.items())
            items.append((item, fields))
            item = fields.get("/Next")

        kept: list = []
        changed = False
        for item, fields in items:
            count = fields.get("/Count")
            is_open = isinstance(count, int) and count > 0
            child = fields.get("/First")
            children, below_changed = None, False
            if child is not None and depth < _MAX_DEPTH:
                children, below_changed = self._prune_outline_level(item, child, is_open, depth + 1, seen)
            changed = changed or below_changed
            se = fields.get("/SE")
            if se is not None and _is_indirect_dict(se) and se.objgen in self.dead:
                del item["/SE"]
            target = self._outline_target(item, fields)
            if target == _DEAD or (target is None and child is not None and children == []):
                self.kill(item)
                changed = True
                kept.extend(children or [])
                continue
            if children is None:
                # No children, or nesting too deep to follow: left as it is,
                # and the sweep still goes through whatever is below.
                below = abs(count) if isinstance(count, int) and child is not None else 0
                if child is not None:
                    self.pending.append(child)
            else:
                below = sum(1 + (b if o else 0) for _, b, o in children)
            kept.append((item, below, is_open))
            self._vet(item, fields, _OUTLINE_KEYS)
            action = item.get("/A") if "/A" in fields else None
            if _type(action) == _DICT:
                self.pending.append(action)  # its keys beyond /D and /Next

        if not changed:
            return kept, False
        for i, (item, _, _) in enumerate(kept):
            item.Parent = parent
            if i:
                item.Prev = kept[i - 1][0]
            elif "/Prev" in item:
                del item["/Prev"]
            if i + 1 < len(kept):
                item.Next = kept[i + 1][0]
            elif "/Next" in item:
                del item["/Next"]
        if not kept:
            for key in ("/First", "/Last", "/Count"):
                if key in parent:
                    del parent[key]
            return kept, True
        parent.First = kept[0][0]
        parent.Last = kept[-1][0]
        visible = sum(1 + (b if o else 0) for _, b, o in kept)
        # Open when /Count is positive; a closed bookmark stores the number
        # negated (PDF 12.3.3). The root counts everything visible.
        parent.Count = visible if parent_open is None or parent_open else -visible
        return kept, True

    def _outline_target(self, item, fields: dict):
        """_DEAD or _LIVE for a bookmark with a target, None without one."""
        states = []
        if "/Dest" in fields:
            states.append(self.dest_state(fields["/Dest"]))
        action = fields.get("/A")
        if action is not None:
            pruned = self.prune_action(action)
            if pruned is None:
                states.append(_DEAD)
            else:
                if pruned is not action:
                    item.A = pruned
                states.append(_LIVE)
        if not states:
            return None
        return _DEAD if all(state == _DEAD for state in states) else _LIVE

    # ── catalog ─────────────────────────────────────────────────────────────

    def prune_catalog(self, root) -> None:
        opener = root.get("/OpenAction")
        if _type(opener) == _ARRAY:
            if self.dest_state(opener) == _DEAD:
                del root["/OpenAction"]
        elif _type(opener) == _DICT:
            pruned = self.prune_action(opener)
            if pruned is None:
                del root["/OpenAction"]
            elif pruned is not opener:
                root.OpenAction = pruned
        aa = root.get("/AA")
        if aa is not None:
            self.prune_additional_actions(root, aa)
        names = root.get("/Names")
        pages_tree = names.get("/Pages") if _type(names) == _DICT else None
        if pages_tree is not None:
            def keep(_key, value):
                return not (_type(value) == _DICT and self.page_dead(value))

            if _prune_tree(pages_tree, "/Names", keep) is None:
                del names["/Pages"]

    def _vet(self, obj, fields: dict, known: frozenset) -> None:
        """Record that a pass checked ``obj``'s ``known`` keys; queue the rest."""
        for key, value in fields.items():
            if key not in known and _type(value) in (_DICT, _ARRAY, _STREAM):
                self.pending.append(value)
        if obj.is_indirect:
            self.vetted.add(obj.objgen)

    # ── the sweep ───────────────────────────────────────────────────────────

    def sweep(self) -> None:
        """Cut every remaining reference to a removed object.

        Everything reachable from the trailer is visited once, except values
        the specification limits to numbers and names (``_NUMBERS_ONLY``) and
        what a pass already read in full. A reference to a removed page,
        annotation, bead, field, structure element or thread is deleted from
        its dictionary, or replaced by null in its array, so nothing that
        belonged to a removed page is written. So is one to any other page
        object outside the page tree, such as one an earlier tool left behind,
        and, in a copied document, to an annotation on no page.
        """
        dead = self.dead
        live_pages = self.live_pages
        templates = self.template_pages
        exact = self.exact
        live_annots = self.live_annots
        containers = (_DICT, _ARRAY, _STREAM)
        # Vetted objects count as visited; what they left over is queued.
        verdicts: dict = dict.fromkeys(self.vetted, False)
        stack: list = [(self.pdf.trailer, None)]
        for obj in self.pending:
            if not obj.is_indirect:
                stack.append((obj, None))
            elif obj.objgen not in verdicts:
                verdicts[obj.objgen] = obj.objgen in dead
                if not verdicts[obj.objgen]:
                    stack.append((obj, None))
        cut = 0

        def is_dead(value, og) -> bool:
            verdict = verdicts.get(og)
            if verdict is None:
                fields = None
                verdict = og in dead
                if not verdict and value._type_code == _DICT and og not in live_pages:
                    fields = dict(value.items())
                    verdict = (
                        (fields.get("/Type") == Name.Page and og not in templates)
                        or (not exact and og not in live_annots and _is_annotation(fields))
                    )
                verdicts[og] = verdict
                if not verdict:
                    stack.append((value, fields))  # visited once, from here
            return verdict

        while stack:
            obj, fields = stack.pop()
            if obj._type_code == _ARRAY:
                doomed = []
                for i, value in enumerate(obj):
                    if getattr(value, "_type_code", None) not in containers:
                        continue
                    if not value.is_indirect:
                        stack.append((value, None))
                    elif is_dead(value, value.objgen):
                        doomed.append(i)
                for i in doomed:
                    obj[i] = None
                cut += len(doomed)
                continue
            doomed = []
            for key, value in (fields.items() if fields is not None else obj.items()):
                if key in _NUMBERS_ONLY or getattr(value, "_type_code", None) not in containers:
                    continue
                if not value.is_indirect:
                    stack.append((value, None))
                elif is_dead(value, value.objgen):
                    doomed.append(key)
            for key in doomed:
                del obj[key]
            cut += len(doomed)
        if cut:
            logger.debug("page removal: cut %d stray references to removed objects", cut)


class _Record:
    """One structure element during pruning."""

    __slots__ = ("obj", "fields", "parent", "page", "kids", "kept", "alive", "had_kids", "single")

    def __init__(self, obj, fields: dict, parent, page):
        self.obj = obj
        self.fields = fields
        self.parent = parent
        self.page = page
        self.kids: list = []
        self.kept: list = []
        self.alive = True
        self.had_kids = False
        self.single = False
