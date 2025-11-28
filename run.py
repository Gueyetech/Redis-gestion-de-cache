"""
Point d'entrée principal de l'application Flask
Lance le serveur web et initialise la base de données
"""
from app import create_app, db
from app.models import User, Student
import os

# Créer l'instance de l'application
app = create_app()

# Contexte de l'application pour les opérations de base de données
with app.app_context():
    # Créer toutes les tables si elles n'existent pas
    db.create_all()
    
    # Créer un utilisateur par défaut si aucun n'existe
    if User.query.count() == 0:
        default_user = User(username='admin')
        default_user.set_password('admin123')
        db.session.add(default_user)
        db.session.commit()
        print("✓ Utilisateur par défaut créé: admin/admin123")
    
    # Créer quelques étudiants de test si la base est vide
    if Student.query.count() == 0:
        test_students = [
            Student(name='Alice Dupont', grade=15.5),
            Student(name='Bob Martin', grade=12.0),
            Student(name='Claire Dubois', grade=17.5),
            Student(name='David Leroux', grade=14.0),
            Student(name='Emma Petit', grade=16.5)
        ]
        db.session.add_all(test_students)
        db.session.commit()
        print("✓ Étudiants de test créés")

if __name__ == '__main__':
    # Démarrer le serveur Flask
    app.run(host='0.0.0.0', port=5000, debug=True)
