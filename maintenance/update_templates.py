#!/usr/bin/env python3
"""
Script to update all url_for() calls in templates to use blueprint prefixes
"""
import os
import re

# Mapping of old endpoint names to new blueprint.endpoint names
URL_MAPPINGS = {
    # Auth routes
    "url_for('login')": "url_for('auth.login')",
    "url_for('logout')": "url_for('auth.logout')",
    "url_for('dashboard')": "url_for('auth.dashboard')",
    "url_for('change_password')": "url_for('auth.change_password')",
    "url_for('set_password')": "url_for('auth.set_password')",
    
    # Main routes
    "url_for('index')": "url_for('main.index')",
    "url_for('uploaded_file'": "url_for('main.uploaded_file'",
    
    # User management routes
    "url_for('gebruikers')": "url_for('gebruikers.list')",
    "url_for('gebruiker_toevoegen')": "url_for('gebruikers.add')",
    "url_for('gebruiker_bewerken'": "url_for('gebruikers.edit'",
    "url_for('gebruiker_verwijderen'": "url_for('gebruikers.delete'",
    "url_for('gebruiker_wachtwoord_reset'": "url_for('gebruikers.reset_password'",
    
    # Evenementen routes
    "url_for('evenementen')": "url_for('evenementen.list')",
    "url_for('add_evenement')": "url_for('evenementen.add')",
    "url_for('evenement_detail'": "url_for('evenementen.detail'",
    "url_for('edit_evenement'": "url_for('evenementen.edit'",
    "url_for('delete_evenement'": "url_for('evenementen.delete'",
    "url_for('export_evenementen_excel')": "url_for('evenementen.export_excel')",
    "url_for('export_evenementen_pdf')": "url_for('evenementen.export_pdf')",
    "url_for('statistieken')": "url_for('evenementen.statistieken')",
    
    # Kontrakten routes
    "url_for('kontrakten')": "url_for('kontrakten.list')",
    "url_for('add_kontrakt')": "url_for('kontrakten.add')",
    "url_for('kontrakt_detail'": "url_for('kontrakten.detail'",
    "url_for('edit_kontrakt'": "url_for('kontrakten.edit'",
    "url_for('delete_kontrakt'": "url_for('kontrakten.delete'",
    "url_for('export_kontrakten_excel')": "url_for('kontrakten.export_excel')",
    "url_for('export_kontrakten_pdf')": "url_for('kontrakten.export_pdf')",
    
    # Sponsors routes
    "url_for('sponsors')": "url_for('sponsors.list')",
    "url_for('add_sponsor')": "url_for('sponsors.add')",
    "url_for('sponsor_detail'": "url_for('sponsors.detail'",
    "url_for('edit_sponsor'": "url_for('sponsors.edit'",
    "url_for('delete_sponsor'": "url_for('sponsors.delete'",
    "url_for('export_sponsors_excel')": "url_for('sponsors.export_excel')",
    "url_for('export_sponsors_pdf')": "url_for('sponsors.export_pdf')",
    
    # Bestuursleden routes
    "url_for('bestuursleden')": "url_for('bestuursleden.list')",
    "url_for('add_bestuurslid')": "url_for('bestuursleden.add')",
    "url_for('bestuurslid_detail'": "url_for('bestuursleden.detail'",
    "url_for('edit_bestuurslid'": "url_for('bestuursleden.edit'",
    "url_for('delete_bestuurslid'": "url_for('bestuursleden.delete'",
    "url_for('export_bestuursleden_excel')": "url_for('bestuursleden.export_excel')",
    "url_for('export_bestuursleden_pdf')": "url_for('bestuursleden.export_pdf')",
    
    # Sponsoringen routes
    "url_for('sponsoringen')": "url_for('sponsoringen.list')",
    "url_for('add_sponsoring')": "url_for('sponsoringen.add')",
    "url_for('sponsoring_detail'": "url_for('sponsoringen.detail'",
    "url_for('edit_sponsoring'": "url_for('sponsoringen.edit'",
    "url_for('delete_sponsoring'": "url_for('sponsoringen.delete'",
    "url_for('export_sponsoringen_excel')": "url_for('sponsoringen.export_excel')",
    "url_for('export_sponsoringen_pdf')": "url_for('sponsoringen.export_pdf')",
    "url_for('download_logos')": "url_for('sponsoringen.download_logos')",
}

def update_template_file(filepath):
    """Update a single template file with new URL mappings"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    changes_made = 0
    
    # Apply all mappings
    for old_url, new_url in URL_MAPPINGS.items():
        if old_url in content:
            content = content.replace(old_url, new_url)
            changes_made += content.count(new_url) - original_content.count(new_url)
    
    # Write back if changes were made
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, changes_made
    
    return False, 0

def main():
    templates_dir = 'templates'
    total_files_updated = 0
    total_changes = 0
    
    print("Updating template files...")
    
    for filename in os.listdir(templates_dir):
        if filename.endswith('.html'):
            filepath = os.path.join(templates_dir, filename)
            updated, changes = update_template_file(filepath)
            if updated:
                total_files_updated += 1
                total_changes += changes
                print(f"✓ Updated {filename} ({changes} changes)")
    
    print(f"\nDone! Updated {total_files_updated} files with {total_changes} total changes.")

if __name__ == '__main__':
    main()
