"""Sanitize a PDF: remove active content, attachments, hidden layers and metadata.

What goes:

- document JavaScript (the /Names JavaScript tree and a script /OpenAction)
  and every additional-actions (/AA) dictionary: document, page, annotation
  and form-field events;
- every action other than moving within the document, resetting a form or
  opening an http, https or mailto link, wherever an action can fire: on
  every reachable dictionary or stream that holds one, whether a link,
  widget, form field, bookmark or anything else, and along each /Next
  chain. The open action, which runs without a click, keeps only moves
  within the document. That covers Launch, JavaScript, GoToR, GoToE,
  SubmitForm, ImportData, media and 3D actions, and URIs such as javascript:
  or file:;
- embedded files: the EmbeddedFiles tree, file attachment annotations,
  associated files (/AF), portfolio (/Collection) settings and the embedded
  file streams of any file specification;
- page templates (/Names /Templates), which only scripts use;
- sound, movie, screen, rich media and 3D annotations;
- XFA form data. AcroForm fields stay fillable and keep their values;
- content in optional-content layers that are hidden when the file opens,
  whether in page contents, form XObjects, annotation appearances, tiling
  patterns, Type 3 glyphs or soft masks. The visible layers become ordinary
  page content, so nothing hidden is left to switch on;
- XMP metadata streams, wherever they are attached, and the document
  information dictionary.

A password needed to open the file is rejected by ``safe_open_pdf``; an owner
password, which only limits what a reader allows, is kept with its limits.

Every walk is bounded: shared and cyclic structures are visited once, so a
file built to make one loop cannot.
"""

from __future__ import annotations

import io
import logging

import pikepdf
from pikepdf import Array, ContentStreamInstruction, Dictionary, Name, Operator

from ..utils.cleanup import remove_files, safe_open_pdf
from ..utils.filenames import temp_output

logger = logging.getLogger(__name__)

# An allowlist, so an action type this code has never heard of is removed too.
_SAFE_ACTIONS = frozenset({"/GoTo", "/GoToDp", "/Named", "/Thread", "/Hide", "/Trans", "/ResetForm", "/URI"})
# The document's open action runs without a click, so it keeps only moves
# within the document: a web or email address there would open by itself.
_OPEN_ACTIONS = frozenset({"/GoTo", "/GoToDp", "/Named", "/Thread"})
_SAFE_URI_SCHEMES = ("http:", "https:", "mailto:")
# Named actions beyond these four run viewer menu commands.
_NAVIGATION_NAMES = frozenset({"/NextPage", "/PrevPage", "/FirstPage", "/LastPage"})
_MEDIA_ANNOTATIONS = frozenset({"/FileAttachment", "/Sound", "/Movie", "/Screen", "/RichMedia", "/3D"})
# Templates are pages kept outside the page tree for scripts to copy in.
_NAME_TREES_REMOVED = ("/JavaScript", "/EmbeddedFiles", "/AlternatePresentations", "/Renditions", "/Templates")
# These keys only ever hold event scripts, attached files, XMP metadata or
# optional-content membership, so they can go wherever they appear.
_KEYS_REMOVED_EVERYWHERE = ("/AA", "/AF", "/EF", "/RF", "/Metadata", "/OC")
# Keys whose value is an action on any owner: a link, widget, field or
# bookmark's /A, and a link's /PA. The catalog's /OpenAction is handled apart.
_ACTION_KEYS = ("/A", "/PA")
# Bounds /Next chains, visibility expressions and page-tree inheritance.
_MAX_DEPTH = 32

# Inside hidden content, painting operators become "n": the path ends without
# being painted, and a clip set with W or W* still applies, as it does when a
# reader skips hidden content.
_PAINT_OPERATORS = frozenset({"S", "s", "f", "F", "f*", "B", "B*", "b", "b*"})
# Operators that draw or mark content, dropped inside hidden content. Every
# other operator only changes the graphics or text state, which a reader
# applies even to hidden content, so it is kept to leave later content as it was.
_DRAWING_OPERATORS = frozenset({"Tj", "TJ", "Do", "sh", "BMC", "BDC", "EMC", "MP", "DP"})


