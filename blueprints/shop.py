"""
Blueprint para funcionalidades de la tienda.

Incluye: index, bÃºsqueda avanzada, carrito persistente, checkout, Ã³rdenes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, make_response, current_app
from flask_login import login_required, current_user
from datetime import datetime
import json
import io
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.enums import TA_CENTER, TA_LEFT

# Importaciones absolutas
from app.models import Toy, Order, OrderItem, User
from app.extensions import db
from app.filters import format_currency
from pagination_helpers import PaginationHelper, paginate_query

# Importar sistemas avanzados
try:
    from advanced_search import AdvancedSearchEngine, create_search_interface_data
    from cache_system import ToyCache, CartCache
    # Temporalmente desactivar sistemas avanzados para forzar uso de sesiÃ³n
    ADVANCED_SYSTEMS_AVAILABLE = False  # TODO: Revisar configuraciÃ³n de Redis
except Exception:
    ADVANCED_SYSTEMS_AVAILABLE = False

# Crear el blueprint de la tienda
shop_bp = Blueprint('shop', __name__)

@shop_bp.route('/')
@shop_bp.route('/index')
def index():
    """PÃ¡gina principal con todos los juguetes activos - CON PAGINACIÃ“N"""
    page = PaginationHelper.get_page_number()
    per_page = PaginationHelper.get_per_page(default=12)
    
    # Consulta optimizada con paginaciÃ³n
    toys_query = Toy.query.filter_by(is_active=True)
    try:
        if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) and getattr(current_user, 'center', None):
            toys_query = toys_query.filter(
                db.or_(
                    ~Toy.centers.any(),
                    Toy.centers.any(center=current_user.center)
                )
            )
    except Exception:
        pass

    toys_pagination = toys_query.order_by(
        Toy.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # URLs de paginaciÃ³n
    pagination_urls = PaginationHelper.build_pagination_urls(
        toys_pagination, 'shop.index'
    )
    
    # Obtener el conteo del carrito o usar 0 si no existe
    cart_count = 0
    if 'cart' in session and isinstance(session['cart'], dict):
        cart_count = sum(item['quantity'] for item in session['cart'].values())
    
    return render_template(
        'index.html', 
        toys=toys_pagination.items,
        pagination=toys_pagination,
        pagination_urls=pagination_urls,
        cart_count=cart_count
    )

@shop_bp.route('/search')
def search():
    """BÃºsqueda avanzada con filtros mÃºltiples y cache"""
    if ADVANCED_SYSTEMS_AVAILABLE:
        return advanced_search()
    else:
        return basic_search()

def advanced_search():
    """BÃºsqueda avanzada con motor inteligente"""
    try:
        # Obtener parÃ¡metros de bÃºsqueda
        query = request.args.get('query', '').strip()
        sort_by = request.args.get('sort', 'relevance')
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 12))
        
        # Construir filtros
        filters = {}
        # Toy type (accept both toy_type and category)
        if request.args.get('toy_type'):
            filters['category'] = request.args.get('toy_type')
        elif request.args.get('category'):
            filters['category'] = request.args.get('category')
        # New filters
        if request.args.get('age') or request.args.get('age_range'):
            filters['age_range'] = request.args.get('age') or request.args.get('age_range')
        if request.args.get('gender'):
            filters['gender'] = request.args.get('gender')
        if request.args.get('price_min'):
            filters['price_min'] = float(request.args.get('price_min'))
        if request.args.get('price_max'):
            filters['price_max'] = float(request.args.get('price_max'))
        if request.args.get('in_stock') == 'true':
            filters['in_stock'] = True
        if request.args.get('on_sale') == 'true':
            filters['on_sale'] = True
        
        # Ejecutar bÃºsqueda
        search_engine = AdvancedSearchEngine()
        results = search_engine.search(
            query=query,
            filters=filters,
            sort_by=sort_by,
            page=page,
            per_page=per_page
        )
        
        # Obtener datos para la interfaz
        interface_data = create_search_interface_data()
        
        # Si es una peticiÃ³n AJAX, devolver JSON
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('format') == 'json':
            return jsonify(results)
        
        return render_template(
            'advanced_search.html',
            results=results['results'],
            pagination=results['pagination'],
            metadata=results['metadata'],
            facets=results['facets'],
            interface_data=interface_data,
            current_query=query,
            current_filters=filters,
            current_sort=sort_by
        )
        
    except Exception as e:
        flash(f'Error en bÃºsqueda avanzada: {str(e)}', 'error')
        return basic_search()

def basic_search():
    """BÃºsqueda bÃ¡sica (fallback)"""
    query = request.args.get('query', '').strip()
    toy_type = (request.args.get('toy_type') or request.args.get('category') or '').strip()
    # New filters
    age = request.args.get('age') or request.args.get('age_range') or ''
    gender = request.args.get('gender', '')
    sort = request.args.get('sort', 'name')
    # Construir consulta base
    toys_query = Toy.query.filter_by(is_active=True)
    # Filtrar por centro si el usuario estÃ¡ autenticado
    try:
        if current_user.is_authenticated and not getattr(current_user, 'is_admin', False) and getattr(current_user, 'center', None):
            toys_query = toys_query.filter(
                db.or_(
                    ~Toy.centers.any(),
                    Toy.centers.any(center=current_user.center)
                )
            )
    except Exception:
        pass
    
    # Aplicar filtros de bÃºsqueda
    if query:
        toys_query = toys_query.filter(
            db.or_(
                Toy.name.ilike(f'%{query}%'),
                Toy.description.ilike(f'%{query}%'),
                Toy.category.ilike(f'%{query}%')
            )
        )
    
    if toy_type:
        normalized_category = toy_type.lower()
        toys_query = toys_query.filter(
            db.func.lower(db.func.trim(Toy.category)) == normalized_category
        )
    
    # Nuevos filtros por columnas del item (Toy)
    if age:
        toys_query = toys_query.filter(Toy.age_range == age)
    if gender:
        toys_query = toys_query.filter(Toy.gender_category == gender)
    
    # Aplicar ordenamiento
    if sort == 'name':
        toys_query = toys_query.order_by(Toy.name.asc())
    elif sort == 'price_asc':
        toys_query = toys_query.order_by(Toy.price.asc())
    elif sort == 'price_desc':
        toys_query = toys_query.order_by(Toy.price.desc())
    else:  # fallback
        toys_query = toys_query.order_by(Toy.created_at.desc())
    
    # Obtener todos los resultados sin paginación para garantizar que se muestren todos los juguetes
    toys = toys_query.all()
    
    # Obtener categorÃ­as para filtros
    categories = db.session.query(Toy.category).filter(
        Toy.is_active == True,
        Toy.category.isnot(None)
    ).distinct().all()

    category_list = sorted({cat[0].strip() for cat in categories if cat[0]})
    
    return render_template(
        'search.html',
        toys=toys,
        query=query,
        category=toy_type,
        toy_type=toy_type,
        age=age,
        gender=gender,
        sort=sort,
        categories=category_list
    )

@shop_bp.route('/search/suggestions')
def search_suggestions():
    """API para sugerencias de autocompletado"""
    if not ADVANCED_SYSTEMS_AVAILABLE:
        return jsonify([])
    
    query = request.args.get('q', '').strip()
    if len(query) < 2:
        return jsonify([])
    
    try:
        search_engine = AdvancedSearchEngine()
        suggestions = search_engine.get_suggestions(query, limit=8)
        return jsonify(suggestions)
    except Exception as e:
        return jsonify([])

@shop_bp.route('/add_to_cart', methods=['POST'])
@login_required
def add_to_cart():
    """Agregar juguete al carrito con cache persistente"""
    toy_id = request.form.get('toy_id')
    quantity = int(request.form.get('quantity', 1))
    
    if not toy_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Juguete no especificado'})
        flash('Juguete no especificado', 'error')
        return redirect(url_for('shop.index'))
    
    toy = Toy.query.get_or_404(toy_id)
    
    # ValidaciÃ³n de stock antes de continuar
    if toy.stock < quantity or toy.stock <= 0:
        out_msg = f"âŒ {toy.name} sin stock disponible"
        # Si la peticiÃ³n es AJAX devolvemos JSON, si no redirigimos con flash
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': out_msg}), 400
        flash(out_msg, 'error')
        return redirect(url_for('shop.index'))
    
    if not toy.is_active:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Este juguete no estÃ¡ disponible'})
        flash('Este juguete no estÃ¡ disponible', 'error')
        return redirect(url_for('shop.index'))
    
    if toy.stock < quantity:
        message = f'Solo hay {toy.stock} unidades disponibles'
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': message})
        flash(message, 'error')
        return redirect(url_for('shop.index'))
    
    # Usar cache del carrito si estÃ¡ disponible
    if ADVANCED_SYSTEMS_AVAILABLE:
        try:
            CartCache.add_item(current_user.id, toy_id, quantity)
            message = f'{toy.name} agregado al carrito'
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True, 'message': message})
            # No mostrar flash aquÃ­ para redirecciones, el usuario verÃ¡ el item en el carrito.
        except Exception as e:
            # Fallback a sesiÃ³n
            is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
            add_to_session_cart(toy_id, quantity, toy.name, show_flash_message=is_ajax)
            if is_ajax:
                # Calcular cart_count para incluir en la respuesta
                cart_count = 0
                if 'cart' in session and isinstance(session['cart'], dict):
                    cart_count = sum(item.get('quantity', 0) for item in session['cart'].values())
                return jsonify({
                    'success': True, 
                    'message': f'{toy.name} agregado al carrito',
                    'cart_count': cart_count
                })
    else:
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        add_to_session_cart(toy_id, quantity, toy.name, show_flash_message=is_ajax)
        if is_ajax:
            # Calcular cart_count para incluir en la respuesta
            cart_count = 0
            if 'cart' in session and isinstance(session['cart'], dict):
                cart_count = sum(item.get('quantity', 0) for item in session['cart'].values())
            return jsonify({
                'success': True, 
                'message': f'{toy.name} agregado al carrito',
                'cart_count': cart_count
            })
    
    return redirect(url_for('shop.view_cart'))

def add_to_session_cart(toy_id, quantity, toy_name, show_flash_message=True):
    """Agregar al carrito usando sesiÃ³n (fallback)"""
    cart = session.get('cart', {})
    toy_id_str = str(toy_id)
    
    # Obtener el juguete para el precio
    toy = Toy.query.get(toy_id)
    if not toy:
        flash('Juguete no encontrado', 'error')
        return
    
    # Bloquear cantidades que exceden el stock disponible
    max_addable = max(0, toy.stock)
    current_qty = 0
    if toy_id_str in cart:
        current_qty = cart[toy_id_str]['quantity'] if isinstance(cart[toy_id_str], dict) else cart[toy_id_str]
    if current_qty + quantity > toy.stock:
        # No agregar; opcionalmente ajustar al mÃ¡ximo
        if show_flash_message:
            flash(f"âŒ Stock insuficiente para {toy_name}", 'error')
        return
    
    if toy_id_str in cart:
        # Si ya existe, actualizar cantidad
        if isinstance(cart[toy_id_str], dict):
            cart[toy_id_str]['quantity'] += quantity
        else:
            # Migrar formato antiguo
            cart[toy_id_str] = {
                'quantity': cart[toy_id_str] + quantity,
                'price': float(toy.price)
            }
    else:
        # Nuevo item
        cart[toy_id_str] = {
            'quantity': quantity,
            'price': float(toy.price)
        }
    
    session['cart'] = cart
    session.modified = True
    if show_flash_message:
        flash(f'{toy_name} agregado al carrito', 'success')

@shop_bp.route('/cart')
@login_required
def view_cart():
    """Ver carrito con datos del cache o sesiÃ³n"""
    cart_items = []
    total = 0
    
    if ADVANCED_SYSTEMS_AVAILABLE and current_user.is_authenticated:
        # Intentar obtener del cache
        try:
            cart_data = CartCache.get_cart(current_user.id)
            if cart_data:
                cart = cart_data.get('items', {})
            else:
                cart = session.get('cart', {})
        except:
            cart = session.get('cart', {})
    else:
        cart = session.get('cart', {})
    
    for toy_id, item in cart.items():
        toy = Toy.query.get(int(toy_id))
        if toy and toy.is_active:
            # Asegurar que item es un diccionario
            if isinstance(item, dict):
                quantity = item.get('quantity', 1)
                price = item.get('price', toy.price)
            else:
                # Formato antiguo - item es solo la cantidad
                quantity = item
                price = toy.price
            
            item_total = float(price) * quantity
            cart_items.append({
                'toy': toy,
                'quantity': quantity,
                'total': item_total
            })
            total += item_total
    
    return render_template('cart.html', 
                         cart_items=cart_items, 
                         total=total,
                         format_currency=format_currency)

@shop_bp.route('/remove_from_cart/<int:toy_id>', methods=['POST'])
@login_required
def remove_from_cart(toy_id):
    """Eliminar un juguete del carrito"""
    if 'cart' not in session:
        return jsonify({'success': False, 'message': 'Carrito no encontrado'})
    
    try:
        toy_id_str = str(toy_id)
        if toy_id_str in session['cart']:
            del session['cart'][toy_id_str]
            session.modified = True
            
            cart = session['cart']
            total = sum(item['quantity'] * item['price'] for item in cart.values())
            
            return jsonify({
                'success': True,
                'message': 'Producto eliminado del carrito',
                'cart_count': sum(item['quantity'] for item in cart.values()),
                'cart_total': format_currency(total)
            })
            
        return jsonify({'success': False, 'message': 'Producto no encontrado en el carrito'})
        
    except Exception as e:
        print(f"Error al eliminar del carrito: {str(e)}")
        return jsonify({'success': False, 'message': 'Error al eliminar del carrito'})

@shop_bp.route('/update_cart/<int:toy_id>', methods=['POST'])
@login_required
def update_cart(toy_id):
    """Actualizar cantidad de un juguete en el carrito"""
    if 'cart' not in session:
        return jsonify({'success': False, 'message': 'Carrito no encontrado'})
    
    try:
        quantity = int(request.form.get('quantity', 1))
        toy_id_str = str(toy_id)
        
        if quantity < 1:
            if toy_id_str in session['cart']:
                del session['cart'][toy_id_str]
                session.modified = True
                cart = session['cart']
                total = sum(item['quantity'] * item['price'] for item in cart.values())
                return jsonify({
                    'success': True,
                    'message': 'Producto eliminado del carrito',
                    'cart_count': sum(item['quantity'] for item in cart.values()),
                    'cart_total': format_currency(total)
                })
        else:
            if toy_id_str in session['cart']:
                session['cart'][toy_id_str]['quantity'] = quantity
                session.modified = True
                cart = session['cart']
                total = sum(item['quantity'] * item['price'] for item in cart.values())
                return jsonify({
                    'success': True,
                    'message': 'Carrito actualizado',
                    'cart_count': sum(item['quantity'] for item in cart.values()),
                    'cart_total': format_currency(total)
                })
        
        return jsonify({'success': False, 'message': 'Producto no encontrado en el carrito'})
        
    except Exception as e:
        print(f"Error al actualizar carrito: {str(e)}")
        return jsonify({'success': False, 'message': 'Error al actualizar el carrito'})

@shop_bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    """Proceso de checkout idempotente y finalizaciÃ³n de compra"""
    # Si se recibe un POST pero el carrito ya estÃ¡ vacÃ­o porque la orden
    # se procesÃ³ en un envÃ­o anterior, redirigir al Ãºltimo resumen de orden.
    if request.method == 'POST' and ('cart' not in session or not session['cart']):
        last_order_id = session.pop('last_order_id', None)
        if last_order_id:
            return redirect(url_for('shop.order_summary', order_id=last_order_id))
    """Proceso de checkout y finalizaciÃ³n de compra"""
    if 'cart' not in session or not session['cart']:
        flash('Tu carrito estÃ¡ vacÃ­o', 'error')
        return redirect(url_for('shop.view_cart'))
    
    # Calcular total y obtener items del carrito
    cart_items = []
    total = 0
    
    try:
        if 'cart' in session:
            for toy_id, item in session['cart'].items():
                toy = Toy.query.get(int(toy_id))
                if toy:
                    subtotal = item['quantity'] * item['price']
                    cart_items.append({
                        'toy': toy,
                        'quantity': item['quantity'],
                        'price': item['price'],
                        'total': subtotal
                    })
                    total += subtotal
    except Exception as e:
        print(f"Error al cargar el carrito: {str(e)}")
        flash('Error al cargar el carrito', 'error')
        return redirect(url_for('shop.view_cart'))
    
    if request.method == 'POST':
        # Verificar balance
        if current_user.balance < total:
            flash('No tienes suficientes ALOHA Dollars', 'error')
            return redirect(url_for('shop.view_cart'))
        
        try:
            # Crear la orden
            order = Order(
                user_id=current_user.id,
                total_price=total,
                order_date=datetime.now(),
                status='completada'
            )
            db.session.add(order)
            
            # Agregar items a la orden y actualizar stock
            for toy_id, item in session['cart'].items():
                # Obtener el juguete con bloqueo para evitar condiciones de carrera
                toy = Toy.query.with_for_update().get(int(toy_id))
                if not toy:
                    raise Exception(f"Juguete con ID {toy_id} no encontrado")
                
                # Verificar stock disponible
                if toy.stock < item['quantity']:
                    raise Exception(f"Stock insuficiente para {toy.name}. Disponible: {toy.stock}, Solicitado: {item['quantity']}")
                
                # Crear item de orden
                order_item = OrderItem(
                    order=order,
                    toy_id=int(toy_id),
                    quantity=item['quantity'],
                    price=item['price']
                )
                db.session.add(order_item)
                
                # Actualizar stock del juguete
                toy.stock -= item['quantity']
                print(f"Stock actualizado para {toy.name}: {toy.stock + item['quantity']} -> {toy.stock}")
            
            # Actualizar balance del usuario
            current_user.balance -= total
            
            # Guardar cambios
            db.session.commit()

            # Guardar el Ãºltimo order_id en sesiÃ³n para manejar reenvÃ­os accidentales
            session['last_order_id'] = order.id
            
            # Limpiar carrito despuÃ©s de confirmar que todo estÃ¡ bien
            session.pop('cart', None)
            
            # Redirigir al resumen de la orden sin mostrar mensaje flash adicional
            # ya que ahora mostramos un modal en la pÃ¡gina de resumen
            return redirect(url_for('shop.order_summary', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error al procesar la compra: {str(e)}"
            print(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('shop.view_cart'))
    
    # Para GET, mostrar la pÃ¡gina de checkout
    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         total=total)

def format_currency(amount):
    """Formatea un monto como moneda"""
    return f"A$ {amount:,.2f}"

def generate_pdf(order):
    """Genera un PDF con el recibo de la orden"""
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_JUSTIFY
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import io
    import os
    
    buffer = None
    try:
        print(f"Iniciando generaciÃ³n de PDF para orden {order.id}")
        
        # Crear buffer y documento
        buffer = io.BytesIO()
        
        # Configurar el documento con mÃ¡rgenes mÃ¡s pequeÃ±os
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        # --- Registro de Fuentes Personalizadas ---
        FUTURA_NORMAL_PATH = '/Users/frobertsv./CascadeProjects/ALOHA Tienda 2025/tienditas-aloha-app-2/static/fonts/Futura-Medium.ttf'
        FUTURA_BOLD_PATH = '/Users/frobertsv./CascadeProjects/ALOHA Tienda 2025/tienditas-aloha-app-2/static/fonts/Futura-Bold.ttf'
        LOGO_PATH = '/Users/frobertsv./CascadeProjects/ALOHA Tienda 2025/tienditas-aloha-app-2/static/images/aloha_logo.png'

        try:
            if os.path.exists(FUTURA_NORMAL_PATH) and 'Futura' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('Futura', FUTURA_NORMAL_PATH))
            if os.path.exists(FUTURA_BOLD_PATH) and 'Futura-Bold' not in pdfmetrics.getRegisteredFontNames():
                pdfmetrics.registerFont(TTFont('Futura-Bold', FUTURA_BOLD_PATH))
            
            # Determinar las fuentes a usar (Futura si estÃ¡ disponible, sino Helvetica por defecto)
            font_name_normal = 'Futura' if 'Futura' in pdfmetrics.getRegisteredFontNames() else 'Helvetica'
            font_name_bold = 'Futura-Bold' if 'Futura-Bold' in pdfmetrics.getRegisteredFontNames() else 'Helvetica-Bold'
            print(f"Usando fuentes: Normal='{font_name_normal}', Bold='{font_name_bold}'")

        except Exception as e:
            print(f"Error al registrar fuentes Futura: {e}. Se usarÃ¡n fuentes por defecto.")
            font_name_normal = 'Helvetica'
            font_name_bold = 'Helvetica-Bold'

        # Obtener estilos base
        styles = getSampleStyleSheet()
        
        # Definir y agregar estilos personalizados solo si no existen en la hoja de estilos.
        # Esto previene el error "Style '...' already defined in stylesheet".
        
        # ParÃ¡metros para la creaciÃ³n de los estilos personalizados.
        # El 'parent' se toma del stylesheet base (styles) para heredar propiedades.
        style_definitions_params = {
            'Title': {'parent': styles['Heading1'], 'fontName': font_name_bold, 'fontSize': 18, 'leading': 22, 'spaceAfter': 10, 'alignment': TA_CENTER, 'textColor': colors.HexColor('#00796B')},
            'Center': {'parent': styles['Normal'], 'fontName': font_name_normal, 'alignment': TA_CENTER},
            'Right': {'parent': styles['Normal'], 'fontName': font_name_normal, 'alignment': TA_RIGHT},
            'Normal': {'parent': styles['Normal'], 'fontName': font_name_normal, 'fontSize': 10, 'leading': 12},
            'NormalBold': {'parent': styles['Normal'], 'fontName': font_name_bold, 'fontSize': 10, 'leading': 12},
            'Subtitle': {'parent': styles['Normal'], 'fontName': font_name_bold, 'fontSize': 14, 'leading': 16, 'spaceAfter': 15, 'alignment': TA_CENTER, 'textColor': colors.HexColor('#004D40')},
            'TableHeader': {'parent': styles['Normal'], 'fontName': font_name_bold, 'fontSize': 10, 'textColor': colors.white, 'alignment': TA_CENTER, 'background': colors.HexColor('#4CAF50')},
            'TableCell': {'parent': styles['Normal'], 'fontName': font_name_normal, 'fontSize': 9},
            'TotalText': {'parent': styles['Normal'], 'fontName': font_name_bold, 'fontSize': 12, 'alignment': TA_RIGHT}
        }

        for name, params in style_definitions_params.items():
            if name not in styles:
                # Crear el objeto ParagraphStyle usando su nombre y los parÃ¡metros definidos.
                style_to_add = ParagraphStyle(name=name, **params)
                styles.add(style_to_add)
            # Si el estilo ya existe (name in styles), no hacemos nada.
            # Se utilizarÃ¡ la definiciÃ³n existente del estilo.
            # Esto evita el error por intentar redefinir un estilo ya presente.
    
        # Generar elementos del PDF
        elements = []

        # --- Logo de ALOHA ---
        if os.path.exists(LOGO_PATH):
            try:
                aloha_logo = Image(LOGO_PATH, width=1.5*72, height=0.75*72) # 1.5 inch width, 0.75 inch height
                aloha_logo.hAlign = 'CENTER'
                elements.append(aloha_logo)
                elements.append(Spacer(1, 12))
            except Exception as e:
                print(f"Error al cargar el logo: {e}")
        else:
            print(f"Advertencia: Logo no encontrado en {LOGO_PATH}")
            elements.append(Paragraph("Tiendita ALOHA", styles["Title"]))

        elements.append(Paragraph("Recibo de Compra", styles["Subtitle"]))
        elements.append(Spacer(1, 20))
        
        # InformaciÃ³n de la orden
        elements.append(Paragraph(f"<b>Orden #:</b> {order.id}", styles["NormalBold"]))
        elements.append(Paragraph(f"<b>Fecha:</b> {order.order_date.strftime('%d/%m/%Y %H:%M')}", styles["Normal"]))
        elements.append(Paragraph(f"<b>Cliente:</b> {order.user.username}", styles["Normal"]))
        elements.append(Spacer(1, 20))
        
        # Tabla de productos
        data = [["Producto", "Cantidad", "Precio", "Subtotal"]]
        for item in order.items:
            data.append([
                item.toy.name,
                str(item.quantity),
                format_currency(item.price),
                format_currency(item.price * item.quantity)
            ])
        
        # Asegurar que todos los elementos de la tabla sean strings
        data = [[str(cell) for cell in row] for row in data]
        
        # Estilo de la tabla
        table_style = [
            ('BACKGROUND', (0, 0), (-1, 0), styles['TableHeader'].background),
            ('TEXTCOLOR', (0, 0), (-1, 0), styles['TableHeader'].textColor),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'), # AlineaciÃ³n general
            ('FONTNAME', (0, 0), (-1, 0), styles['TableHeader'].fontName),
            ('FONTSIZE', (0, 0), (-1, 0), styles['TableHeader'].fontSize),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), styles['TableCell'].fontName),
            ('FONTSIZE', (0, 1), (-1, -1), styles['TableCell'].fontSize),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),      # Columna Producto a la izquierda
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Columna Cantidad al centro
            ('ALIGN', (2, 1), (3, -1), 'RIGHT'),   # Columnas Precio y Subtotal a la derecha
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('GRID', (0,0), (-1,-1), 1, colors.HexColor('#DDDDDD'))
        ]
        
        # Crear tabla con ancho de columnas proporcional
        table = Table(data, colWidths=[doc.width*0.5, doc.width*0.15, doc.width*0.15, doc.width*0.2])
        table.setStyle(TableStyle(table_style))
        elements.append(table)
        elements.append(Spacer(1, 20))
        
        # Total
        elements.append(Paragraph(f"<b>Total: {format_currency(order.total_price)}</b>", styles["TotalText"]))
        elements.append(Spacer(1, 30))
        
        # Mensaje de agradecimiento
        elements.append(Paragraph("Â¡Gracias por su compra en Tiendita ALOHA!", styles["Center"]))
        elements.append(Paragraph("Para cualquier consulta, contÃ¡ctenos en info@aloha.edu.gt o visite www.aloha.edu.gt", styles["Center"]))
        
        # Generar PDF
        print("Construyendo documento PDF...")
        doc.build(elements)
        
        # Obtener el PDF generado
        pdf = buffer.getvalue()
        if not pdf:
            raise ValueError("No se pudo generar el PDF: el buffer estÃ¡ vacÃ­o")
            
        print(f"PDF generado exitosamente, tamaÃ±o: {len(pdf)} bytes")
        return pdf
        
    except Exception as e:
        print(f"Error al generar el PDF: {str(e)}")
        import traceback
        traceback.print_exc()
        raise
    finally:
        if buffer:
            try:
                buffer.close()
            except:
                pass

@shop_bp.route('/order/<int:order_id>/pdf')
@login_required
def download_receipt(order_id):
    """Descargar recibo en PDF"""
    try:
        print(f"\n=== Inicio de generaciÃ³n de PDF para orden {order_id} ===")
        print(f"Usuario actual: {current_user.id} (Admin: {current_user.is_admin})")
        
        # Obtener la orden
        order = Order.query.get_or_404(order_id)
        print(f"Orden encontrada: ID={order.id}, Usuario={order.user_id}, Total={order.total_price}")
        
        # Verificar permisos
        if order.user_id != current_user.id and not current_user.is_admin:
            print(f"Error de permisos: Usuario {current_user.id} intentando acceder a orden de usuario {order.user_id}")
            flash('No tienes permiso para ver esta orden', 'error')
            return redirect(url_for('shop.index'))
        
        # Generar PDF
        print("Iniciando generaciÃ³n de PDF...")
        try:
            # Verificar si la orden tiene items
            if not order.items:
                raise ValueError("La orden no contiene items")
                
            # Verificar que los precios sean vÃ¡lidos
            for item in order.items:
                if item.price is None or item.quantity is None:
                    raise ValueError(f"Item {item.id} tiene precio o cantidad invÃ¡lidos")
            
            # Generar el PDF
            pdf = generate_pdf(order)
            
            if not pdf:
                raise ValueError("El PDF generado estÃ¡ vacÃ­o")
                
            print(f"PDF generado exitosamente, tamaÃ±o: {len(pdf)} bytes")
            
            # Crear respuesta con buffer
            response = make_response(pdf)
            response.mimetype = 'application/pdf'
            response.headers['Content-Disposition'] = f'attachment; filename=recibo_orden_{order_id}.pdf'
            response.headers['Content-Length'] = len(pdf)
            response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '0'
            
            print("Respuesta preparada correctamente")
            return response
            
        except Exception as e:
            print(f"\n!!! Error durante la generaciÃ³n del PDF:")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje: {str(e)}")
            print("\nTraceback completo:")
            import traceback
            traceback.print_exc()
            
            flash(f'Error al generar el PDF: {str(e)}', 'error')
            return redirect(url_for('shop.order_summary', order_id=order_id))
            
    except Exception as e:
        print(f"\n!!! Error en la ruta download_receipt:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje: {str(e)}")
        print("\nTraceback completo:")
        import traceback
        traceback.print_exc()
        
        flash('Error al procesar la solicitud. Por favor intente nuevamente mÃ¡s tarde.', 'error')
        return redirect(url_for('shop.order_summary', order_id=order_id))

@shop_bp.route('/order/<int:order_id>')
@login_required
def order_summary(order_id):
    """Ver resumen de una orden especÃ­fica"""
    try:
        order = Order.query.get_or_404(order_id)
        
        # Verificar permisos
        if order.user_id != current_user.id and not current_user.is_admin:
            flash('No tienes permiso para ver esta orden', 'error')
            return redirect(url_for('shop.index'))
        
        # Verificar que la orden tenga items
        if not order.items:
            flash('La orden no contiene items', 'error')
            return redirect(url_for('shop.index'))
        
        # Registrar visualizaciÃ³n de la orden
        print(f"Visualizando orden #{order_id} por usuario {current_user.username}")
        
        # Pasar la funciÃ³n format_currency al contexto de la plantilla
        return render_template('order_summary.html', 
                             order=order,
                             format_currency=format_currency)
    except Exception as e:
        print(f"Error al cargar la orden {order_id}: {str(e)}")
        flash('OcurriÃ³ un error al cargar la orden', 'error')
        return redirect(url_for('shop.index'))


@shop_bp.route('/api/debug/session')
@login_required
def debug_session():
    """Endpoint temporal para debug de sesiÃ³n"""
    import json
    from flask import jsonify
    
    session_data = {
        'user_id': current_user.id if current_user.is_authenticated else None,
        'username': current_user.username if current_user.is_authenticated else None,
        'cart': session.get('cart', {}),
        'cart_count': sum(item.get('quantity', 0) for item in session.get('cart', {}).values()) if isinstance(session.get('cart', {}), dict) else 0,
        'session_keys': list(session.keys())
    }
    
    return jsonify(session_data)
