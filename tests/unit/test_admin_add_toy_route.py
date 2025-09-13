import io
import os
import sys
import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.models import User, Toy
from app.config import Config


class TestConfig(Config):
    TESTING = True
    WTF_CSRF_ENABLED = False
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SECRET_KEY = 'test'
    LOGIN_DISABLED = False  # We'll simulate login


@pytest.fixture()
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # create admin user
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


def login_as_admin(client, app):
    with client.session_transaction() as sess:
        sess['_user_id'] = '1'
        sess['_fresh'] = True


def test_add_toy_redirects_to_inventory(client, app):
    login_as_admin(client, app)
    data = {
        'name': 'Muñeco Ñandú',
        'description': 'Juguete con acentos: á, é, í, ó, ú y la letra ñ',
        'price': '9.99',
        'toy_type': 'Otro',
        'gender': 'Mixto',
        'age_range': '4-6',
        'stock': '5'
    }
    response = client.post('/admin/toys/add', data=data, follow_redirects=False)
    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/toys')
    with app.app_context():
        toy = Toy.query.filter_by(name='Muñeco Ñandú').first()
        assert toy is not None
        assert toy.price == 9.99
        assert 'ñ' in toy.name
        assert 'á' in toy.description
