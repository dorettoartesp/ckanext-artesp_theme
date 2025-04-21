#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import subprocess
import sys

def compile_catalog():
    """Compile the PO files to MO files."""
    print("Compiling translation catalogs...")
    
    # Path to the i18n directory
    i18n_dir = os.path.join('ckanext', 'artesp_theme', 'i18n')
    
    # Get all language directories
    lang_dirs = [d for d in os.listdir(i18n_dir) 
                if os.path.isdir(os.path.join(i18n_dir, d)) and d != 'pot']
    
    for lang in lang_dirs:
        po_file = os.path.join(i18n_dir, lang, 'LC_MESSAGES', 'ckanext-artesp_theme.po')
        mo_dir = os.path.join(i18n_dir, lang, 'LC_MESSAGES')
        mo_file = os.path.join(mo_dir, 'ckanext-artesp_theme.mo')
        
        if not os.path.exists(po_file):
            print(f"Warning: PO file not found for language {lang}")
            continue
        
        # Create the directory if it doesn't exist
        if not os.path.exists(mo_dir):
            os.makedirs(mo_dir)
        
        # Use msgfmt to compile the PO file to MO file
        try:
            # Try using Python's gettext module
            from babel.messages.mofile import write_mo
            from babel.messages.pofile import read_po
            
            with open(po_file, 'rb') as f:
                catalog = read_po(f)
            
            with open(mo_file, 'wb') as f:
                write_mo(f, catalog)
            
            print(f"Compiled {lang} translation")
        except ImportError:
            # Fall back to using msgfmt command
            try:
                subprocess.check_call(['msgfmt', '-o', mo_file, po_file])
                print(f"Compiled {lang} translation using msgfmt")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"Error: Failed to compile {lang} translation")
                print("Make sure you have msgfmt installed or babel available")
                continue

if __name__ == '__main__':
    compile_catalog()
    print("Done!")
