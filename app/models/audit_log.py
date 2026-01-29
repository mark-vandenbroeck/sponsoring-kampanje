from . import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('gebruiker.id'), nullable=True)
    user_name = db.Column(db.String(100), nullable=True)  # Snapshot of name
    
    target_type = db.Column(db.String(50), nullable=False)
    target_id = db.Column(db.Integer, nullable=True)
    
    action = db.Column(db.String(20), nullable=False)  # CREATE, UPDATE, DELETE
    changes = db.Column(db.JSON, nullable=True)  # Stores diff: {'field': [old, new]}
    
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to user (optional, for convenience)
    user = db.relationship('Gebruiker', backref='audit_logs', lazy=True)

    def get_changes(self):
        """Returns changes as a dictionary, handling JSON deserialization safely"""
        import json
        if not self.changes:
            return {}
        
        if isinstance(self.changes, dict):
            return self.changes
            
        try:
            return json.loads(self.changes)
        except:
            return {}

    def __repr__(self):
        return f'<AuditLog {self.action} {self.target_type} {self.target_id}>'
