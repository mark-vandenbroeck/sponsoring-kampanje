#!/usr/bin/env python3
"""
Script to migrate data from the local SQLite database to the Supabase PostgreSQL database.
"""

import os
from sqlalchemy import create_engine, MetaData, select, text
from dotenv import load_dotenv

# Load env variables from .env if present
load_dotenv()

# Source database (SQLite)
basedir = os.path.abspath(os.path.dirname(__file__))
sqlite_uri = f'sqlite:///{os.path.join(basedir, "data", "sponsoring.db")}'
sqlite_engine = create_engine(sqlite_uri)

# Target database (Postgres)
postgres_uri = os.environ.get('DATABASE_URL')
if not postgres_uri:
    print("Geen DATABASE_URL gevonden in de omgevingsvariabelen of .env.")
    postgres_uri = input("Voer je Supabase PostgreSQL Connection String (URI) in: ").strip()

if not postgres_uri:
    print("❌ FOUT: Geen PostgreSQL URI opgegeven. Migratie afgebroken.")
    exit(1)

# Format postgres protocol for SQLAlchemy compatibility
if postgres_uri.startswith('postgres://'):
    postgres_uri = postgres_uri.replace('postgres://', 'postgresql://', 1)

# Security-masked URI for display
masked_pg_uri = postgres_uri
if '@' in postgres_uri:
    parts = postgres_uri.split('@')
    creds = parts[0].split(':')
    if len(creds) > 2:
        masked_pg_uri = f"{creds[0]}:{creds[1]}:****@{parts[1]}"

print("\n🔗 Database verbindingen instellen...")
print(f"Source (SQLite)   : {sqlite_uri}")
print(f"Target (Postgres) : {masked_pg_uri}\n")

try:
    pg_engine = create_engine(postgres_uri)
    
    # Reflect tables
    metadata_src = MetaData()
    metadata_src.reflect(bind=sqlite_engine)
    
    metadata_dst = MetaData()
    metadata_dst.reflect(bind=pg_engine)
    
except Exception as e:
    print(f"❌ FOUT bij verbinden met de databases: {e}")
    exit(1)

# Tables in order of foreign key dependency (parents first)
tables_to_migrate = [
    'gebruiker',
    'evenement',
    'bestuurslid',
    'kontrakt',
    'sponsor',
    'sponsoring',
    'audit_logs'
]

try:
    print("🧹 Target-database leegmaken (in omgekeerde volgorde om FK-fouten te voorkomen)...")
    for table_name in reversed(tables_to_migrate):
        if table_name in metadata_dst.tables:
            table_dst = metadata_dst.tables[table_name]
            with pg_engine.connect() as conn_dst:
                conn_dst.execute(table_dst.delete())
                conn_dst.commit()
    print("✅ Target-database succesvol leeggemaakt.\n")

    print("🚀 Start migratie van data...")
    
    for table_name in tables_to_migrate:
        if table_name not in metadata_src.tables:
            print(f"⚠️  Tabel '{table_name}' bestaat niet in SQLite. Overslaan.")
            continue
            
        if table_name not in metadata_dst.tables:
            print(f"❌ Tabel '{table_name}' bestaat nog niet in Postgres.")
            print("Zorg ervoor dat de app ten minste één keer is opgestart op Render zodat de tabellen zijn aangemaakt.")
            exit(1)
            
        table_src = metadata_src.tables[table_name]
        table_dst = metadata_dst.tables[table_name]
        
        # Read all rows from SQLite
        with sqlite_engine.connect() as conn_src:
            results = conn_src.execute(select(table_src)).fetchall()
            
        if not results:
            print(f"ℹ️  Tabel '{table_name}' is leeg in SQLite. Overslaan.")
            continue
            
        print(f"📦 '{table_name}': {len(results)} records kopiëren...")
        
        # Map rows to dictionaries
        columns = table_src.columns.keys()
        insert_data = []
        for row in results:
            insert_data.append(dict(zip(columns, row)))
            
        # Execute insert on target database
        with pg_engine.connect() as conn_dst:
            # Table is already cleared, just insert the data
            conn_dst.execute(table_dst.insert(), insert_data)
            conn_dst.commit()
            
        # Reset Primary Key Sequences in Postgres (since we inserted explicit IDs)
        # Sequence name is usually table_name_id_seq (or audit_logs_id_seq)
        seq_name = f"{table_name}_id_seq" if table_name != 'audit_logs' else "audit_logs_id_seq"
        
        with pg_engine.connect() as conn_dst:
            try:
                # Reset sequence to the max id in the table
                conn_dst.execute(text(f"SELECT setval('{seq_name}', (SELECT MAX(id) FROM {table_name}))"))
                conn_dst.commit()
            except Exception as seq_err:
                # Some tables might not have a sequence
                pass
                
        print(f"✅ Tabel '{table_name}' succesvol gemigreerd.")
        
    print("\n🎉 Migratie succesvol afgerond!")
    
except Exception as e:
    print(f"\n❌ FOUT tijdens de migratie: {e}")
