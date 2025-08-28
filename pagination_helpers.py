"""
Helpers de paginación para Tiendita ALOHA
"""

from flask import request, url_for
from urllib.parse import urlencode

class PaginationHelper:
    """Helper para manejar paginación de manera consistente"""
    
    @staticmethod
    def get_page_number():
        """Obtener número de página desde request"""
        try:
            return int(request.args.get('page', 1))
        except (TypeError, ValueError):
            return 1
    
    @staticmethod
    def get_per_page(default=12, max_per_page=50):
        """Obtener cantidad de items por página"""
        try:
            per_page = int(request.args.get('per_page', default))
            return min(per_page, max_per_page)
        except (TypeError, ValueError):
            return default
    
    @staticmethod
    def build_pagination_urls(pagination, endpoint, **kwargs):
        """Construir URLs para navegación de páginas"""
        def build_url(page):
            """Build a pagination URL preserving current query args"""
            # start with current request args so existing filters persist
            args = request.args.to_dict()
            # allow explicit kwargs to override/augment request args
            args.update(kwargs)
            # set the desired page number
            args['page'] = page
            return url_for(endpoint, **args)
        
        urls = {}
        
        if pagination.has_prev:
            urls['prev'] = build_url(pagination.prev_num)
            urls['first'] = build_url(1)
        
        if pagination.has_next:
            urls['next'] = build_url(pagination.next_num)
            urls['last'] = build_url(pagination.pages)
        
        # Páginas cercanas
        urls['pages'] = []
        start = max(1, pagination.page - 2)
        end = min(pagination.pages + 1, pagination.page + 3)
        
        for page_num in range(start, end):
            urls['pages'].append({
                'number': page_num,
                'url': build_url(page_num),
                'current': page_num == pagination.page
            })
        
        return urls

def paginate_query(query, page=None, per_page=None, error_out=False):
    """Helper para paginar cualquier query"""
    if page is None:
        page = PaginationHelper.get_page_number()
    if per_page is None:
        per_page = PaginationHelper.get_per_page()
    
    return query.paginate(
        page=page, 
        per_page=per_page, 
        error_out=error_out
    )
