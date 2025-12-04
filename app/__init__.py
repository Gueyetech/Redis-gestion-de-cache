"""
Initialisation de l'application Flask
Configure tous les composants : base de données, Redis, Flask-Login, sessions
"""
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import redis
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Initialiser les extensions
db = SQLAlchemy()
login_manager = LoginManager()
redis_client = None

def create_app():
    """Factory pattern pour créer l'application Flask"""
    app = Flask(__name__)
    
    # Configuration de l'application
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://student_user:student_pass@localhost:5432/student_grades_db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Configuration des sessions (côté client avec cookie sécurisé)
    app.config['SESSION_COOKIE_SECURE'] = False  # Mettre True en production avec HTTPS
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 heure
    
    # Initialiser Redis pour le cache
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    global redis_client
    redis_client = redis.from_url(redis_url, decode_responses=True)
    
    # Initialiser les extensions avec l'application
    db.init_app(app)
    login_manager.init_app(app)
    
    # Configuration de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Veuillez vous connecter pour accéder à cette page.'
    
    # Importer et enregistrer les blueprints
    from app.auth import auth_bp
    from app.routes import main_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    
    return app

@login_manager.user_loader
def load_user(user_id):
    """Callback pour charger un utilisateur depuis son ID"""
    from app.models import User
    return User.query.get(int(user_id))
