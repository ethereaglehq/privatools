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

The pruner then makes the document agree with its page tree, in two layers.

Repair passes keep the rest of the document working. Destinations, links,
bookmarks, named destinations, form fields, threads and the structure tree lose
whatever points at a page that is not in the tree: a bookmark whose page went
is removed and its children move up, a field keeps its widgets on the remaining
pages, a tagged document stays tagged. A piece a pass cannot read is dropped,
or left to the sweep when it belongs to a page that stays, and the pass carries
on. A pass that fails outright drops the whole structure it was repairing
(the outline, the form, the tags, the threads) rather than leave it half done.

A sweep then walks everything reachable from the trailer and cuts any
reference to a removed page, annotation, bead, field, structure element or
thread that is left, to any other page object outside the page tree, and to
what a damaged or crafted file hides from the passes (see :meth:`_Pruner.sweep`).
It skips only the structure elements the tree pass read in full, and reads a
long array item by item only when its serialization holds a reference or a
page.

The catalog, the page tree and the kept pages are never cut or killed,
whatever points at them: the set of removed objects refuses them (a crafted
file can put them where a pass expects an annotation, a bead or a structure
element), and the sweep never cuts a reference to them. Passes still edit
them, as they must: a kept page's /Annots, the catalog's /OpenAction.

A mistake in a pass could still hide a page reference from the sweep, so
:meth:`PageRemoval.save` checks what it wrote, with a walk of its own that
takes none of the sweep's verdicts. The page tree it writes must list exactly
the pages kept, and no other page object may reach the output. A stray page
means a reference the sweep skipped: it sweeps again skipping nothing and
saves again. If a page is still stray, or the page tree is not the one
expected, it deletes the output and raises :class:`PageLeakError` (HTTP 422)
rather than return a file that holds removed pages or lost kept ones.

Every pass is meant to take time in proportion to what it reads, and every
review of this module found another way to share objects that made a pass
read or copy one of them once per owner. So the work is counted too, against
one :class:`WorkBudget` per request that all its jobs share, and a request
that takes far more than its upload warrants is refused the same way
(:class:`PageWorkError`), as is an output with far more objects than its
input: a shape nobody has found yet costs linear work, then a clear 422.

Not handled, because none of it points at a page: document-level objects that
only a removed page used, such as an optional-content layer, a named
JavaScript, an attachment or an XMP thumbnail, stay in the file.

Performance: pikepdf reads an object from the file the first time it is
touched, and each key lookup costs about a microsecond, so the passes read each
object once, through ``items()``. Shared objects (an action chain shared by
many links, a bead ring shared by many threads, an array shared by many pages
or elements, a list of bookmarks shared by many headings) are handled once,
not once per owner, and verdicts about them are remembered: hostile files are
built that way, and a walk per owner is quadratic, or exponential when
owners nest.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from contextvars import ContextVar
from decimal import Decimal
from pathlib import Path
from typing import NoReturn

import pikepdf
from pikepdf import Array, Name, ObjectType

from .exceptions import ToolError

logger = logging.getLogger(__name__)

# Guards against malformed or hostile input: the nesting depth of trees and
# action chains, and the length of linked lists (outline siblings, bead rings).
_MAX_DEPTH = 64
_MAX_CHAIN = 1_000_000
# The sweep keeps a dictionary's entries, read to judge it, for its visit, but
# only while fewer objects than this wait: a wide array of dictionaries would
# otherwise hold all their entries at once.
_HELD = 4096

_DICT = ObjectType.dictionary
_ARRAY = ObjectType.array
_STREAM = ObjectType.stream
_STRING = ObjectType.string
_NAME = ObjectType.name_
# A stream's dictionary works wherever a dictionary is expected: PDFium reads
# it there (GetDictFor, GetDictAt), so the passes must too.
_DICTLIKE = (_DICT, _STREAM)
_CONTAINERS = (_DICT, _ARRAY, _STREAM)
# What pikepdf hands back for PDF numbers, booleans and null.
_SCALARS = frozenset((int, bool, float, Decimal, type(None)))
# Compared on every object the sweep visits. pikepdf builds a new Name on each
# attribute access (``Name.Page`` costs a microsecond), so these are built once.
_PAGE = Name.Page
_ANNOT = Name.Annot
_BEAD = Name.Bead
_CONTENT_TYPES = frozenset((Name.MCR, Name.OBJR))
# What the sweep judges an object by its /Type as. _ROOT: a type a document has
# one of, reached only from its catalog (and a root from its own items); another
# one in the output was carried in with a copied page by a reference no valid
# file makes, with everything under it.
_SWEPT_PAGE, _SWEPT_ROOT, _SWEPT_ELEMENT, _SWEPT_BEAD, _SWEPT_ANNOT = range(5)
_SWEPT_TYPES = {
    Name.Page: _SWEPT_PAGE,
    Name.Catalog: _SWEPT_ROOT,
    Name.Outlines: _SWEPT_ROOT,
    Name.StructTreeRoot: _SWEPT_ROOT,
    Name.StructElem: _SWEPT_ELEMENT,
    Name.Bead: _SWEPT_BEAD,
    Name.Annot: _SWEPT_ANNOT,
}

# An array this long is first checked as a whole, in qpdf's serialization,
# for an object reference or a page dictionary. Without either, nothing in it
# can lead to a page: a font's widths (a /W of thousands of numbers is copied
# into every part a split writes), a function's samples, an ink path.
_SCAN = 64

# Keys of a structure element whose values the tree pass follows itself.
# Everything else an element holds is left to the sweep.
_ELEMENT_WALKED = frozenset(("/K", "/P", "/Pg", "/Ref"))
# Text an element carries for all its content: once part of that content was
# on a removed page, the text describes the removed part too.
_ELEMENT_TEXTS = ("/ActualText", "/Alt", "/E")

_LIVE = "live"
_DEAD = "dead"
_UNKNOWN = "unknown"
_MISSING = object()
# Stands for "a removed page" where a structure element's /Pg is not a page.
_REMOVED_PAGE = object()
# Returned for something in a name or number tree's place that is no tree node.
_FOREIGN = object()
# A bookmark list being settled: a list that reaches it again counts it as
# surviving.
_PENDING = object()
# What the memo of pruned actions holds for an action that stays as it is:
# each owner then gets its own object back, and can tell nothing changed.
_SAME = object()
# An explicit destination holds at most a type and four numbers after its
# page (/FitR left bottom right top).
_MAX_VIEW = 5


class PageLeakError(ToolError):
    """Removed pages would still be in the output, so none is returned (HTTP 422)."""

    status_code = 422
    default_detail = (
        "The pages could not be removed completely: something in this PDF still "
        "points to them in a way that cannot be undone safely, so no file was made."
    )


class PageWorkError(PageLeakError):
    """Removing the pages would take far longer than the file warrants (HTTP 422)."""

    default_detail = (
        "This PDF is built in a way that would take far too long to process "
        "safely, so no file was made."
    )


# Set on a Pdf whose structure tree prune_structure_tree_to_pages pruned.
_PRUNED_TO = "_page_removal_tags_pruned_to"

# ── the work budget ─────────────────────────────────────────────────────────
#
# A step is an entry of a dictionary or an item of an array read, an item of
# an array made, or a link of a chain followed. A request may take
# _STEPS_FLOOR steps, once, and the larger of _STEPS_PER_BYTE for each byte
# uploaded and _STEPS_PER_OBJECT for each object of the documents it builds
# by copying; past that it is refused. Bytes, not objects: a valid tagged
# file can hold hundreds of marked-content ids per object, and pruning reads
# each of them, but each takes room in the file. Measured on 376 requests
# over real and generated files, every tool included, a request took at most
# 0.08 steps per byte uploaded (0.07 on the third-party files), and 103,000
# steps in all; a file tagged word by word takes about 0.5.
_STEPS_PER_BYTE = 25
_STEPS_PER_OBJECT = 100
_STEPS_FLOOR = 1_000_000
# An output may hold _GROWTH times the objects of its input, plus
# _GROWTH_FLOOR. Pruning removes objects; the few it makes replace others.
_GROWTH = 2
_GROWTH_FLOOR = 10_000


class _OutOfSteps(BaseException):
    """A request went past its budget.

    Not an Exception: the passes contain their own errors with ``except
    Exception``, one bad object at a time, and this must stop the whole job.
    """


class WorkBudget:
    """The steps one request may take, shared by all its jobs.

    A tool's service makes one per request, sized by the bytes uploaded
    (:meth:`for_files`), and passes it to every page removal call: the
    copier, each part's pruning and save, the structure prunes. A request
    that removes pages from one document, or writes a part for every page,
    has one budget, whose floor counts once. ``tool`` is the route's name,
    for the log of a refusal.
    """

    __slots__ = ("tool", "size", "objects", "used", "limit")

    def __init__(self, tool: str, size: int):
        self.tool = tool
        self.size = size  # bytes uploaded
        self.objects = 0  # in the documents built by copying, before pruning
        self.used = 0
        self.limit = _STEPS_FLOOR + _STEPS_PER_BYTE * size

    @classmethod
    def for_files(cls, tool: str, *paths) -> WorkBudget:
        """A budget for a request that uploaded the files at ``paths``."""
        size = 0
        for path in paths:
            try:
                size += os.path.getsize(path)
            except (OSError, TypeError, ValueError):
                pass  # not a file: the floor still stands
        return cls(tool, size)

    def add_objects(self, count: int) -> None:
        """A document built by copying holds ``count`` objects to prune."""
        self.objects += count
        self.limit = _STEPS_FLOOR + max(
            _STEPS_PER_BYTE * self.size, _STEPS_PER_OBJECT * self.objects,
        )

    @contextmanager
    def charging(self):
        """Count the steps taken inside; past the budget, refuse the request."""
        token = _BUDGET.set(self)
        try:
            yield self
        except _OutOfSteps:
            _refuse(
                self.tool,
                f"its work passed {self.limit} steps, allowed for {self.size} bytes "
                f"uploaded and {self.objects} objects copied",
                PageWorkError,
            )
        finally:
            _BUDGET.reset(token)


_BUDGET: ContextVar[WorkBudget | None] = ContextVar("page_removal_budget", default=None)


def _charge(steps: int) -> None:
    """Count ``steps`` against the running request's budget."""
    budget = _BUDGET.get()
    if budget is not None:
        budget.used += steps
        if budget.used > budget.limit:
            raise _OutOfSteps


def _refuse(tool: str, problem: str, error: type[PageLeakError] = PageLeakError) -> NoReturn:
    # Counts and structure only: no text of the document is logged.
    logger.error(
        "page removal refused the output of %s: %s", tool, problem,
        extra={"error_class": "PageLeakError"},
    )
    raise error() from None


