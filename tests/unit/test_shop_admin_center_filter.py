import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.config import Config
from app.models import Center, Toy, ToyCenterAvailability, User


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

        north_center = Center(slug='north-hub', name='North Hub', discount_percentage=0)
        south_center = Center(slug='south-hub', name='South Hub', discount_percentage=0)
        db.session.add_all([north_center, south_center])

        global_toy = Toy(name='Global Toy', description='All centers', price=10.0, category='General', stock=5)
        north_toy = Toy(name='North Toy', description='North only', price=12.0, category='General', stock=3)
        south_toy = Toy(name='South Toy', description='South only', price=12.0, category='General', stock=3)
        db.session.add_all([global_toy, north_toy, south_toy])
        db.session.flush()

        north_toy.centers.append(ToyCenterAvailability(center='north-hub'))
        south_toy.centers.append(ToyCenterAvailability(center='south-hub'))

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


def test_admin_center_filter_includes_global_toys(client):
    login_as_admin(client)
    response = client.get('/search', query_string={'center': 'North-Hub'})

    assert response.status_code == 200
    html = response.data.decode('utf-8')

    assert 'North Toy' in html
    assert 'Global Toy' in html
    assert 'South Toy' not in html
    assert '<option value="north-hub" selected' in html
