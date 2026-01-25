#!/usr/bin/env python3
"""
Fix remaining URL references that are missing .list suffix
"""
import os
import re

def fix_urls_in_file(filepath):
    """Fix URL references in a single template file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Fix patterns like url_for('evenementen', ...) to url_for('evenementen.list', ...)
    # This handles cases where there are query parameters
    patterns = [
        (r"url_for\('evenementen'([,\)])", r"url_for('evenementen.list'\1"),
        (r"url_for\('kontrakten'([,\)])", r"url_for('kontrakten.list'\1"),
        (r"url_for\('sponsors'([,\)])", r"url_for('sponsors.list'\1"),
        (r"url_for\('bestuursleden'([,\)])", r"url_for('bestuursleden.list'\1"),
        (r"url_for\('sponsoringen'([,\)])", r"url_for('sponsoringen.list'\1"),
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
    
    print("Fixing remaining URL references...")
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            if fix_urls_in_file(filepath):
                total_files_updated += 1
                print(f"✓ Fixed {filename}")
    
    print(f"\nDone! Updated {total_files_updated} files.")

if __name__ == '__main__':
    main()
