"""
Blueprint para funcionalidades de administración
Incluye: dashboard, gestión de juguetes (CRUD), inventario inteligente
"""

import os
import logging
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, abort, Response
from flask_login import login_required, current_user, login_user, logout_user
from datetime import datetime, timedelta
from sqlalchemy import desc, or_
from sqlalchemy.orm import selectinload
from decimal import Decimal, InvalidOperation

# Importaciones absolutas
from app.models import User, Toy, Order, OrderItem, ToyCenterAvailability
from app.extensions import db
from app.forms import ToyForm, AddUserForm, EditUserForm
from pagination_helpers import PaginationHelper, paginate_query

# 💾 Importar Sistema de Backup Simplificado
try:
    from utils.backup_system_simple import backup_manager
    BACKUP_SYSTEM_AVAILABLE = True
except ImportError:
    backup_manager = None
    BACKUP_SYSTEM_AVAILABLE = False

# Importar sistemas avanzados
try:
    from inventory_system import InventoryManager
    from cache_system import DashboardCache
    ADVANCED_SYSTEMS_AVAILABLE = True
except ImportError:
    ADVANCED_SYSTEMS_AVAILABLE = False

# 🔐 Importar Rate Limiter
try:
    from utils.rate_limiter import moderate_rate_limit, strict_rate_limit, relaxed_rate_limit
    RATE_LIMITING_AVAILABLE = True
except ImportError:
    # Fallback si no está disponible
    def moderate_rate_limit(message=None):
        def decorator(f):
            return f
        return decorator
    def strict_rate_limit(message=None):
        def decorator(f):
            return f
        return decorator
    def relaxed_rate_limit(message=None):
        def decorator(f):
            return f
        return decorator
    RATE_LIMITING_AVAILABLE = False

# ✅ Sistema de backup simplificado ya importado arriba