def sanitize_pdf(data: bytes) -> str:
    """Write a sanitized copy of the PDF in ``data`` to a temp file and return its path."""
    output_path = temp_output("sanitized", "pdf")
    with safe_open_pdf(io.BytesIO(data)) as pdf:
        _remove_hidden_layers(pdf)
        _remove_document_features(pdf)
        memo: dict[tuple[int, int], bool] = {}
        for page in pdf.pages:
            _sanitize_annotations(page.obj, memo)
        _clean_everywhere(pdf, memo)
        if "/Info" in pdf.trailer:
            del pdf.trailer["/Info"]
        try:
            pdf.save(str(output_path), encryption=pdf.is_encrypted)
        except Exception:
            remove_files(output_path)
            raise
    return str(output_path)


# ── Actions ──────────────────────────────────────────────────────────────────

def _is_safe_action(action: Dictionary, on_open: bool = False) -> bool:
    kind = action.get("/S")
    if not isinstance(kind, Name) or str(kind) not in (_OPEN_ACTIONS if on_open else _SAFE_ACTIONS):
        return False
    if kind == Name.URI:
        return str(action.get("/URI", "")).strip().lower().startswith(_SAFE_URI_SCHEMES)
    if kind == Name.Named:
        return str(action.get("/N", "")) in _NAVIGATION_NAMES
    if kind == Name.Thread:
        # A thread in another file is a remote go-to.
        return "/F" not in action
    return True


def _keep_action(action, memo: dict, depth: int = 0, on_open: bool = False) -> bool:
    """Say whether ``action`` is safe, cutting unsafe steps from its /Next chain.

    Only a dictionary can be kept: an action stored as a stream is removed.
    ``memo`` records each indirect action once, so shared or cyclic chains are
    walked a bounded number of times. ``on_open`` applies the open action's
    stricter rule to the whole chain.
    """
    if not isinstance(action, Dictionary) or depth > _MAX_DEPTH:
        return False
    key = action.objgen if action.is_indirect else None
    if key in memo:
        return memo[key]
    safe = _is_safe_action(action, on_open)
    if key is not None:
        memo[key] = safe  # recorded before the chain is walked, so a cycle stops here
    following = action.get("/Next")
    if safe and following is not None:
        steps = list(following) if isinstance(following, Array) else [following]
        kept = [step for step in steps if _keep_action(step, memo, depth + 1, on_open)]
        if not kept:
            del action["/Next"]
        elif len(kept) != len(steps):
            action.Next = Array(kept)
    return safe


def _filter_action_key(owner, key: str, memo: dict, on_open: bool = False) -> None:
    """Remove ``owner[key]`` unless it is a safe action; the owner may be a stream."""
    if key in owner and not _keep_action(owner[key], memo, on_open=on_open):
        del owner[key]


def _is_action(value) -> bool:
    """Whether a value under /A or /PA is an action, not something else by that name.

    In a tagged PDF a structure element's /A holds layout attributes: a
    dictionary without /S, or an array of them. Readers know an action by its
    /S, so a dictionary with /S, a script or a following action is one, and
    so is anything stored as a stream, which attributes never are.
    """
    if isinstance(value, pikepdf.Stream):
        return True
    if not isinstance(value, Dictionary):
        return False
    return any(key in value for key in ("/S", "/JS", "/Next")) or value.get("/Type") == Name.Action


def _remove_document_features(pdf: pikepdf.Pdf) -> None:
    root = pdf.Root
    names = root.get("/Names")
    if isinstance(names, Dictionary):
        for key in _NAME_TREES_REMOVED:
            if key in names:
                del names[key]
    for key in ("/Collection", "/NeedsRendering"):
        if key in root:
            del root[key]
    acroform = root.get("/AcroForm")
    if isinstance(acroform, Dictionary) and "/XFA" in acroform:
        del acroform["/XFA"]


