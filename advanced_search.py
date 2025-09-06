#!/usr/bin/env python3
"""
Sistema de Búsqueda Avanzada para Tiendita ALOHA
Filtros múltiples, búsqueda inteligente y ordenamiento avanzado
"""

import os
import sys
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy import and_, or_, func, desc, asc

# Agregar el directorio actual al path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import url_for
from app import create_app
from app.extensions import db
from app.models import Toy, Order, OrderItem
from cache_system import ToyCache, cached

class AdvancedSearchEngine:
    """Motor de búsqueda avanzada para juguetes"""
    
    def __init__(self):
        self.app = create_app()
        
        # Configuración de filtros disponibles
        self.available_filters = {
            'category': {
                'type': 'select',
                'label': 'Categoría',
                'options': self._get_categories()
            },
            'price_min': {
                'type': 'number',
                'label': 'Precio mínimo',
                'min': 0
            },
            'price_max': {
                'type': 'number',
                'label': 'Precio máximo',
                'min': 0
            },
            'in_stock': {
                'type': 'checkbox',
                'label': 'Solo con stock disponible'
            },
            'on_sale': {
                'type': 'checkbox',
                'label': 'En oferta'
            }
        }

        # Agregar filtros para nuevas columnas del item (Toy)
        # - age_range (rango de edad)
        # - gender (mapea a Toy.gender_category)
        self.available_filters.update({
            'age_range': {
                'type': 'select',
                'label': 'Rango de edad',
                'options': self._get_age_ranges()
            },
            'gender': {
                'type': 'select',
                'label': 'Gnero',
                'options': self._get_gender_categories()
            }
        })

        # Opciones de ordenamiento
        self.sort_options = {
            'relevance': {'label': 'Relevancia', 'default': True},
            'name_asc': {'label': 'Nombre A-Z'},
            'name_desc': {'label': 'Nombre Z-A'},
            'price_asc': {'label': 'Precio menor a mayor'},
            'price_desc': {'label': 'Precio mayor a menor'},
            'newest': {'label': 'Más recientes'},
            'popular': {'label': 'Más populares'},
            'stock_desc': {'label': 'Mayor stock'}
        }
    
    def _get_categories(self) -> List[Dict]:
        """Obtener categorías disponibles"""
        with self.app.app_context():
            categories = db.session.query(
                Toy.category,
                func.count(Toy.id).label('count')
            ).filter(
                Toy.is_active == True
            ).group_by(Toy.category).all()
            
            return [
                {'value': cat.category, 'label': cat.category, 'count': cat.count}
                for cat in categories if cat.category
            ]
    
    def _get_age_ranges(self) -> List[Dict]:
        """Obtener rangos de edad disponibles desde Toy.age_range"""
        with self.app.app_context():
            age_ranges = db.session.query(
                Toy.age_range,
                func.count(Toy.id).label('count')
            ).filter(
                Toy.is_active == True,
                Toy.age_range.isnot(None)
            ).group_by(Toy.age_range).all()

            return [
                {'value': ar.age_range, 'label': ar.age_range, 'count': ar.count}
                for ar in age_ranges if ar.age_range
            ]

    def _get_gender_categories(self) -> List[Dict]:
        """Obtener categoras de gnero disponibles desde Toy.gender_category"""
        with self.app.app_context():
            genders = db.session.query(
                Toy.gender_category,
                func.count(Toy.id).label('count')
            ).filter(
                Toy.is_active == True,
                Toy.gender_category.isnot(None)
            ).group_by(Toy.gender_category).all()

            return [
                {'value': g.gender_category, 'label': g.gender_category, 'count': g.count}
                for g in genders if g.gender_category
            ]

    def _get_age_groups(self) -> List[Dict]:
        """Obtener grupos de edad disponibles"""
        # NOTA: El modelo Toy no tiene campo age_group, devolver lista vacía
        # TODO: Si se necesita filtro por edad, agregar campo age_group al modelo Toy
        return []
    
    def search(self, 
               query: str = "", 
               filters: Dict = None, 
               sort_by: str = "relevance",
               page: int = 1,
               per_page: int = 12) -> Dict:
        """
        Realizar búsqueda avanzada con filtros y ordenamiento
        
        Args:
            query: Término de búsqueda
            filters: Diccionario de filtros aplicados
            sort_by: Criterio de ordenamiento
            page: Página actual
            per_page: Elementos por página
            
        Returns:
            Diccionario con resultados, paginación y metadatos
        """
        filters = filters or {}
        
        # Intentar obtener del cache
        cache_key = f"{query}_{filters}_{sort_by}_{page}_{per_page}"
        cached_result = ToyCache.get_search_results(query, filters, page)
        if cached_result:
            return cached_result
        
        with self.app.app_context():
            # Construir query base
            query_obj = Toy.query.filter(Toy.is_active == True)
            
            # Aplicar filtros de texto
            if query.strip():
                search_terms = query.strip().split()
                text_conditions = []
                
                for term in search_terms:
                    term_conditions = [
                        Toy.name.ilike(f"%{term}%"),
                        Toy.description.ilike(f"%{term}%"),
                        Toy.category.ilike(f"%{term}%")
                    ]
                    'image_url': (
                        url_for('static', filename=toy.image_url)
                        if toy.image_url
                        else url_for('static', filename='images/toys/default_toy.png')
                    ),
                
                if text_conditions:
                    query_obj = query_obj.filter(and_(*text_conditions))
            
            # Aplicar filtros específicos
            query_obj = self._apply_filters(query_obj, filters)
            
            # Aplicar ordenamiento
            query_obj = self._apply_sorting(query_obj, sort_by, query)
            
            # Obtener total de resultados
            total = query_obj.count()
            
            # Aplicar paginación
            offset = (page - 1) * per_page
            toys = query_obj.offset(offset).limit(per_page).all()
            
            # Convertir a diccionarios
            results = []
            for toy in toys:
                toy_data = {
                    'id': toy.id,
                    'name': toy.name,
                    'description': toy.description,
                    'price': float(toy.price),
                    'stock': toy.stock,
                    'category': toy.category,
                    'image_url': url_for('static', filename=toy.image_url),
                    'is_on_sale': toy.price < toy.original_price if hasattr(toy, 'original_price') else False,
                    'popularity_score': self._calculate_popularity(toy.id)
                }
                
                # Calcular relevancia si hay búsqueda por texto
                if query.strip():
                    toy_data['relevance_score'] = self._calculate_relevance(toy, query)
                
                results.append(toy_data)
            
            # Calcular paginación
            total_pages = (total + per_page - 1) // per_page
            has_prev = page > 1
            has_next = page < total_pages
            
            # Preparar respuesta
            response = {
                'results': results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': total,
                    'total_pages': total_pages,
                    'has_prev': has_prev,
                    'has_next': has_next,
                    'prev_page': page - 1 if has_prev else None,
                    'next_page': page + 1 if has_next else None
                },
                'metadata': {
                    'query': query,
                    'filters_applied': filters,
                    'sort_by': sort_by,
                    'search_time': datetime.now().isoformat(),
                    'cache_hit': False
                },
                'facets': self._generate_facets(filters)
            }
            
            # Cachear resultado
            ToyCache.set_search_results(query, filters, response, page, ttl=300)
            
            return response
    
    def _apply_filters(self, query_obj, filters: Dict):
        """Aplicar filtros específicos a la consulta"""
        
        # Filtro por categoría
        if filters.get('category'):
            query_obj = query_obj.filter(Toy.category == filters['category'])

        # Filtro por rango de edad (Toy.age_range)
        if filters.get('age_range'):
            query_obj = query_obj.filter(Toy.age_range == filters['age_range'])

        # Filtro por gnero (Toy.gender_category) acepta 'gender' o 'gender_category'
        gender_value = filters.get('gender') or filters.get('gender_category')
        if gender_value:
            query_obj = query_obj.filter(Toy.gender_category == gender_value)

        # Filtro por rango de precios
        if filters.get('price_min') is not None:
            query_obj = query_obj.filter(Toy.price >= float(filters['price_min']))
        
        if filters.get('price_max') is not None:
            query_obj = query_obj.filter(Toy.price <= float(filters['price_max']))
        
        # Filtro por stock disponible
        if filters.get('in_stock'):
            query_obj = query_obj.filter(Toy.stock > 0)
        
        # Filtro por ofertas (requiere campo original_price)
        if filters.get('on_sale'):
            if hasattr(Toy, 'original_price'):
                query_obj = query_obj.filter(Toy.price < Toy.original_price)
        
        return query_obj
    
    def _apply_sorting(self, query_obj, sort_by: str, search_query: str = ""):
        """Aplicar ordenamiento a la consulta"""
        
        if sort_by == 'name_asc':
            return query_obj.order_by(asc(Toy.name))
        elif sort_by == 'name_desc':
            return query_obj.order_by(desc(Toy.name))
        elif sort_by == 'price_asc':
            return query_obj.order_by(asc(Toy.price))
        elif sort_by == 'price_desc':
            return query_obj.order_by(desc(Toy.price))
        elif sort_by == 'newest':
            return query_obj.order_by(desc(Toy.created_at))
        elif sort_by == 'stock_desc':
            return query_obj.order_by(desc(Toy.stock))
        elif sort_by == 'popular':
            # Ordenar por popularidad (requiere subconsulta)
            popularity_subquery = db.session.query(
                OrderItem.toy_id,
                func.sum(OrderItem.quantity).label('total_sold')
            ).join(Order).filter(
                Order.is_active == True
            ).group_by(OrderItem.toy_id).subquery()
            
            query_obj = query_obj.outerjoin(
                popularity_subquery,
                Toy.id == popularity_subquery.c.toy_id
            ).order_by(desc(popularity_subquery.c.total_sold))
            
            return query_obj
        else:  # relevance o default
            if search_query.strip():
                # Para relevancia, ordenar por coincidencias en nombre primero
                return query_obj.order_by(
                    desc(Toy.name.ilike(f"%{search_query}%")),
                    desc(Toy.created_at)
                )
            else:
                return query_obj.order_by(desc(Toy.created_at))
    
    def _calculate_relevance(self, toy, query: str) -> float:
        """Calcular score de relevancia para un juguete"""
        score = 0.0
        query_lower = query.lower()
        
        # Coincidencia exacta en nombre (peso alto)
        if query_lower in toy.name.lower():
            score += 10.0
        
        # Coincidencia en descripción
        if toy.description and query_lower in toy.description.lower():
            score += 5.0
        
        # Coincidencia en categoría
        if toy.category and query_lower in toy.category.lower():
            score += 3.0
        
        # Bonus por stock disponible
        if toy.stock > 0:
            score += 1.0
        
        # Bonus por popularidad
        score += self._calculate_popularity(toy.id) * 0.1
        
        return round(score, 2)
    
    def _calculate_popularity(self, toy_id: int) -> float:
        """Calcular score de popularidad basado en ventas"""
        try:
            total_sold = db.session.query(
                func.sum(OrderItem.quantity)
            ).join(Order).filter(
                OrderItem.toy_id == toy_id,
                Order.is_active == True
            ).scalar() or 0
            
            return float(total_sold)
        except:
            return 0.0
    
    def _generate_facets(self, current_filters: Dict) -> Dict:
        """Generar facetas para refinamiento de búsqueda"""
        facets = {}
        
        # Facetas de categorías
        categories = self._get_categories()
        facets['categories'] = [
            {
                'value': cat['value'],
                'label': cat['label'],
                'count': cat['count'],
                'active': current_filters.get('category') == cat['value']
            }
            for cat in categories
        ]
        
        # Facetas de rangos de edad
        age_ranges = self._get_age_ranges()
        facets['age_ranges'] = [
            {
                'value': ar['value'],
                'label': ar['label'],
                'count': ar['count'],
                'active': current_filters.get('age_range') == ar['value']
            }
            for ar in age_ranges
        ]

        # Facetas de gnero
        genders = self._get_gender_categories()
        facets['genders'] = [
            {
                'value': g['value'],
                'label': g['label'],
                'count': g['count'],
                'active': (current_filters.get('gender') or current_filters.get('gender_category')) == g['value']
            }
            for g in genders
        ]

        # Rangos de precio sugeridos
        facets['price_ranges'] = [
            {'label': 'Menos de $10', 'min': 0, 'max': 10},
            {'label': '$10 - $25', 'min': 10, 'max': 25},
            {'label': '$25 - $50', 'min': 25, 'max': 50},
            {'label': '$50 - $100', 'min': 50, 'max': 100},
            {'label': 'Más de $100', 'min': 100, 'max': None}
        ]
        
        return facets
    
    def get_suggestions(self, partial_query: str, limit: int = 5) -> List[str]:
        """Obtener sugerencias de autocompletado"""
        if len(partial_query) < 2:
            return []
        
        with self.app.app_context():
            # Buscar en nombres de juguetes
            suggestions = db.session.query(Toy.name).filter(
                Toy.is_active == True,
                Toy.name.ilike(f"%{partial_query}%")
            ).limit(limit).all()
            
            return [s.name for s in suggestions]
    
    def get_popular_searches(self, limit: int = 10) -> List[Dict]:
        """Obtener búsquedas populares basadas en categorías más vendidas"""
        with self.app.app_context():
            popular = db.session.query(
                Toy.category,
                func.sum(OrderItem.quantity).label('total_sold')
            ).join(OrderItem).join(Order).filter(
                Order.is_active == True,
                Toy.is_active == True
            ).group_by(Toy.category).order_by(
                desc('total_sold')
            ).limit(limit).all()
            
            return [
                {
                    'query': cat.category,
                    'label': f"Juguetes de {cat.category}",
                    'popularity': int(cat.total_sold)
                }
                for cat in popular if cat.category
            ]

