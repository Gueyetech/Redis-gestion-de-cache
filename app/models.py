"""
Modèles de base de données SQLAlchemy
Définit les structures de données pour User et Student
"""
from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

class User(UserMixin, db.Model):
    """
    Modèle User pour l'authentification
    Stocke les informations d'identification des utilisateurs
    """
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        """Hash le mot de passe avant de le stocker"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Vérifie si le mot de passe est correct"""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.username}>'


class Student(db.Model):
    """
    Modèle Student pour stocker les informations des étudiants et leurs notes
    """
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    grade = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        """Convertit l'objet Student en dictionnaire pour JSON"""
        return {
            'id': self.id,
            'name': self.name,
            'grade': self.grade,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<Student {self.name}: {self.grade}>'