def _sanitize_annotations(page: Dictionary, memo: dict) -> None:
    """Drop media and file annotations, and links left doing nothing.

    An annotation stored as a stream is dropped too: no reader can draw one.
    """
    annots = page.get("/Annots")
    if not isinstance(annots, Array):
        return
    kept, removed = [], set()
    for annot in annots:
        if not isinstance(annot, Dictionary):
            continue
        subtype = str(annot.get("/Subtype", ""))
        if subtype not in _MEDIA_ANNOTATIONS:
            _filter_action_key(annot, "/A", memo)
            _filter_action_key(annot, "/PA", memo)
            # A link left with neither an action nor a destination does nothing.
            if subtype != "/Link" or "/A" in annot or "/Dest" in annot:
                kept.append(annot)
                continue
        if annot.is_indirect:
            removed.add(annot.objgen)
    # Pop-up notes belong to the annotation that owns them.
    kept = [
        annot for annot in kept
        if not (
            annot.get("/Subtype") == Name.Popup
            and isinstance(annot.get("/Parent"), Dictionary)
            and annot.Parent.is_indirect
            and annot.Parent.objgen in removed
        )
    ]
    if len(kept) != len(annots):
        page.Annots = Array(kept)


def _clean_everywhere(pdf: pikepdf.Pdf, memo: dict) -> None:
    """Visit every reachable dictionary and stream once, whatever it is.

    Each loses the keys in ``_KEYS_REMOVED_EVERYWHERE``, and each action it
    holds is judged by the allowlist. Nothing here assumes where an action
    lives or what holds it: readers take a stream as a bookmark, an action or
    an open action, and act on objects that no walk from the page tree or the
    form's field list reaches, such as a parent field missing from /Fields.
    """
    open_memo: dict[tuple[int, int], bool] = {}  # the open action's stricter rule
    stack, seen = [pdf.trailer], set()
    while stack:
        obj = stack.pop()
        if isinstance(obj, Array):
            stack.extend(obj)
            continue
        if not isinstance(obj, (Dictionary, pikepdf.Stream)):
            continue
        if obj.is_indirect:
            if obj.objgen in seen:
                continue
            seen.add(obj.objgen)
        for key in _KEYS_REMOVED_EVERYWHERE:
            if key in obj:
                del obj[key]
        for key in _ACTION_KEYS:
            if key in obj and _is_action(obj[key]):
                _filter_action_key(obj, key, memo)
        # An /OpenAction array, name or string is a destination: open at a page.
        if isinstance(obj.get("/OpenAction"), (Dictionary, pikepdf.Stream)):
            _filter_action_key(obj, "/OpenAction", open_memo, on_open=True)
        stack.extend(obj.values())


# ── Optional content (layers) ────────────────────────────────────────────────

def _default_states(properties: Dictionary) -> dict[tuple[int, int], bool]:
    """Map each optional content group to whether it is on when the file opens."""
    config = properties.get("/D")
    if not isinstance(config, Dictionary):
        config = Dictionary()
    on = {group.objgen for group in config.get("/ON", Array()) if isinstance(group, Dictionary)}
    off = {group.objgen for group in config.get("/OFF", Array()) if isinstance(group, Dictionary)}
    base_off = config.get("/BaseState") == Name.OFF
    groups = properties.get("/OCGs")
    states = {}
    for group in groups if isinstance(groups, Array) else ():
        if isinstance(group, Dictionary) and group.is_indirect:
            states[group.objgen] = group.objgen in on if base_off else group.objgen not in off
    return states


class _Layers:
    """Whether optional content is visible when the file opens.

    Anything unknown or malformed counts as visible, as it does in readers, so
    the worst a strange file gets is content that stops being hidden. Each
    membership dictionary is evaluated once per document, and one that refers
    back to itself counts as visible, so no file can make evaluation run long:
    without that, a dictionary naming itself ten times in its /VE took some
    10^16 steps.
    """

    def __init__(self, properties: Dictionary):
        self.states = _default_states(properties)
        self.memberships: dict[tuple[int, int], bool] = {}

    def visible(self, oc, depth: int = 0) -> bool:
        """Evaluate an optional content group or membership dictionary."""
        if not isinstance(oc, Dictionary) or depth > _MAX_DEPTH:
            return True
        if oc.get("/Type") != Name.OCMD:
            return self.states.get(oc.objgen, True) if oc.is_indirect else True
        key = oc.objgen if oc.is_indirect else None
        if key in self.memberships:
            return self.memberships[key]
        if key is not None:
            self.memberships[key] = True  # what a reference back to it sees while it is evaluated
        result = self._membership(oc, depth)
        if key is not None:
            self.memberships[key] = result
        return result

    def _membership(self, oc: Dictionary, depth: int) -> bool:
        expression = oc.get("/VE")
        if expression is not None:
            return self._expression(expression, depth + 1)
        groups = oc.get("/OCGs")
        members = [groups] if isinstance(groups, Dictionary) else list(groups) if isinstance(groups, Array) else []
        values = [self.visible(member, depth + 1) for member in members]
        if not values:
            return True
        policy = oc.get("/P")
        if policy == Name.AllOn:
            return all(values)
        if policy == Name.AnyOff:
            return not all(values)
        if policy == Name.AllOff:
            return not any(values)
        return any(values)

    def _expression(self, expression, depth: int) -> bool:
        if depth > _MAX_DEPTH:
            return True
        if isinstance(expression, Dictionary):
            return self.visible(expression, depth)
        if not isinstance(expression, Array) or len(expression) < 2:
            return True
        operator, operands = expression[0], [self._expression(e, depth + 1) for e in expression[1:]]
        if operator == Name.Not:
            return not operands[0]
        if operator == Name.And:
            return all(operands)
        if operator == Name.Or:
            return any(operands)
        return True


