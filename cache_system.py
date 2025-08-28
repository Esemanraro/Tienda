#!/usr/bin/env python3
"""
Sistema de Cache Redis para Tiendita ALOHA
Cache inteligente para consultas frecuentes, sesiones y carrito persistente
"""

import os
import json
import pickle
from datetime import datetime, timedelta
from typing import Any, Optional, Dict, List
from functools import wraps

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    print("⚠️ Redis no está instalado. Instalando...")

class CacheManager:
    """Gestor de cache Redis con fallback a memoria"""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        self.redis_client = None
        self.memory_cache = {}  # Fallback cache
        self.cache_stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0
        }
        
        self._connect_redis()
    
    def _connect_redis(self):
        """Conectar a Redis con manejo de errores"""
        if not REDIS_AVAILABLE:
            print("📝 Usando cache en memoria como fallback")
            return
            
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=False)
            # Test connection
            self.redis_client.ping()
            print("✅ Conectado a Redis exitosamente")
        except Exception as e:
            print(f"⚠️ No se pudo conectar a Redis: {str(e)}")
            print("📝 Usando cache en memoria como fallback")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Obtener valor del cache"""
        try:
            if self.redis_client:
                value = self.redis_client.get(key)
                if value is not None:
                    self.cache_stats['hits'] += 1
                    return pickle.loads(value)
            else:
                # Fallback a memoria
                if key in self.memory_cache:
                    item = self.memory_cache[key]
                    if item['expires'] > datetime.now():
                        self.cache_stats['hits'] += 1
                        return item['value']
                    else:
                        del self.memory_cache[key]
            
            self.cache_stats['misses'] += 1
            return None
            
        except Exception as e:
            print(f"❌ Error obteniendo cache {key}: {str(e)}")
            self.cache_stats['misses'] += 1
            return None
    
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """Establecer valor en cache con TTL en segundos"""
        try:
            if self.redis_client:
                serialized = pickle.dumps(value)
                result = self.redis_client.setex(key, ttl, serialized)
                self.cache_stats['sets'] += 1
                return result
            else:
                # Fallback a memoria
                expires = datetime.now() + timedelta(seconds=ttl)
                self.memory_cache[key] = {
                    'value': value,
                    'expires': expires
                }
                self.cache_stats['sets'] += 1
                return True
                
        except Exception as e:
            print(f"❌ Error estableciendo cache {key}: {str(e)}")
            return False
    
    def delete(self, key: str) -> bool:
        """Eliminar clave del cache"""
        try:
            if self.redis_client:
                result = self.redis_client.delete(key) > 0
            else:
                result = key in self.memory_cache
                if result:
                    del self.memory_cache[key]
            
            if result:
                self.cache_stats['deletes'] += 1
            return result
            
        except Exception as e:
            print(f"❌ Error eliminando cache {key}: {str(e)}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """Eliminar claves que coincidan con un patrón"""
        try:
            if self.redis_client:
                keys = self.redis_client.keys(pattern)
                if keys:
                    deleted = self.redis_client.delete(*keys)
                    self.cache_stats['deletes'] += deleted
                    return deleted
            else:
                # Fallback a memoria
                import fnmatch
                keys_to_delete = [k for k in self.memory_cache.keys() 
                                if fnmatch.fnmatch(k, pattern)]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                self.cache_stats['deletes'] += len(keys_to_delete)
                return len(keys_to_delete)
            
            return 0
            
        except Exception as e:
            print(f"❌ Error eliminando patrón {pattern}: {str(e)}")
            return 0
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas del cache"""
        total_requests = self.cache_stats['hits'] + self.cache_stats['misses']
        hit_rate = (self.cache_stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        stats = {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'sets': self.cache_stats['sets'],
            'deletes': self.cache_stats['deletes'],
            'hit_rate': round(hit_rate, 2),
            'total_requests': total_requests,
            'backend': 'Redis' if self.redis_client else 'Memory'
        }
        
        if self.redis_client:
            try:
                info = self.redis_client.info()
                stats['redis_memory'] = info.get('used_memory_human', 'N/A')
                stats['redis_keys'] = info.get('db0', {}).get('keys', 0)
            except:
                pass
        else:
            stats['memory_keys'] = len(self.memory_cache)
        
        return stats

# Instancia global del cache
cache = CacheManager()

def cached(ttl: int = 3600, key_prefix: str = ""):
    """Decorador para cachear resultados de funciones"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # Intentar obtener del cache
            result = cache.get(cache_key)
            if result is not None:
                return result
            
            # Ejecutar función y cachear resultado
            result = func(*args, **kwargs)
            cache.set(cache_key, result, ttl)
            return result
        
        return wrapper
    return decorator

class ToyCache:
    """Cache específico para juguetes"""
    
    @staticmethod
    def get_active_toys(page: int = 1, per_page: int = 12) -> Optional[List]:
        """Obtener juguetes activos con cache"""
        key = f"toys:active:page:{page}:per_page:{per_page}"
        return cache.get(key)
    
    @staticmethod
    def set_active_toys(toys_data: List, page: int = 1, per_page: int = 12, ttl: int = 300):
        """Cachear juguetes activos (5 minutos)"""
        key = f"toys:active:page:{page}:per_page:{per_page}"
        cache.set(key, toys_data, ttl)
    
    @staticmethod
    def get_toy_by_id(toy_id: int) -> Optional[Dict]:
        """Obtener juguete por ID con cache"""
        key = f"toy:id:{toy_id}"
        return cache.get(key)
    
    @staticmethod
    def set_toy_by_id(toy_id: int, toy_data: Dict, ttl: int = 600):
        """Cachear juguete por ID (10 minutos)"""
        key = f"toy:id:{toy_id}"
        cache.set(key, toy_data, ttl)
    
    @staticmethod
    def invalidate_toy(toy_id: int):
        """Invalidar cache de un juguete específico"""
        cache.delete(f"toy:id:{toy_id}")
        # Invalidar también las listas de juguetes
        cache.clear_pattern("toys:active:*")
        cache.clear_pattern("toys:search:*")
    
    @staticmethod
    def get_search_results(query: str, filters: Dict, page: int = 1) -> Optional[List]:
        """Obtener resultados de búsqueda con cache"""
        filter_str = json.dumps(filters, sort_keys=True)
        key = f"toys:search:{hash(query + filter_str)}:page:{page}"
        return cache.get(key)
    
    @staticmethod
    def set_search_results(query: str, filters: Dict, results: List, page: int = 1, ttl: int = 300):
        """Cachear resultados de búsqueda (5 minutos)"""
        filter_str = json.dumps(filters, sort_keys=True)
        key = f"toys:search:{hash(query + filter_str)}:page:{page}"
        cache.set(key, results, ttl)

class CartCache:
    """Cache para carritos de compra persistentes"""
    
    @staticmethod
    def get_cart(user_id: int) -> Optional[Dict]:
        """Obtener carrito del usuario"""
        key = f"cart:user:{user_id}"
        return cache.get(key)
    
    @staticmethod
    def set_cart(user_id: int, cart_data: Dict, ttl: int = 86400):
        """Guardar carrito del usuario (24 horas)"""
        key = f"cart:user:{user_id}"
        cart_data['last_updated'] = datetime.now().isoformat()
        cache.set(key, cart_data, ttl)
    
    @staticmethod
    def add_item(user_id: int, toy_id: int, quantity: int = 1):
        """Agregar item al carrito"""
        cart = CartCache.get_cart(user_id) or {'items': {}}
        
        if str(toy_id) in cart['items']:
            cart['items'][str(toy_id)] += quantity
        else:
            cart['items'][str(toy_id)] = quantity
        
        CartCache.set_cart(user_id, cart)
    
    @staticmethod
    def remove_item(user_id: int, toy_id: int):
        """Remover item del carrito"""
        cart = CartCache.get_cart(user_id)
        if cart and str(toy_id) in cart['items']:
            del cart['items'][str(toy_id)]
            CartCache.set_cart(user_id, cart)
    
    @staticmethod
    def clear_cart(user_id: int):
        """Limpiar carrito del usuario"""
        cache.delete(f"cart:user:{user_id}")

class DashboardCache:
    """Cache para estadísticas del dashboard"""
    
    @staticmethod
    def get_stats() -> Optional[Dict]:
        """Obtener estadísticas del dashboard"""
        return cache.get("dashboard:stats")
    
    @staticmethod
    def set_stats(stats: Dict, ttl: int = 300):
        """Cachear estadísticas del dashboard (5 minutos)"""
        cache.set("dashboard:stats", stats, ttl)
    
    @staticmethod
    def invalidate_stats():
        """Invalidar cache de estadísticas"""
        cache.delete("dashboard:stats")

def install_redis():
    """Instalar Redis usando pip"""
    try:
        import subprocess
        import sys
        
        print("📦 Instalando Redis...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "redis"])
        print("✅ Redis instalado exitosamente")
        
        global REDIS_AVAILABLE
        REDIS_AVAILABLE = True
        
        # Reinicializar el cache manager
        global cache
        cache = CacheManager()
        
        return True
    except Exception as e:
        print(f"❌ Error instalando Redis: {str(e)}")
        return False

def test_cache_system():
    """Probar el sistema de cache"""
    print("🧪 PROBANDO SISTEMA DE CACHE")
    print("=" * 40)
    
    # Test básico
    print("📝 Test básico de set/get...")
    cache.set("test_key", {"message": "Hello Cache!"}, 60)
    result = cache.get("test_key")
    print(f"✅ Resultado: {result}")
    
    # Test con decorador
    print("\n🎯 Test con decorador...")
    
    @cached(ttl=30, key_prefix="test")
    def expensive_function(x, y):
        print(f"  🔄 Ejecutando función costosa con {x}, {y}")
        return x * y + 42
    
    # Primera llamada (miss)
    result1 = expensive_function(5, 10)
    print(f"  Primera llamada: {result1}")
    
    # Segunda llamada (hit)
    result2 = expensive_function(5, 10)
    print(f"  Segunda llamada: {result2}")
    
    # Test de carrito
    print("\n🛒 Test de carrito...")
    CartCache.add_item(1, 123, 2)
    CartCache.add_item(1, 456, 1)
    cart = CartCache.get_cart(1)
    print(f"  Carrito usuario 1: {cart}")
    
    # Estadísticas
    print("\n📊 Estadísticas del cache:")
    stats = cache.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")
    
    # Limpiar
    cache.delete("test_key")
    CartCache.clear_cart(1)
    
    print("\n✅ Pruebas completadas")

def main():
    """Función principal"""
    print("💾 SISTEMA DE CACHE REDIS - TIENDITA ALOHA")
    print("=" * 50)
    
    if not REDIS_AVAILABLE:
        print("⚠️ Redis no está disponible")
        install_choice = input("¿Deseas instalar Redis? (y/n): ").lower()
        if install_choice == 'y':
            if install_redis():
                print("🔄 Reiniciando sistema de cache...")
            else:
                print("📝 Continuando con cache en memoria")
    
    # Mostrar información del sistema
    stats = cache.get_stats()
    print(f"\n📊 Backend de cache: {stats['backend']}")
    print(f"🎯 Hit rate: {stats['hit_rate']}%")
    print(f"📈 Total requests: {stats['total_requests']}")
    
    # Ejecutar pruebas
    test_cache_system()
    
    return cache

if __name__ == "__main__":
    cache_system = main()
