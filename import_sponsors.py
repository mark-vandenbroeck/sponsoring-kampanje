import argparse
import csv
import sys
from typing import Optional

from app import app, db, Sponsor, Bestuurslid


EXPECTED_HEADERS = {
    "BEDRIJF",
    "CONTACT",
    "STRAAT",
    "HUISNUMMER",
    "POSTCODE",
    "GEMEENTE",
    "BTW_NUMMER",
    "TELEFOON",
    "EMAIL",
    "BESTUURSLID",
    "OPMERKINGEN",
}


def normalize(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    text = value.strip()
    return text if text else None


def import_sponsors(csv_path: str) -> None:
    created = 0
    updated = 0
    bestuursleden_created = 0

    with app.app_context():
        with open(csv_path, newline='', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)

            # Validate headers
            fieldnames = set(reader.fieldnames or [])
            missing = EXPECTED_HEADERS - fieldnames
            if missing:
                raise SystemExit(
                    f"Ontbrekende kolommen in CSV: {', '.join(sorted(missing))}. "
                    f"Verwacht: {', '.join(sorted(EXPECTED_HEADERS))}"
                )

            for row in reader:
                naam = normalize(row.get("BEDRIJF"))
                if not naam:
                    print("Sla rij over: BEDRIJF (naam) is leeg", file=sys.stderr)
                    continue

                kontaktpersoon = normalize(row.get("CONTACT"))
                straat = normalize(row.get("STRAAT"))
                huisnummer = normalize(row.get("HUISNUMMER"))
                postcode = normalize(row.get("POSTCODE"))
                gemeente = normalize(row.get("GEMEENTE"))
                btw_nummer = normalize(row.get("BTW_NUMMER"))
                telefoon = normalize(row.get("TELEFOON"))
                email = normalize(row.get("EMAIL"))
                bestuurslid_initialen = normalize(row.get("BESTUURSLID"))
                opmerkingen = row.get("OPMERKINGEN") or None

                # Resolve/create bestuurslid by initialen if provided
                bestuurslid_id = None
                if bestuurslid_initialen:
                    bl = Bestuurslid.query.filter_by(initialen=bestuurslid_initialen).first()
                    if bl is None:
                        bl = Bestuurslid(initialen=bestuurslid_initialen, naam=None)
                        db.session.add(bl)
                        db.session.flush()  # get id
                        bestuursleden_created += 1
                    bestuurslid_id = bl.id

                sponsor = Sponsor.query.filter_by(naam=naam).first()
                if sponsor is None:
                    sponsor = Sponsor(
                        naam=naam,
                        straat=straat,
                        huisnummer=huisnummer,
                        postcode=postcode,
                        gemeente=gemeente,
                        kontaktpersoon=kontaktpersoon,
                        telefoon=telefoon,
                        email=email,
                        btw_nummer=btw_nummer,
                        bestuurslid_id=bestuurslid_id,
                        opmerkingen=opmerkingen,
                    )
                    db.session.add(sponsor)
                    created += 1
                else:
                    sponsor.straat = straat
                    sponsor.huisnummer = huisnummer
                    sponsor.postcode = postcode
                    sponsor.gemeente = gemeente
                    sponsor.kontaktpersoon = kontaktpersoon
                    sponsor.telefoon = telefoon
                    sponsor.email = email
                    sponsor.btw_nummer = btw_nummer
                    sponsor.bestuurslid_id = bestuurslid_id
                    sponsor.opmerkingen = opmerkingen
                    updated += 1

            db.session.commit()

    print(
        f"Import voltooid. Aangemaakt: {created}, Bijgewerkt: {updated}, "
        f"Nieuwe bestuursleden: {bestuursleden_created}"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Importeer sponsors uit een CSV-bestand.")
    parser.add_argument("csv_path", help="Pad naar CSV-bestand met kolommen: "
                                       "BEDRIJF, CONTACT, STRAAT, HUISNUMMER, POSTCODE, GEMEENTE, "
                                       "BTW_NUMMER, TELEFOON, EMAIL, BESTUURSLID, OPMERKINGEN")
    args = parser.parse_args()
    import_sponsors(args.csv_path)


if __name__ == "__main__":
    main()