def _inherited_resources(page: Dictionary):
    node = page
    for _ in range(_MAX_DEPTH):
        if not isinstance(node, Dictionary):
            return None
        if "/Resources" in node:
            return node.Resources
        node = node.get("/Parent")
    return None


def _appearance_streams(annot: Dictionary) -> list:
    appearances = annot.get("/AP")
    if not isinstance(appearances, Dictionary):
        return []
    streams = []
    for key in ("/N", "/R", "/D"):
        entry = appearances.get(key)
        if isinstance(entry, pikepdf.Stream):
            streams.append(entry)
        elif isinstance(entry, Dictionary):
            streams += [state for state in entry.values() if isinstance(state, pikepdf.Stream)]
    return streams


def _nested_content(resources) -> list:
    """Content streams that resources draw other than form XObjects.

    Tiling pattern cells, Type 3 glyphs and soft-mask groups can hold layered
    content too; left alone, their hidden parts would show once the layer
    settings are gone. Each comes with the resources it is drawn with.
    """
    if not isinstance(resources, Dictionary):
        return []
    found = []
    patterns = resources.get("/Pattern")
    if isinstance(patterns, Dictionary):
        found += [
            (pattern, resources) for pattern in patterns.values()
            if isinstance(pattern, pikepdf.Stream) and pattern.get("/PatternType") == 1
        ]
    fonts = resources.get("/Font")
    if isinstance(fonts, Dictionary):
        for font in fonts.values():
            procs = font.get("/CharProcs") if isinstance(font, Dictionary) and font.get("/Subtype") == Name.Type3 else None
            if isinstance(procs, Dictionary):
                glyph_resources = font.get("/Resources", resources)
                found += [(proc, glyph_resources) for proc in procs.values() if isinstance(proc, pikepdf.Stream)]
    states = resources.get("/ExtGState")
    if isinstance(states, Dictionary):
        for state in states.values():
            mask = state.get("/SMask") if isinstance(state, Dictionary) else None
            group = mask.get("/G") if isinstance(mask, Dictionary) else None
            if isinstance(group, pikepdf.Stream):
                found.append((group, resources))
    return found


def _hidden_equivalent(operator: str, operands) -> list | None:
    """What stays of an instruction inside hidden content; None keeps it unchanged."""
    if operator in _PAINT_OPERATORS:
        return [ContentStreamInstruction([], Operator("n"))]
    if operator in _DRAWING_OPERATORS:
        return []
    if operator == "'":
        return [ContentStreamInstruction([], Operator("T*"))]
    if operator == '"':
        spacing = [
            ContentStreamInstruction([operands[0]], Operator("Tw")),
            ContentStreamInstruction([operands[1]], Operator("Tc")),
        ] if len(operands) == 3 else []
        return spacing + [ContentStreamInstruction([], Operator("T*"))]
    return None


