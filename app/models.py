from .extensions import db
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import CheckConstraint
from flask_login import UserMixin

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    # Force password reset on first login or when set by admin
    must_change_password = db.Column(db.Boolean, default=False)
    balance = db.Column(db.Float, default=0.0)
    # User selected UI theme (site-wide), e.g., 'aloha-light', 'aloha-dark', 'patriotic'
    theme = db.Column(db.String(32), nullable=True, index=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    last_login = db.Column(db.DateTime)
    center = db.Column(db.String(64), index=True)
    profile_pic = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (CheckConstraint('balance >= 0'),)
    
    # Relaciones
    orders = db.relationship('Order', backref='user', lazy='select', cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        return str(self.id)
        
    def to_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Toy(db.Model):
    __tablename__ = 'toy'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Unicode(100), nullable=False, index=True)
    description = db.Column(db.UnicodeText)
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))
    # Categoria de Juguete (tipo)
    category = db.Column(db.Unicode(50), index=True)
    # Categoria de Edad (rango)
    age_range = db.Column(db.Unicode(20), index=True)
    # Categoria de Genero
    gender_category = db.Column(db.Unicode(20), index=True)
    stock = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (CheckConstraint('price > 0'),)
    
    # Relaciones
    order_items = db.relationship('OrderItem', backref='toy', lazy=True)
    # Centros en los que el juguete está disponible (many-to-many simplificado)
    centers = db.relationship(
        'ToyCenterAvailability',
        backref='toy',
        lazy='select',
        cascade='all, delete-orphan'
    )

class Order(db.Model):
    __tablename__ = 'order'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    total_price = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='completada', nullable=False)  # completada, en_proceso, cancelada
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    deleted_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relaciones
    items = db.relationship('OrderItem', backref='order', lazy='select', cascade='all, delete-orphan')

class OrderItem(db.Model):
    __tablename__ = 'order_item'
    
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id', ondelete='CASCADE'), nullable=False)
    toy_id = db.Column(db.Integer, db.ForeignKey('toy.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, onupdate=datetime.now)
    is_active = db.Column(db.Boolean, default=True)
    
    __table_args__ = (CheckConstraint('quantity > 0'),)


class ToyCenterAvailability(db.Model):
    __tablename__ = 'toy_center_availability'

    id = db.Column(db.Integer, primary_key=True)
    toy_id = db.Column(
        db.Integer,
        db.ForeignKey('toy.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    # Mantener centros como texto para alinear con User.center
    center = db.Column(db.Unicode(64), nullable=False, index=True)

    __table_args__ = (
        db.UniqueConstraint('toy_id', 'center', name='uq_toy_center'),
    )
