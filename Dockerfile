# Image de base Python
FROM python:3.11-slim

# Définir le répertoire de travail
WORKDIR /app

# Copier les fichiers de dépendances
COPY requirements.txt .

# Installer les dépendances avec timeout étendu pour connexions lentes
# Installer les dépendances (sans vérification de hash à cause de connexion lente)
RUN pip install --no-cache-dir --timeout=1000 --disable-pip-version-check \
    Flask==3.0.0 \
    Flask-Login==0.6.3 \
    SQLAlchemy==2.0.23 \
    Flask-SQLAlchemy==3.1.1 \
    redis==5.0.1 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0 \
    werkzeug==3.0.1

# Copier le code de l'application
COPY . .

# Exposer le port Flask
EXPOSE 5000

# Variables d'environnement par défaut
ENV FLASK_APP=run.py
ENV FLASK_ENV=development

# Commande de démarrage
CMD ["python", "run.py"]
