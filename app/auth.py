"""
Gestion de l'authentification
Routes pour login et logout avec Flask-Login
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User
from app import db

# Créer un blueprint pour les routes d'authentification
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Route de connexion
    GET: Affiche le formulaire de login
    POST: Traite les credentials et connecte l'utilisateur
    """
    # Rediriger si déjà connecté
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember', False)
        
        # Validation des champs
        if not username or not password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return render_template('login.html')
        
        # Rechercher l'utilisateur
        user = User.query.filter_by(username=username).first()
        
        # Vérifier les credentials
        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f'Bienvenue, {user.username}!', 'success')
            
            # Rediriger vers la page demandée ou l'accueil
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.index'))
        else:
            flash('Nom d\'utilisateur ou mot de passe incorrect.', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """
    Route de déconnexion
    Déconnecte l'utilisateur et le redirige vers la page de login
    """
    logout_user()
    flash('Vous avez été déconnecté avec succès.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """
    Route d'inscription (optionnel)
    Permet de créer de nouveaux comptes utilisateurs
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Validation
        if not username or not password or not confirm_password:
            flash('Veuillez remplir tous les champs.', 'danger')
            return render_template('register.html')
        
        if password != confirm_password:
            flash('Les mots de passe ne correspondent pas.', 'danger')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('Le mot de passe doit contenir au moins 6 caractères.', 'danger')
            return render_template('register.html')
        
        # Vérifier si l'utilisateur existe déjà
        if User.query.filter_by(username=username).first():
            flash('Ce nom d\'utilisateur est déjà pris.', 'danger')
            return render_template('register.html')
        
        # Créer le nouvel utilisateur
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        
        flash('Compte créé avec succès! Vous pouvez maintenant vous connecter.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')
