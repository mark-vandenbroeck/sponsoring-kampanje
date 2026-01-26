import csv
import sys
import os
from flask import Flask
from app import app, db, Sponsoring, Evenement, Sponsor, Kontrakt, Bestuurslid

def import_sponsoringen(csv_path):
    created_count = 0
    updated_count = 0
    errors = []
    
    with app.app_context():
        with open(csv_path, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row_num, row in enumerate(reader, start=2):  # Start at 2 for header
                try:
                    # Get evenementcode and find evenement
                    evenementcode = row.get('evenementcode')
                    if not evenementcode:
                        errors.append(f"Rij {row_num}: Geen evenementcode gevonden")
                        continue
                    
                    evenement = Evenement.query.filter_by(evenementcode=evenementcode).first()
                    if not evenement:
                        errors.append(f"Rij {row_num}: Evenement met code '{evenementcode}' niet gevonden")
                        continue
                    
                    # Get sponsor naam and find sponsor
                    sponsor_naam = row.get('BEDRIJF')
                    if not sponsor_naam:
                        errors.append(f"Rij {row_num}: Geen bedrijfsnaam gevonden")
                        continue
                    
                    sponsor = Sponsor.query.filter_by(naam=sponsor_naam).first()
                    if not sponsor:
                        errors.append(f"Rij {row_num}: Sponsor '{sponsor_naam}' niet gevonden")
                        continue
                    
                    # Get kontrakt naam and find kontrakt for this event
                    kontrakt_naam = row.get('NAAM')
                    if not kontrakt_naam:
                        errors.append(f"Rij {row_num}: Geen kontrakt naam gevonden")
                        continue
                    
                    kontrakt = Kontrakt.query.filter_by(
                        evenement_id=evenement.id,
                        kontrakt=kontrakt_naam
                    ).first()
                    if not kontrakt:
                        errors.append(f"Rij {row_num}: Kontrakt '{kontrakt_naam}' niet gevonden voor evenement '{evenementcode}'")
                        continue
                    
                    # Get bestuurslid initialen and find or create bestuurslid
                    bestuurslid_initialen = row.get('AANGEBRACHT_DOOR')
                    bestuurslid = None
                    if bestuurslid_initialen:
                        bestuurslid = Bestuurslid.query.filter_by(initialen=bestuurslid_initialen).first()
                        if not bestuurslid:
                            # Create new bestuurslid with initialen as naam
                            bestuurslid = Bestuurslid(
                                initialen=bestuurslid_initialen,
                                naam=bestuurslid_initialen
                            )
                            db.session.add(bestuurslid)
                            db.session.flush()  # Assign ID before commit
                            print(f"Created new Bestuurslid: {bestuurslid_initialen}")
                    
                    # Parse numeric fields
                    def parse_float(value, field_name):
                        try:
                            return float(value) if value else 0.0
                        except ValueError:
                            print(f"Warning: Invalid {field_name} '{value}' in rij {row_num}, using 0.0")
                            return 0.0
                    
                    bedrag_kaarten = parse_float(row.get('BEDRAG_KAARTEN', '0'), 'bedrag_kaarten')
                    netto_bedrag_excl_btw = parse_float(row.get('NETTO_BEDRAG_EXCL_BTW', '0'), 'netto_bedrag_excl_btw')
                    facturatiebedrag_incl_btw = parse_float(row.get('FACTURATIE_BEDRAG_INCL_BTW', '0'), 'facturatiebedrag_incl_btw')
                    
                    # Parse boolean fields
                    def parse_bool(value, field_name):
                        if not value:
                            return False
                        return value.lower() in ['ja', 'yes', 'true', '1', 'j', 'y']
                    
                    gefactureerd = parse_bool(row.get('GEFACTUREERD', ''), 'gefactureerd')
                    betaald = parse_bool(row.get('BETAALD', ''), 'betaald')
                    
                    # Get opmerkingen
                    opmerkingen = row.get('OPMERKINGEN', '')
                    
                    # Check if sponsoring already exists (combination of evenement, sponsor, kontrakt)
                    existing_sponsoring = Sponsoring.query.filter_by(
                        evenement_id=evenement.id,
                        sponsor_id=sponsor.id,
                        kontrakt_id=kontrakt.id
                    ).first()
                    
                    if existing_sponsoring:
                        # Update existing sponsoring
                        existing_sponsoring.aangebracht_door_id = bestuurslid.id if bestuurslid else None
                        existing_sponsoring.bedrag_kaarten = bedrag_kaarten
                        existing_sponsoring.netto_bedrag_excl_btw = netto_bedrag_excl_btw
                        existing_sponsoring.facturatiebedrag_incl_btw = facturatiebedrag_incl_btw
                        existing_sponsoring.gefactureerd = gefactureerd
                        existing_sponsoring.betaald = betaald
                        existing_sponsoring.opmerkingen = opmerkingen
                        db.session.add(existing_sponsoring)
                        updated_count += 1
                        print(f"Updated sponsoring: {sponsor_naam} - {kontrakt_naam} ({evenementcode})")
                    else:
                        # Create new sponsoring
                        sponsoring = Sponsoring(
                            evenement_id=evenement.id,
                            sponsor_id=sponsor.id,
                            kontrakt_id=kontrakt.id,
                            aangebracht_door_id=bestuurslid.id if bestuurslid else None,
                            bedrag_kaarten=bedrag_kaarten,
                            netto_bedrag_excl_btw=netto_bedrag_excl_btw,
                            facturatiebedrag_incl_btw=facturatiebedrag_incl_btw,
                            gefactureerd=gefactureerd,
                            betaald=betaald,
                            opmerkingen=opmerkingen
                        )
                        db.session.add(sponsoring)
                        created_count += 1
                        print(f"Created sponsoring: {sponsor_naam} - {kontrakt_naam} ({evenementcode})")
                
                except Exception as e:
                    errors.append(f"Rij {row_num}: Onverwachte fout - {str(e)}")
                    continue
        
        db.session.commit()
    
    print(f"\n--- Import Resultaten ---")
    print(f"Sponsoringen aangemaakt: {created_count}")
    print(f"Sponsoringen bijgewerkt: {updated_count}")
    print(f"Totaal verwerkt: {created_count + updated_count}")
    
    if errors:
        print(f"\n--- Fouten ({len(errors)}) ---")
        for error in errors:
            print(error)
    else:
        print("\nGeen fouten gevonden!")

def main():
    if len(sys.argv) < 2:
        print("Gebruik: python import_sponsoringen.py <pad_naar_csv_bestand>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    if not os.path.exists(csv_path):
        print(f"Fout: CSV-bestand niet gevonden op '{csv_path}'")
        sys.exit(1)
    
    import_sponsoringen(csv_path)

if __name__ == '__main__':
    main()
