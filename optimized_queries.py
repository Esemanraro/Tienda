"""
Ejemplos de consultas optimizadas para Tiendita ALOHA
"""

from models import User, Toy, Order, OrderItem
from extensions import db
from sqlalchemy import func, and_, or_
from pagination_helpers import paginate_query

class OptimizedQueries:
    """Colección de consultas optimizadas"""
    
    @staticmethod
    def get_toys_with_pagination(page=1, per_page=12, search=None, category=None, order_by='created_at'):
        """
        Búsqueda optimizada de juguetes con paginación
        Usa índices: idx_toy_active_category, idx_toy_name_lower, idx_toy_active_price
        """
        query = Toy.query.filter_by(is_active=True)
        
        # Filtro por búsqueda (usa índice idx_toy_name_lower)
        if search:
            query = query.filter(Toy.name.ilike(f'%{search}%'))
        
        # Filtro por categoría (usa índice idx_toy_active_category)
        if category:
            query = query.filter_by(category=category)
        
        # Ordenamiento optimizado
        if order_by == 'price_asc':
            query = query.order_by(Toy.price.asc())
        elif order_by == 'price_desc':
            query = query.order_by(Toy.price.desc())
        elif order_by == 'name':
            query = query.order_by(Toy.name.asc())
        else:  # created_at por defecto
            query = query.order_by(Toy.created_at.desc())
        
        return paginate_query(query, page, per_page)
    
    @staticmethod
    def get_user_orders_with_items(user_id, page=1, per_page=10):
        """
        Obtener órdenes de usuario con eager loading de items
        Usa índice: idx_order_user_active
        """
        return Order.query.filter_by(
            user_id=user_id, 
            is_active=True
        ).options(
            db.joinedload(Order.items).joinedload(OrderItem.toy)
        ).order_by(Order.order_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_dashboard_stats():
        """
        Estadísticas optimizadas para dashboard
        Usa índices: idx_order_active_total, idx_user_active_created
        """
        # Usar una sola consulta para múltiples estadísticas
        stats = db.session.query(
            func.sum(Order.total_price).label('total_sales'),
            func.count(Order.id).label('total_orders'),
            func.avg(Order.total_price).label('avg_order_value')
        ).filter(Order.is_active == True).first()
        
        total_users = User.query.filter_by(is_active=True).count()
        
        return {
            'total_sales': stats.total_sales or 0,
            'total_orders': stats.total_orders or 0,
            'avg_order_value': stats.avg_order_value or 0,
            'total_users': total_users
        }
    
    @staticmethod
    def get_popular_toys(limit=10):
        """
        Obtener juguetes más vendidos
        Usa índice: idx_orderitem_toy_active
        """
        return db.session.query(
            Toy.id,
            Toy.name,
            Toy.category,
            Toy.price,
            func.sum(OrderItem.quantity).label('total_sold'),
            func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
        ).join(OrderItem).join(Order).filter(
            and_(
                Toy.is_active == True,
                OrderItem.is_active == True,
                Order.is_active == True
            )
        ).group_by(Toy.id).order_by(
            func.sum(OrderItem.quantity).desc()
        ).limit(limit).all()
    
    @staticmethod
    def get_sales_by_category():
        """
        Ventas agrupadas por categoría
        Usa índices: idx_toy_active_category, idx_orderitem_toy_active
        """
        return db.session.query(
            Toy.category,
            func.count(func.distinct(Toy.id)).label('unique_toys'),
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
        ).join(OrderItem).join(Order).filter(
            and_(
                Toy.is_active == True,
                OrderItem.is_active == True,
                Order.is_active == True
            )
        ).group_by(Toy.category).order_by(
            func.sum(OrderItem.quantity * OrderItem.price).desc()
        ).all()
    
    @staticmethod
    def search_toys_advanced(search_term, filters=None, page=1, per_page=12):
        """
        Búsqueda avanzada de juguetes con múltiples filtros
        """
        query = Toy.query.filter_by(is_active=True)
        
        if search_term:
            # Búsqueda en nombre y descripción
            search_filter = or_(
                Toy.name.ilike(f'%{search_term}%'),
                Toy.description.ilike(f'%{search_term}%')
            )
            query = query.filter(search_filter)
        
        if filters:
            if filters.get('category'):
                query = query.filter_by(category=filters['category'])
            
            if filters.get('min_price'):
                query = query.filter(Toy.price >= filters['min_price'])
            
            if filters.get('max_price'):
                query = query.filter(Toy.price <= filters['max_price'])
            
            if filters.get('in_stock'):
                query = query.filter(Toy.stock > 0)
        
        # Ordenamiento por relevancia (nombre primero, luego descripción)
        if search_term:
            query = query.order_by(
                Toy.name.ilike(f'%{search_term}%').desc(),
                Toy.created_at.desc()
            )
        else:
            query = query.order_by(Toy.created_at.desc())
        
        return paginate_query(query, page, per_page)
