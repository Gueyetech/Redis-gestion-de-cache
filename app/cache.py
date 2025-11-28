"""
Gestionnaire de cache Redis
Fournit des fonctions pour mettre en cache, récupérer et invalider les données
"""
import json
import time
from app import redis_client
import os

# TTL du cache en secondes (récupéré depuis les variables d'environnement)
CACHE_TTL = int(os.getenv('CACHE_TTL', 300))

class CacheManager:
    """Classe pour gérer les opérations de cache Redis"""
    
    @staticmethod
    def get_cache_key(prefix, identifier='all'):
        """
        Génère une clé de cache standardisée
        Ex: students:all, students:filter:alice
        """
        return f"{prefix}:{identifier}"
    
    @staticmethod
    def get_students_from_cache(filter_name=None):
        """
        Récupère les étudiants depuis le cache Redis
        
        Args:
            filter_name: Nom à filtrer (optionnel)
            
        Returns:
            tuple: (données, temps_accès_ms, is_from_cache)
        """
        start_time = time.time()
        
        # Générer la clé de cache
        if filter_name:
            cache_key = CacheManager.get_cache_key('students', f'filter:{filter_name.lower()}')
        else:
            cache_key = CacheManager.get_cache_key('students', 'all')
        
        try:
            # Tenter de récupérer depuis le cache
            cached_data = redis_client.get(cache_key)
            
            if cached_data:
                # Données trouvées dans le cache
                end_time = time.time()
                access_time = (end_time - start_time) * 1000  # Convertir en ms
                
                students = json.loads(cached_data)
                return students, access_time, True
            
            # Pas de données en cache
            return None, 0, False
            
        except Exception as e:
            print(f"Erreur lors de la récupération du cache: {e}")
            return None, 0, False
    
    @staticmethod
    def set_students_to_cache(students, filter_name=None):
        """
        Stocke les étudiants dans le cache Redis avec TTL
        
        Args:
            students: Liste des étudiants (format dict)
            filter_name: Nom du filtre (optionnel)
        """
        # Générer la clé de cache
        if filter_name:
            cache_key = CacheManager.get_cache_key('students', f'filter:{filter_name.lower()}')
        else:
            cache_key = CacheManager.get_cache_key('students', 'all')
        
        try:
            # Sérialiser les données en JSON
            data_json = json.dumps(students)
            
            # Stocker avec TTL
            redis_client.setex(cache_key, CACHE_TTL, data_json)
            
            return True
            
        except Exception as e:
            print(f"Erreur lors de la mise en cache: {e}")
            return False
    
    @staticmethod
    def invalidate_students_cache():
        """
        Invalide tout le cache des étudiants
        Utilisé après des opérations de création, mise à jour ou suppression
        """
        try:
            # Chercher toutes les clés commençant par 'students:'
            pattern = CacheManager.get_cache_key('students', '*')
            keys = redis_client.keys(pattern)
            
            if keys:
                # Supprimer toutes les clés trouvées
                redis_client.delete(*keys)
                print(f"✓ Cache invalidé: {len(keys)} clés supprimées")
                return len(keys)
            
            return 0
            
        except Exception as e:
            print(f"Erreur lors de l'invalidation du cache: {e}")
            return 0
    
    @staticmethod
    def get_cache_stats():
        """
        Récupère des statistiques sur le cache Redis
        
        Returns:
            dict: Statistiques du cache
        """
        try:
            info = redis_client.info('stats')
            
            return {
                'total_connections': info.get('total_connections_received', 0),
                'total_commands': info.get('total_commands_processed', 0),
                'keyspace_hits': info.get('keyspace_hits', 0),
                'keyspace_misses': info.get('keyspace_misses', 0),
                'used_memory_human': redis_client.info('memory').get('used_memory_human', 'N/A')
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des stats: {e}")
            return {}
    
    @staticmethod
    def store_performance_metric(source, access_time):
        """
        Stocke une métrique de performance dans Redis
        Utilisé pour comparer cache vs base de données
        
        Args:
            source: 'cache' ou 'database'
            access_time: Temps d'accès en millisecondes
        """
        try:
            metric_key = f'metrics:{source}'
            
            # Ajouter la métrique à une liste (limitée aux 100 dernières valeurs)
            redis_client.lpush(metric_key, access_time)
            redis_client.ltrim(metric_key, 0, 99)  # Garder seulement 100 valeurs
            
        except Exception as e:
            print(f"Erreur lors du stockage de la métrique: {e}")
    
    @staticmethod
    def get_performance_metrics():
        """
        Récupère les métriques de performance pour générer les graphiques
        
        Returns:
            dict: Métriques de cache et base de données
        """
        try:
            # Récupérer les métriques
            cache_metrics = redis_client.lrange('metrics:cache', 0, -1)
            db_metrics = redis_client.lrange('metrics:database', 0, -1)
            
            # Convertir en float
            cache_times = [float(m) for m in cache_metrics] if cache_metrics else []
            db_times = [float(m) for m in db_metrics] if db_metrics else []
            
            # Calculer les moyennes
            avg_cache = sum(cache_times) / len(cache_times) if cache_times else 0
            avg_db = sum(db_times) / len(db_times) if db_times else 0
            
            return {
                'cache': {
                    'times': cache_times[:20],  # 20 dernières valeurs pour le graphique
                    'average': round(avg_cache, 2),
                    'count': len(cache_times)
                },
                'database': {
                    'times': db_times[:20],
                    'average': round(avg_db, 2),
                    'count': len(db_times)
                }
            }
            
        except Exception as e:
            print(f"Erreur lors de la récupération des métriques: {e}")
            return {'cache': {'times': [], 'average': 0, 'count': 0},
                    'database': {'times': [], 'average': 0, 'count': 0}}
