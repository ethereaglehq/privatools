import pikepdf

from ..utils.cleanup import safe_open_pdf
from ..utils.exceptions import ValidationError
from ..utils.filenames import temp_output


def _iter_fields(fields_array):
    """Recursively iterate AcroForm fields including nested kids."""
    for field in fields_array:
        kids = field.get("/Kids")
        ft = field.get("/FT")

        if ft is not None:
            yield field

        if kids is not None:
            yield from _iter_fields(kids)


def _pdf_value_to_string(value) -> str:
    if value is None:
        return ""

    text = str(value)
    if text.startswith("/"):
        return text[1:]
    return text


def _normalize_field_type(field) -> str:
    ft = str(field.get("/FT", "/Tx"))
    flags = int(field.get("/Ff", 0) or 0)

    if ft == "/Btn":
        if flags & (1 << 15):
            return "radio"
        if flags & (1 << 16):
            return "button"
        return "checkbox"
    if ft == "/Ch":
        return "choice"
    if ft == "/Sig":
        return "signature"
    return "text"


def _extract_choice_options(field) -> list[str]:
    options = field.get("/Opt")
    if options is None:
        return []

    parsed: list[str] = []
    for option in options:
        if isinstance(option, pikepdf.Array) and len(option) > 0:
            label = _pdf_value_to_string(option[-1])
        else:
            label = _pdf_value_to_string(option)

        if label:
            parsed.append(label)

    return parsed


def _widgets(field) -> list:
    """The widget annotations that draw `field` on the page.

    A field with one widget is often a single merged dictionary; otherwise its
    widgets are its /Kids, which is how every radio group is built. A kid with
    a /T of its own is a child field, not a widget of this one.
    """
    kids = field.get("/Kids")
    if kids is None:
        return [field]
    return [kid for kid in kids if "/T" not in kid]


def _appearance_states(widget) -> list[str]:
    """A button widget's normal appearance states, such as ["Off", "Yes"]."""
    ap = widget.get("/AP")
    if not ap or "/N" not in ap:
        return []
    normal_appearance = ap["/N"]
    if not isinstance(normal_appearance, pikepdf.Dictionary):
        return []
    return [_pdf_value_to_string(state) for state in normal_appearance.keys()]


def _extract_button_options(field) -> list[str]:
    options: list[str] = []
    for widget in _widgets(field):
        for label in _appearance_states(widget):
            if label and label.lower() != "off" and label not in options:
                options.append(label)

    return options


def _set_button_state(field, state) -> None:
    """Record `state` as the field's value and show it on its widgets.

    Each widget shows the state if it has an appearance for it; the others,
    the unchosen buttons of a radio group, show Off.
    """
    field["/V"] = state
    for widget in _widgets(field):
        states = _appearance_states(widget)
        if states and _pdf_value_to_string(state) not in states:
            widget["/AS"] = pikepdf.Name("/Off")
        else:
            widget["/AS"] = state


def _checkbox_on_state(field):
    options = _extract_button_options(field)
    if options:
        return pikepdf.Name(f"/{options[0]}")
    return pikepdf.Name("/Yes")


def _to_pdf_name(value: str):
    cleaned = value.strip()
    if not cleaned:
        return pikepdf.Name("/Off")
    if not cleaned.startswith("/"):
        cleaned = f"/{cleaned}"
    return pikepdf.Name(cleaned)


def _is_truthy_checkbox(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on", "checked"}


def get_form_fields(input_path: str) -> list:
    with safe_open_pdf(input_path) as pdf:
        try:
            acroform = pdf.Root.AcroForm
            fields_array = acroform.Fields
        except AttributeError as exc:
            raise ValidationError("PDF has no form fields") from exc

        result = []
        for field in _iter_fields(fields_array):
            name = _pdf_value_to_string(field.get("/T", "")).strip()
            if not name:
                continue

            field_type = _normalize_field_type(field)
            value = _pdf_value_to_string(field.get("/V", ""))
            item = {
                "name": name,
                "type": field_type,
                "value": value,
            }

            if field_type == "choice":
                options = _extract_choice_options(field)
                if options:
                    item["options"] = options
            elif field_type in {"checkbox", "radio"}:
                options = _extract_button_options(field)
                if options:
                    item["options"] = options

            result.append(item)

        return result


def fill_form(input_path: str, field_values: dict) -> str:
    output_path = temp_output("filled_form", "pdf")

    with safe_open_pdf(input_path) as pdf:
        try:
            acroform = pdf.Root.AcroForm
            fields_array = acroform.Fields
        except AttributeError as exc:
            raise ValidationError("PDF has no form fields") from exc

        for field in _iter_fields(fields_array):
            name = _pdf_value_to_string(field.get("/T", "")).strip()
            if not name or name not in field_values:
                continue

            raw_value = str(field_values[name])
            field_type = _normalize_field_type(field)

            if field_type == "checkbox":
                if _is_truthy_checkbox(raw_value):
                    state = _checkbox_on_state(field)
                else:
                    state = pikepdf.Name("/Off")
                _set_button_state(field, state)
            elif field_type == "radio":
                state = _to_pdf_name(raw_value)
                options = _extract_button_options(field)
                chosen = _pdf_value_to_string(state)
                if options and chosen != "Off" and chosen not in options:
                    # The page sends every field back, touched or not; leave a
                    # value the form already had as it is, however odd.
                    if chosen == _pdf_value_to_string(field.get("/V", "")):
                        continue
                    raise ValidationError(
                        f"'{raw_value}' is not an option of radio field '{name}'. "
                        f"Choose one of: {', '.join(options)}."
                    )
                _set_button_state(field, state)
            elif field_type == "choice":
                field["/V"] = pikepdf.String(raw_value)
                if "/AP" in field:
                    del field["/AP"]
            else:
                field["/V"] = pikepdf.String(raw_value)
                if "/AP" in field:
                    del field["/AP"]

        try:
            acroform["/NeedAppearances"] = pikepdf.Boolean(True)
        except (AttributeError, TypeError):
            # Older AcroForm with read-only dict — value isn't critical.
            pass

        pdf.save(str(output_path))

    return str(output_path)
