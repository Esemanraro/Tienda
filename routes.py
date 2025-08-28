import os
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify, current_app
from flask_login import login_user, login_required, logout_user, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DecimalField, IntegerField, SelectField, FileField, TextAreaField
from wtforms.validators import DataRequired, Length, NumberRange
from models import User, Toy, Order, OrderItem
from extensions import db
from datetime import datetime, timedelta
from forms import ToyForm

# Crear el blueprint
bp = Blueprint('main', __name__)

# Formularios
class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    center = StringField('Center', validators=[DataRequired()])

@bp.route('/')
@bp.route('/index')
def index():
    toys = Toy.query.filter_by(is_active=True).all()
    return render_template('index.html', toys=toys)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        print("Usuario ya autenticado, redirigiendo a index")
        return redirect(url_for('main.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        print(f"Intentando login con usuario: {form.username.data}")
        user = User.query.filter_by(username=form.username.data).first()
        
        if user:
            print(f"Usuario encontrado: {user.username}")
            if user.check_password(form.password.data):
                print("Contraseña correcta, iniciando sesión")
                user.last_login = datetime.now()
                db.session.commit()
                
                if login_user(user, remember=True):
                    print("Login exitoso")
                    flash('¡Bienvenido de nuevo!', 'success')
                    return redirect(url_for('main.index'))
                else:
                    print("Error en login_user")
                    flash('Error al iniciar sesión', 'error')
            else:
                print("Contraseña incorrecta")
                flash('Contraseña incorrecta', 'error')
        else:
            print("Usuario no encontrado")
            flash('Usuario no encontrado', 'error')
    
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash('El nombre de usuario ya existe')
            return redirect(url_for('main.register'))
        
        user = User(
            username=form.username.data,
            center=form.center.data,
            balance=0.0,
            created_at=datetime.now(),
            last_login=datetime.now()
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        
        flash('¡Registro exitoso! Ahora puedes iniciar sesión')
        return redirect(url_for('main.login'))
    
    return render_template('register.html', form=form)

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@bp.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Acceso denegado', 'error')
        return redirect(url_for('main.index'))
    
    toy_form = ToyForm() # Crear instancia del formulario
    
    # Obtener estadísticas
    sales_stats = {
        'total_sales': 0,
        'total_orders': 0,
        'total_users': 0,
        'sales_by_category': []
    }
    
    try:
        # Total de ventas
        sales_stats['total_sales'] = db.session.query(
            db.func.sum(Order.total_price)
        ).filter(Order.is_active == True).scalar() or 0
        
        # Total de órdenes
        sales_stats['total_orders'] = Order.query.filter_by(
            is_active=True
        ).count()
        
        # Total de usuarios
        sales_stats['total_users'] = User.query.filter_by(
            is_active=True
        ).count()
        
        # Ventas por categoría
        sales_by_category = db.session.query(
            Toy.category,
            db.func.count(OrderItem.id).label('quantity'),
            db.func.sum(OrderItem.price * OrderItem.quantity).label('amount')
        ).join(OrderItem).join(Order).filter(
            Order.is_active == True
        ).group_by(Toy.category).all()
        
        sales_stats['sales_by_category'] = [
            {
                'category': cat,
                'quantity': qty,
                'amount': amt or 0
            } for cat, qty, amt in sales_by_category
        ]
        
    except Exception as e:
        print(f"Error al obtener estadísticas: {str(e)}")
        flash('Error al cargar estadísticas', 'error')
    
    # Obtener órdenes recientes
    recent_orders = Order.query.filter_by(
        is_active=True
    ).order_by(Order.order_date.desc()).limit(5).all()
    
    # Obtener usuarios recientes
    recent_users = User.query.filter_by(
        is_active=True
    ).order_by(User.created_at.desc()).limit(5).all()
    
    # Obtener todos los juguetes
    toys = Toy.query.filter_by(is_active=True).order_by(Toy.created_at.desc()).all()
    
    # Datos para el gráfico
    dates = []
    sales_data = []
    try:
        # Ventas de los últimos 7 días
        for i in range(7):
            date = datetime.now() - timedelta(days=i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            daily_sales = db.session.query(
                db.func.sum(Order.total_price)
            ).filter(
                Order.is_active == True,
                db.func.date(Order.order_date) == date.date()
            ).scalar() or 0
            
            sales_data.append(daily_sales)
        
        # Invertir las listas para mostrar en orden cronológico
        dates.reverse()
        sales_data.reverse()
        
    except Exception as e:
        print(f"Error al obtener datos del gráfico: {str(e)}")
        dates = []
        sales_data = []
    
    return render_template(
        'admin_dashboard.html',
        sales_stats=sales_stats,
        recent_orders=recent_orders,
        recent_users=recent_users,
        dates=dates,
        sales_data=sales_data,
        toy_form=toy_form,  # Pasar el formulario a la plantilla
        toys=toys  # Pasar la lista de juguetes
    )

@bp.route('/add_toy', methods=['POST'])
@login_required
def add_toy():
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
            
            # Crear nuevo juguete
            new_toy = Toy(
                name=toy_form.name.data,
                description=toy_form.description.data,
                price=toy_form.price.data,
                category=toy_form.category.data,
                stock=toy_form.stock.data,
                image_url=image_filename
            )
            
            db.session.add(new_toy)
            db.session.commit()
            flash('¡Juguete agregado exitosamente!', 'success')
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al agregar el juguete: {str(e)}', 'error')
    else:
        for field, errors in toy_form.errors.items():
            for error in errors:
                flash(f'Error en {field}: {error}', 'error')
    
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/edit_toy/<int:toy_id>', methods=['GET', 'POST'])
@login_required
def edit_toy(toy_id):
    toy = Toy.query.get_or_404(toy_id)
    toy_form = ToyForm(obj=toy)
    
    if request.method == 'POST' and toy_form.validate_on_submit():
        try:
            # Manejar la imagen si se subió una nueva
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
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al actualizar el juguete: {str(e)}', 'error')
        
        return redirect(url_for('main.admin_dashboard'))
    
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

@bp.route('/delete_toy/<int:toy_id>', methods=['POST'])
@login_required
def delete_toy(toy_id):
    try:
        toy = Toy.query.get_or_404(toy_id)
        
        # Eliminar imagen si existe
        if toy.image_url:
            image_path = os.path.join(current_app.static_folder, toy.image_url)
            if os.path.exists(image_path):
                os.remove(image_path)
        
        # Soft delete: marcar como eliminado en lugar de eliminar físicamente
        toy.deleted_at = datetime.now()
        toy.is_active = False
        
        db.session.commit()
        flash('¡Juguete eliminado exitosamente!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error al eliminar el juguete: {str(e)}', 'error')
    
    return redirect(url_for('main.admin_dashboard'))

@bp.route('/search')
def search():
    query = request.args.get('query', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'name')
    
    toys = Toy.query.filter_by(is_active=True)
    
    if query:
        toys = toys.filter(Toy.name.ilike(f'%{query}%'))
    if category:
        toys = toys.filter(Toy.category == category)
    
    if sort == 'price_low':
        toys = toys.order_by(Toy.price.asc())
    elif sort == 'price_high':
        toys = toys.order_by(Toy.price.desc())
    else:
        toys = toys.order_by(Toy.name.asc())
    
    toys = toys.all()
    return render_template('search.html', toys=toys)

@bp.route('/add_to_cart/<int:toy_id>', methods=['POST'])
@login_required
def add_to_cart(toy_id):
    """Agregar un juguete al carrito"""
    try:
        toy = Toy.query.get_or_404(toy_id)
        
        if 'cart' not in session:
            session['cart'] = {}
        
        toy_id_str = str(toy_id)
        
        if toy_id_str in session['cart']:
            session['cart'][toy_id_str]['quantity'] += 1
        else:
            session['cart'][toy_id_str] = {
                'quantity': 1,
                'price': float(toy.price)
            }
        
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': '¡Producto agregado al carrito!',
            'cart_count': sum(item['quantity'] for item in session['cart'].values())
        })
        
    except Exception as e:
        print(f"Error al agregar al carrito: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al agregar el producto al carrito'
        }), 400

@bp.route('/view_cart')
@login_required
def view_cart():
    """Ver el contenido del carrito"""
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
    
    return render_template('cart.html', cart_items=cart_items, total=total)

@bp.route('/remove_from_cart/<int:toy_id>', methods=['POST'])
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

@bp.route('/update_cart/<int:toy_id>', methods=['POST'])
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

@bp.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    if 'cart' not in session or not session['cart']:
        flash('Tu carrito está vacío', 'error')
        return redirect(url_for('main.view_cart'))
    
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
        return redirect(url_for('main.view_cart'))
    
    if request.method == 'POST':
        # Verificar balance
        if current_user.balance < total:
            flash('No tienes suficientes ALOHA Dollars', 'error')
            return redirect(url_for('main.view_cart'))
        
        try:
            # Crear la orden
            order = Order(
                user_id=current_user.id,
                total_price=total,
                order_date=datetime.now()
            )
            db.session.add(order)
            
            # Agregar items a la orden
            for toy_id, item in session['cart'].items():
                order_item = OrderItem(
                    order=order,
                    toy_id=int(toy_id),
                    quantity=item['quantity'],
                    price=item['price']
                )
                db.session.add(order_item)
            
            # Actualizar balance del usuario
            current_user.balance -= total
            
            # Guardar cambios y limpiar carrito
            db.session.commit()
            session.pop('cart', None)
            
            flash('¡Compra realizada con éxito!', 'success')
            return redirect(url_for('main.order_summary', order_id=order.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Error al procesar la compra: {str(e)}")
            flash('Error al procesar la compra', 'error')
            return redirect(url_for('main.view_cart'))
    
    return render_template('checkout.html', 
                         cart_items=cart_items, 
                         total=total)

@bp.route('/order/<int:order_id>')
@login_required
def order_summary(order_id):
    order = Order.query.get_or_404(order_id)
    if order.user_id != current_user.id and not current_user.is_admin:
        flash('No tienes permiso para ver esta orden', 'error')
        return redirect(url_for('main.index'))
    return render_template('order_summary.html', order=order)

@bp.route('/add_balance', methods=['POST'])
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
        return redirect(url_for('main.profile'))
        
    except Exception as e:
        db.session.rollback()
        print(f"Error al agregar balance: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

# Helper function para los templates
def get_toy(toy_id):
    """Helper function to get toy by id"""
    return Toy.query.get(int(toy_id))

@bp.route('/change_password', methods=['POST'])
@login_required
def change_password():
    current_password = request.form.get('current_password')
    new_password = request.form.get('new_password')
    confirm_password = request.form.get('confirm_password')
    
    if not current_user.check_password(current_password):
        flash('Contraseña actual incorrecta', 'error')
        return redirect(url_for('main.profile'))
    
    if new_password != confirm_password:
        flash('Las contraseñas nuevas no coinciden', 'error')
        return redirect(url_for('main.profile'))
    
    current_user.set_password(new_password)
    db.session.commit()
    flash('Contraseña actualizada correctamente', 'success')
    return redirect(url_for('main.profile'))

@bp.route('/update_center', methods=['POST'])
@login_required
def update_center():
    data = request.get_json()
    new_center = data.get('center')
    
    if new_center:
        current_user.center = new_center
        db.session.commit()
        return jsonify({'success': True})
    
    return jsonify({'success': False})
