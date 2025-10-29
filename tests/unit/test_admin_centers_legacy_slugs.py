import os
import re
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.config import Config
from app.models import Order, User


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

        admin = User(
            username='admin',
            email='admin@example.com',
            is_admin=True,
            is_active=True,
        )
        admin.set_password('password')
        db.session.add(admin)
        db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def login_as_admin(client, admin_id='1'):
    with client.session_transaction() as session:
        session['_user_id'] = admin_id
        session['_fresh'] = True


def test_legacy_center_slug_is_listed_with_metrics(client, app):
    login_as_admin(client)

    with app.app_context():
        legacy_user = User(
            username='legacy-user',
            email='legacy@example.com',
            is_admin=False,
            is_active=True,
            balance=25.5,
            center='legacy-hub',
        )
        legacy_user.set_password('Password123!')
        db.session.add(legacy_user)
        db.session.flush()

        legacy_order = Order(
            user_id=legacy_user.id,
            subtotal_price=200.0,
            discount_percentage=15.0,
            discount_amount=30.0,
            discounted_total=170.0,
            discount_center='legacy-hub',
            total_price=170.0,
            status='completada',
        )
        db.session.add(legacy_order)
        db.session.commit()

    response = client.get('/admin/centers')
    assert response.status_code == 200

    html = response.get_data(as_text=True)

    assert 'Legacy Hub' in html
    assert 'legacy-hub' in html
    assert 'Solo lectura' in html
    assert 'Centro legado sin registro editable.' in html
    assert 'A$ 25.50' in html
    assert 'A$ 170.00' in html
    assert 'A$ 30.00' in html
    assert re.search(r"Centros activos</span>\s*<span class=\"stat-value\">1</span>", html)
