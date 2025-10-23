#!/usr/bin/env python3
"""
Script om admin gebruiker aan te maken in de database
"""

from app import app, db, Gebruiker
from werkzeug.security import generate_password_hash

def create_admin_user():
    with app.app_context():
        # Check if admin user already exists
        admin_user = Gebruiker.query.filter_by(email='admin@kampanje.be').first()
        
        if admin_user:
            print("Admin gebruiker bestaat al!")
            print(f"Email: {admin_user.email}")
            print(f"Rol: {admin_user.rol}")
            return
        
        # Create admin user
        admin_user = Gebruiker(
            email='admin@kampanje.be',
            password_hash=None,  # No password set initially
            rol='beheerder'
        )
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Admin gebruiker aangemaakt!")
        print("Email: admin@kampanje.be")
        print("Wachtwoord: Laat leeg bij eerste login")
        print("Rol: beheerder")

if __name__ == '__main__':
    create_admin_user()