def create_search_interface_data() -> Dict:
    """Crear datos para la interfaz de búsqueda avanzada"""
    engine = AdvancedSearchEngine()
    
    return {
        'filters': engine.available_filters,
        'sort_options': engine.sort_options,
        'popular_searches': engine.get_popular_searches(),
        'price_ranges': [
            {'label': 'Todos los precios', 'value': ''},
            {'label': 'Menos de $10', 'value': '0-10'},
            {'label': '$10 - $25', 'value': '10-25'},
            {'label': '$25 - $50', 'value': '25-50'},
            {'label': '$50 - $100', 'value': '50-100'},
            {'label': 'Más de $100', 'value': '100-'}
        ]
    }

def test_search_engine():
    """Probar el motor de búsqueda"""
    print("🔍 PROBANDO MOTOR DE BÚSQUEDA AVANZADA")
    print("=" * 50)
    
    engine = AdvancedSearchEngine()
    
    # Test 1: Búsqueda simple
    print("📝 Test 1: Búsqueda simple...")
    results = engine.search(query="oso", page=1, per_page=5)
    print(f"  Resultados encontrados: {results['pagination']['total']}")
    print(f"  Primeros resultados: {[r['name'] for r in results['results'][:3]]}")
    
    # Test 2: Búsqueda con filtros
    print("\n🎯 Test 2: Búsqueda con filtros...")
    filters = {
        'category': 'Peluches',
        'price_min': 10,
        'price_max': 50,
        'in_stock': True
    }
    results = engine.search(query="", filters=filters, page=1, per_page=5)
    print(f"  Resultados con filtros: {results['pagination']['total']}")
    
    # Test 3: Ordenamiento
    print("\n📊 Test 3: Diferentes ordenamientos...")
    for sort_option in ['price_asc', 'price_desc', 'newest']:
        results = engine.search(sort_by=sort_option, per_page=3)
        if results['results']:
            first_result = results['results'][0]
            print(f"  {sort_option}: {first_result['name']} - ${first_result['price']}")
    
    # Test 4: Sugerencias
    print("\n💡 Test 4: Sugerencias de autocompletado...")
    suggestions = engine.get_suggestions("o")
    print(f"  Sugerencias para 'o': {suggestions}")
    
    # Test 5: Búsquedas populares
    print("\n🔥 Test 5: Búsquedas populares...")
    popular = engine.get_popular_searches(5)
    for search in popular:
        print(f"  {search['label']}: {search['popularity']} ventas")
    
    print("\n✅ Pruebas completadas")

def main():
    """Función principal"""
    print("🔍 SISTEMA DE BÚSQUEDA AVANZADA - TIENDITA ALOHA")
    print("=" * 55)
    
    # Crear datos de interfaz
    interface_data = create_search_interface_data()
    
    print("📋 Filtros disponibles:")
    for key, filter_config in interface_data['filters'].items():
        print(f"  • {filter_config['label']} ({filter_config['type']})")
    
    print(f"\n📊 Opciones de ordenamiento: {len(interface_data['sort_options'])}")
    for key, sort_config in interface_data['sort_options'].items():
        default = " (por defecto)" if sort_config.get('default') else ""
        print(f"  • {sort_config['label']}{default}")
    
    print(f"\n🔥 Búsquedas populares: {len(interface_data['popular_searches'])}")
    for search in interface_data['popular_searches'][:5]:
        print(f"  • {search['label']}")
    
    # Ejecutar pruebas
    test_search_engine()
    
    return interface_data

if __name__ == "__main__":
    search_data = main()
