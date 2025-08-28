import re
from functools import wraps
from flask import abort, request, current_app, session
from flask_login import current_user
import bleach
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import logging
import pyotp

# Configurar logging básico
logger = logging.getLogger('security')
logger.setLevel(logging.INFO)

# La configuración del FileHandler se moverá a una función
def setup_logging(app):
    if not logger.handlers:
        fh = logging.FileHandler(app.config.get('SECURITY_LOG_FILENAME', 'security.log'))
        fh.setFormatter(logging.Formatter(app.config.get('LOG_FORMAT')))
        logger.addHandler(fh)

def validate_password(password):
    """Valida que la contraseña cumpla con los requisitos mínimos"""
    min_length = 8  # Valor por defecto
    if current_app:
        min_length = current_app.config.get('PASSWORD_MIN_LENGTH', 8)
    
    if len(password) < min_length:
        return False, 'Password too short'
    if not any(c.isupper() for c in password):
        return False, 'Password must contain uppercase letters'
    if not any(c.islower() for c in password):
        return False, 'Password must contain lowercase letters'
    if not any(c.isdigit() for c in password):
        return False, 'Password must contain numbers'
    return True, 'Password valid'

def sanitize_input(text):
    """Sanitiza input de usuario para prevenir XSS"""
    if not text:
        return ''
    clean_text = bleach.clean(text, strip=True)
    return clean_text

def validate_file_content(file):
    """Valida el contenido del archivo subido"""
    if not file:
        return False, 'No file provided'
    if not file.filename:
        return False, 'Invalid filename'
    if not allowed_file(file.filename):
        return False, 'File type not allowed'
    if file.content_length > current_app.config['MAX_CONTENT_LENGTH']:
        return False, 'File too large'
    return True, 'File valid'

def allowed_file(filename):
    """Valida que el tipo de archivo sea permitido"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def validate_age(birth_date):
    """Valida la edad del usuario"""
    today = datetime.now().date()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    if age < current_app.config['MIN_AGE']:
        return False, 'User too young'
    if age > current_app.config['MAX_AGE']:
        return False, 'User too old'
    return True, 'Age valid'

def secure_headers():
    """Retorna headers de seguridad para las respuestas"""
    return current_app.config['SECURITY_HEADERS']

def admin_required(f):
    """Decorador para rutas que requieren acceso de administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            log_security_event('unauthorized_admin_access_attempt', 'User attempted to access admin area')
            abort(403)
        if current_app.config['ADMIN_2FA_REQUIRED'] and not verify_2fa():
            log_security_event('2fa_verification_failed', 'Admin 2FA verification failed')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def generate_2fa_secret():
    """Genera un secreto para autenticación de dos factores"""
    return pyotp.random_base32()

def verify_2fa(token, secret):
    """Verifica un token de autenticación de dos factores"""
    totp = pyotp.TOTP(secret)
    return totp.verify(token)

def check_rate_limit(user_id, action_type):
    """Verifica límites de tasa para diferentes acciones"""
    key = f'{action_type}:{user_id}'
    current_time = datetime.now()
    attempts = session.get(key, [])
    attempts = [ts for ts in attempts if current_time - ts < timedelta(minutes=1)]
    if len(attempts) >= 5:
        return False
    attempts.append(current_time)
    session[key] = attempts
    return True

def validate_transaction(user, amount):
    """Valida una transacción basada en límites y patrones"""
    if amount > current_app.config['MAX_SINGLE_TRANSACTION_AMOUNT']:
        return False, 'Amount exceeds single transaction limit'
    if not user.check_transaction_limits(amount):
        return False, 'Daily transaction limit reached'
    return True, 'Transaction valid'

def log_security_event(event_type, description):
    """Registra eventos de seguridad"""
    logger.info({
        'event_type': event_type,
        'description': description,
        'user_id': current_user.id if current_user.is_authenticated else None,
        'ip_address': request.remote_addr,
        'timestamp': datetime.now().isoformat()
    })

def validate_session():
    """Valida que la sesión esté activa y no haya expirado"""
    if 'last_activity' not in session:
        session['last_activity'] = datetime.now()
        return True
        
    last_activity = session['last_activity']
    if isinstance(last_activity, str):
        last_activity = datetime.fromisoformat(last_activity)
    
    # Permitir 30 minutos de inactividad
    if datetime.now() - last_activity > timedelta(minutes=30):
        return False
    
    return True
