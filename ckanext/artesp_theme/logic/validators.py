import ckan.plugins.toolkit as tk
import re
from datetime import datetime


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
    Convert string boolean values to actual boolean for proper display
    as "Sim"/"Não" in forms and templates.

    Args:
        value: String or boolean value
        context: CKAN validation context

    Returns:
        Boolean value or original value if conversion not possible
    """
    if value is None or value == '':
        return value

    # If already a boolean, return as-is
    if isinstance(value, bool):
        return value

    # Convert string representations to boolean
    if isinstance(value, str):
        value_lower = value.lower().strip()
        if value_lower in ('true', '1', 'yes', 'sim', 'verdadeiro'):
            return True
        elif value_lower in ('false', '0', 'no', 'não', 'nao', 'falso'):
            return False

    # Return original value if no conversion possible
    return value


def get_validators():
    return {
        "artesp_theme_required": artesp_theme_required,
        "artesp_date_br_to_iso": artesp_date_br_to_iso,
        "artesp_date_iso_to_br": artesp_date_iso_to_br,
        "artesp_boolean_validator": artesp_boolean_validator,
    }
