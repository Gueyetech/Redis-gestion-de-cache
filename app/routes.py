"""
Routes principales de l'application
Gestion des étudiants (CRUD) avec cache Redis
"""
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Student
from app.cache import CacheManager
import time

# Créer un blueprint pour les routes principales
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@login_required
def index():
    """Page d'accueil - Liste des étudiants"""
    return render_template('index.html', user=current_user)


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard avec graphiques de performance"""
    return render_template('dashboard.html', user=current_user)


@main_bp.route('/api/students', methods=['GET'])
@login_required
def get_students():
    """
    API pour récupérer les étudiants avec cache Redis
    Support du filtrage par nom
    
    Query params:
        - name: Filtre par nom (optionnel)
    
    Returns:
        JSON avec les étudiants et les métriques de performance
    """
    filter_name = request.args.get('name', '').strip()
    
    # Essayer de récupérer depuis le cache
    cached_students, cache_time, from_cache = CacheManager.get_students_from_cache(filter_name if filter_name else None)
    
    if from_cache:
        # Données trouvées dans le cache
        CacheManager.store_performance_metric('cache', cache_time)
        
        return jsonify({
            'success': True,
            'students': cached_students,
            'from_cache': True,
            'access_time': round(cache_time, 2),
            'count': len(cached_students)
        })
    
    # Pas de cache - récupérer depuis la base de données
    start_time = time.time()
    
    try:
        # Query de base
        query = Student.query
        
        # Appliquer le filtre si présent
        if filter_name:
            query = query.filter(Student.name.ilike(f'%{filter_name}%'))
        
        # Exécuter la requête
        students = query.order_by(Student.name).all()
        
        # Mesurer le temps d'accès
        end_time = time.time()
        db_time = (end_time - start_time) * 1000  # Convertir en ms
        
        # Convertir en dictionnaires
        students_dict = [student.to_dict() for student in students]
        
        # Stocker les métriques de performance
        CacheManager.store_performance_metric('database', db_time)
        
        # Mettre en cache pour les prochaines requêtes
        CacheManager.set_students_to_cache(students_dict, filter_name if filter_name else None)
        
        return jsonify({
            'success': True,
            'students': students_dict,
            'from_cache': False,
            'access_time': round(db_time, 2),
            'count': len(students_dict)
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/students', methods=['POST'])
@login_required
def add_student():
    """
    API pour ajouter un nouvel étudiant
    Invalide automatiquement le cache
    
    Body JSON:
        - name: Nom de l'étudiant
        - grade: Note (0-20)
    """
    try:
        data = request.get_json()
        
        # Validation des données
        if not data or 'name' not in data or 'grade' not in data:
            return jsonify({
                'success': False,
                'error': 'Nom et note sont requis'
            }), 400
        
        name = data['name'].strip()
        grade = float(data['grade'])
        
        # Validation de la note
        if grade < 0 or grade > 20:
            return jsonify({
                'success': False,
                'error': 'La note doit être entre 0 et 20'
            }), 400
        
        if not name:
            return jsonify({
                'success': False,
                'error': 'Le nom ne peut pas être vide'
            }), 400
        
        # Créer le nouvel étudiant
        new_student = Student(name=name, grade=grade)
        db.session.add(new_student)
        db.session.commit()
        
        # Invalider le cache
        CacheManager.invalidate_students_cache()
        
        return jsonify({
            'success': True,
            'message': 'Étudiant ajouté avec succès',
            'student': new_student.to_dict()
        }), 201
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Format de note invalide'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/students/<int:student_id>', methods=['PUT'])
@login_required
def update_student(student_id):
    """
    API pour modifier un étudiant existant
    Invalide automatiquement le cache
    
    Path param:
        - student_id: ID de l'étudiant
    
    Body JSON:
        - name: Nouveau nom (optionnel)
        - grade: Nouvelle note (optionnel)
    """
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'error': 'Étudiant non trouvé'
            }), 404
        
        data = request.get_json()
        
        # Mettre à jour les champs si fournis
        if 'name' in data:
            name = data['name'].strip()
            if not name:
                return jsonify({
                    'success': False,
                    'error': 'Le nom ne peut pas être vide'
                }), 400
            student.name = name
        
        if 'grade' in data:
            grade = float(data['grade'])
            if grade < 0 or grade > 20:
                return jsonify({
                    'success': False,
                    'error': 'La note doit être entre 0 et 20'
                }), 400
            student.grade = grade
        
        db.session.commit()
        
        # Invalider le cache
        CacheManager.invalidate_students_cache()
        
        return jsonify({
            'success': True,
            'message': 'Étudiant modifié avec succès',
            'student': student.to_dict()
        })
        
    except ValueError:
        return jsonify({
            'success': False,
            'error': 'Format de note invalide'
        }), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/students/<int:student_id>', methods=['DELETE'])
@login_required
def delete_student(student_id):
    """
    API pour supprimer un étudiant
    Invalide automatiquement le cache
    
    Path param:
        - student_id: ID de l'étudiant
    """
    try:
        student = Student.query.get(student_id)
        
        if not student:
            return jsonify({
                'success': False,
                'error': 'Étudiant non trouvé'
            }), 404
        
        db.session.delete(student)
        db.session.commit()
        
        # Invalider le cache
        CacheManager.invalidate_students_cache()
        
        return jsonify({
            'success': True,
            'message': 'Étudiant supprimé avec succès'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/performance-metrics', methods=['GET'])
@login_required
def get_performance_metrics():
    """
    API pour récupérer les métriques de performance
    Utilisé pour générer les graphiques du dashboard
    """
    try:
        metrics = CacheManager.get_performance_metrics()
        cache_stats = CacheManager.get_cache_stats()
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'cache_stats': cache_stats
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@main_bp.route('/api/cache/clear', methods=['POST'])
@login_required
def clear_cache():
    """
    API pour vider manuellement le cache
    Utile pour les tests et la démonstration
    """
    try:
        deleted_keys = CacheManager.invalidate_students_cache()
        
        return jsonify({
            'success': True,
            'message': f'Cache vidé: {deleted_keys} clés supprimées'
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
