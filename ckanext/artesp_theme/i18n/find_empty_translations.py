#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script to find empty translations in a PO file.
This script identifies entries in a PO file where the msgstr is empty.
"""

import os
import sys
import re
import argparse
from collections import namedtuple

# Define a structure to hold translation entries
TranslationEntry = namedtuple('TranslationEntry', [
    'line_number',
    'msgid',
    'msgstr',
    'location',
    'is_empty'
])

def parse_po_file(file_path):
    """
    Parse a PO file and extract translation entries.
    
    Args:
        file_path (str): Path to the PO file
        
    Returns:
        list: List of TranslationEntry objects
    """
    entries = []
    current_entry = None
    current_line = 0
    location = None
    msgid_lines = []
    msgstr_lines = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    i = 0
    while i < len(lines):
        current_line = i + 1  # Line numbers are 1-based
        line = lines[i].strip()
        
        # Check for location comments
        if line.startswith('#:'):
            location = line[2:].strip()
        
        # Start of a new msgid
        elif line.startswith('msgid '):
            # Save previous entry if it exists
            if msgid_lines:
                msgid = ''.join(msgid_lines).strip('"')
                msgstr = ''.join(msgstr_lines).strip('"')
                is_empty = msgstr == ''
                entries.append(TranslationEntry(
                    line_number=entry_line,
                    msgid=msgid,
                    msgstr=msgstr,
                    location=entry_location,
                    is_empty=is_empty
                ))
                
            # Reset for new entry
            entry_line = current_line
            entry_location = location
            msgid_lines = [line[6:].strip()]
            msgstr_lines = []
            location = None
        
        # Continuation of msgid
        elif line.startswith('"') and msgid_lines and not msgstr_lines:
            msgid_lines.append(line)
        
        # Start of msgstr
        elif line.startswith('msgstr '):
            msgstr_lines = [line[7:].strip()]
        
        # Continuation of msgstr
        elif line.startswith('"') and msgstr_lines:
            msgstr_lines.append(line)
        
        i += 1
    
    # Add the last entry if there is one
    if msgid_lines:
        msgid = ''.join(msgid_lines).strip('"')
        msgstr = ''.join(msgstr_lines).strip('"')
        is_empty = msgstr == ''
        entries.append(TranslationEntry(
            line_number=entry_line,
            msgid=msgid,
            msgstr=msgstr,
            location=entry_location,
            is_empty=is_empty
        ))
    
    return entries

def find_empty_translations(entries):
    """
    Find entries with empty translations.
    
    Args:
        entries (list): List of TranslationEntry objects
        
    Returns:
        list: List of TranslationEntry objects with empty translations
    """
    return [entry for entry in entries if entry.is_empty and entry.msgid]

def print_empty_translations(empty_entries):
    """
    Print empty translations in a readable format.
    
    Args:
        empty_entries (list): List of TranslationEntry objects with empty translations
    """
    if not empty_entries:
        print("No empty translations found!")
        return
    
    print(f"Found {len(empty_entries)} empty translations:\n")
    
    for i, entry in enumerate(empty_entries, 1):
        print(f"[{i}] Line {entry.line_number}:")
        if entry.location:
            print(f"    Location: {entry.location}")
        print(f"    msgid: \"{entry.msgid}\"")
        print(f"    msgstr: \"\"")
        print()

def main():
    parser = argparse.ArgumentParser(description='Find empty translations in a PO file')
    parser.add_argument('po_file', nargs='?', 
                        default='pt_BR/LC_MESSAGES/ckanext-artesp_theme.po',
                        help='Path to the PO file (default: pt_BR/LC_MESSAGES/ckanext-artesp_theme.po)')
    args = parser.parse_args()
    
    # Resolve the file path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    if os.path.isabs(args.po_file):
        po_file_path = args.po_file
    else:
        po_file_path = os.path.join(script_dir, args.po_file)
    
    if not os.path.exists(po_file_path):
        print(f"Error: File not found: {po_file_path}")
        return 1
    
    print(f"Analyzing file: {po_file_path}\n")
    
    # Parse the PO file
    entries = parse_po_file(po_file_path)
    
    # Find and print empty translations
    empty_entries = find_empty_translations(entries)
    print_empty_translations(empty_entries)
    
    # Print summary
    total_entries = len([e for e in entries if e.msgid])
    empty_count = len(empty_entries)
    if total_entries > 0:
        completion_percentage = ((total_entries - empty_count) / total_entries) * 100
        print(f"Translation completion: {completion_percentage:.2f}% ({total_entries - empty_count}/{total_entries})")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
