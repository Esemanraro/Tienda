import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.models import User, Toy, Order, OrderItem
from app.config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test'
    LOGIN_DISABLED = False


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        admin = User(username='admin', email='admin@example.com', is_admin=True)
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login_as_admin(client):
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True


def setup_order(app):
    with app.app_context():
        buyer = User(username='buyer', email='buyer@example.com', balance=0.0)
        buyer.set_password('password')
        toy = Toy(name='Dragon Azul', description='Juguete legendario', price=15.0, stock=3)
        db.session.add_all([buyer, toy])
        db.session.commit()

        order = Order(user_id=buyer.id, total_price=30.0, status='completed', is_active=True)
        db.session.add(order)
        db.session.commit()

        item = OrderItem(order_id=order.id, toy_id=toy.id, quantity=2, price=15.0)
        item.is_active = True
        db.session.add(item)
        db.session.commit()

        return order.id, buyer.id, toy.id


def test_delete_order_restores_stock_and_balance(client, app):
    login_as_admin(client)
    order_id, buyer_id, toy_id = setup_order(app)

    response = client.post(f'/admin/orders/{order_id}/delete', follow_redirects=False)
    assert response.status_code in {302, 200}

    with app.app_context():
        toy = Toy.query.get(toy_id)
        buyer = User.query.get(buyer_id)
        order = Order.query.get(order_id)
        item = OrderItem.query.filter_by(order_id=order_id).first()

        assert toy.stock == 5
        assert pytest.approx(buyer.balance, rel=1e-6) == 30.0
        assert order.status == 'cancelled'
        assert order.is_active is False
        assert order.deleted_at is not None
        assert item.is_active is False


def test_delete_order_twice_returns_error(client, app):
    login_as_admin(client)
    order_id, buyer_id, toy_id = setup_order(app)

    first_response = client.post(f'/admin/orders/{order_id}/delete', follow_redirects=False)
    assert first_response.status_code in {302, 200}

    second_response = client.post(f'/admin/orders/{order_id}/delete', follow_redirects=False)
    assert second_response.status_code in {302, 400}

    with app.app_context():
        buyer = User.query.get(buyer_id)
        toy = Toy.query.get(toy_id)
        order = Order.query.get(order_id)

        assert pytest.approx(buyer.balance, rel=1e-6) == 30.0
        assert toy.stock == 5
        assert order.status == 'cancelled'

