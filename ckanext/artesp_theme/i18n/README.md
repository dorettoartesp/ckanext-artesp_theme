# Internationalization (i18n) Guide for ARTESP CKAN Theme

This guide explains how to extract, translate, and compile messages for the ARTESP CKAN theme extension, with a focus on Brazilian Portuguese (pt_BR) translations.

## Prerequisites

Make sure you have the following packages installed:

- Babel
- polib (optional, for advanced PO file manipulation)

These should be included in the extension's requirements.

## Directory Structure

```
i18n/
├── ckanext-artesp_theme.pot  # Template file containing all translatable strings
├── pt_BR/                    # Brazilian Portuguese translations
│   └── LC_MESSAGES/
│       ├── ckanext-artesp_theme.po  # Editable translation file
│       └── ckanext-artesp_theme.mo  # Compiled translation file (binary)
└── README.md                 # This file
```

## Translation Workflow

### 1. Extract Messages

Extract all translatable strings from the extension's templates and Python files into a POT file:

```bash
cd /path/to/ckanext-artesp_theme
python setup.py extract_messages
```

This command will update the `ckanext/artesp_theme/i18n/ckanext-artesp_theme.pot` file with all the latest translatable strings.

### 2. Initialize or Update Catalog

#### For a new language (first time only):

```bash
python setup.py init_catalog -l pt_BR
```

This creates a new PO file for Brazilian Portuguese.

> ⚠️ **WARNING**: Using `init_catalog` on a language that already exists will **OVERWRITE ALL EXISTING TRANSLATIONS**.
> Always use `update_catalog` for existing languages.
>
> If you're using the Makefile, the `make i18n-init LANG=pt_BR` command includes a safety check that will warn you and ask for confirmation before overwriting existing translations.

#### For updating an existing language:

```bash
python setup.py update_catalog
```

This updates the existing PO files with any new or changed strings from the POT file while preserving existing translations.

### 3. Translate Messages

Edit the PO file for Brazilian Portuguese:

```bash
nano ckanext/artesp_theme/i18n/pt_BR/LC_MESSAGES/ckanext-artesp_theme.po
```

For each entry in the file:

- Translate the `msgid` (English) to `msgstr` (Portuguese)
- For plural forms, translate both `msgstr[0]` (singular) and `msgstr[1]` (plural)
- Remove any `#, fuzzy` markers after you've translated the string

Example:

```
#: ckanext/artesp_theme/templates/home/snippets/latest_datasets.html:30
#, python-brace-format
msgid "{num} Resource"
msgid_plural "{num} Resources"
msgstr[0] "{num} Recurso"
msgstr[1] "{num} Recursos"
```

### 4. Compile Catalog

After translating, compile the PO file into a binary MO file:

```bash
python setup.py compile_catalog
```

This creates or updates the `ckanext/artesp_theme/i18n/pt_BR/LC_MESSAGES/ckanext-artesp_theme.mo` file.

The compile command also shows statistics about the translation status:

```
530 of 530 messages (100%) translated in ckanext/artesp_theme/i18n/pt_BR/LC_MESSAGES/ckanext-artesp_theme.po
```

If you're using the Makefile, you can also check translation statistics without compiling:

```bash
make i18n-stats
```

### 5. Apply Changes

Restart the CKAN container to apply the translations:

```bash
docker-compose restart ckan
```

## Translation Tips

### Marking Strings for Translation in Templates

- For simple strings: `{{ _('String to translate') }}`
- For blocks of text: `{% trans %}String to translate{% endtrans %}`
- For pluralization: `{{ ungettext('Singular', 'Plural', count) }}`
- For strings with variables: `{{ _('Hello, {name}').format(name=user_name) }}`

### Marking Strings for Translation in Python

```python
from ckan.plugins.toolkit import _

def my_function():
    return _('String to translate')
```

### Common Translation Issues

1. **Fuzzy Entries**: Entries marked with `#, fuzzy` are suggestions that need review. After translating, remove this marker.

2. **Plural Forms**: Brazilian Portuguese uses two plural forms:
   - `msgstr[0]` for singular (n=1)
   - `msgstr[1]` for plural (n>1)

3. **Format Strings**: Keep format specifiers like `{name}` or `%s` intact in translations.

4. **HTML Tags**: Preserve HTML tags in translations, ensuring they are properly opened and closed.

5. **Missing Translations**: If a string isn't being translated, check:
   - Is it properly marked for translation in the template/code?
   - Has it been extracted to the POT file?
   - Has it been translated in the PO file?
   - Has the catalog been compiled and CKAN restarted?

## Additional Resources

- [CKAN Internationalization Documentation](https://docs.ckan.org/en/latest/contributing/i18n.html)
- [Babel Documentation](http://babel.pocoo.org/en/latest/)
- [GNU gettext Manual](https://www.gnu.org/software/gettext/manual/gettext.html)
