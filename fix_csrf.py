#!/usr/bin/env python3
"""
Fix CSRF token implementation in all templates.
Replace {{ csrf_token() }} with proper hidden input field.
"""
import os
import re

def fix_csrf_in_file(filepath):
    """Fix CSRF token in a single template file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Replace {{ csrf_token() }} with proper hidden input
    # Match both with and without surrounding whitespace
    patterns = [
        (r'\{\{\s*csrf_token\(\)\s*\}\}', '<input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    return False

def main():
    templates_dir = 'templates'
    total_files_updated = 0
    
    print("Fixing CSRF tokens in template files...")
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            if fix_csrf_in_file(filepath):
                total_files_updated += 1
                print(f"✓ Fixed {filename}")
    
    print(f"\nDone! Updated {total_files_updated} files.")

if __name__ == '__main__':
    main()
