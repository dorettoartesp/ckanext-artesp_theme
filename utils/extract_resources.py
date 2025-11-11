#!/usr/bin/env python3
"""
Extract all resources from CKAN instance with metadata.

Usage:
    python extract_resources.py [--output OUTPUT_FILE] [--format FORMAT]

Environment Variables:
    CKAN_RESOURCES_API_KEY: API key for CKAN instance
"""

import os
import sys
import json
import csv
import argparse
from datetime import datetime
from typing import List, Dict, Any
import requests
from pathlib import Path


CKAN_URL = 'https://dadosabertos.artesp.sp.gov.br'


def get_api_key() -> str:
    """Get API key from environment variable."""
    api_key = os.environ.get('CKAN_RESOURCES_API_KEY')
    if not api_key:
        print("Warning: CKAN_RESOURCES_API_KEY not set in environment. "
              "Will attempt to fetch public data only.", file=sys.stderr)
    return api_key


def fetch_all_packages(api_key: str = None) -> List[str]:
    """Fetch list of all package IDs from CKAN."""
    url = f'{CKAN_URL}/api/3/action/package_list'
    headers = {}
    if api_key:
        headers['Authorization'] = api_key
    
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            raise Exception(f"API returned success=false: {data.get('error')}")
        
        return data['result']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching package list: {e}", file=sys.stderr)
        sys.exit(1)


def fetch_package_details(package_id: str, api_key: str = None) -> Dict[str, Any]:
    """Fetch detailed information about a package."""
    url = f'{CKAN_URL}/api/3/action/package_show'
    params = {'id': package_id}
    headers = {}
    if api_key:
        headers['Authorization'] = api_key
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not data.get('success'):
            raise Exception(f"API returned success=false: {data.get('error')}")
        
        return data['result']
    except requests.exceptions.RequestException as e:
        print(f"Error fetching package {package_id}: {e}", file=sys.stderr)
        return None


def extract_resources(api_key: str = None) -> List[Dict[str, Any]]:
    """Extract all resources with metadata from CKAN instance."""
    print(f"Fetching packages from {CKAN_URL}...")
    packages = fetch_all_packages(api_key)
    print(f"Found {len(packages)} packages")
    
    all_resources = []
    
    for i, package_id in enumerate(packages, 1):
        print(f"Processing package {i}/{len(packages)}: {package_id}", end='\r')
        
        package = fetch_package_details(package_id, api_key)
        if not package:
            continue
        
        for resource in package.get('resources', []):
            resource_data = {
                # Package metadata
                'package_id': package.get('id'),
                'package_name': package.get('name'),
                'package_title': package.get('title'),
                'package_notes': package.get('notes', ''),
                'package_organization': package.get('organization', {}).get('name') if package.get('organization') else '',
                'package_organization_title': package.get('organization', {}).get('title') if package.get('organization') else '',
                'package_license': package.get('license_title', ''),
                'package_author': package.get('author', ''),
                'package_author_email': package.get('author_email', ''),
                'package_maintainer': package.get('maintainer', ''),
                'package_maintainer_email': package.get('maintainer_email', ''),
                'package_metadata_created': package.get('metadata_created', ''),
                'package_metadata_modified': package.get('metadata_modified', ''),
                'package_tags': ','.join([tag.get('name', '') for tag in package.get('tags', [])]),
                
                # Resource metadata
                'resource_id': resource.get('id'),
                'resource_name': resource.get('name'),
                'resource_description': resource.get('description', ''),
                'resource_format': resource.get('format', ''),
                'resource_mimetype': resource.get('mimetype', ''),
                'resource_size': resource.get('size', ''),
                'resource_url': resource.get('url', ''),
                'resource_created': resource.get('created', ''),
                'resource_last_modified': resource.get('last_modified', ''),
                'resource_url_type': resource.get('url_type', ''),
                'resource_hash': resource.get('hash', ''),
            }
            
            # Add any extra fields (custom metadata)
            for key, value in resource.items():
                if key not in resource_data and not key.startswith('_'):
                    resource_data[f'resource_{key}'] = str(value) if value is not None else ''
            
            all_resources.append(resource_data)
    
    print(f"\nExtracted {len(all_resources)} resources from {len(packages)} packages")
    return all_resources


def save_to_json(resources: List[Dict[str, Any]], output_file: str):
    """Save resources to JSON file."""
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(resources, f, indent=2, ensure_ascii=False)
    print(f"Saved to {output_file}")


def save_to_csv(resources: List[Dict[str, Any]], output_file: str):
    """Save resources to CSV file."""
    if not resources:
        print("No resources to save")
        return
    
    # Get all unique keys from all resources
    all_keys = set()
    for resource in resources:
        all_keys.update(resource.keys())
    
    fieldnames = sorted(all_keys)
    
    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(resources)
    
    print(f"Saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description='Extract all resources from CKAN instance with metadata'
    )
    parser.add_argument(
        '--output',
        '-o',
        default=f'ckan_resources_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
        help='Output file name (without extension)'
    )
    parser.add_argument(
        '--format',
        '-f',
        choices=['json', 'csv', 'both'],
        default='json',
        help='Output format (default: json)'
    )
    
    args = parser.parse_args()
    
    # Get API key from environment
    api_key = get_api_key()
    
    # Extract resources
    resources = extract_resources(api_key)
    
    if not resources:
        print("No resources found")
        sys.exit(1)
    
    # Save to file(s)
    if args.format in ['json', 'both']:
        save_to_json(resources, f'{args.output}.json')
    
    if args.format in ['csv', 'both']:
        save_to_csv(resources, f'{args.output}.csv')


if __name__ == '__main__':
    main()
