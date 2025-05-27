# ARTESP Custom Validators

This document describes the custom validators implemented in the ckanext-artesp_theme extension to support the ARTESP dataset schema with Portuguese labels and Brazilian date formats.

## Overview

The extension implements three custom validators that work with the ARTESP dataset schema deployed via the `ckan_dcat` Ansible role:

1. **artesp_date_br_to_iso** - Converts Brazilian date format (dd/mm/yyyy) to ISO format (yyyy-mm-dd) for database storage
2. **artesp_date_iso_to_br** - Converts ISO format back to Brazilian format for form display
3. **artesp_boolean_validator** - Converts string boolean values to actual boolean types for proper "Sim"/"Não" display

## Validators Details

### artesp_date_br_to_iso

**Purpose**: Convert Brazilian date format to ISO format for database storage.

**Input**: Date string in Brazilian format (dd/mm/yyyy) or ISO format
**Output**: Date string in ISO format (yyyy-mm-dd)

**Examples**:
- `"15/03/2024"` → `"2024-03-15"`
- `"1/1/2024"` → `"2024-01-01"`
- `"2024-03-15"` → `"2024-03-15"` (already ISO)

**Error Handling**:
- Validates actual date values (e.g., rejects 32/01/2024)
- Raises `Invalid` exception with Portuguese error messages
- Accepts empty values without validation

### artesp_date_iso_to_br

**Purpose**: Convert ISO date format to Brazilian format for display.

**Input**: Date string in ISO format (yyyy-mm-dd) or Brazilian format
**Output**: Date string in Brazilian format (dd/mm/yyyy)

**Examples**:
- `"2024-03-15"` → `"15/3/2024"`
- `"2024-01-01"` → `"1/1/2024"`
- `"15/3/2024"` → `"15/3/2024"` (already Brazilian)

**Features**:
- Removes leading zeros from day and month for display
- Returns original value if format is not recognized
- Handles empty values gracefully

### artesp_boolean_validator

**Purpose**: Convert string boolean values to actual boolean types.

**Input**: String or boolean value
**Output**: Boolean value or original value if conversion not possible

**True Values**: `"true"`, `"True"`, `"1"`, `"yes"`, `"sim"`, `"verdadeiro"`
**False Values**: `"false"`, `"False"`, `"0"`, `"no"`, `"não"`, `"nao"`, `"falso"`

**Examples**:
- `"true"` → `True`
- `"sim"` → `True`
- `"false"` → `False`
- `"não"` → `False`
- `"invalid"` → `"invalid"` (unchanged)

## Schema Integration

These validators are used in the ARTESP dataset schema (`artesp_dataset_schema.yaml`) for the following fields:

### Date Fields
- **coberturaTemporalInicio** (Temporal Coverage Start)
- **coberturaTemporalFim** (Temporal Coverage End)
- **dataDescontinuacao** (Discontinuation Date)

### Boolean Fields
- **atualizacaoVersao** (Version Update)
- **descontinuado** (Discontinued)
- **dadosRacaEtnia** (Contains race/ethnicity data)
- **dadosGenero** (Contains gender data)
- **dadosIdade** (Contains age data)

## Usage in Schema

```yaml
# Date field example
- field_name: coberturaTemporalInicio
  label: Cobertura Temporal Início
  form_snippet: date.html
  display_snippet: date.html
  validators: ignore_missing artesp_date_br_to_iso
  output_validators: artesp_date_iso_to_br
  help_text: Data de início da cobertura temporal (dd/mm/aaaa)

# Boolean field example
- field_name: descontinuado
  label: Descontinuado
  preset: select
  choices:
    - value: "true"
      label: Sim
    - value: "false"
      label: Não
  validators: ignore_missing scheming_choices
  output_validators: artesp_boolean_validator
  form_include_blank_choice: true
```

## Testing

The validators include comprehensive tests in `tests/logic/test_validators.py`:

```bash
# Run tests (from CKAN virtual environment)
pytest ckanext/artesp_theme/tests/logic/test_validators.py -v
```

## Error Messages

All error messages are in Portuguese:

- `"Data deve estar no formato dd/mm/aaaa"` - Invalid date format
- `"Data inválida. Use o formato dd/mm/aaaa"` - Invalid ISO date
- `"Data inválida. Verifique se o dia, mês e ano estão corretos"` - Invalid date values

## Implementation Notes

1. **Date Validation**: Uses Python's `datetime.strptime()` for robust date validation
2. **Format Flexibility**: Accepts both single and double-digit days/months (1/1/2024 or 01/01/2024)
3. **Error Handling**: Provides user-friendly Portuguese error messages
4. **Empty Values**: Gracefully handles empty/None values without validation
5. **Bidirectional**: Date validators work in both directions (BR→ISO and ISO→BR)

## Plugin Registration

The validators are registered in the plugin class via the `IValidators` interface:

```python
class ArtespThemePlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IValidators)
    
    def get_validators(self):
        return validators.get_validators()
```

This makes them available throughout CKAN for use in schemas and forms.
