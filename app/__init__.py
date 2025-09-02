"""
Factory de la aplicación Tiendita ALOHA.
Este módulo crea y configura la aplicación Flask.
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, session, redirect, url_for
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache

# Extensiones compartidas
from .extensions import db, migrate, login_manager

# Modelos y utilidades
from . import models as models  # register once; access via models.User / models.Toy
from .security import secure_headers, log_security_event  # validate_session no se usa aquí

# Inicializadores locales (no crear nuevas instancias globales de db/migrate aquí)
csrf = CSRFProtect()
cache = Cache()

# Flask-Login: configuración base
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'


# -------- Helpers / filtros que estaban en app/app.py --------

def format_currency_value(value):
    """Formatea un número como moneda (A$) — versión interna para Jinja/global."""
    if value is None:
        return "A$ 0.00"
    try:
        return f"A$ {float(value):.2f}"
    except (ValueError, TypeError):
        return "A$ 0.00"


def get_toy(toy_id):
    try:
        return models.Toy.query.get(int(toy_id))
    except (ValueError, TypeError):
        return None


@login_manager.user_loader
def load_user(user_id):
    try:
        return models.User.query.get(int(user_id))
    except Exception:
        return None


def create_app(config_class=None):
    """Crea y configura la aplicación Flask."""
    # Directorios de templates/static (como tenías en tu factory)
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))

    app = Flask(
        __name__,
        template_folder=template_dir,
        static_folder=static_dir,
        static_url_path='/static'
    )

    # Dev: autoreload de templates
    app.config['TEMPLATES_AUTO_RELOAD'] = True

    # Cargar configuración
    if config_class is None:
        if os.environ.get('FLASK_ENV') == 'production':
            from .config import ProductionConfig
            config_class = ProductionConfig
        else:
            from .config import DevelopmentConfig
            config_class = DevelopmentConfig

    app.config.from_object(config_class)

    # Seguridad de cookies
    app.config.setdefault('SESSION_COOKIE_HTTPONLY', True)
    app.config.setdefault('SESSION_COOKIE_SAMESITE', 'Lax')
    if app.config.get('ENV') == 'production':
        app.config['SESSION_COOKIE_SECURE'] = True

    # Logging de seguridad (como en app/app.py)
    logging.basicConfig(
        filename=app.config.get('SECURITY_LOG_FILENAME', 'security.log'),
        level=logging.INFO,
        format=app.config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # -------- Inicializar extensiones --------
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Cache/Redis: usar Redis si existe, si no SimpleCache (evita warnings en dev)
    try:
        from redis import Redis
        import rq
        app.redis = Redis.from_url(app.config['REDIS_URL'])
        app.task_queue = rq.Queue('aloha-tasks', connection=app.redis)
        cache.init_app(app, config={'CACHE_TYPE': 'redis', 'CACHE_REDIS_URL': app.config['REDIS_URL']})
    except Exception as e:
        print("⚠️ No Redis; usando SimpleCache:", e)
        app.redis = None
        app.task_queue = None
        cache.init_app(app, config={'CACHE_TYPE': 'SimpleCache'})

    # -------- Middleware de seguridad (migrado desde app/app.py) --------
    @app.before_request
    def _before_request():
        # omitir archivos estáticos
        if request.endpoint and 'static' in request.endpoint:
            return

        # rutas públicas
        public_routes = ['auth.login', 'auth.register', 'shop.index', 'shop.search', 'static']

        # permitir rutas públicas
        if request.endpoint and request.endpoint in public_routes:
            return

        # exigir autenticación
        if not current_user.is_authenticated:
            print(f"Usuario no autenticado intentando acceder a: {request.endpoint}")
            return redirect(url_for('auth.login'))

        # actualizar timestamp de sesión
        session['last_activity'] = datetime.now()
        return None

    @app.after_request
    def _after_request(response):
        # Cabeceras de seguridad
        headers = secure_headers()

        # CSP relajada para permitir inline en este proyecto
        headers['Content-Security-Policy'] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "img-src 'self' data:; style-src 'self' 'unsafe-inline';"
        )
        for k, v in headers.items():
            response.headers[k] = v
        return response

    # -------- Blueprints --------
    # Nota: import absoluto de paquetes hermanos; ejecutar siempre desde el root del proyecto
    from blueprints.auth import auth_bp
    from blueprints.shop import shop_bp
    from blueprints.admin import admin_bp
    from blueprints.user import user_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(shop_bp, url_prefix='/')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(user_bp, url_prefix='/user')

    # -------- Filtros / globals para Jinja --------
    # Mantener tus filtros de .filters si existen
    try:
        from .filters import format_currency, format_date
        app.add_template_global(format_currency, name='format_currency')
        app.add_template_global(format_date, name='format_date')
        app.jinja_env.filters['format_currency'] = format_currency
        app.jinja_env.filters['format_date'] = format_date
    except Exception:
        # Fallback a la función local si no existe .filters
        app.add_template_global(format_currency_value, name='format_currency')
        app.jinja_env.filters['format_currency'] = format_currency_value

    # Exponer get_toy globalmente (lo tenías en app/app.py)
    app.jinja_env.globals.update(get_toy=get_toy)

    # Context processor global para cart_count (ya lo tenías)
    @app.context_processor
    def inject_cart_count():
        cart_count = 0
        if 'cart' in session and isinstance(session['cart'], dict):
            cart_count = sum(item.get('quantity', 0) for item in session['cart'].values())
        return dict(cart_count=cart_count)

    # -------- Manejadores de error --------
    # Mantén los tuyos existentes y añade 400 que usabas en app/app.py
    try:
        from .errors import page_not_found, internal_server_error, forbidden
        app.register_error_handler(404, page_not_found)
        app.register_error_handler(500, internal_server_error)
        app.register_error_handler(403, forbidden)
    except Exception:
        # Registro mínimo si no hay módulo errors
        @app.errorhandler(403)
        def _forbidden(e):
            log_security_event('forbidden_access', getattr(e, "description", "Forbidden"))
            return "Access forbidden.", 403

    @app.errorhandler(400)
    def _bad_request(e):
        log_security_event('bad_request', getattr(e, "description", "Bad request"))
        return "Bad request.", 400

    # -------- Ruta de prueba de CSP (opcional, solo dev) --------
    @app.route('/test_csp')
    def test_csp():
        resp = app.make_response("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Test CSP</title>
            <meta http-equiv="Content-Security-Policy"
                  content="default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:; style-src 'self' 'unsafe-inline';">
            <script>
                document.addEventListener('DOMContentLoaded', function() {
                    console.log('Script ejecutado correctamente');
                    document.body.innerHTML += '<p>Script ejecutado correctamente</p>';
                });
            </script>
        </head>
        <body>
            <h1>Prueba de CSP</h1>
            <p>Si ves este mensaje, la página se cargó correctamente.</p>
            <button onclick="alert('¡Hola!')">Haz clic aquí</button>
        </body>
        </html>
        """)
        resp.headers['Content-Security-Policy'] = (
            "default-src 'self' 'unsafe-inline' 'unsafe-eval'; img-src 'self' data:; style-src 'self' 'unsafe-inline';"
        )
        return resp

    # Crear tablas si no existen (desarrollo)
    with app.app_context():
        db.create_all()

    # Debug: ver a qué DB apunta
    try:
        print(f"DEBUG: SQLALCHEMY_DATABASE_URI = {app.config['SQLALCHEMY_DATABASE_URI']}")
    except Exception:
        pass

    return app
