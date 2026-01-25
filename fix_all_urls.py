#!/usr/bin/env python3
"""
Comprehensive fix for all remaining old-style URL references
"""
import os
import re

def fix_all_urls_in_file(filepath):
    """Fix all URL references in a single template file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Comprehensive mapping of old to new URL patterns
    replacements = {
        # Export routes
        "url_for('export_evenementen_excel')": "url_for('evenementen.export_excel')",
        "url_for('export_evenementen_pdf')": "url_for('evenementen.export_pdf')",
        "url_for('export_kontrakten_excel'": "url_for('kontrakten.export_excel'",
        "url_for('export_kontrakten_pdf'": "url_for('kontrakten.export_pdf'",
        "url_for('export_sponsors_excel'": "url_for('sponsors.export_excel'",
        "url_for('export_sponsors_pdf'": "url_for('sponsors.export_pdf'",
        "url_for('export_bestuursleden_excel')": "url_for('bestuursleden.export_excel')",
        "url_for('export_bestuursleden_pdf')": "url_for('bestuursleden.export_pdf')",
        "url_for('export_sponsoringen_excel'": "url_for('sponsoringen.export_excel'",
        "url_for('export_sponsoringen_pdf'": "url_for('sponsoringen.export_pdf'",
        
        # Detail routes
        "url_for('evenement_detail'": "url_for('evenementen.detail'",
        "url_for('kontrakt_detail'": "url_for('kontrakten.detail'",
        "url_for('sponsor_detail'": "url_for('sponsors.detail'",
        "url_for('bestuurslid_detail'": "url_for('bestuursleden.detail'",
        "url_for('sponsoring_detail'": "url_for('sponsoringen.detail'",
        
        # Edit routes
        "url_for('edit_evenement'": "url_for('evenementen.edit'",
        "url_for('edit_kontrakt'": "url_for('kontrakten.edit'",
        "url_for('edit_sponsor'": "url_for('sponsors.edit'",
        "url_for('edit_bestuurslid'": "url_for('bestuursleden.edit'",
        "url_for('edit_sponsoring'": "url_for('sponsoringen.edit'",
        
        # Delete routes
        "url_for('delete_evenement'": "url_for('evenementen.delete'",
        "url_for('delete_kontrakt'": "url_for('kontrakten.delete'",
        "url_for('delete_sponsor'": "url_for('sponsors.delete'",
        "url_for('delete_bestuurslid'": "url_for('bestuursleden.delete'",
        "url_for('delete_sponsoring'": "url_for('sponsoringen.delete'",
    }
    
    for old, new in replacements.items():
        content = content.replace(old, new)
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, content.count('\n') - original_content.count('\n')
    
    return False, 0

def main():
    templates_dir = 'templates'
    total_files_updated = 0
    total_changes = 0
    
    print("Fixing all remaining URL references...")
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            updated, changes = fix_all_urls_in_file(filepath)
            if updated:
                total_files_updated += 1
                print(f"✓ Fixed {filename}")
    
    print(f"\nDone! Updated {total_files_updated} files.")

if __name__ == '__main__':
    main()
