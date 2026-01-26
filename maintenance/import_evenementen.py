import argparse
import csv
import sys
from datetime import datetime
from typing import Optional

# Ensure we can import the Flask app and database/models
from app import app, db, Evenement


def parse_date(value: str) -> Optional[datetime]:
    if value is None:
        return None
    text = value.strip()
    if not text:
        return None
    # Try common date formats used in the app/data
    fmts = [
        "%Y-%m-%dT%H:%M:%S",  # 2024-06-01T00:00:00
        "%d/%m/%Y",  # 26/10/2025
        "%Y-%m-%d",  # 2025-10-26
        "%d-%m-%Y",  # 26-10-2025
        "%m/%d/%Y",  # 10/26/2025
    ]
    for fmt in fmts:
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    raise ValueError(f"Kan datum niet parsen: '{value}'. Ondersteunde formaten: {', '.join(fmts)}")


def import_evenementen(csv_path: str) -> None:
    created = 0
    updated = 0

    with app.app_context():
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Validate expected headers exist
            expected = {"KORTE_NAAM", "NAAM", "WANNEER", "OMSCHRIJVING"}
            missing = expected - set(reader.fieldnames or [])
            if missing:
                raise SystemExit(
                    f"Ontbrekende kolommen in CSV: {', '.join(sorted(missing))}. "
                    f"Verwacht: {', '.join(sorted(expected))}"
                )

            for row in reader:
                korte_naam = (row.get("KORTE_NAAM") or "").strip()
                naam = (row.get("NAAM") or "").strip()
                wanneer_raw = row.get("WANNEER")
                omschrijving = row.get("OMSCHRIJVING") or None

                if not korte_naam:
                    print("Sla rij over: KORTE_NAAM is leeg", file=sys.stderr)
                    continue

                # Parse date if provided (optional). If empty, keep None.
                datum_dt = None
                if wanneer_raw and wanneer_raw.strip():
                    datum_dt = parse_date(wanneer_raw)

                evenement = Evenement.query.filter_by(evenementcode=korte_naam).first()

                if evenement is None:
                    evenement = Evenement(
                        evenementcode=korte_naam,
                        naam=naam or korte_naam,
                        datum=datum_dt.date() if isinstance(datum_dt, datetime) else None,
                        locatie='niet ingevuld',
                        omschrijving=omschrijving,
                    )
                    db.session.add(evenement)
                    created += 1
                else:
                    # Overwrite existing fields as requested
                    evenement.naam = naam or evenement.naam
                    evenement.datum = datum_dt.date() if isinstance(datum_dt, datetime) else None
                    # locatie vast invullen zoals gevraagd
                    evenement.locatie = 'niet ingevuld'
                    evenement.omschrijving = omschrijving
                    updated += 1

            db.session.commit()

    print(f"Import voltooid. Aangemaakt: {created}, Bijgewerkt: {updated}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Importeer evenementen uit een CSV-bestand.")
    parser.add_argument("csv_path", help="Pad naar CSV-bestand met kolommen: KORTE_NAAM, NAAM, WANNEER, OMSCHRIJVING")
    args = parser.parse_args()
    import_evenementen(args.csv_path)


if __name__ == "__main__":
    main()