def _strip_hidden_content(instructions, resources, layers: _Layers):
    """Drop hidden optional content and unwrap the visible sections.

    Returns the new instructions, whether anything changed, and the form
    XObjects drawn from visible content, which need the same treatment.

    A caveat: text drawn inside hidden content no longer advances the text
    position, so visible text continuing on the same line of the same text
    object would move left. Layers normally wrap whole text objects.
    """
    resources = resources if isinstance(resources, Dictionary) else Dictionary()
    properties = resources.get("/Properties")
    xobjects = resources.get("/XObject")
    out, forms = [], []
    sections: list[tuple[bool, bool]] = []  # (is optional content, visible) per open marked-content section
    hidden = 0  # open optional-content sections that are hidden
    changed = False
    for instruction in instructions:
        if isinstance(instruction, pikepdf.ContentStreamInlineImage):
            if hidden:
                changed = True
            else:
                out.append(instruction)
            continue
        operator, operands = str(instruction.operator), instruction.operands
        if operator == "BDC" and len(operands) == 2 and operands[0] == Name.OC:
            oc = operands[1]
            if isinstance(oc, Name):
                oc = properties.get(str(oc)) if isinstance(properties, Dictionary) else None
            visible = layers.visible(oc)
            sections.append((True, visible))
            if not visible:
                hidden += 1
            changed = True
            continue
        if operator in ("BDC", "BMC"):
            sections.append((False, True))
        elif operator == "EMC" and sections:
            is_optional, visible = sections.pop()
            if is_optional:
                if not visible:
                    hidden -= 1
                changed = True
                continue
        if hidden:
            replacement = _hidden_equivalent(operator, operands)
            if replacement is not None:
                out += replacement
                changed = True
                continue
        elif operator == "Do" and operands and isinstance(xobjects, Dictionary):
            xobject = xobjects.get(str(operands[0]))
            if isinstance(xobject, pikepdf.Stream):
                if not layers.visible(xobject.get("/OC")):
                    changed = True
                    continue
                if xobject.get("/Subtype") == Name.Form:
                    forms.append(xobject)
        out.append(instruction)
    return out, changed, forms


def _remove_hidden_layers(pdf: pikepdf.Pdf) -> None:
    properties = pdf.Root.get("/OCProperties")
    if not isinstance(properties, Dictionary):
        return
    layers = _Layers(properties)
    visited: set[tuple[int, int]] = set()  # content streams done
    expanded: set[tuple[int, int]] = set()  # shared resource dictionaries whose nested content is queued
    changed_any = False
    for page in pdf.pages:
        page_resources = _inherited_resources(page.obj)
        work = [(page, page_resources)]
        annots = page.obj.get("/Annots")
        if isinstance(annots, Array):
            # Hidden widgets stay, and become visible, so the form keeps its fields.
            kept = [
                annot for annot in annots
                if not isinstance(annot, Dictionary)
                or annot.get("/Subtype") == Name.Widget
                or layers.visible(annot.get("/OC"))
            ]
            if len(kept) != len(annots):
                page.obj.Annots = Array(kept)
                changed_any = True
            for annot in kept:
                if isinstance(annot, Dictionary):
                    work += [(stream, page_resources) for stream in _appearance_streams(annot)]
        while work:
            owner, resources = work.pop()
            if isinstance(owner, pikepdf.Stream):
                if owner.objgen in visited:
                    continue
                visited.add(owner.objgen)
                resources = owner.get("/Resources", resources)
            shared = resources.objgen if isinstance(resources, Dictionary) and resources.is_indirect else None
            if shared not in expanded:
                if shared is not None:
                    expanded.add(shared)
                work += [item for item in _nested_content(resources) if item[0].objgen not in visited]
            try:
                instructions = pikepdf.parse_content_stream(owner)
            except pikepdf.PdfError:
                # Left as it is: without /OCProperties its layers all show.
                logger.warning("Sanitize: could not parse a content stream; its layers become visible")
                continue
            out, changed, forms = _strip_hidden_content(instructions, resources, layers)
            work += [(form, resources) for form in forms]
            if changed:
                data = pikepdf.unparse_content_stream(out)
                if isinstance(owner, pikepdf.Stream):
                    owner.write(data)
                else:
                    owner.obj.Contents = pdf.make_stream(data)
                changed_any = True
    del pdf.Root["/OCProperties"]
    if changed_any:
        # Images and forms drawn only by hidden content are now unused.
        pdf.remove_unreferenced_resources()
