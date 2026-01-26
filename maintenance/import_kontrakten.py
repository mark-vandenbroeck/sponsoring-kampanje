import csv
import sys
import os
from flask import Flask
from app import app, db, Kontrakt, Evenement

def import_kontrakten(csv_path):
    created_count = 0
    updated_count = 0
    
    with app.app_context():
        # Find the event with code 'EZ24'
        evenement = Evenement.query.filter_by(evenementcode='EZ24').first()
        if not evenement:
            print(f"Fout: Evenement met code 'EZ24' niet gevonden!")
            return
        
        print(f"Gevonden evenement: {evenement.naam} (code: {evenement.evenementcode})")
        
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                kontrakt_naam = row.get('NAAM')
                if not kontrakt_naam:
                    print(f"Skipping row due to missing 'NAAM' (kontrakt): {row}")
                    continue
                
                # Parse bedrag
                bedrag_str = row.get('BEDRAG_N', '0')
                try:
                    bedrag = float(bedrag_str) if bedrag_str else 0.0
                except ValueError:
                    print(f"Warning: Invalid bedrag '{bedrag_str}' for kontrakt '{kontrakt_naam}', using 0.0")
                    bedrag = 0.0
                
                tegenprestatie = row.get('TEGENPRESTATIE', '')
                
                # Check if kontrakt already exists for this event
                existing_kontrakt = Kontrakt.query.filter_by(
                    evenement_id=evenement.id,
                    kontrakt=kontrakt_naam
                ).first()
                
                if existing_kontrakt:
                    # Update existing kontrakt
                    existing_kontrakt.bedrag = bedrag
                    existing_kontrakt.tegenprestatie = tegenprestatie
                    db.session.add(existing_kontrakt)
                    updated_count += 1
                    print(f"Updated kontrakt: {kontrakt_naam}")
                else:
                    # Create new kontrakt
                    kontrakt = Kontrakt(
                        evenement_id=evenement.id,
                        kontrakt=kontrakt_naam,
                        bedrag=bedrag,
                        tegenprestatie=tegenprestatie
                    )
                    db.session.add(kontrakt)
                    created_count += 1
                    print(f"Created kontrakt: {kontrakt_naam}")
        
        db.session.commit()
    
    print(f"\n--- Import Resultaten ---")
    print(f"Kontrakten aangemaakt: {created_count}")
    print(f"Kontrakten bijgewerkt: {updated_count}")
    print(f"Totaal verwerkt: {created_count + updated_count}")

def main():
    if len(sys.argv) < 2:
        print("Gebruik: python import_kontrakten.py <pad_naar_csv_bestand>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"Fout: CSV-bestand niet gevonden op '{csv_path}'")
        sys.exit(1)
    
    import_kontrakten(csv_path)

if __name__ == '__main__':
    main()