# Crear el blueprint de administración
admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    """Panel de administración principal - OPTIMIZADO CON INVENTARIO INTELIGENTE"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    toy_form = ToyForm()
    page = PaginationHelper.get_page_number()
    per_page = PaginationHelper.get_per_page(default=20)
    
    # Obtener estadísticas optimizadas con cache
    sales_stats = get_dashboard_stats_optimized()

    # Resumen de usuarios
    total_users = User.query.count()
    admins_count = User.query.filter_by(is_admin=True).count()
    inactive_count = User.query.filter_by(is_active=False).count()

    # Sistema de inventario inteligente
    inventory_data = {}
    if ADVANCED_SYSTEMS_AVAILABLE:
        try:
            # Intentar obtener del cache primero
            inventory_data = DashboardCache.get_stats()
            
            if not inventory_data:
                # Generar datos de inventario
                inventory_manager = InventoryManager()
                inventory_report = inventory_manager.generate_inventory_report()
                
                inventory_data = {
                    'alerts': inventory_report['alerts'][:5],  # Top 5 alertas
                    'predictions': inventory_report['predictions'][:3],  # Top 3 predicciones
                    'stats': inventory_report['stats'],
                    'summary': inventory_report['summary']
                }
                
                # Cachear por 5 minutos
                DashboardCache.set_stats(inventory_data, ttl=300)
        except Exception as e:
            print(f"⚠️ Error en sistema de inventario: {str(e)}")
            inventory_data = {'error': 'Sistema de inventario no disponible'}
    
    # Obtener órdenes recientes (usa índice idx_order_active_date)
    recent_orders = Order.query.filter_by(
        is_active=True
    ).order_by(Order.order_date.desc()).limit(5).all()
    
    # Obtener usuarios recientes (usa índice idx_user_active_created)
    recent_users = User.query.filter_by(
        is_active=True
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Obtener juguetes con paginación (usa índice idx_toy_active_created)
    toys_pagination = Toy.query.filter_by(is_active=True).order_by(
        Toy.created_at.desc()
    ).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    # URLs de paginación para juguetes
    pagination_urls = PaginationHelper.build_pagination_urls(
        toys_pagination, 'admin.dashboard'
    )
    
    # Datos para el gráfico de ventas (últimos 7 días)
    chart_data = get_sales_chart_data()
    
    return render_template('admin_dashboard.html',
                         toys=toys_pagination.items,
                         pagination=toys_pagination,
                         pagination_urls=pagination_urls,
                         toy_form=toy_form,
                         recent_orders=recent_orders,
                         recent_users=recent_users,
                         sales_stats=sales_stats,
                         inventory_data=inventory_data,  # Nuevos datos de inventario
                         advanced_systems=ADVANCED_SYSTEMS_AVAILABLE,
                         dates=chart_data['dates'],
                         sales_data=chart_data['sales_data'],
                         total_users_count=total_users,
                         admins_count=admins_count,
                         inactive_count=inactive_count)

def get_dashboard_stats_optimized():
    """Obtener estadísticas con caché manual (5 min)"""
    from flask import current_app
    cache = current_app.extensions.get('cache')

    if cache:
        cached = cache.get('dashboard_stats')
        if cached:
            return cached

    sales_stats = {
        'total_sales': 0,
        'total_orders': 0,
        'total_users': 0,
        'avg_order_value': 0,
        'sales_by_category': []
    }
    
    try:
        # Estadísticas principales con una sola consulta (usa índices optimizados)
        main_stats = db.session.query(
            db.func.sum(Order.total_price).label('total_sales'),
            db.func.count(Order.id).label('total_orders'),
            db.func.avg(Order.total_price).label('avg_order_value')
        ).filter(Order.is_active == True).first()
        
        sales_stats['total_sales'] = main_stats.total_sales or 0
        sales_stats['total_orders'] = main_stats.total_orders or 0
        sales_stats['avg_order_value'] = main_stats.avg_order_value or 0
        
        # Total de usuarios activos (usa índice idx_user_active_created)
        sales_stats['total_users'] = User.query.filter_by(is_active=True).count()
        
        # Ventas por categoría optimizada (usa índices idx_orderitem_toy_active)
        sales_by_category = db.session.query(
            Toy.category,
            db.func.sum(OrderItem.quantity).label('quantity'),
            db.func.sum(OrderItem.quantity * OrderItem.price).label('amount')
        ).join(OrderItem).join(Order).filter(
            Order.is_active == True,
            OrderItem.is_active == True,
            Toy.is_active == True
        ).group_by(Toy.category).order_by(
            db.func.sum(OrderItem.quantity * OrderItem.price).desc()
        ).all()
        
        sales_stats['sales_by_category'] = [
            {
                'category': cat,
                'quantity': int(qty or 0),
                'amount': float(amt or 0)
            } for cat, qty, amt in sales_by_category
        ]
        
    except Exception as e:
        print(f"Error al obtener estadísticas: {str(e)}")
        flash('Error al cargar estadísticas', 'error')
    
    # Guardar en caché durante 5 min (si el backend lo permite)
    if cache:
        if hasattr(cache, 'set'):
            cache.set('dashboard_stats', sales_stats, timeout=300)
        elif isinstance(cache, dict):
            cache['dashboard_stats'] = sales_stats
    
    return sales_stats

def get_sales_chart_data():
    """Obtener datos para el gráfico de ventas de los últimos 7 días"""
    dates = []
    sales_data = []
    
    try:
        # Ventas de los últimos 7 días (usa índice idx_order_active_date)
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            daily_sales = db.session.query(
                db.func.sum(Order.total_price)
            ).filter(
                Order.is_active == True,
                db.func.date(Order.order_date) == date.date()
            ).scalar() or 0
            
            sales_data.append(float(daily_sales))
        
        # Invertir las listas para mostrar en orden cronológico
        dates.reverse()
        sales_data.reverse()
        
    except Exception as e:
        print(f"Error al obtener datos del gráfico: {str(e)}")
        dates = ['Sin datos'] * 7
        sales_data = [0] * 7
    
    return {'dates': dates, 'sales_data': sales_data}


@admin_bp.route('/users')
@login_required
def all_users():
    """Página para administrar usuarios con paginación."""
    if not current_user.is_admin:
        flash('Acceso denegado. No tienes permisos de administrador.', 'danger')
        return redirect(url_for('shop.index'))

    page = PaginationHelper.get_page_number()
    per_page = PaginationHelper.get_per_page(default=15)

    search_term = request.args.get('search', '')
    users_query = User.query

    if search_term:
        users_query = users_query.filter(
            or_(
                User.username.ilike(f'%{search_term}%'),
                User.email.ilike(f'%{search_term}%')
            )
        )

    status_filter = request.args.get('status', 'all')

    if status_filter == 'active':
        users_query = users_query.filter(User.is_active == True)
    elif status_filter == 'inactive':
        users_query = users_query.filter(User.is_active == False)
    elif status_filter == 'admin':
        users_query = users_query.filter(User.is_admin == True)
    # 'all' requires no additional filtering on status

    total_users_count = users_query.count() # Count before pagination for accurate total

    # Ordenamiento
    sort_field = request.args.get('sort', 'created_at')
    sort_dir = request.args.get('dir', 'desc')

    sort_map = {
        'username': User.username,
        'created_at': User.created_at,
        'center': User.center,
        'is_active': User.is_active,
        'last_login': User.last_login
    }

    sort_column = sort_map.get(sort_field, User.created_at)
    if sort_dir == 'asc':
        users_query = users_query.order_by(sort_column.asc())
    else:
        users_query = users_query.order_by(sort_column.desc())

    users_pagination = paginate_query(users_query, page, per_page)
    
    pagination_urls = PaginationHelper.build_pagination_urls(
        users_pagination, 'admin.all_users', search=search_term, status=status_filter
    )
    
    today_start_dt = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    return render_template('admin_users.html',
                           users=users_pagination,
                           pagination=users_pagination,
                           pagination_urls=pagination_urls,
                           search_query=search_term, # Renamed for consistency with template
                           status_filter=status_filter,
                           total_users=total_users_count,
                           today_start=today_start_dt,
                           sort=sort_field,
                           dir=sort_dir,
                           title="Administrar Usuarios")


@admin_bp.route('/toggle_admin/<int:user_id>', methods=['POST'])
@login_required
def toggle_admin(user_id):
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('shop.index'))

    user_to_toggle = User.query.get_or_404(user_id)
    
    # Admins cannot remove admin status from themselves
    if user_to_toggle.id == current_user.id and user_to_toggle.is_admin:
        flash('No puedes quitarte el rol de administrador a ti mismo.', 'warning')
        return redirect(url_for('admin.all_users'))

    user_to_toggle.is_admin = not user_to_toggle.is_admin
    try:
        db.session.commit()
        flash(f'Rol de administrador para {user_to_toggle.username} actualizado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar rol de administrador: {str(e)}', 'danger')
    return redirect(url_for('admin.all_users'))


@admin_bp.route('/toggle_user/<int:user_id>', methods=['POST'])
@login_required
def toggle_user(user_id):
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('shop.index'))

    user_to_toggle = User.query.get_or_404(user_id)

    # Admins cannot deactivate themselves
    if user_to_toggle.id == current_user.id and not user_to_toggle.is_active:
        flash('No puedes desactivar tu propia cuenta de administrador.', 'warning')
        return redirect(url_for('admin.all_users'))
        
    user_to_toggle.is_active = not user_to_toggle.is_active
    try:
        db.session.commit()
        flash(f'Estado de activación para {user_to_toggle.username} actualizado.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al actualizar estado de activación: {str(e)}', 'danger')
    return redirect(url_for('admin.all_users'))


@admin_bp.route('/toys/add', methods=['POST'])
@admin_bp.route('/add_toy', methods=['GET', 'POST'])
@login_required
@moderate_rate_limit(message="⚠️ Demasiados intentos de agregar juguetes. Espera un momento.")
def add_toy():
    """Agregar un nuevo juguete"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    toy_form = ToyForm()
    if toy_form.validate_on_submit():
        try:
            # Manejar la imagen si se subió una
            image_filename = None
            if toy_form.image.data:
                image_file = toy_form.image.data
                if image_file.filename != '':
                    # Crear directorio de imágenes si no existe
                    upload_folder = os.path.join(current_app.static_folder, 'images', 'toys')
                    os.makedirs(upload_folder, exist_ok=True)
                    
                    # Generar nombre único para la imagen
                    filename = secure_filename(image_file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                    image_filename = timestamp + filename
                    
                    # Guardar la imagen
                    image_path = os.path.join(upload_folder, image_filename)
                    image_file.save(image_path)
                    
                    # Guardar la ruta relativa en la base de datos
                    image_filename = f'images/toys/{image_filename}'

            # Validar centros seleccionados (mínimo uno)
            selected_centers = request.form.getlist('centers') or []
            
            # Crear nuevo juguete con categorias separadas
            new_toy = Toy(
                name=toy_form.name.data,
                description=toy_form.description.data,
                price=toy_form.price.data,
                category=toy_form.toy_type.data,
                age_range=toy_form.age_range.data,
                gender_category=toy_form.gender.data,
                stock=toy_form.stock.data,
                image_url=image_filename
            )
            
            db.session.add(new_toy)
            db.session.flush()

            # Asociar centros seleccionados al juguete
            if selected_centers:
                seen = set()
                for center in selected_centers:
                    if center in seen:
                        continue
                    seen.add(center)
                    db.session.add(ToyCenterAvailability(toy_id=new_toy.id, center=center))

            db.session.commit()
            flash('¡Juguete agregado exitosamente!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el juguete: {str(e)}', 'error')
    else:
        for field, errors in toy_form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')
    
    return redirect(url_for('admin.toys_page'))

@admin_bp.route('/bulk_upload_toys', methods=['GET', 'POST'])
@login_required
def bulk_upload_toys():
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))

    if request.method == 'POST':
        csv_file = request.files.get('csv_file')
        image_files = request.files.getlist('images')

        if not csv_file:
            flash('Se requiere un archivo CSV', 'error')
            return redirect(url_for('admin.bulk_upload_toys'))

        import csv
        import re
        from io import StringIO

        csv_stream = StringIO(csv_file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(csv_stream)

        image_map = {}
        for img in image_files:
            if img and img.filename:
                filename = secure_filename(img.filename)
                base = os.path.splitext(filename)[0].strip().lower().replace(' ', '_')
                image_map[base] = (img, filename)

        current_app.logger.info('Iniciando carga masiva de juguetes')
        created = 0
        errors = []
        for idx, row in enumerate(reader, start=1):
            data = {k.strip().lower(): v.strip() for k, v in row.items() if k}
            name = data.get('name')
            if not name:
                current_app.logger.warning(f'Fila {idx} sin nombre, se omite')
                continue

            current_app.logger.info(f'Procesando fila {idx}: {name}')

            try:
                try:
                    price = float(data.get('price', 0))
                except ValueError:
                    price = 0.0
                try:
                    stock = int(data.get('stock', 0))
                except ValueError:
                    stock = 0

                toy = Toy(
                    name=name,
                    description=data.get('description', ''),
                    price=price,
                    stock=stock,
                    age_range=data.get('age range') or data.get('age_range'),
                    gender_category=data.get('gender category') or data.get('gender_category'),
                    category=data.get('category')
                )

                base_name = os.path.splitext(secure_filename(name))[0].lower().replace(' ', '_')
                if base_name in image_map:
                    img, filename = image_map[base_name]
                    upload_folder = os.path.join(current_app.static_folder, 'images', 'toys')
                    os.makedirs(upload_folder, exist_ok=True)
                    img.save(os.path.join(upload_folder, filename))
                    toy.image_url = f'images/toys/{filename}'

                db.session.add(toy)
                db.session.commit()

                centers_str = data.get('center')
                if centers_str:
                    centers = [c.strip().lower() for c in re.split(r'[;,]', centers_str) if c.strip()]
                    if 'all' not in centers:
                        for center in centers:
                            db.session.add(ToyCenterAvailability(toy_id=toy.id, center=center))
                        db.session.commit()

                created += 1
                current_app.logger.info(f'✔️ Fila {idx} procesada: {name}')
            except Exception as e:
                db.session.rollback()
                error_msg = f'❌ Error en fila {idx} ({name}): {e}'
                current_app.logger.error(error_msg)
                errors.append(error_msg)

        for err in errors:
            flash(err, 'error')
        flash(f'{created} juguetes cargados exitosamente. {len(errors)} errores.',
              'success' if not errors else 'warning')
        current_app.logger.info(f'Carga masiva completada: {created} éxitos, {len(errors)} errores')
        return redirect(url_for('admin.toys_page'))

    return render_template('bulk_upload_toys.html')

@admin_bp.route('/edit_toy/<int:toy_id>', methods=['GET', 'POST'])
@login_required
def edit_toy(toy_id):
    """Editar un juguete existente"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    toy = Toy.query.get_or_404(toy_id)
    toy_form = ToyForm(obj=toy)
    
    if request.method == 'POST' and toy_form.validate_on_submit():
        try:
            # Manejar la imagen si se subió una nueva y optimizar
            if toy_form.image.data and toy_form.image.data.filename != '':
                image_file = toy_form.image.data
                
                # Crear directorio de imágenes si no existe
                upload_folder = os.path.join(current_app.static_folder, 'images', 'toys')
                os.makedirs(upload_folder, exist_ok=True)
                
                # Eliminar imagen anterior si existe
                if toy.image_url:
                    old_image_path = os.path.join(current_app.static_folder, toy.image_url)
                    if os.path.exists(old_image_path):
                        os.remove(old_image_path)
                
                # Generar nombre único para la nueva imagen
                filename = secure_filename(image_file.filename)
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                image_filename = timestamp + filename
                
                # Guardar la nueva imagen
                image_path = os.path.join(upload_folder, image_filename)
                image_file.save(image_path)
                
                # Actualizar la ruta en el objeto
                toy.image_url = f'images/toys/{image_filename}'
            
            # Actualizar los datos del juguete
            toy.name = toy_form.name.data
            toy.description = toy_form.description.data
            toy.price = toy_form.price.data
            toy.category = toy_form.category.data
            toy.stock = toy_form.stock.data
            toy.updated_at = datetime.now()
            
            db.session.commit()
            flash('¡Juguete actualizado exitosamente!', 'success')
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'success': True})
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el juguete: {str(e)}', 'error')
            return jsonify({'success': False, 'message': str(e)}), 500 if request.headers.get('X-Requested-With') == 'XMLHttpRequest' else redirect(url_for('admin.dashboard'))
        
        return redirect(url_for('admin.dashboard'))
    
    if request.method == 'POST' and not toy_form.validate_on_submit():
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'errors': toy_form.errors}), 400
        else:
            for field, errors in toy_form.errors.items():
                for error in errors:
                    flash(f'Error en {field}: {error}', 'error')
            return redirect(url_for('admin.dashboard'))

    # Para GET request, devolver datos del juguete como JSON
    if request.method == 'GET':
        toy_data = {
            'id': toy.id,
            'name': toy.name,
            'description': toy.description,
            'price': float(toy.price),
            'category': toy.category,
            'stock': toy.stock,
            'image_url': url_for('static', filename=toy.image_url)
        }
        return jsonify(toy_data)

@admin_bp.route('/delete_toy/<int:toy_id>', methods=['POST'])
@login_required
@moderate_rate_limit(message="⚠️ Demasiados intentos de eliminación. Espera un momento.")
def delete_toy(toy_id):
    """Eliminar un juguete (soft delete) - CORREGIDO PARA AJAX"""
    if not current_user.is_admin:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Acceso denegado'}), 403
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    try:
        current_app.logger.info(f"Eliminando juguete {toy_id} - Headers: {dict(request.headers)}")
        toy = Toy.query.get_or_404(toy_id)
        
        # Eliminar imagen si existe
        if toy.image_url:
            image_path = os.path.join(current_app.static_folder, toy.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
                current_app.logger.info(f"Imagen eliminada: {image_path}")
        
        # Soft delete: marcar como eliminado en lugar de eliminar físicamente
        toy.deleted_at = datetime.now()
        toy.is_active = False
        
        db.session.commit()
        current_app.logger.info(f"Juguete {toy_id} eliminado exitosamente")
        
        # Respuesta diferente para AJAX vs formulario normal
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': '¡Juguete eliminado exitosamente!',
                'toy_id': toy_id
            })
        else:
            flash('¡Juguete eliminado exitosamente!', 'success')
            return redirect(url_for('admin.toys_page'))

    except Exception as e:
        db.session.rollback()
        error_msg = f'Error al eliminar el juguete: {str(e)}'
        current_app.logger.error(error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': False,
                'message': error_msg
            }), 500
        else:
            flash(error_msg, 'error')
            return redirect(url_for('admin.toys_page'))
@admin_bp.route('/toys/<int:toy_id>/stock', methods=['POST'])
@login_required
def update_toy_stock(toy_id):
    """Ajustar el stock de un juguete"""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    toy = Toy.query.get_or_404(toy_id)
    try:
        data = request.get_json() or {}
        delta = int(data.get('delta', 0))
        toy.stock = max(0, toy.stock + delta)
        db.session.commit()
        return jsonify({'success': True, 'stock': toy.stock})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# NUEVA RUTA: Gestión dedicada de juguetes
@admin_bp.route('/toys')
@login_required
def toys_page():
    """Página independiente para gestionar juguetes"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))

    toy_form = ToyForm()
    toys = (
        Toy.query.options(selectinload(Toy.centers))
        .filter_by(is_active=True)
        .order_by(Toy.created_at.desc())
        .all()
    )

    return render_template('admin/inventory.html', toy_form=toy_form, toys=toys)

# Administrar centros por juguete (obtener/actualizar)
@admin_bp.route('/toys/<int:toy_id>/centers', methods=['GET', 'POST'])
@login_required
def manage_toy_centers(toy_id):
    """Obtener o actualizar disponibilidad por centro para un juguete."""
    if not current_user.is_admin:
        return jsonify({'success': False, 'message': 'Acceso denegado'}), 403

    toy = Toy.query.get_or_404(toy_id)

    if request.method == 'GET':
        # Centros actuales asignados al juguete
        current = [c.center for c in ToyCenterAvailability.query.filter_by(toy_id=toy.id).all()]
        return jsonify({'success': True, 'centers': current})

    # POST: actualizar lista de centros
    try:
        if request.is_json:
            payload = request.get_json() or {}
            new_centers = payload.get('centers', []) or []
        else:
            new_centers = request.form.getlist('centers') or []

        # Normalizar (opcional): valores en minúscula para consistencia
        new_centers = [c.strip().lower() for c in new_centers if isinstance(c, str)]

        # Centros actuales
        existing_rows = ToyCenterAvailability.query.filter_by(toy_id=toy.id).all()
        existing = {row.center for row in existing_rows}

        # Eliminar los que ya no están
        to_remove = [row for row in existing_rows if row.center not in set(new_centers)]
        for row in to_remove:
            db.session.delete(row)

        # Agregar nuevos
        to_add = [c for c in new_centers if c not in existing]
        for center in to_add:
            db.session.add(ToyCenterAvailability(toy_id=toy.id, center=center))

        db.session.commit()
        return jsonify({'success': True, 'centers': new_centers})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# NUEVA IMPLEMENTACIÓN: Edición de juguetes simple y robusta
@admin_bp.route('/toy_edit_new/<int:toy_id>', methods=['POST'])
@login_required
@moderate_rate_limit(message="⚠️ Demasiados intentos de edición. Espera un momento.")
def toy_edit_new(toy_id):
    """Nueva implementación simple para editar juguetes"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    toy = Toy.query.get_or_404(toy_id)
    
    if request.method == 'GET':
        # Devolver datos del juguete para el modal
        return jsonify({
            'success': True,
            'toy': {
                'id': toy.id,
                'name': toy.name,
                'description': toy.description,
                'price': float(toy.price),
                'category': toy.category,
                'stock': toy.stock,
                'image_url': url_for('static', filename=toy.image_url)
            }
        })
    
    elif request.method == 'POST':
        try:
            # Log para debugging
            current_app.logger.info(f"Editando juguete {toy_id} - Datos recibidos: {request.form}")
            
            # Actualizar datos básicos
            toy.name = request.form.get('name', toy.name)
            toy.description = request.form.get('description', toy.description)
            toy.price = float(request.form.get('price', toy.price))
            toy.category = request.form.get('category', toy.category)
            toy.stock = int(request.form.get('stock', toy.stock))
            toy.updated_at = datetime.now()
            
            # Guardar cambios
            db.session.commit()
            
            current_app.logger.info(f"Juguete {toy_id} actualizado exitosamente")
            
            # Respuesta para AJAX
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': 'Juguete actualizado exitosamente',
                    'toy': {
                        'id': toy.id,
                        'name': toy.name,
                        'price': float(toy.price),
                        'stock': toy.stock
                    }
                })
            else:
                flash('Juguete actualizado exitosamente', 'success')
                return redirect(url_for('admin.toys_page'))
                
        except Exception as e:
            db.session.rollback()
            error_msg = f"Error al actualizar juguete: {str(e)}"
            current_app.logger.error(error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': False,
                    'message': error_msg
                }), 500
            else:
                flash(error_msg, 'error')
                return redirect(url_for('admin.toys_page'))

@admin_bp.route('/inventory')
@login_required
def inventory_dashboard():
    """Dashboard completo de inventario inteligente"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    if not ADVANCED_SYSTEMS_AVAILABLE:
        flash('Sistema de inventario no disponible', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    try:
        inventory_manager = InventoryManager()
        report = inventory_manager.generate_inventory_report()
        
        return render_template('inventory_dashboard.html',
                             report=report,
                             timestamp=datetime.now())
    except Exception as e:
        flash(f'Error cargando inventario: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))

@admin_bp.route('/inventory/alerts')
@login_required
def inventory_alerts():
    """API endpoint para obtener alertas de inventario"""
    if not current_user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    if not ADVANCED_SYSTEMS_AVAILABLE:
        return jsonify({'error': 'Sistema no disponible'}), 503
    
    try:
        inventory_manager = InventoryManager()
        alerts = inventory_manager.check_low_stock()
        
        return jsonify({
            'alerts': alerts,
            'count': len(alerts),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/orders')
@login_required
def all_orders():
    """Mostrar todas las órdenes con paginación"""
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('shop.index'))
    
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Obtener parámetros de búsqueda y filtrado
    search_query = request.args.get('search', '').strip()
    status_filter = request.args.get('status', 'all')
    
    # Construir consulta base
    query = Order.query
    
    # Aplicar filtros
    if search_query:
        search = f"%{search_query}%"
        query = query.join(User).filter(
            or_(
                Order.id.like(search.replace(' ', '')),  # Buscar por ID de orden
                User.username.ilike(search),              # Buscar por nombre de usuario
                User.email.ilike(search)                  # Buscar por email
            )
        )
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    # Ordenar por fecha más reciente primero
    orders = query.order_by(desc(Order.order_date)).paginate(page=page, per_page=per_page, error_out=False)
    
    # Calcular totales
    total_orders = orders.total
    
    return render_template('admin_orders.html', 
                         orders=orders,
                         search_query=search_query,
                         status_filter=status_filter,
                         total_orders=total_orders)

@admin_bp.route('/inventory/send-alerts', methods=['POST'])
@login_required
def send_inventory_alerts():
    """Enviar alertas de inventario por email"""
    if not current_user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    if not ADVANCED_SYSTEMS_AVAILABLE:
        return jsonify({'error': 'Sistema de inventario no disponible'}), 503
        
    try:
        # Obtener alertas de inventario
        inventory_manager = InventoryManager()
        report = inventory_manager.generate_inventory_report()
        alerts = report['alerts']
        
        # Filtrar solo alertas críticas y de advertencia
        critical_alerts = [a for a in alerts if a['level'] in ['critical', 'warning']]
        
        if not critical_alerts:
            return jsonify({'message': 'No hay alertas críticas para enviar'})
            
        # Aquí iría la lógica para enviar el correo electrónico
        # Por ahora solo simulamos el envío
        email_sent = True  # Simulamos que el correo se envió correctamente
        
        if email_sent:
            return jsonify({
                'message': f'Se enviaron {len(critical_alerts)} alertas por correo electrónico',
                'alerts': critical_alerts
            })
        else:
            return jsonify({'error': 'Error al enviar las alertas'}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error en send_inventory_alerts: {str(e)}")
        return jsonify({'error': str(e)}), 500

@admin_bp.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.dashboard'))
    
    form = AddUserForm()
    if form.validate_on_submit():
        existing_user_username = User.query.filter_by(username=form.username.data).first()
        existing_user_email = User.query.filter_by(email=form.email.data).first()
        
        error = False
        if existing_user_username:
            form.username.errors.append('Este nombre de usuario ya está en uso.')
            error = True
        if existing_user_email:
            form.email.errors.append('Este correo electrónico ya está en uso.')
            error = True
        
        if error:
            flash('Por favor corrige los errores en el formulario.', 'warning')
            return render_template('admin_add_user.html', title='Agregar Usuario', form=form)

        new_user = User(
            username=form.username.data,
            email=form.email.data,
            center=form.center.data,
            is_admin=form.is_admin.data,
            is_active=form.is_active.data
        )
        new_user.set_password(form.password.data)
        
        try:
            db.session.add(new_user)
            db.session.commit()
            flash(f'Usuario {new_user.username} agregado exitosamente.', 'success')
            return redirect(url_for('admin.all_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar usuario: {str(e)}', 'danger')
            current_app.logger.error(f"Error adding user {form.username.data}: {str(e)}")

    return render_template('admin_add_user.html', title='Agregar Usuario', form=form)

@admin_bp.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.dashboard'))

    user_to_edit = User.query.get_or_404(user_id)
    form = EditUserForm(original_username=user_to_edit.username, original_email=user_to_edit.email, obj=user_to_edit)

    if form.validate_on_submit():
        error = False
        if form.username.data != user_to_edit.username:
            if User.query.filter(User.username == form.username.data, User.id != user_id).first():
                form.username.errors.append('Este nombre de usuario ya está en uso por otro usuario.')
                error = True
        
        if form.email.data != user_to_edit.email:
            if User.query.filter(User.email == form.email.data, User.id != user_id).first():
                form.email.errors.append('Este correo electrónico ya está en uso por otro usuario.')
                error = True
            
        if error:
            flash('Por favor corrige los errores en el formulario.', 'warning')
            return render_template('admin_edit_user.html', title='Editar Usuario', form=form, user_id=user_id)

        user_to_edit.username = form.username.data
        user_to_edit.email = form.email.data
        user_to_edit.center = form.center.data
        user_to_edit.is_admin = form.is_admin.data
        user_to_edit.is_active = form.is_active.data
        
        if form.new_password.data:
            user_to_edit.set_password(form.new_password.data)
            
        try:
            db.session.commit()
            flash(f'Usuario {user_to_edit.username} actualizado exitosamente.', 'success')
            return redirect(url_for('admin.all_users'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar usuario: {str(e)}', 'danger')
            current_app.logger.error(f"Error updating user {user_to_edit.username}: {str(e)}")
            
    return render_template('admin_edit_user.html', title='Editar Usuario', form=form, user_id=user_id)

@admin_bp.route('/view_user/<int:user_id>')
@login_required
def view_user(user_id):
    """Muestra los detalles de un usuario específico para administradores."""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('admin.all_users'))

    user = User.query.get_or_404(user_id)
    return render_template('admin_view_user.html', user=user)

# ---------------------- Acciones masivas sobre usuarios ----------------------
@admin_bp.route('/bulk_users_action', methods=['POST'])
@login_required
def bulk_users_action():
    """Procesa acciones masivas (activar, desactivar, eliminar) sobre usuarios seleccionados en la tabla."""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('shop.index'))

    action = request.form.get('action')
    user_ids = request.form.getlist('user_ids')

    if not user_ids:
        flash('No se seleccionó ningún usuario.', 'warning')
        return redirect(url_for('admin.all_users'))

    valid_actions = {'activate', 'deactivate', 'delete'}
    if action not in valid_actions:
        flash('Acción no válida.', 'danger')
        return redirect(url_for('admin.all_users'))

    users_query = User.query.filter(User.id.in_(user_ids))
    affected = 0
    for user in users_query:
        # Prevenir que el admin actual se borre o se desactive a sí mismo
        if user.id == current_user.id and action in {'deactivate', 'delete'}:
            flash('No puedes desactivar o eliminar tu propia cuenta.', 'warning')
            continue

        if action == 'activate':
            if not user.is_active:
                user.is_active = True
                affected += 1
        elif action == 'deactivate':
            if user.is_active:
                user.is_active = False
                affected += 1
        elif action == 'delete':
            db.session.delete(user)
            affected += 1

    try:
        db.session.commit()
        if affected:
            action_map = {
                'activate': 'activados',
                'deactivate': 'desactivados',
                'delete': 'eliminados'
            }
            flash(f'{affected} usuario(s) {action_map[action]} correctamente.', 'success')
        else:
            flash('No se realizaron cambios.', 'info')
    except Exception as e:
        db.session.rollback()
        flash(f'Error al procesar usuarios: {str(e)}', 'danger')

    return redirect(url_for('admin.all_users'))

# ------------------------------
# Export CSV utilities
# ------------------------------
def _generate_csv_response(csv_content: str, filename: str) -> Response:
    """Utility to return a CSV response with appropriate headers."""
    return Response(
        csv_content,
        mimetype='text/csv',
        headers={
            'Content-Disposition': f'attachment; filename="{filename}"'
        }
    )


@admin_bp.route('/export_orders')
@login_required
def export_orders():
    """Exportar todas las órdenes en CSV."""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('shop.index'))

    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)

    # encabezados
    writer.writerow(['ID', 'Fecha', 'Usuario', 'Centro', 'Total', 'Items'])

    orders = Order.query.order_by(Order.order_date.desc()).all()
    for order in orders:
        item_count = sum(item.quantity for item in order.items)
        writer.writerow([
            order.id,
            order.order_date.strftime('%Y-%m-%d %H:%M'),
            order.user.username,
            order.user.center,
            f"{order.total_price:.2f}",
            item_count
        ])

    return _generate_csv_response(output.getvalue(), 'ordenes.csv')


@admin_bp.route('/export_inventory')
@login_required
def export_inventory():
    """Exportar inventario de juguetes en CSV."""
    if not current_user.is_admin:
        flash('Acceso denegado.', 'danger')
        return redirect(url_for('shop.index'))

    import csv, io
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(['ID', 'Nombre', 'Categoría', 'Precio', 'Stock', 'Activo'])

    toys = Toy.query.filter_by(deleted_at=None).order_by(Toy.name.asc()).all()
    for toy in toys:
        writer.writerow([
            toy.id,
            toy.name,
            toy.category,
            f"{toy.price:.2f}",
            toy.stock,
            'Sí' if toy.is_active else 'No'
        ])

    return _generate_csv_response(output.getvalue(), 'inventario.csv')

# ------------------------------
# Ajustar saldo de usuario (Aloha Dólares)
# ------------------------------
@admin_bp.route('/adjust_balance/<int:user_id>', methods=['POST'])
@login_required
def adjust_balance(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403

    user = User.query.get_or_404(user_id)

    try:
        data = request.get_json()
        amount = Decimal(str(data.get('amount', '0')))
        reason = data.get('reason', '')
    except (InvalidOperation, TypeError):
        return jsonify({'error': 'Cantidad inválida'}), 400

    new_balance = user.balance + float(amount)
    if new_balance < 0:
        return jsonify({'error': 'El saldo no puede quedar negativo'}), 400

    user.balance = new_balance

    # TODO: registrar en BalanceLog si se implementa
    try:
        db.session.commit()
        return jsonify({'message': 'Saldo actualizado', 'new_balance': user.balance})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


# ===============================
# 💾 SISTEMA DE BACKUP INTEGRADO
# ===============================

@admin_bp.route('/backup')
@login_required
def backup_dashboard():
    """Dashboard de gestión de backups (solo superuser)"""
    if not current_user.is_admin:
        abort(403)
    
    if not BACKUP_SYSTEM_AVAILABLE:
        flash('⚠️ Sistema de backup no disponible', 'warning')
        return redirect(url_for('admin.dashboard'))
    
    # Obtener lista de backups existentes
    try:
        backup_manager.init_app(current_app)
        backups = backup_manager.list_backups()
    except Exception as e:
        current_app.logger.error(f"Error listing backups: {e}")
        backups = []
        flash('⚠️ Error al listar backups', 'warning')
    
    return render_template('admin_backup.html', backups=backups)

@admin_bp.route('/backup/create', methods=['POST'])
@login_required
@strict_rate_limit(message="⚠️ Solo se permite un backup cada 5 minutos.")
def create_backup():
    """Crear un nuevo backup (solo superuser)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    if not BACKUP_SYSTEM_AVAILABLE:
        return jsonify({'error': 'Sistema de backup no disponible'}), 500
    
    backup_type = request.form.get('backup_type', 'full')
    
    try:
        backup_manager.init_app(current_app)
        result = backup_manager.create_backup(backup_type)
        
        if result:
            current_app.logger.info(f"✅ Backup created by {current_user.username}: {result}")
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({
                    'success': True,
                    'message': f'✅ Backup {backup_type} creado exitosamente',
                    'backup_path': result
                })
            else:
                flash(f'✅ Backup {backup_type} creado exitosamente', 'success')
                return redirect(url_for('admin.backup_dashboard'))
        else:
            error_msg = f'❌ Error al crear backup {backup_type}'
            current_app.logger.error(error_msg)
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'danger')
                return redirect(url_for('admin.backup_dashboard'))
                
    except Exception as e:
        error_msg = f'❌ Error inesperado al crear backup: {str(e)}'
        current_app.logger.error(error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('admin.backup_dashboard'))

@admin_bp.route('/backup/download/<filename>')
@login_required
def download_backup(filename):
    """Descargar un archivo de backup (solo superuser)"""
    if not current_user.is_admin:
        abort(403)
    
    if not BACKUP_SYSTEM_AVAILABLE:
        abort(404)
    
    try:
        backup_manager.init_app(current_app)
        backup_path = backup_manager.backup_dir / filename
        
        if not backup_path.exists() or not backup_path.name.startswith('tiendita_backup_'):
            abort(404)
        
        current_app.logger.info(f"📥 Backup downloaded by {current_user.username}: {filename}")
        
        from flask import send_file
        return send_file(
            backup_path,
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )
        
    except Exception as e:
        current_app.logger.error(f"Error downloading backup: {e}")
        abort(500)

@admin_bp.route('/backup/delete/<filename>', methods=['POST'])
@login_required
@moderate_rate_limit(message="⚠️ Demasiados intentos de eliminación de backup.")
def delete_backup(filename):
    """Eliminar un archivo de backup (solo superuser)"""
    if not current_user.is_admin:
        return jsonify({'error': 'Acceso denegado'}), 403
    
    if not BACKUP_SYSTEM_AVAILABLE:
        return jsonify({'error': 'Sistema de backup no disponible'}), 500
    
    try:
        backup_manager.init_app(current_app)
        backup_path = backup_manager.backup_dir / filename
        
        if not backup_path.exists() or not backup_path.name.startswith('tiendita_backup_'):
            return jsonify({'error': 'Backup no encontrado'}), 404
        
        backup_path.unlink()
        current_app.logger.info(f"🗑️ Backup deleted by {current_user.username}: {filename}")
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'✅ Backup {filename} eliminado exitosamente'
            })
        else:
            flash(f'✅ Backup {filename} eliminado exitosamente', 'success')
            return redirect(url_for('admin.backup_dashboard'))
            
    except Exception as e:
        error_msg = f'❌ Error al eliminar backup: {str(e)}'
        current_app.logger.error(error_msg)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'error': error_msg}), 500
        else:
            flash(error_msg, 'danger')
            return redirect(url_for('admin.backup_dashboard'))
