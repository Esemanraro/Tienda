import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.config import Config
from app.models import Center, User


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
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(app):
    return app.test_client()


def test_register_normalizes_email_before_save(client, app):
    with app.app_context():
        center = Center(slug='david', name='David', discount_percentage=0)
        db.session.add(center)
        db.session.commit()

    form_data = {
        'username': 'newuser',
        'email': 'NewUser@Example.COM ',
        'password': 'Password123',
        'center': 'david',
    }

    response = client.post('/auth/register', data=form_data, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')

    with app.app_context():
        created_user = User.query.filter_by(username='newuser').first()
        assert created_user is not None
        assert created_user.email == 'newuser@example.com'


def test_register_rejects_duplicate_email_case_insensitive(client, app):
    with app.app_context():
        existing_user = User(
            username='existing',
            email='existing@example.com',
            center='david',
            is_admin=False,
            is_active=True,
        )
        existing_user.set_password('Existing123')
        db.session.add(existing_user)
        db.session.commit()

    form_data = {
        'username': 'anotheruser',
        'email': 'Existing@Example.COM',
        'password': 'Password123',
        'center': 'david',
    }

    response = client.post('/auth/register', data=form_data, follow_redirects=False)

    assert response.status_code == 200

    with app.app_context():
        assert User.query.count() == 1
        assert User.query.filter_by(username='anotheruser').first() is None


def test_register_accepts_legacy_only_center_slug(client, app):
    legacy_slug = 'legacy-only-center'

    with app.app_context():
        # Seed legacy data without creating a Center row.
        assert Center.query.filter_by(slug=legacy_slug).first() is None

        legacy_user = User(
            username='legacy_seed',
            email='legacy-seed@example.com',
            center=legacy_slug,
            is_admin=False,
            is_active=True,
        )
        legacy_user.set_password('LegacySeed123')
        db.session.add(legacy_user)
        db.session.commit()

    form_data = {
        'username': 'legacy_new_user',
        'email': 'legacy_new@example.com',
        'password': 'Password123',
        'center': legacy_slug,
    }

    response = client.post('/auth/register', data=form_data, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/auth/login')

    with app.app_context():
        created_user = User.query.filter_by(username='legacy_new_user').first()
        assert created_user is not None
        assert created_user.center == legacy_slug
