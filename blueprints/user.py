"""
Blueprint para funcionalidades de usuario
Incluye: perfil, balance, cambio de contraseña, actualización de centro, historial de órdenes
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, abort, current_app
from flask_login import login_required, current_user
from datetime import datetime
from sqlalchemy import desc

# Importaciones absolutas
from app.models import Toy, Order, OrderItem, User
from app.extensions import db
from app.filters import format_currency

# Crear el blueprint de usuario
user_bp = Blueprint('user', __name__, url_prefix='/user')

@user_bp.route('/profile')
@login_required
def profile():
    """Página de perfil del usuario con historial de órdenes"""
    # Obtener las órdenes del usuario ordenadas por fecha descendente
    orders = Order.query.filter_by(user_id=current_user.id).order_by(desc(Order.order_date)).all()
    
    # Formatear las órdenes para la vista
    formatted_orders = []
    for order in orders:
        formatted_orders.append({
            'id': order.id,
            'order_date': order.order_date.strftime('%d/%m/%Y %H:%M'),
            'total': format_currency(order.total_price),
            'status': order.status,
            'item_count': sum(item.quantity for item in order.items)
        })
    
    return render_template('profile.html', orders=formatted_orders)

@user_bp.route('/add_balance', methods=['POST'])
@login_required
def add_balance():
    """Agregar balance al usuario"""
    if not request.form.get('csrf_token'):
        return jsonify({'success': False, 'message': 'CSRF token missing'}), 400
        
    try:
        amount = float(request.form.get('amount', 0))
        if amount <= 0:
            return jsonify({'success': False, 'message': 'Cantidad inválida'}), 400
            
        current_user.balance += amount
        db.session.commit()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({
                'success': True,
                'message': f'Se agregaron A$ {amount:.2f} a tu balance',
                'new_balance': f"A$ {current_user.balance:.2f}"
            })
            
        flash(f'Se agregaron A$ {amount:.2f} a tu balance', 'success')
        return redirect(url_for('user.profile'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar balance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@user_bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    """Cambiar contraseña del usuario"""
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Contraseña actual incorrecta', 'error')
        return redirect(url_for('user.profile'))
    
    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden', 'error')
        return redirect(url_for('user.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Contraseña actualizada correctamente', 'success')
    return redirect(url_for('user.profile'))

@user_bp.route('/update_center', methods=['POST'])
@login_required
def update_center():
    """Actualizar centro del usuario"""
    data = request.get_json()
    new_center = data.get('center')
    
    if new_center:
        current_user.center = new_center
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})

@user_bp.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    """Guardar preferencia de tema del usuario actual."""
    try:
        data = request.get_json() or {}
        theme = (data.get('theme') or '').strip()
        allowed = {
            'aloha-light', 'aloha-dark', 'cherry-blossom', 'underwater', 'halloween', 'patriotic'
        }
        if theme not in allowed:
            return jsonify({'success': False, 'message': 'Tema inválido'}), 400
        current_user.theme = theme
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 400

# Helper function para los templates
def get_toy(toy_id):
    """Helper function to get toy by id"""
    return Toy.query.get(int(toy_id))
