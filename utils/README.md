# CKAN Utilities

## Seed Test Data Script

O script `seed_test_data.py` cria uma carga de teste idempotente com:

- organizacoes e grupos de apoio;
- varios datasets regulares;
- um dataset dedicado a testes com muitos recursos.

### Uso recomendado neste projeto

Use o wrapper em `bin/seed_test_data`, que cria um token temporario no
container `ckan-dev` e executa a seed dentro do ambiente Docker:

```bash
bin/seed_test_data
```

No ambiente local deste projeto, o wrapper usa `CKAN_SEED_OWNER_ORG=artesp`
por padrao para respeitar a governanca que limita datasets a organizacao
ARTESP.

Tambem existe um atalho no `Makefile`:

```bash
make seed
```

Exemplo com carga maior:

```bash
bin/seed_test_data \
  --dataset-count 15 \
  --resources-per-dataset 10 \
  --heavy-dataset-resources 180
```

Exemplo sobrescrevendo a organizacao fixa ou adicionando argumentos extras:

```bash
make seed SEED_OWNER_ORG=artesp SEED_ARGS="--dataset-count 15 --resources-per-dataset 10"
```

### Parametros uteis

- `--prefix`: muda o prefixo dos slugs criados.
- `--owner-org`: fixa a organizacao dos datasets, util para ambientes com governanca restrita a `artesp`.
- `--dataset-count`: numero de datasets regulares.
- `--resources-per-dataset`: numero de recursos por dataset regular.
- `--heavy-dataset-resources`: numero de recursos no dataset pesado.
- `--skip-heavy-dataset`: pula o dataset com muitos recursos.

## Extract Resources Script

The `extract_resources.py` script extracts all resources from the CKAN instance with their metadata.

### Usage

1. Set the API key in your environment:
   ```bash
   export CKAN_RESOURCES_API_KEY='your-api-key-here'
   ```
   
   Or load from .env file:
   ```bash
   source ../../.env
   ```

2. Run the script:
   ```bash
   # Extract to JSON (default)
   python extract_resources.py
   
   # Extract to CSV
   python extract_resources.py --format csv
   
   # Extract to both JSON and CSV
   python extract_resources.py --format both
   
   # Specify custom output file name
   python extract_resources.py --output my_export --format both
   ```

### Output

The script will create files with the following information for each resource:

**Package Metadata:**
- Package ID, name, title, description
- Organization name and title
- License information
- Author and maintainer details
- Creation and modification dates
- Tags

**Resource Metadata:**
- Resource ID, name, description
- Format and MIME type
- File size
- Download URL
- Creation and modification dates
- URL type and hash
- Any custom metadata fields

### Requirements

The script requires Python 3.6+ and the `requests` library:

```bash
pip install requests
```

### Notes

- The script connects to: `https://dadosabertos.artesp.sp.gov.br`
- If no API key is provided, it will attempt to fetch public data only
- The script includes progress indicators during extraction
- Failed package fetches are skipped with error messages
