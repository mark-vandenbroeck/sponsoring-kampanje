#!/usr/bin/env python3
"""
Script om admin gebruiker aan te maken in de database
"""

from app import create_app
from app.models import db, Gebruiker

app = create_app()

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
            rol='beheerder'
        )
        admin_user.set_password('DeKampanje!1840')
        
        db.session.add(admin_user)
        db.session.commit()
        
        print("✅ Admin gebruiker aangemaakt!")
        print("Email: admin@kampanje.be")
        print("Wachtwoord: DeKampanje!1840")
        print("Rol: beheerder")

if __name__ == '__main__':
    create_admin_user()