def remove_pages(pdf: pikepdf.Pdf, indices: Iterable[int], *, budget: WorkBudget) -> PageRemoval:
    """Delete the pages at the 0-based ``indices`` and everything pointing at them.

    ``budget`` is the request's (:class:`WorkBudget`). Save the result with
    :meth:`PageRemoval.save`.
    """
    with budget.charging():
        pages = _page_objs(pdf)
        doomed = sorted(set(indices), reverse=True)
        removed = [pages[i] for i in doomed]
        if doomed:
            _repair_page_count(pdf, len(pages))
        for i in doomed:
            del pdf.pages[i]
        pruner = _Pruner(pdf, removed=removed)
        pruner.run()
    # The file's objects are not counted: a crafted cross-reference table can
    # claim objects that are not there almost for free, and counting its
    # entries costs memory. A real file holds fewer than a quarter of its
    # bytes (the densest one made to test this holds one in 7 bytes).
    return PageRemoval(pdf, pruner, budget, input_objects=budget.size // 4)


def prune_to_page_tree(pdf: pikepdf.Pdf, *, budget: WorkBudget) -> PageRemoval:
    """Drop every reference to a page that is not in ``pdf``'s page tree.

    For a document built by copying pages in (:class:`PageCopier`), right
    before it is saved. Anything that belongs to no page of ``pdf``, such as an
    annotation in no page's /Annots or a bead in no page's /B, came from a page
    that was left behind and is dropped with it. ``budget`` is the request's
    (:class:`WorkBudget`). Save the result with :meth:`PageRemoval.save`.
    """
    objects = len(pdf.objects)  # before pruning: built in memory, cheap to count
    budget.add_objects(objects)
    with budget.charging():
        pruner = _Pruner(pdf, removed=None)
        pruner.run()
    return PageRemoval(pdf, pruner, budget, input_objects=objects)


def prune_structure_tree_to_pages(
    pdf: pikepdf.Pdf, indices: Iterable[int], *, budget: WorkBudget | None = None,
) -> None:
    """Prune ``pdf``'s structure tree, in memory, to the pages at ``indices``.

    For tools that copy a structure tree into a new document. qpdf turns the
    /Pg of an element whose page was not copied into null, and a null /Pg reads
    exactly like no /Pg at all, so the elements of the pages left behind cannot
    be told apart afterwards. The tree has to be pruned in the source, while
    every page reference is intact, and copied after. Only the structure tree
    changes, and, when nothing tagged survives, the pages' /StructParents and
    the catalog's /MarkInfo /Marked. ``pdf`` must not be saved afterwards.

    A second call for the same pages does nothing: Extract and Merge prune
    before copying pages, so no copied page can carry the unpruned tree, and
    the tree is then carried over by functions that prune it themselves.
    ``budget`` is the request's (:class:`WorkBudget`); without one, the file
    ``pdf`` was read from sizes a budget of its own.
    """
    keep = frozenset(indices)
    if getattr(pdf, _PRUNED_TO, None) == keep:
        return
    if budget is None:
        budget = WorkBudget.for_files("structure-tree", pdf.filename)
    with budget.charging():
        pages = _page_objs(pdf)
        if keep >= set(range(len(pages))):
            return
        pruner = _Pruner(
            pdf,
            removed=[page for i, page in enumerate(pages) if i not in keep],
            live_pages={pages[i].objgen for i in keep},
        )
        pruner.prune_structure_tree(pdf.Root)
    try:
        setattr(pdf, _PRUNED_TO, keep)
    except AttributeError:  # a pikepdf without instance attributes: prune again
        pass


class PageRemoval:
    """A document whose removed pages have been pruned, ready to save."""

    def __init__(self, pdf: pikepdf.Pdf, pruner: _Pruner, budget: WorkBudget, *, input_objects: int):
        self.pdf = pdf
        self._pruner = pruner
        self._budget = budget
        # At least the objects of the document before pruning (see _GROWTH).
        self._input_objects = input_objects
        # The pages the output's page tree must list, in order.
        self.expected = [page.objgen for page in pruner.pages]

    def save(self, path) -> None:
        """Save to ``path``, and refuse an output that holds removed pages.

        After saving, what the save wrote is checked. Its page tree, read from
        /Kids as written, must list the pages kept and nothing else: a cut in
        the tree would lose a kept page, or leave a file no reader can open.
        And every object the save wrote, that is everything reachable from the
        trailer, is walked, and no page object may be outside that tree. A
        stray page means a reference the sweep skipped: the document is swept
        again with no shortcuts and saved again. If the tree is wrong, a page
        still stray, or the output holds far more objects than the input (see
        _GROWTH), the output is deleted, the refusal logged with the tool's
        name and the reason, and :class:`PageLeakError` raised. The second
        sweep counts against the request's budget. An output that could not be
        saved or checked is deleted too, and the error raised.

        The check walks the document in memory rather than reading the file
        back: on a 500-page file that costs a quarter of the time, and it does
        not hold a second parsed copy of every object.
        """
        path = str(path)
        tool = self._budget.tool
        try:
            with self._budget.charging():
                self.pdf.save(path)
                problem, stray = self._check()
                if problem is None and stray:
                    logger.warning(
                        "page removal in %s: %d page object(s) outside the page tree "
                        "reached the output; sweeping again without shortcuts", tool, stray,
                    )
                    self._pruner.sweep(exhaustive=True)
                    self.pdf.save(path)
                    problem, stray = self._check()
                    if problem is None and stray:
                        problem = f"{stray} page object(s) outside the page tree after a second sweep"
                if problem is not None:
                    _refuse(tool, problem)
        except BaseException:
            # Whatever stopped the check, an output it did not pass is not left behind.
            Path(path).unlink(missing_ok=True)
            raise

    def _check(self) -> tuple[str | None, int]:
        """(what is wrong with the output or None, stray page objects)."""
        written, problem = _written_pages(self.pdf)
        if problem is not None:
            return problem, 0
        if written != self.expected:
            if len(written) != len(self.expected):
                return f"the page tree lists {len(written)} pages, {len(self.expected)} expected", 0
            return f"the page tree lists other pages than the {len(written)} expected", 0
        stray, objects = _pages_outside_tree(self.pdf, written, self._pruner.inert)
        allowed = _GROWTH * self._input_objects + _GROWTH_FLOOR
        if objects > allowed:
            return f"it holds {objects} objects, {allowed} allowed for {self._input_objects} in its input", 0
        return None, stray


class PageCopier:
    """Copies pages out of one document into new ones.

    Named destinations stay behind with the source's catalog, so a link on a
    copied page that names its target would lead nowhere in the copy. Each
    such name is replaced by an explicit destination when its target page is
    copied too, and by a null one when it is not, which
    :func:`prune_to_page_tree` then removes. Build one copier per source and
    reuse it across the documents made from it, so the name tree is read once.

    Before a page is copied, the structure destinations (/SD) of the GoTo
    actions on it are deleted from the source. An /SD names a structure
    element, and through its /P chain the whole unpruned structure tree would
    be copied with the page, tags of the pages left behind included. The /D
    each such action must also have keeps the link working.

    ``budget`` is the request's (:class:`WorkBudget`); its copies count
    against it.
    """

    def __init__(self, src: pikepdf.Pdf, *, budget: WorkBudget):
        self.src = src
        self.budget = budget
        self._pages: list | None = None
        self._string_dests: dict[bytes, object] | None = None
        self._name_dests: dict[str, object] | None = None
        self._stripped: set = set()
        self._strip_seen: set = set()  # fields and actions already stripped
        self._strip_annots: set = set()  # annotations and /Annots arrays already read

    def copy(self, dst: pikepdf.Pdf, indices: Iterable[int]) -> None:
        """Append ``src.pages[i]`` for each index to ``dst``, in order."""
        with self.budget.charging():
            self._copy(dst, list(indices))

    def _copy(self, dst: pikepdf.Pdf, indices: list) -> None:
        if self._pages is None:
            # One pass: `pages[i]` costs a copy of the whole page list.
            self._pages = [page for page in self.src.pages]
        for i in indices:
            page = self._pages[i].obj
            if page.objgen not in self._stripped:
                self._stripped.add(page.objgen)
                self._strip_structure_destinations(page)
        start = len(dst.pages)
        for i in indices:
            dst.pages.append(self._pages[i])
        copied = _page_objs(dst)[start:]
        page_map: dict[tuple[int, int], object] = {}
        for i, page in zip(indices, copied):
            page_map.setdefault(self._pages[i].obj.objgen, page)
        seen: set = set()  # one walk per copy: shared actions are read once
        resolved: dict = {}  # name -> (page, view) or None, looked up once per copy
        for page in copied:
            for owner, key, value in _destination_slots(page, seen):
                if _type(value) in (_STRING, _NAME):
                    try:
                        self._resolve(owner, key, value, page_map, resolved)
                    except Exception:  # noqa: BLE001 - left as it is; the pruner judges it
                        logger.debug("page copy: named destination not resolved", exc_info=True)

    def _strip_structure_destinations(self, page) -> None:
        owners = [page]
        for annot in _unread(page.get("/Annots"), self._strip_annots):
            if _type(annot) not in _DICTLIKE:
                continue
            if annot.is_indirect:
                if annot.objgen in self._strip_annots:
                    continue
                self._strip_annots.add(annot.objgen)
            owners.append(annot)
            parent, steps = annot.get("/Parent"), 0
            while _type(parent) in _DICTLIKE and steps < _MAX_DEPTH:
                _charge(1)
                if parent.is_indirect:
                    if parent.objgen in self._strip_seen:
                        break
                    self._strip_seen.add(parent.objgen)
                owners.append(parent)
                parent, steps = parent.get("/Parent"), steps + 1
        for owner in owners:
            try:
                for action in _owner_actions(owner, self._strip_seen):
                    for step in _action_chain(action, self._strip_seen):
                        if step.get("/S") == Name.GoTo and "/SD" in step:
                            del step["/SD"]
            except Exception:  # noqa: BLE001 - one unreadable owner must not stop the copy
                logger.debug("page copy: could not read an action", exc_info=True)

    def _resolve(self, owner, key: str, value, page_map: dict, resolved: dict) -> None:
        """Replace a named destination by an explicit one to the copied page.

        Each name is looked up once per copy, however many links name it.
        """
        name = (bytes(value), None) if _type(value) == _STRING else (None, str(value))
        found = resolved.get(name, _MISSING)
        if found is _MISSING:
            found = resolved[name] = self._explicit_view(value, page_map)
        if found is not None:
            page, view = found
            owner[key] = _new_array([page, *view])

    def _explicit_view(self, value, page_map: dict):
        """(the copied page or None, the view) a name stands for, or None."""
        if _type(value) == _STRING:
            dest = self._lookup_string(bytes(value))
        else:
            dest = self._lookup_name(str(value))
        if dest is None:
            return None  # not a name the source defines either; nothing to resolve
        view = _items(dest)
        target = view.pop(0) if view else None
        page = page_map.get(target.objgen) if _is_indirect_dictlike(target) else None
        # A longer view is no view at all, and it would be copied into every
        # link that names it.
        if page is None or len(view) > _MAX_VIEW or any(getattr(v, "is_indirect", False) for v in view):
            view = [Name.Fit]
        return page, view

    def _lookup_string(self, name: bytes):
        if self._string_dests is None:
            self._string_dests = {}
            names = self.src.Root.get("/Names")
            tree = names.get("/Dests") if _type(names) in _DICTLIKE else None
            for key, value in _tree_entries(tree, "/Names"):
                if _type(key) == _STRING:
                    self._string_dests.setdefault(bytes(key), value)
        return _explicit(self._string_dests.get(name))

    def _lookup_name(self, name: str):
        if self._name_dests is None:
            self._name_dests = {}
            dests = self.src.Root.get("/Dests")
            if _type(dests) in _DICTLIKE:
                self._name_dests.update(_entries(dests))
        return _explicit(self._name_dests.get(name))


def copy_pages(dst: pikepdf.Pdf, src: pikepdf.Pdf, indices: Iterable[int], *, budget: WorkBudget) -> None:
    """Append ``src``'s pages at ``indices`` to ``dst``; see :class:`PageCopier`."""
    PageCopier(src, budget=budget).copy(dst, indices)


# ── helpers ─────────────────────────────────────────────────────────────────


def _type(obj):
    return getattr(obj, "_type_code", None)


def _is_indirect_dictlike(obj) -> bool:
    return _type(obj) in _DICTLIKE and obj.is_indirect


def _items(array) -> list:
    items = [item for item in array]
    _charge(len(items))
    return items


def _entries(obj):
    """A dictionary's or stream's entries, read at once."""
    entries = obj.items().mapping
    _charge(len(entries))
    return entries


def _new_array(items: list) -> Array:
    _charge(len(items))
    return Array(items)


def _same(a, b) -> bool:
    """True for one object: the same wrapper, or the same indirect object."""
    return a is b or (
        getattr(a, "is_indirect", False) and getattr(b, "is_indirect", False) and a.objgen == b.objgen
    )


def _array(obj) -> list:
    return _items(obj) if _type(obj) == _ARRAY else []


def _unread(obj, seen: set):
    """The items of an array, or nothing when it is indirect and in ``seen``."""
    if _type(obj) != _ARRAY:
        return ()
    if obj.is_indirect:
        if obj.objgen in seen:
            return ()
        seen.add(obj.objgen)
    _charge(len(obj))
    return obj


def _distinct(lists):
    """Each list once, however many owners share it.

    The passes keep one list per page, and pages that share an /Annots or /B
    array share one list object. The lists must stay referenced while this
    runs, so identities are not reused.
    """
    done: set = set()
    for items in lists:
        if id(items) not in done:
            done.add(id(items))
            yield items


def _read_array(obj, cache: dict) -> list:
    """The items of an array, read once however many pages share it."""
    if _type(obj) != _ARRAY:
        return []
    if not obj.is_indirect:
        return _items(obj)
    items = cache.get(obj.objgen)
    if items is None:
        items = cache[obj.objgen] = _items(obj)
    return items


def _first(array):
    for item in array:
        return item
    return None


def _page_objs(pdf: pikepdf.Pdf) -> list:
    # Iterate: `pdf.pages[i]` copies qpdf's whole page list on every call.
    return [page.obj for page in pdf.pages]


def _int_key(value, keys: set) -> None:
    """Add a ParentTree key; anything but an integer is not one."""
    if type(value) is int:
        keys.add(value)


def _repair_page_count(pdf: pikepdf.Pdf, count: int) -> None:
    """Make the root /Count agree with the pages qpdf found.

    Removing a page makes qpdf rebuild the tree from /Kids and then refuse a
    root /Count that disagrees ("/Count is wrong after flattening pages
    tree"); the number of pages it found is the right one.
    """
    try:
        node = pdf.Root.get("/Pages")
        if _type(node) in _DICTLIKE and node.get("/Count") != count:
            node["/Count"] = count
    except Exception:  # noqa: BLE001 - qpdf reports the problem itself if it matters
        logger.debug("page removal: could not repair /Count", exc_info=True)


def _written_pages(pdf: pikepdf.Pdf) -> tuple[list, str | None]:
    """The pages the page tree lists, in order, as a save writes them.

    Read from the catalog's /Pages and each node's /Kids, not from qpdf's list
    of pages: qpdf keeps that list for its pages API, and a reference cut
    from /Kids, or the /Pages entry cut from the catalog, does not change it.
    Returns the pages' object ids and None, or what makes the tree unreadable:
    no catalog, no page tree, a /Count that does not match. The reason names
    no text of the document.
    """
    root = pdf.trailer.get("/Root")
    if _type(root) not in _DICTLIKE:
        return [], "the output has no catalog"
    tree = root.get("/Pages")
    if _type(tree) not in _DICTLIKE:  # direct, as some files have it, or indirect
        return [], "the output has no page tree"
    pages: list = []
    seen: set = set()  # indirect inner nodes: one met again is a loop, not read twice
    stack = [iter((tree,))]
    while stack:
        node = next(stack[-1], _MISSING)
        if node is _MISSING:
            stack.pop()
            continue
        if _type(node) not in _DICTLIKE:
            continue  # neither a node nor a page: not listed
        kids = node.get("/Kids")
        if _type(kids) != _ARRAY:
            pages.append(node.objgen if node.is_indirect else None)
        elif node.is_indirect and node.objgen in seen:
            continue
        elif len(stack) > _MAX_DEPTH:
            return pages, "the page tree is nested too deep"
        else:
            if node.is_indirect:
                seen.add(node.objgen)
            stack.append(iter(kids))
    count = tree.get("/Count")
    if type(count) is not int:
        return pages, "the page tree's /Count is not a number"
    if count != len(pages):
        return pages, f"the page tree's /Count says {count}, it lists {len(pages)} pages"
    return pages, None


def _pages_outside_tree(pdf: pikepdf.Pdf, listed, inert: set = frozenset()) -> tuple[int, int]:
    """(page objects reachable from the trailer that the page tree does not
    list, objects reachable from the trailer).

    That is what a save writes: qpdf writes every object reachable from the
    trailer, and nothing else. ``listed`` names the pages the written tree
    lists (:func:`_written_pages`). The walk is not the sweep's and takes none
    of its verdicts: it reads every value, except the long arrays that hold no
    reference or page (:func:`_holds_no_objects`). ``inert`` names indirect
    ones the sweep already found so, which it does not search again. A page
    dictionary written in place, which no page tree can list, counts too.
    """
    listed = set(listed)
    names = pdf.Root.get("/Names")
    if _type(names) in _DICTLIKE:
        # Template pages live outside the page tree on purpose (PDF 12.7.6).
        for _, page in _tree_entries(names.get("/Templates"), "/Names"):
            if _is_indirect_dictlike(page):
                listed.add(page.objgen)
    seen: set = set()
    stray = 0
    stack = [pdf.trailer]
    while stack:
        obj = stack.pop()
        if obj._type_code == _ARRAY:
            if len(obj) >= _SCAN and (
                (obj.is_indirect and obj.objgen in inert) or _holds_no_objects(obj)
            ):
                continue
            values = obj
        else:
            fields = obj.items().mapping
            if fields.get("/Type") == _PAGE and not (obj.is_indirect and obj.objgen in listed):
                stray += 1
            values = fields.values()
        for value in values:
            if value.__class__ in _SCALARS or getattr(value, "_type_code", None) not in _CONTAINERS:
                continue
            if value.is_indirect:
                og = value.objgen
                if og in seen:
                    continue
                seen.add(og)
            stack.append(value)
    return stray, len(seen)


def _explicit(dest):
    """The explicit destination array behind a named-destination value."""
    if _type(dest) in _DICTLIKE:
        dest = dest.get("/D")
    return dest if _type(dest) == _ARRAY else None


def _indirect(lists) -> set:
    """The ids of the indirect dictionaries and streams in the lists."""
    found: set = set()
    for items in _distinct(lists):
        for item in items:
            if _is_indirect_dictlike(item):
                found.add(item.objgen)
    return found


def _is_bead(obj) -> bool:
    """A bead has a rectangle and neighbours, or says it is one.

    Not its page: in a copy, the /P of a bead whose page was left behind is
    null, and that bead must still be found to be removed.
    """
    return ("/R" in obj and ("/N" in obj or "/V" in obj)) or obj.get("/Type") == _BEAD


def _is_annotation(obj) -> bool:
    """For a pikepdf dictionary or stream, or a plain dict of its entries."""
    return obj.get("/Type") == _ANNOT or ("/Rect" in obj and "/Subtype" in obj)


def _holds_no_objects(array) -> bool:
    """True for an array that references no object and holds no page.

    Walking a long array of numbers item by item costs a few microseconds an
    item; qpdf writes it out a few times faster, and a search of the text
    finds any reference (``N G R``) or page dictionary (``/Page``) in it.
    """
    for i, value in enumerate(array):
        if i == 8:
            break
        if getattr(value, "is_indirect", False):
            return False  # it references objects: no need to look further
    raw = array.unparse(resolved=True)
    return b" R" not in raw and b"/Page" not in raw


def _owner_actions(owner, seen: set):
    """The actions an annotation, field or page holds in /A and /AA.

    An /AA dictionary shared by many owners is read once: ``seen`` holds the
    ones already read.
    """
    action = owner.get("/A")
    if action is not None:
        yield action
    aa = owner.get("/AA")
    if _type(aa) in _DICTLIKE:
        if aa.is_indirect:
            if aa.objgen in seen:
                return
            seen.add(aa.objgen)
        yield from _entries(aa).values()


def _action_chain(action, seen: set, depth: int = 0):
    """Each action in a chain (the action and its /Next), each object once."""
    if depth > _MAX_DEPTH or _type(action) not in _DICTLIKE:
        return
    if action.is_indirect:
        if action.objgen in seen:
            return
        seen.add(action.objgen)
    _charge(1)
    yield action
    nxt = action.get("/Next")
    # A /Next array shared by many actions is read once, like its actions.
    for sub in (_unread(nxt, seen) if _type(nxt) == _ARRAY else [nxt]):
        yield from _action_chain(sub, seen, depth + 1)


def _destination_slots(page, seen: set):
    """(owner, key, value) for each destination on a page and its annotations.

    ``seen`` is shared by every page of one copy, so an annotation, action or
    /Annots array shared by many owners is read once.
    """
    for annot in _unread(page.get("/Annots"), seen):
        if _type(annot) not in _DICTLIKE:
            continue
        if annot.is_indirect:
            if annot.objgen in seen:
                continue
            seen.add(annot.objgen)
        dest = annot.get("/Dest")
        if dest is not None:
            yield annot, "/Dest", dest
        for action in _owner_actions(annot, seen):
            yield from _goto_slots(action, seen)
    aa = page.get("/AA")
    if _type(aa) in _DICTLIKE:
        for action in _entries(aa).values():
            yield from _goto_slots(action, seen)


def _goto_slots(action, seen: set):
    for step in _action_chain(action, seen):
        if step.get("/S") == Name.GoTo and "/D" in step:
            yield step, "/D", step.get("/D")


def _tree_entries(node, leaf_key: str, depth: int = 0, seen: set | None = None):
    """Yield (key, value) pairs of a name or number tree, in order."""
    if seen is None:
        seen = set()
    if depth > _MAX_DEPTH or _type(node) not in _DICTLIKE:
        return
    if node.is_indirect:
        if node.objgen in seen:
            return
        seen.add(node.objgen)
    entries = node.get(leaf_key)
    if _type(entries) == _ARRAY:
        _charge(len(entries))
        it = iter(entries)
        for key in it:
            value = next(it, _MISSING)
            if value is _MISSING:
                break
            yield key, value
    for kid in _array(node.get("/Kids")):
        yield from _tree_entries(kid, leaf_key, depth + 1, seen)


def _prune_tree(node, leaf_key: str, keep: Callable, depth: int = 0, seen: set | None = None):
    """Filter a name or number tree in place, fixing /Limits and empty nodes.

    ``keep(key, value)`` decides each entry and may modify ``value`` in place;
    an entry it cannot decide goes. Returns ``(first_key, last_key)`` of what
    is left, or None when nothing is. A leaf is read as a stream, without a
    list of all its entries, and rebuilt only when something went.

    A tree node has no /Type and holds ``leaf_key`` or /Kids. Anything else
    found in a node's place, such as the page tree a crafted catalog names as
    its /Names /Pages, is not this function's to change: it is left as it is,
    and ``_FOREIGN`` returned for it.
    """
    if seen is None:
        seen = set()
    if depth > _MAX_DEPTH or _type(node) not in _DICTLIKE:
        return None
    if "/Type" in node or (leaf_key not in node and "/Kids" not in node):
        return _FOREIGN
    if node.is_indirect:
        if node.objgen in seen:
            return None
        seen.add(node.objgen)
    first = last = None
    changed = False
    entries = node.get(leaf_key)
    if _type(entries) == _ARRAY:
        _charge(len(entries))
        flags = bytearray()
        it = iter(entries)
        for key in it:
            value = next(it, _MISSING)
            if value is _MISSING:
                break
            try:
                ok = bool(keep(key, value))
            except Exception:  # noqa: BLE001 - an entry that cannot be read goes
                logger.debug("page removal: tree entry dropped", exc_info=True)
                ok = False
            flags.append(ok)
            if ok:
                if first is None:
                    first = key
                last = key
        if not all(flags) or len(entries) != 2 * len(flags):
            # Built from the pairs as they are read: a list of them all would
            # hold a Python object for every entry of a large leaf.
            _charge(2 * flags.count(1))
            node[leaf_key] = Array(_kept_pairs(entries, flags))
            changed = True
    foreign = False
    kids = node.get("/Kids")
    if _type(kids) == _ARRAY:
        items = _items(kids)
        kept_kids = []
        for kid in items:
            limits = _prune_tree(kid, leaf_key, keep, depth + 1, seen)
            if limits is None:
                continue
            kept_kids.append(kid)
            if limits is _FOREIGN:
                foreign = True
                continue
            if first is None:
                first = limits[0]
            last = limits[1]
        if len(kept_kids) != len(items):
            node["/Kids"] = _new_array(kept_kids)
            changed = True
    if first is None:
        return _FOREIGN if foreign else None
    if changed and "/Limits" in node:
        node["/Limits"] = Array([first, last])
    return first, last


def _kept_pairs(entries, flags: bytearray):
    it = iter(entries)
    for ok in flags:
        key = next(it)
        value = next(it)
        if ok:
            yield key
            yield value


# ── the pruner ──────────────────────────────────────────────────────────────


class _Removed(set):
    """What the passes removed; the sweep cuts every reference to it.

    Refuses the catalog, the page tree and the kept pages (``protected``),
    whichever pass offers them: a crafted file can list them among a removed
    page's annotations or beads, or make them look like a dead link or a
    structure element of a removed page, and the sweep would then cut a kept
    page out of the tree, or the tree or the catalog out of the file.
    """

    def __init__(self, protected: set):
        super().__init__()
        self.protected = protected

    def add(self, og) -> None:
        if og not in self.protected:
            super().add(og)

    def update(self, *others) -> None:
        for other in others:
            super().update(set(other).difference(self.protected))

    def __ior__(self, other):
        self.update(other)
        return self


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
        # The page tree's inner nodes. Removing pages flattens the tree, so
        # usually this is just its root.
        self.tree_nodes: set = set()
        in_tree = {page.objgen for page in pages}
        nodes = [pdf.Root.get("/Pages")]
        while nodes and len(self.tree_nodes) < _MAX_CHAIN:
            node = nodes.pop()
            if _type(node) not in _DICTLIKE:
                continue
            if node.is_indirect:
                if node.objgen in self.tree_nodes or node.objgen in in_tree:
                    continue
                self.tree_nodes.add(node.objgen)
            # A direct node, which only the root can be once qpdf has read
            # the pages, is read once: its container holds it once.
            nodes.extend(_array(node.get("/Kids")))
        # Never cut or killed, whatever points at them (see _Removed).
        self.protected: set = self.tree_nodes | self.live_pages
        if pdf.Root.is_indirect:
            self.protected.add(pdf.Root.objgen)
        self.template_pages: set = set()
        self.dead_names: set[bytes] = set()
        self.dead_legacy: set[str] = set()
        self.dead_elements: set = set()
        self.alive_elements: set = set()
        self.dropped_annots: list = []  # taken off live pages by the annotation pass
        # Structure elements the tree pass read in full, and values it left to
        # the sweep.
        self.vetted: set = set()
        self.pending: list = []
        self._actions: dict = {}  # indirect action -> its pruned chain, or _SAME
        # Shared arrays and dictionaries decided once, for every owner: a
        # /Next, Hide /T or form action /Fields array -> its replacement, a
        # /Next array whose owner went -> the head that took its place, an
        # /AA dictionary -> whether pruning emptied it.
        self._arrays: dict = {}
        self._heads: dict = {}
        self._aa_done: dict = {}
        self._annot_verdicts: dict = {}
        self._removed_owners: set | None = None
        self.outline_items: set = set()  # bookmarks the outline pass walked
        self.inert: set = set()  # long indirect arrays that hold no reference
        # Bookmarks the outline pass could not reach, judged once each: is it
        # dead, and does nothing survive from it to the end of its list?
        self._stray_verdicts: dict = {}
        self._stray_rests: dict = {}

        # Each page's annotations and beads, read once and shared by the
        # passes. Pages that share one array share one list, which the passes
        # read once (_distinct).
        arrays: dict = {}
        self.annots_of: dict = {}
        self.beads_of: dict = {}
        for page in self.pages:
            self.annots_of[page.objgen] = _read_array(page.get("/Annots"), arrays)
            self.beads_of[page.objgen] = _read_array(page.get("/B"), arrays)
        self.removed_annots = [_read_array(page.get("/Annots"), arrays) for page in self.removed]
        removed_beads = [_read_array(page.get("/B"), arrays) for page in self.removed]
        self.live_annots = _indirect(self.annots_of.values())
        self.live_beads = _indirect(self.beads_of.values())
        self.dead_annots = _indirect(self.removed_annots) - self.live_annots - self.protected
        # A dictionary the catalog holds, such as the outline root or the form,
        # listed among a removed page's annotations is no annotation of that
        # page unless it looks like one; cut, it would take every bookmark or
        # field along.
        for value in _entries(pdf.Root).values():
            if _is_indirect_dictlike(value) and value.objgen in self.dead_annots and not _is_annotation(value):
                self.dead_annots.discard(value.objgen)
        self.dead_beads = _indirect(removed_beads) - self.live_beads - self.protected
        # Everything removed by any pass; the sweep cuts references to these.
        self.dead = _Removed(self.protected)
        self.dead.update(self.removed_pages, self.dead_annots, self.dead_beads)

    # ── predicates ──────────────────────────────────────────────────────────

    def page_dead(self, obj) -> bool:
        """True for a page reference that does not lead to a page in the output."""
        if obj is _REMOVED_PAGE:
            return True
        if obj is None:
            return True  # qpdf's stand-in for a page that was not copied
        if _type(obj) not in _DICTLIKE:
            return False  # a page number or something else: not ours to judge
        if not obj.is_indirect:
            return obj.get("/Type") == _PAGE
        og = obj.objgen
        if og in self.live_pages:
            return False
        if og in self.removed_pages:
            return True  # even when it is also listed as a template
        if og in self.template_pages or og in self.tree_nodes:
            return False
        return obj.get("/Type") == _PAGE

    def _is_page(self, obj) -> bool:
        """Is ``obj`` a page (in the tree, removed, or typed as one)?"""
        if _type(obj) not in _DICTLIKE:
            return False
        if obj.is_indirect and (obj.objgen in self.live_pages or obj.objgen in self.removed_pages):
            return True
        return obj.get("/Type") == _PAGE

    def annot_dead(self, obj) -> bool:
        if not _is_indirect_dictlike(obj):
            return False
        og = obj.objgen
        if og in self.dead:
            return True
        if og in self.live_annots or og in self.protected:
            return False
        verdict = self._annot_verdicts.get(og)
        if verdict is None:
            verdict = self._annot_verdicts[og] = self._judge_off_page(obj)
        return verdict

    def _judge_off_page(self, obj) -> bool:
        """An annotation on no live page: did it belong to a removed one?"""
        if not self.exact:
            return _is_annotation(obj)
        if obj.objgen in self.dead_annots:
            return True
        # Listed in no removed page's /Annots, but its /P names one.
        page = obj.get("/P")
        return _is_indirect_dictlike(page) and page.objgen in self.removed_pages

    def bead_dead(self, obj) -> bool:
        if not _is_indirect_dictlike(obj):
            return False
        og = obj.objgen
        if og in self.dead:
            return True
        if og in self.live_beads or og in self.protected:
            return False
        if not self.exact:
            return True
        if og in self.dead_beads:
            return True
        page = obj.get("/P")
        return _is_indirect_dictlike(page) and page.objgen in self.removed_pages

    def dest_state(self, dest) -> str:
        kind = _type(dest)
        if kind in _DICTLIKE:  # a named destination's << /D [...] >> form
            dest = dest.get("/D")
            kind = _type(dest)
        if kind == _ARRAY:
            target = _first(dest)
            if target is None or _type(target) in _DICTLIKE:
                if target is None and len(dest) == 0:
                    return _UNKNOWN
                return _DEAD if self.page_dead(target) else _LIVE
            return _UNKNOWN
        if kind == _STRING:
            return _DEAD if bytes(dest) in self.dead_names else _UNKNOWN
        if kind == _NAME:
            return _DEAD if str(dest) in self.dead_legacy else _UNKNOWN
        return _UNKNOWN

    def _is_protected(self, obj) -> bool:
        return obj.is_indirect and obj.objgen in self.protected

    def kill(self, obj) -> None:
        # The catalog, the page tree and kept pages are refused by self.dead.
        if getattr(obj, "is_indirect", False):
            self.dead.add(obj.objgen)

    def _field_dead(self, obj) -> bool:
        return _is_indirect_dictlike(obj) and obj.objgen in self.dead

    # ── actions ─────────────────────────────────────────────────────────────

    def prune_action(self, action, depth: int = 0):
        """Return the action chain without actions that reach removed pages.

        Returns ``action`` itself (possibly edited), a replacement when the
        head of the chain had to go, or None when nothing is left. An indirect
        action is pruned once however many owners share it; one that cannot be
        read goes. An action that stays is returned as the caller's own
        object: pikepdf hands every reader a new one, and an owner that got
        another reader's would take the action for a replacement.
        """
        if depth > _MAX_DEPTH or _type(action) not in _DICTLIKE:
            return action
        og = action.objgen if action.is_indirect else None
        if og is not None:
            done = self._actions.get(og, _MISSING)
            if done is not _MISSING:
                return action if done is _SAME else done
            self._actions[og] = _SAME  # in progress: a loop back here keeps it
        try:
            result = self._prune_action(action, depth)
        except Exception:  # noqa: BLE001 - an unreadable action goes
            logger.debug("page removal: action dropped", exc_info=True)
            self.kill(action)
            result = None
        if og is not None:
            self._actions[og] = _SAME if result is action else result
        return result

    def _shared_array(self, array, decide):
        """Decide an array once, however many owners share it.

        ``decide(items)`` returns the items to keep. Returns None when all of
        them stay, _MISSING when none does, or the replacement, which is
        indirect when ``array`` is: the owners that shared the array share
        its replacement, instead of each getting a copy.
        """
        key = array.objgen if array.is_indirect else None
        if key is not None:
            done = self._arrays.get(key, _MISSING)
            if done is not _MISSING:
                return done
            self._arrays[key] = None  # in progress: a loop back here keeps it
        items = _items(array)
        kept = decide(items)
        if len(kept) == len(items) and all(map(_same, kept, items)):
            result = None
        elif not kept:
            result = _MISSING
        else:
            result = _new_array(kept) if key is None else self.pdf.make_indirect(_new_array(kept))
        if key is not None:
            self._arrays[key] = result
        return result

    def _prune_action(self, action, depth: int):
        fields = _entries(action)
        nxt = fields.get("/Next")
        if nxt is not None:
            if _type(nxt) == _ARRAY:
                replacement = self._shared_array(nxt, lambda subs: [
                    pruned for pruned in (self.prune_action(sub, depth + 1) for sub in subs)
                    if pruned is not None
                ])
                if replacement is _MISSING:
                    del action["/Next"]
                elif replacement is not None:
                    action["/Next"] = replacement
            else:
                pruned = self.prune_action(nxt, depth + 1)
                if pruned is None:
                    if "/Next" in action:
                        del action["/Next"]
                elif pruned is not nxt:
                    action["/Next"] = pruned

        if not self._action_dead(action, fields):
            return action
        self.kill(action)
        rest = action.get("/Next")
        if rest is None:
            return None
        if _type(rest) != _ARRAY:
            return rest
        # The head goes; its successors run in the same order without it.
        # A /Next array shared by many dead actions makes its head take their
        # place once, not once per owner.
        key = rest.objgen if rest.is_indirect else None
        if key is not None and key in self._heads:
            return self._heads[key]
        subs = _items(rest)
        head, tail = subs[0], subs[1:]
        if tail and _type(head) in _DICTLIKE:
            own = head.get("/Next")
            own_list = [] if own is None else (_items(own) if _type(own) == _ARRAY else [own])
            head["/Next"] = _new_array(own_list + tail)
        if key is not None:
            self._heads[key] = head
        return head

    def _action_dead(self, action, fields: dict) -> bool:
        kind = fields.get("/S")
        if kind == Name.GoTo:
            return self.dest_state(fields.get("/D")) == _DEAD
        if kind == Name.Thread:
            thread, bead = fields.get("/D"), fields.get("/B")
            return (
                (_is_indirect_dictlike(thread) and thread.objgen in self.dead)
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
            replacement = self._shared_array(targets, lambda items: [
                t for t in items if not self.annot_dead(t) and not self._field_dead(t)])
            if replacement is _MISSING:
                return True
            if replacement is not None:
                action["/T"] = replacement
            return False
        if kind in (Name.SubmitForm, Name.ResetForm):
            fields_ = fields.get("/Fields")
            if _type(fields_) == _ARRAY:
                replacement = self._shared_array(fields_, lambda items: [
                    f for f in items if not self._field_dead(f) and not self.annot_dead(f)])
                # An empty list would mean "every field", the opposite.
                if replacement is _MISSING:
                    return True
                if replacement is not None:
                    action["/Fields"] = replacement
        return False

    def prune_additional_actions(self, owner, aa) -> None:
        """Prune an /AA dictionary; one shared by many owners, once."""
        if _type(aa) not in _DICTLIKE:
            return
        key = aa.objgen if aa.is_indirect else None
        emptied = self._aa_done.get(key) if key is not None else None
        if emptied is None:
            for trigger, action in list(_entries(aa).items()):
                pruned = self.prune_action(action)
                if pruned is None:
                    # A null entry is absent to pikepdf: there is nothing to delete.
                    if trigger in aa:
                        del aa[trigger]
                elif pruned is not action:
                    aa[trigger] = pruned
            emptied = not aa.keys()
            if key is not None:
                self._aa_done[key] = emptied
        if emptied and "/AA" in owner:
            del owner["/AA"]

    # ── passes ──────────────────────────────────────────────────────────────

    def run(self) -> None:
        root = self.pdf.Root
        catalog = _entries(root)
        self._contained(self._collect_templates, catalog)
        self._contained(self.prune_named_destinations, catalog,
                        fallback=lambda: self._drop(root, "/Dests", ("/Names", "/Dests")))
        # Fields and threads first: actions that name fields (reset, submit,
        # hide) or threads are pruned with the annotations and need to know
        # which of them went.
        self._contained(self.prune_fields, catalog,
                        fallback=lambda: self._drop(root, "/AcroForm"))
        self._contained(self.prune_threads, root, catalog, fallback=self._drop_threads)
        self._contained(self.prune_page_annotations)
        self._contained(self.prune_structure_tree, root,
                        fallback=lambda: self._untag(root))
        self._contained(self.prune_outline, catalog,
                        fallback=lambda: self._drop(root, "/Outlines"))
        self._contained(self.prune_catalog, root,
                        fallback=lambda: self._drop(root, "/OpenAction", "/AA", ("/Names", "/Pages")))
        # Not contained: a sweep that fails fails the request.
        self.sweep()

    def _contained(self, run_pass: Callable, *args, fallback: Callable | None = None) -> None:
        """Run a repair pass; if it fails outright, drop what it was repairing.

        The passes contain errors per item already, so this is the last line.
        The fallback removes the whole structure the pass was working on, so
        nothing it had not yet pruned can keep a removed page's content.
        """
        try:
            run_pass(*args)
        except Exception:  # noqa: BLE001 - see the docstring
            logger.warning("page removal: %s failed on this file", run_pass.__name__, exc_info=True)
            if fallback is not None:
                fallback()

    @staticmethod
    def _drop(root, *keys) -> None:
        for key in keys:
            owner = root
            if isinstance(key, tuple):
                owner = root.get(key[0])
                key = key[1]
                if _type(owner) not in _DICTLIKE:
                    continue
            if key in owner:
                del owner[key]

    def _drop_threads(self) -> None:
        self._drop(self.pdf.Root, "/Threads")
        for page in self.pages:
            if "/B" in page:
                del page["/B"]

    def _untag(self, root) -> None:
        """Say the document is untagged rather than keep a tree half pruned."""
        self._drop(root, "/StructTreeRoot")
        mark = root.get("/MarkInfo")
        if _type(mark) in _DICTLIKE and "/Marked" in mark:
            del mark["/Marked"]
            if not mark.keys():
                del root["/MarkInfo"]
        for page in self.pages:
            if "/StructParents" in page:
                del page["/StructParents"]

    def _collect_templates(self, catalog: dict) -> None:
        # Template pages live outside the page tree on purpose (PDF 12.7.6).
        names = catalog.get("/Names")
        if _type(names) in _DICTLIKE:
            for _, page in _tree_entries(names.get("/Templates"), "/Names"):
                if _is_indirect_dictlike(page):
                    self.template_pages.add(page.objgen)

    def prune_named_destinations(self, catalog: dict) -> None:
        names = catalog.get("/Names")
        tree = names.get("/Dests") if _type(names) in _DICTLIKE else None
        if tree is not None:
            def keep(key, value):
                try:
                    if self.dest_state(value) != _DEAD:
                        return True
                except Exception:  # noqa: BLE001 - an unreadable entry goes
                    logger.debug("page removal: named destination dropped", exc_info=True)
                if _type(key) == _STRING:
                    self.dead_names.add(bytes(key))
                self.kill(value)
                return False

            if _prune_tree(tree, "/Names", keep) is None and "/Dests" in names:
                del names["/Dests"]
        dests = catalog.get("/Dests")
        if _type(dests) in _DICTLIKE:
            for key, value in list(_entries(dests).items()):
                try:
                    dead = self.dest_state(value) == _DEAD
                except Exception:  # noqa: BLE001 - an unreadable entry goes
                    dead = True
                if dead:
                    self.dead_legacy.add(key)
                    self.kill(value)
                    if key in dests:
                        del dests[key]

    def prune_fields(self, catalog: dict) -> None:
        acroform = catalog.get("/AcroForm")
        acroform = acroform if _type(acroform) in _DICTLIKE else None
        seen: set = set()
        removed_any = False
        # An indirect /Kids array shared by fields -> what replaced it: None
        # when nothing went, _MISSING when every kid did.
        shared_kids: dict = {}

        def alive(field, depth: int) -> bool:
            nonlocal removed_any
            if depth > _MAX_DEPTH or _type(field) not in _DICTLIKE:
                return True
            if field.is_indirect:
                if field.objgen in self.protected:
                    return True  # the catalog or a page is no field: left alone
                if field.objgen in seen:
                    return field.objgen not in self.dead
                seen.add(field.objgen)
            try:
                fields = _entries(field)
                kids = fields.get("/Kids")
                if _type(kids) == _ARRAY and len(kids):
                    key = kids.objgen if kids.is_indirect else None
                    if key is not None and key in shared_kids:
                        replacement = shared_kids[key]
                    else:
                        items = _items(kids)
                        kept = [kid for kid in items if alive(kid, depth + 1)]
                        if len(kept) == len(items):
                            replacement = None
                        elif not kept:
                            replacement = _MISSING
                        elif key is None:
                            replacement = _new_array(kept)
                        else:  # the fields that share it share its replacement
                            replacement = self.pdf.make_indirect(_new_array(kept))
                        if key is not None:
                            shared_kids[key] = replacement
                    if replacement is None:
                        return True
                    removed_any = True
                    if replacement is _MISSING:
                        self.kill(field)
                        return False
                    field["/Kids"] = replacement
                    return True
                if _is_annotation(fields) and self.annot_dead(field):
                    self.kill(field)
                    removed_any = True
                    return False
                return True
            except Exception:  # noqa: BLE001 - an unreadable field goes
                logger.debug("page removal: form field dropped", exc_info=True)
                self.kill(field)
                removed_any = True
                return False

        if acroform is not None:
            fields = acroform.get("/Fields")
            if _type(fields) == _ARRAY:
                items = _items(fields)
                kept = [field for field in items if alive(field, 0)]
                if len(kept) != len(items):
                    acroform["/Fields"] = _new_array(kept)
        # A copied document has no /AcroForm, but a widget's field still
        # reaches its sibling widgets on the pages left behind.
        climbed: set = set()  # widgets and fields already climbed from
        for annots in _distinct(self.annots_of.values()):
            for annot in annots:
                if _type(annot) not in _DICTLIKE:
                    continue
                if annot.is_indirect:
                    if annot.objgen in climbed:
                        continue
                    climbed.add(annot.objgen)
                parent = annot.get("/Parent")
                if _type(parent) not in _DICTLIKE or annot.get("/Subtype") != Name.Widget:
                    continue
                top, steps = parent, 0
                while top is not None and steps < _MAX_DEPTH:
                    _charge(1)
                    if top.is_indirect:
                        if top.objgen in climbed:
                            top = None  # its field tree was reached from another widget
                            break
                        climbed.add(top.objgen)
                    up = top.get("/Parent")
                    if _type(up) not in _DICTLIKE:
                        break
                    top, steps = up, steps + 1
                if top is not None:
                    alive(top, 0)
        if acroform is None:
            return
        order = acroform.get("/CO")
        if _type(order) == _ARRAY:
            items = _items(order)
            kept = [f for f in items if not self._field_dead(f)]
            if len(kept) != len(items):
                acroform["/CO"] = _new_array(kept)
        if removed_any and "/XFA" in acroform:
            # XFA keeps every field's value in its own XML, so the values of
            # the fields that went would stay in the file. Without it the
            # remaining fields still work from the AcroForm.
            del acroform["/XFA"]

    def prune_page_annotations(self) -> None:
        decided: dict = {}  # annotation -> goes, for annotations shared by pages
        remaining: list = []  # (page, annotation, its entries) for what stays
        listed: set = set()
        # An indirect /Annots array shared by pages is decided once, and the
        # pages that shared it share what replaces it.
        shared: dict = {}  # array -> (the annotations kept, the replacement)
        for page in self.pages:
            annots = self.annots_of[page.objgen]
            if annots:
                array = page.get("/Annots")
                key = array.objgen if _type(array) == _ARRAY and array.is_indirect else None
                done = shared.get(key) if key is not None else None
                if done is None:
                    done = self._prune_annots(page, annots, key is not None, decided, remaining, listed)
                    if key is not None:
                        shared[key] = done
                kept, replacement = done
                self.annots_of[page.objgen] = kept
                if replacement is _MISSING:
                    if "/Annots" in page:
                        del page["/Annots"]
                elif replacement is not None:
                    page["/Annots"] = replacement
            aa = page.get("/AA")
            if aa is not None:
                self.prune_additional_actions(page, aa)
        # Replies and popups can point at annotations of removed pages and at
        # links removed above, on any page.
        for page, annot, fields in remaining:
            try:
                for key in ("/IRT", "/Popup"):
                    if key in fields and self.annot_dead(fields[key]) and key in annot:
                        del annot[key]
                if "/P" in fields and self.page_dead(fields["/P"]):
                    annot["/P"] = page
            except Exception:  # noqa: BLE001 - the sweep still cuts what is dead
                logger.debug("page removal: annotation links left to the sweep", exc_info=True)

    def _prune_annots(self, page, annots: list, shared: bool, decided: dict, remaining: list, listed: set):
        """Decide one /Annots array; return (the annotations kept, what replaces
        the array: None when nothing went, _MISSING when everything did)."""
        kept, removed = [], []
        for annot in annots:
            og = annot.objgen if _is_indirect_dictlike(annot) else None
            if og is not None and og in decided:
                (removed if decided[og] else kept).append(annot)
                continue
            fields = _entries(annot) if _type(annot) in _DICTLIKE else {}
            try:
                goes = self._annotation_goes(annot, fields)
            except Exception:  # noqa: BLE001 - a kept page's own annotation: the sweep checks it
                logger.debug("page removal: annotation left as it is", exc_info=True)
                goes = False
            if og is not None:
                decided[og] = goes
            if goes:
                removed.append(annot)
            else:
                kept.append(annot)
                if og is None or og not in listed:
                    remaining.append((page, annot, fields))
                    if og is not None:
                        listed.add(og)
        for annot in removed:
            if _is_indirect_dictlike(annot) and annot.objgen not in self.dead:
                self.live_annots.discard(annot.objgen)
                self.dead.add(annot.objgen)
                self.dropped_annots.append(annot)
        if not removed:
            return annots, None
        if not kept:
            return kept, _MISSING
        return kept, (self.pdf.make_indirect(_new_array(kept)) if shared else _new_array(kept))

    def _annotation_goes(self, annot, fields: dict) -> bool:
        """Decide one annotation on a live page; edits what stays in place."""
        if not fields or (annot.is_indirect and annot.objgen in self.protected):
            return False  # a page or the catalog listed as an annotation: left alone
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
                annot["/A"] = pruned
        if "/AA" in fields:
            self.prune_additional_actions(annot, fields["/AA"])
        if subtype == Name.Link:
            has_dest, has_action = "/Dest" in fields, action is not None
            if (has_dest or has_action) and (dest_dead or not has_dest) and (action_dead or not has_action):
                return True
        if dest_dead and "/Dest" in annot:
            del annot["/Dest"]
        if action_dead and "/A" in annot:
            del annot["/A"]
        return False

    def prune_threads(self, root, catalog: dict) -> None:
        threads = catalog.get("/Threads")
        candidates = _array(threads)
        listed = {t.objgen for t in candidates if _is_indirect_dictlike(t)}
        for beads in _distinct(self.beads_of.values()):
            for bead in beads:
                thread = bead.get("/T") if _type(bead) in _DICTLIKE else None
                if _is_indirect_dictlike(thread) and thread.objgen not in listed:
                    listed.add(thread.objgen)
                    candidates.append(thread)
        ring_of: dict = {}  # bead -> the ring it was walked in, for every thread
        budget = [_MAX_CHAIN]
        dead_threads = set()
        for thread in candidates:
            if _type(thread) not in _DICTLIKE or self._is_protected(thread):
                continue
            try:
                first = thread.get("/F")
                ring = ring_of.get(first.objgen) if _is_indirect_dictlike(first) else None
                if ring is None:
                    ring = self._walk_ring(first, ring_of, budget)
                if ring:
                    if not _is_indirect_dictlike(first) or self.bead_dead(first):
                        thread["/F"] = ring[0]
                    continue
            except Exception:  # noqa: BLE001 - an unreadable thread goes
                logger.debug("page removal: article thread dropped", exc_info=True)
            self.kill(thread)
            if thread.is_indirect:
                dead_threads.add(thread.objgen)
        if dead_threads and _type(threads) == _ARRAY:
            kept = [t for t in _items(threads) if not (_is_indirect_dictlike(t) and t.objgen in dead_threads)]
            if kept:
                root["/Threads"] = _new_array(kept)
            else:
                del root["/Threads"]

    def _walk_ring(self, first, ring_of: dict, budget: list) -> list:
        """Walk a bead ring once, relink its live beads; return them.

        ``ring_of`` and ``budget`` are shared by all threads, so a ring many
        threads start in is walked once.
        """
        ring, bead = [], first
        while (
            _is_indirect_dictlike(bead)
            and bead.objgen not in ring_of
            and bead.objgen not in self.protected
            and _is_bead(bead)  # something else in a ring ends it
            and budget[0] > 0
        ):
            budget[0] -= 1
            _charge(1)
            ring.append(bead)
            ring_of[bead.objgen] = None  # placeholder while walking
            bead = bead.get("/N")
        live = [b for b in ring if not self.bead_dead(b)]
        for b in ring:
            ring_of[b.objgen] = live
        if len(live) != len(ring):
            for b in ring:
                if self.bead_dead(b):
                    self.kill(b)
            for i, b in enumerate(live):
                b["/N"] = live[(i + 1) % len(live)]
                b["/V"] = live[i - 1]
        return live

    # ── structure tree ──────────────────────────────────────────────────────

    def prune_structure_tree(self, root) -> None:
        tree = root.get("/StructTreeRoot")
        if _type(tree) not in _DICTLIKE:
            return
        kids = tree.get("/K")
        if kids is None:
            return
        records = self._walk_structure(tree, kids)
        top = records[0]
        if top.had_kids and not top.kept:
            self._untag(root)  # nothing tagged is left: say so
            return

        dead_keys = self._dead_struct_keys()
        seen_values: dict = {}

        def keep_parent_entry(key, value):
            if type(key) is int and key in dead_keys:
                return False  # the key of a removed page or annotation
            if _type(value) == _ARRAY:
                og = value.objgen if value.is_indirect else None
                if og is not None and og in seen_values:
                    return seen_values[og]
                left = False
                _charge(len(value))
                for i, item in enumerate(value):
                    if _is_indirect_dictlike(item) and item.objgen not in self.alive_elements:
                        value[i] = None
                    elif item is not None:
                        left = True
                if og is not None:
                    seen_values[og] = left
                return left
            if _is_indirect_dictlike(value):
                return value.objgen in self.alive_elements
            return value is not None

        parent_tree = tree.get("/ParentTree")
        if parent_tree is not None and _prune_tree(parent_tree, "/Nums", keep_parent_entry) is None:
            if "/ParentTree" in tree:
                del tree["/ParentTree"]

        def keep_id(_key, value):
            return not (_is_indirect_dictlike(value) and value.objgen not in self.alive_elements)

        id_tree = tree.get("/IDTree")
        if id_tree is not None and _prune_tree(id_tree, "/Names", keep_id) is None:
            if "/IDTree" in tree:
                del tree["/IDTree"]

        known = set(self.alive_elements)
        if tree.is_indirect:
            known.add(tree.objgen)
        pruned_refs: set = set()
        for record in records[1:]:
            if not record.alive:
                continue
            try:
                refs = record.ref
                if _type(refs) == _ARRAY:
                    og = refs.objgen if refs.is_indirect else None
                    if og is None or og not in pruned_refs:
                        if og is not None:
                            pruned_refs.add(og)
                        items = _items(refs)
                        # Elements only: a reference to anything but a live
                        # one (a removed element, one outside the tree) goes.
                        kept = [r for r in items if not _is_indirect_dictlike(r) or r.objgen in self.alive_elements]
                        if len(kept) != len(items):
                            if kept:
                                record.obj["/Ref"] = _new_array(kept)
                            else:
                                del record.obj["/Ref"]
                    self.pending.append(record.obj.get("/Ref"))
                elif refs is not None:
                    self._unvet(record.obj)  # not an array: the sweep reads it
                parent = record.p
                if _is_indirect_dictlike(parent) and parent.objgen in known:
                    continue
                if _is_indirect_dictlike(parent) and parent.objgen in self.dead_elements:
                    record.obj["/P"] = record.parent.obj
                elif parent is not None:
                    self._unvet(record.obj)  # a /P the pass did not follow
            except Exception:  # noqa: BLE001 - left to the sweep
                logger.debug("page removal: element links left to the sweep", exc_info=True)
                self._unvet(record.obj)
        self.dead.update(self.dead_elements)

    def _unvet(self, obj) -> None:
        if obj.is_indirect:
            self.vetted.discard(obj.objgen)
            self.pending.append(obj)

    def _dead_struct_keys(self) -> set:
        """ParentTree keys that belonged to removed pages and annotations."""
        dead, live = set(), set()
        for page in self.removed:
            _int_key(page.get("/StructParents"), dead)
        for annots in _distinct(self.removed_annots):
            for annot in annots:
                if _is_indirect_dictlike(annot) and annot.objgen in self.dead:
                    _int_key(annot.get("/StructParent"), dead)
        # Links the annotation pass took off live pages: their element can
        # survive (it owns the link text), but their key is gone with them.
        for annot in self.dropped_annots:
            _int_key(annot.get("/StructParent"), dead)
        if not dead:
            return dead
        for page in self.pages:
            _int_key(page.get("/StructParents"), live)
        for annots in _distinct(self.annots_of.values()):
            for annot in annots:
                if _type(annot) in _DICTLIKE:
                    _int_key(annot.get("/StructParent"), live)
        return dead - live

    def _walk_structure(self, tree, kids):
        """Prune the element tree below ``tree``; return its records, root first.

        Iterative, so a deep tree cannot exhaust the interpreter stack. Each
        element is read once; a record keeps only what the later steps need.
        """
        top = _Record(tree, None, None)
        records = [top]
        pending = [(top, kids)]
        seen: set = set()  # elements, each read once
        seen_kids: set = set()  # indirect /K arrays, each read once
        while pending:
            record, raw = pending.pop()
            if _type(raw) == _ARRAY and raw.is_indirect:
                if raw.objgen in seen_kids:
                    # Another element's kids, read with that element: this one
                    # keeps them as they are, its page decides whether it
                    # stays, and the sweep reads them.
                    record.recheck = True
                    record.had_kids = True
                    record.shared = True
                    continue
                seen_kids.add(raw.objgen)
            items = _items(raw) if _type(raw) == _ARRAY else ([] if raw is None else [raw])
            record.single = _type(raw) != _ARRAY
            record.had_kids = bool(items)
            page = record.page
            for item in items:
                try:
                    kind = _type(item)
                    if kind not in _DICTLIKE:
                        if kind == _ARRAY:
                            # Not a valid kid: it stays while the element does,
                            # without keeping it, and the sweep reads it.
                            record.recheck = True
                            record.kids.append((item, None))
                        else:
                            # A marked-content id, or a value that is no kid
                            # at all: either way, on the element's page.
                            record.kids.append((item, self._mcid_alive(page)))
                        continue
                    if item.is_indirect and item.objgen in seen:
                        # An element met before, under another parent or in a
                        # loop: the kid stays as it is without keeping this
                        # element alive, and the sweep checks this element's /K.
                        record.recheck = True
                        record.kids.append((item, None))
                        continue
                    fields = _entries(item)
                    typ = fields.get("/Type")
                    if (
                        "/MCID" in fields
                        or "/Obj" in fields
                        or (_type(typ) == _NAME and typ in _CONTENT_TYPES)
                    ):
                        alive = self._content_alive(fields, page)
                        record.kids.append((item, alive))
                        if alive:
                            self.pending.append(item)  # /Stm, /StmOwn, /Obj: the sweep's
                        continue
                    if "/S" not in fields:
                        # Neither an element nor marked content: it stays while
                        # the element does, without keeping it, and the sweep
                        # reads it with the element.
                        record.recheck = True
                        record.kids.append((item, None))
                        continue
                    if item.is_indirect:
                        seen.add(item.objgen)
                    own = fields.get("/Pg")
                    kids_page = own if own is not None else page
                    if own is not None and not self._is_page(own):
                        # A /Pg that is not a page: only the ParentTree says
                        # whose content the element owns.
                        removed = item.is_indirect and item.objgen in self._owners_of_removed_content()
                        kids_page = _REMOVED_PAGE if removed else page
                    child = _Record(item, record, kids_page)
                    child.pg = own
                    child.p = fields.get("/P")
                    child.ref = fields.get("/Ref")
                    child.texts = [key for key in _ELEMENT_TEXTS if key in fields]
                    for key, value in fields.items():
                        if key in _ELEMENT_WALKED or value.__class__ in _SCALARS:
                            continue
                        vtype = _type(value)
                        if vtype in _DICTLIKE and value.is_indirect:
                            # The sweep can only cut this reference by reading
                            # the element itself.
                            child.recheck = True
                        elif vtype in _CONTAINERS:
                            self.pending.append(value)
                    records.append(child)
                    record.kids.append(child)
                    pending.append((child, fields.get("/K")))
                except Exception:  # noqa: BLE001 - an unreadable kid goes
                    logger.debug("page removal: structure item dropped", exc_info=True)
                    record.kids.append((item, False))
        for record in reversed(records):
            kept, deciding, live = [], 0, 0
            for kid in record.kids:
                if isinstance(kid, _Record):
                    deciding += 1
                    if kid.alive:
                        kept.append(kid.obj)
                        live += 1
                elif kid[1] is None:
                    kept.append(kid[0])  # neither keeps nor drops the element
                else:
                    deciding += 1
                    if kid[1]:
                        kept.append(kid[0])
                        live += 1
            record.kept = kept
            if record is top:
                if len(kept) != len(record.kids) and kept:
                    tree["/K"] = _new_array(kept)
                continue
            elem = record.obj
            try:
                if deciding:
                    record.alive = bool(live)
                else:  # no kids that say where it is: its page decides
                    record.alive = record.page is None or not self.page_dead(record.page)
                if not record.alive:
                    if elem.is_indirect:
                        self.dead_elements.add(elem.objgen)
                    continue
                if len(kept) != len(record.kids):
                    elem["/K"] = kept[0] if record.single and len(kept) == 1 else _new_array(kept)
                if len(kept) != len(record.kids) or record.shared:
                    # Its text spoke for the content that went too. An element
                    # whose kids were read with another element cannot show
                    # that nothing went, so its text goes as well.
                    for key in record.texts:
                        if key in elem:
                            del elem[key]
                own = record.pg
                if own is not None:
                    if self.page_dead(own):
                        del elem["/Pg"]
                    elif not (_is_indirect_dictlike(own) and own.objgen in self.live_pages):
                        record.recheck = True  # not a page: the sweep reads it
                if elem.is_indirect:
                    self.alive_elements.add(elem.objgen)
                    if record.recheck:
                        # Reached only through vetted elements, it would be
                        # skipped: the sweep is sent to it.
                        self.pending.append(elem)
                    else:
                        self.vetted.add(elem.objgen)
                elif record.recheck and record.parent is not top:
                    record.parent.recheck = True  # a direct element is read with its parent
            except Exception:  # noqa: BLE001 - an unreadable element goes
                logger.debug("page removal: structure element dropped", exc_info=True)
                record.alive = False
                if elem.is_indirect:
                    self.alive_elements.discard(elem.objgen)
                    self.vetted.discard(elem.objgen)
                    self.dead_elements.add(elem.objgen)
        return records

    def _owners_of_removed_content(self) -> set:
        """Elements the ParentTree files under a removed page's content.

        Read only for an element whose /Pg is not a page, where nothing else
        says which page its marked content is on.
        """
        if self._removed_owners is None:
            owners: set = set()
            keys: set = set()
            for page in self.removed:
                _int_key(page.get("/StructParents"), keys)
            tree = self.pdf.Root.get("/StructTreeRoot")
            if keys and _type(tree) in _DICTLIKE:
                for key, value in _tree_entries(tree.get("/ParentTree"), "/Nums"):
                    if type(key) is int and key in keys:
                        for item in (_items(value) if _type(value) == _ARRAY else [value]):
                            if _is_indirect_dictlike(item):
                                owners.add(item.objgen)
            self._removed_owners = owners
        return self._removed_owners

    def _mcid_alive(self, page) -> bool:
        """A marked-content id lives on its element's page."""
        return page is None or not self.page_dead(page)

    def _content_alive(self, fields: dict, page) -> bool:
        """A marked-content reference or an object reference."""
        own = fields.get("/Pg")
        page = own if own is not None else page
        if "/Obj" in fields or fields.get("/Type") == Name.OBJR:
            target = fields.get("/Obj")
            if target is None or self.annot_dead(target):
                return False
            if _is_indirect_dictlike(target) and target.objgen in self.dead:
                return False
        return page is None or not self.page_dead(page)

    # ── outline ─────────────────────────────────────────────────────────────

    def prune_outline(self, catalog: dict) -> None:
        outlines = catalog.get("/Outlines")
        if _type(outlines) not in _DICTLIKE or self._is_protected(outlines):
            return
        first = outlines.get("/First")
        if first is not None:
            self._prune_outline_level(outlines, first, None, 0, set())

    def _prune_outline_level(self, parent, first, parent_open, depth: int, seen: set):
        """Prune the bookmarks under ``parent`` and relink what stays.

        A bookmark whose target was on a removed page goes, and its surviving
        children take its place. So does a heading without a target of its own
        once all its children are gone, and a bookmark that cannot be read.
        ``parent_open`` is None for the outline root. Returns ``(kept,
        changed)``: the kept children as ``(item, descendants visible when it
        is open, is open)``, and whether anything at or below this level
        changed. Bookmarks are not vetted: the sweep reads them all.
        """
        kept: list = []
        changed = False
        item = first
        while (
            _is_indirect_dictlike(item)
            and item.objgen not in seen
            and item.objgen not in self.protected  # a crafted /Next: the list ends there
            and len(seen) < _MAX_CHAIN
        ):
            seen.add(item.objgen)
            self.outline_items.add(item.objgen)
            if item.objgen in self.dead:
                # A removed page or the like where a bookmark belongs: it goes,
                # and with it the rest of a list no bookmark continues.
                changed = True
                item = item.get("/Next")
                continue
            nxt = None
            try:
                fields = _entries(item)
                nxt = fields.get("/Next")
                count = fields.get("/Count")
                is_open = type(count) is int and count > 0
                child = fields.get("/First")
                children, below_changed = None, False
                if child is not None and depth < _MAX_DEPTH:
                    children, below_changed = self._prune_outline_level(item, child, is_open, depth + 1, seen)
                changed = changed or below_changed
                se = fields.get("/SE")
                if se is not None and _is_indirect_dictlike(se) and se.objgen in self.dead:
                    del item["/SE"]
                target = self._outline_target(item, fields)
                if target == _DEAD or (target is None and child is not None and children == []):
                    self.kill(item)
                    changed = True
                    kept.extend(children or [])
                else:
                    if children is None:
                        below = abs(count) if type(count) is int and child is not None else 0
                    else:
                        below = sum(1 + (b if o else 0) for _, b, o in children)
                    kept.append((item, below, is_open))
            except Exception:  # noqa: BLE001 - an unreadable bookmark goes
                logger.debug("page removal: bookmark dropped", exc_info=True)
                self.kill(item)
                changed = True
            item = nxt

        if not changed:
            return kept, False
        for i, (item, _, _) in enumerate(kept):
            item["/Parent"] = parent
            if i:
                item["/Prev"] = kept[i - 1][0]
            elif "/Prev" in item:
                del item["/Prev"]
            if i + 1 < len(kept):
                item["/Next"] = kept[i + 1][0]
            elif "/Next" in item:
                del item["/Next"]
        if not kept:
            for key in ("/First", "/Last", "/Count"):
                if key in parent:
                    del parent[key]
            return kept, True
        parent["/First"] = kept[0][0]
        parent["/Last"] = kept[-1][0]
        visible = sum(1 + (b if o else 0) for _, b, o in kept)
        # Open when /Count is positive; a closed bookmark stores the number
        # negated (PDF 12.3.3). The root counts everything visible.
        parent["/Count"] = visible if parent_open is None or parent_open else -visible
        return kept, True

    def _stray_bookmark_dead(self, item, fields, depth: int = 0) -> bool:
        """The outline pass's verdict, for a bookmark it could not reach.

        Dead when its target was on a removed page, or, for a heading without
        a target, when it has children and none of them survives. Its list is
        not relinked: past a break, no viewer shows it anyway.

        Each bookmark is judged once, and each list read once, however many
        headings share it: headings that share their children would otherwise
        be walked once per path, twice as often with each level of nesting.
        A bookmark reached again while it is being judged counts as surviving.
        """
        og = item.objgen if item.is_indirect else None
        verdict = self._stray_verdicts.get(og) if og is not None else None
        if verdict is not None:
            return verdict
        if og is not None:
            self._stray_verdicts[og] = False  # in progress
        target = self._outline_target(item, fields)
        if target is not None:
            verdict = target == _DEAD
        elif depth >= _MAX_DEPTH:
            verdict = False
        else:
            verdict = self._stray_list_dead(fields.get("/First"), depth + 1)
        if og is not None:
            self._stray_verdicts[og] = verdict
        return verdict

    def _stray_list_dead(self, first, depth: int) -> bool:
        """True when the bookmark list from ``first`` has items and none survives.

        The list is walked to its end, or to the first item whose rest is
        already known, and then settled from the back, so that no item is read
        twice however many lists join it. A loop in /Next ends the list.
        """
        if not _is_indirect_dictlike(first) or first.objgen in self.protected:
            return False  # no children: a heading without any is not judged here
        rests = self._stray_rests
        chain: list = []
        on_chain: set = set()
        item, rest = first, True
        while (
            _is_indirect_dictlike(item)
            and item.objgen not in self.protected
            and item.objgen not in on_chain
            and len(chain) < _MAX_CHAIN
        ):
            known = rests.get(item.objgen)
            if known is not None:
                rest = known is True  # _PENDING: being settled further out
                break
            rests[item.objgen] = _PENDING
            on_chain.add(item.objgen)
            chain.append(item)
            _charge(1)
            item = item.get("/Next")
        for item in reversed(chain):
            og = item.objgen
            if rest and og not in self.dead:
                if og in self.outline_items:
                    rest = False  # kept by the outline pass
                else:
                    rest = self._stray_bookmark_dead(item, _entries(item), depth)
            rests[og] = rest
        return rest

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
                    item["/A"] = pruned
                states.append(_LIVE)
        if not states:
            return None
        return _DEAD if all(state == _DEAD for state in states) else _LIVE

    # ── catalog ─────────────────────────────────────────────────────────────

    def prune_catalog(self, root) -> None:
        opener = root.get("/OpenAction")
        try:
            if _type(opener) == _ARRAY:
                if self.dest_state(opener) == _DEAD:
                    del root["/OpenAction"]
            elif _type(opener) in _DICTLIKE:
                pruned = self.prune_action(opener)
                if pruned is None:
                    del root["/OpenAction"]
                elif pruned is not opener:
                    root["/OpenAction"] = pruned
        except Exception:  # noqa: BLE001 - an unreadable open action goes
            logger.debug("page removal: open action dropped", exc_info=True)
            self._drop(root, "/OpenAction")
        aa = root.get("/AA")
        if aa is not None:
            self.prune_additional_actions(root, aa)
        names = root.get("/Names")
        pages_tree = names.get("/Pages") if _type(names) in _DICTLIKE else None
        if pages_tree is not None:
            def keep(_key, value):
                return not (_type(value) in _DICTLIKE and self.page_dead(value))

            if _prune_tree(pages_tree, "/Names", keep) is None and "/Pages" in names:
                del names["/Pages"]

    # ── the sweep ───────────────────────────────────────────────────────────

    def sweep(self, exhaustive: bool = False) -> None:
        """Cut every remaining reference to a removed object.

        Everything reachable from the trailer is visited once. A reference is
        deleted from its dictionary, or replaced by null in its array, when it
        leads to:

        * a removed page, annotation, bead, field, structure element or thread;
        * any other page object outside the page tree (one an earlier tool
          left behind, say), or a page dictionary written in place;
        * a structure element the tree pass did not keep, or a bead or
          bookmark of a removed page that the passes could not reach through
          a broken ring or list;
        * another document's catalog, outline or structure tree, carried in
          with a copied page, and in a copied document an annotation on no page.

        So nothing that belonged to a removed page is written.

        Unless ``exhaustive``, structure elements the tree pass read in full
        are skipped (what it left over was queued in ``pending``). A long array
        is read item by item only if it can hold a reference
        (:func:`_holds_no_objects`). A dictionary's entries are read once, to
        judge it and to visit it.
        """
        dead = self.dead
        templates = self.template_pages
        removed_pages = self.removed_pages
        exact = self.exact
        live_annots = self.live_annots
        alive_elements = self.alive_elements
        outline_items = self.outline_items
        protected = self.protected
        root = self.pdf.Root
        own_roots = {
            obj.objgen for obj in (root, root.get("/Outlines"), root.get("/StructTreeRoot"))
            if _is_indirect_dictlike(obj)
        }
        verdicts: dict = {} if exhaustive else dict.fromkeys(self.vetted, False)
        # (object, its entries if they were read to judge it)
        stack: list = [(self.pdf.trailer, None)]
        cut = 0

        def is_dead(value, og) -> bool:
            verdict = verdicts.get(og)
            if verdict is not None:
                return verdict
            fields = None
            if og in protected:
                # The catalog, the page tree and kept pages are never cut,
                # whatever a pass concluded (self.dead refuses them as well).
                verdict = False
            else:
                verdict = og in dead
            if not verdict and og not in protected and value._type_code in _DICTLIKE:
                fields = _entries(value)
                typ = fields.get("/Type")
                kind = _SWEPT_TYPES.get(typ) if _type(typ) == _NAME else None
                if kind == _SWEPT_PAGE:
                    verdict = og not in templates
                elif kind == _SWEPT_ROOT:
                    verdict = og not in own_roots  # another document's
                elif kind == _SWEPT_ELEMENT:
                    verdict = og not in alive_elements  # removed, or outside the tree
                elif kind == _SWEPT_BEAD:
                    verdict = self.bead_dead(value)  # its ring may not have been walkable
                elif og not in live_annots and (
                    kind == _SWEPT_ANNOT or ("/Rect" in fields and "/Subtype" in fields)
                ):
                    if exact:
                        page = fields.get("/P")
                        verdict = _is_indirect_dictlike(page) and page.objgen in removed_pages
                    else:
                        verdict = True
                elif (
                    og not in outline_items
                    and "/Title" in fields
                    and ("/Parent" in fields or "/Prev" in fields or "/Next" in fields)
                ):
                    # A bookmark past a break in its list, which the outline
                    # pass could not reach. Judging it can rewrite its /A, so
                    # its entries are read again for the visit.
                    try:
                        verdict = self._stray_bookmark_dead(value, fields)
                    except Exception:  # noqa: BLE001 - unreadable: the visit reads it
                        verdict = False
                    fields = None
            verdicts[og] = verdict
            if not verdict:  # visited once, from here
                stack.append((value, fields if len(stack) < _HELD else None))
            return verdict

        def cut_direct(value) -> bool:
            """Queue a direct value for its visit; True for a page written in place."""
            if value._type_code == _ARRAY:
                stack.append((value, None))
                return False
            entries = _entries(value)
            if entries.get("/Type") == _PAGE:
                return True  # no page tree can list a page that is not an object
            stack.append((value, entries if len(stack) < _HELD else None))
            return False

        if not exhaustive:
            for value in self.pending:
                if value.__class__ in _SCALARS or _type(value) not in _CONTAINERS:
                    continue
                if not value.is_indirect:
                    stack.append((value, None))
                else:
                    is_dead(value, value.objgen)

        while stack:
            obj, fields = stack.pop()
            if obj._type_code == _ARRAY:
                if len(obj) >= _SCAN and _holds_no_objects(obj):
                    if obj.is_indirect:
                        self.inert.add(obj.objgen)
                    continue
                doomed = []
                _charge(len(obj))
                for i, value in enumerate(obj):
                    if value.__class__ in _SCALARS or getattr(value, "_type_code", None) not in _CONTAINERS:
                        continue
                    if value.is_indirect:
                        if is_dead(value, value.objgen):
                            doomed.append(i)
                    elif cut_direct(value):
                        doomed.append(i)
                for i in doomed:
                    obj[i] = None
                cut += len(doomed)
                continue
            if fields is None:
                fields = _entries(obj)
            doomed = []
            for key, value in fields.items():
                if value.__class__ in _SCALARS or getattr(value, "_type_code", None) not in _CONTAINERS:
                    continue
                if value.is_indirect:
                    if is_dead(value, value.objgen):
                        doomed.append(key)
                    continue
                if cut_direct(value):
                    doomed.append(key)
            for key in doomed:
                del obj[key]
            cut += len(doomed)
        if cut:
            logger.debug("page removal: cut %d stray references to removed objects", cut)


class _Record:
    """One structure element during pruning."""

    __slots__ = (
        "obj", "parent", "page", "kids", "kept", "alive", "had_kids", "single",
        "pg", "p", "ref", "texts", "recheck", "shared",
    )

    def __init__(self, obj, parent, page):
        self.obj = obj
        self.parent = parent
        self.page = page
        self.kids: list = []
        self.kept: list = []
        self.alive = True
        self.had_kids = False
        self.single = False
        self.pg = None
        self.p = None
        self.ref = None
        self.texts: list = []
        self.recheck = False
        self.shared = False  # its /K was read with another element
