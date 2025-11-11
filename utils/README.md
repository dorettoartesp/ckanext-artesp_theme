# CKAN Utilities

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
