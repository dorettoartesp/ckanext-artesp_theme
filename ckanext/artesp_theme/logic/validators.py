import json
import re
from datetime import datetime

import ckan.plugins.toolkit as tk

from ckanext.artesp_theme.logic.rating import RATING_CRITERIA


RATING_COMMENT_MAX_LENGTH = 5000
_RATING_TRUE = {"true", "1", "yes", "sim", "verdadeiro"}
_RATING_FALSE = {"false", "0", "no", "não", "nao", "falso"}


def artesp_theme_required(value):
    if not value or value is tk.missing:
        raise tk.Invalid(tk._("Required"))
    return value


def artesp_date_br_to_iso(value, context):
    """
    Convert Brazilian date format (dd/mm/yyyy) to ISO format (yyyy-mm-dd)
    for storage in CKAN database.

    Args:
        value: Date string in Brazilian format (dd/mm/yyyy) or ISO format
        context: CKAN validation context

    Returns:
        Date string in ISO format (yyyy-mm-dd)

    Raises:
        Invalid: If date format is incorrect or date is invalid
    """
    if not value or value.strip() == '':
        return value

    # Remove any extra whitespace
    value = value.strip()

    # Check if it's already in ISO format (yyyy-mm-dd)
    iso_pattern = r'^\d{4}-\d{2}-\d{2}$'
    if re.match(iso_pattern, value):
        # Validate that it's a real date
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError:
            raise tk.Invalid(tk._('Data inválida. Use o formato dd/mm/aaaa'))

    # Check Brazilian format (dd/mm/yyyy)
    br_pattern = r'^(\d{1,2})/(\d{1,2})/(\d{4})$'
    match = re.match(br_pattern, value)

    if not match:
        raise tk.Invalid(tk._('Data deve estar no formato dd/mm/aaaa'))

    day, month, year = match.groups()

    # Validate and convert the date
    try:
        # Pad day and month with zeros if needed
        day = day.zfill(2)
        month = month.zfill(2)

        # Validate that it's a real date
        datetime.strptime(f'{year}-{month}-{day}', '%Y-%m-%d')

        # Return in ISO format
        return f'{year}-{month}-{day}'
    except ValueError:
        raise tk.Invalid(tk._('Data inválida. Verifique se o dia, mês e ano estão corretos'))


def artesp_date_iso_to_br(value, context):
    """
    Convert ISO date format (yyyy-mm-dd) to Brazilian format (dd/mm/yyyy)
    for display in forms and views.

    Args:
        value: Date string in ISO format (yyyy-mm-dd) or Brazilian format
        context: CKAN validation context

    Returns:
        Date string in Brazilian format (dd/mm/yyyy)
    """
    if not value or value.strip() == '':
        return value

    # Remove any extra whitespace
    value = value.strip()

    # Check if it's already in Brazilian format (dd/mm/yyyy)
    br_pattern = r'^\d{1,2}/\d{1,2}/\d{4}$'
    if re.match(br_pattern, value):
        return value

    # Check ISO format (yyyy-mm-dd)
    iso_pattern = r'^(\d{4})-(\d{2})-(\d{2})$'
    match = re.match(iso_pattern, value)

    if not match:
        # Return as-is if not in expected format
        return value

    year, month, day = match.groups()

    # Convert to Brazilian format (remove leading zeros from day and month)
    day = str(int(day))
    month = str(int(month))

    return f'{day}/{month}/{year}'


def artesp_boolean_validator(value, context):
    """
    Convert string boolean values to actual boolean and validate against
    allowed values [True, False] for proper display as "Sim"/"Não" in forms and templates.

    Args:
        value: String or boolean value
        context: CKAN validation context

    Returns:
        Boolean value

    Raises:
        Invalid: If value cannot be converted to boolean or is not in allowed values
    """
    if value is None or value == '':
        return value

    # If already a boolean, validate it's in allowed values
    if isinstance(value, bool):
        if value in [True, False]:
            return value
        else:
            raise tk.Invalid(tk._('Value must be one of [True, False]'))

    # Convert string representations to boolean
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ('true', '1', 'yes', 'sim', 'verdadeiro'):
            return True
        elif value_lower in ('false', '0', 'no', 'não', 'nao', 'falso'):
            return False
        else:
            raise tk.Invalid(tk._('Value must be one of [True, False]'))

    # If we get here, the value type is not supported
    raise tk.Invalid(tk._('Value must be one of [True, False]'))


def _coerce_rating_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value in (0, 1):
            return bool(value)
        raise tk.Invalid(tk._("Value must be one of [True, False]"))
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in _RATING_TRUE:
            return True
        if lowered in _RATING_FALSE:
            return False
    raise tk.Invalid(tk._("Value must be one of [True, False]"))


def rating_overall_validator(value, context):
    """Validate the overall rating as an integer between 1 and 5."""
    if value is None or value == "" or value is tk.missing:
        raise tk.Invalid(tk._("Overall rating is required"))
    if isinstance(value, bool):
        raise tk.Invalid(tk._("Overall rating must be an integer between 1 and 5"))
    if isinstance(value, float) and not value.is_integer():
        raise tk.Invalid(tk._("Overall rating must be an integer between 1 and 5"))
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise tk.Invalid(tk._("Overall rating must be an integer between 1 and 5"))
    if parsed < 1 or parsed > 5:
        raise tk.Invalid(tk._("Overall rating must be an integer between 1 and 5"))
    return parsed


def rating_criteria_validator(value, context):
    """Validate the boolean criteria dict against the canonical RATING_CRITERIA.

    Accepts a dict or a JSON string. All keys must be in RATING_CRITERIA.
    Values are coerced to bool when possible, else rejected.
    Returns a normalized dict of bools (possibly empty).
    """
    if value is None or value == "" or value is tk.missing:
        return {}
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            raise tk.Invalid(tk._("Criteria must be a JSON object of booleans"))
    if not isinstance(value, dict):
        raise tk.Invalid(tk._("Criteria must be a JSON object of booleans"))

    allowed = set(RATING_CRITERIA)
    unknown = set(value.keys()) - allowed
    if unknown:
        raise tk.Invalid(
            tk._("Unknown criteria keys: {keys}").format(
                keys=", ".join(sorted(unknown))
            )
        )

    normalized = {}
    for key, raw in value.items():
        normalized[key] = _coerce_rating_bool(raw)
    return normalized


def rating_comment_validator(value, context):
    """Normalize a rating comment.

    Empty strings, whitespace-only strings and None become None.
    Leading/trailing whitespace is stripped; internal spacing is preserved.
    Rejects non-string input and comments longer than RATING_COMMENT_MAX_LENGTH.
    """
    if value is None or value is tk.missing:
        return None
    if not isinstance(value, str):
        raise tk.Invalid(tk._("Comment must be a string"))
    stripped = value.strip()
    if not stripped:
        return None
    if len(stripped) > RATING_COMMENT_MAX_LENGTH:
        raise tk.Invalid(
            tk._("Comment must be at most {n} characters").format(
                n=RATING_COMMENT_MAX_LENGTH
            )
        )
    return stripped


def get_validators():
    return {
        "artesp_theme_required": artesp_theme_required,
        "artesp_date_br_to_iso": artesp_date_br_to_iso,
        "artesp_date_iso_to_br": artesp_date_iso_to_br,
        "artesp_boolean_validator": artesp_boolean_validator,
        "rating_overall_validator": rating_overall_validator,
        "rating_criteria_validator": rating_criteria_validator,
        "rating_comment_validator": rating_comment_validator,
    }
