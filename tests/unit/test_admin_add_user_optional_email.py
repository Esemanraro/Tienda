import os
import sys

import pytest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from app import create_app, db
from app.config import Config
from app.models import User


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
        admin = User(username='admin', email='admin@example.com', is_admin=True, center='david', is_active=True)
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
    with client.session_transaction() as session:
        session['_user_id'] = '1'
        session['_fresh'] = True


def test_admin_can_create_user_without_email(client, app):
    login_as_admin(client)

    form_data = {
        'username': 'student-no-email',
        'email': '',
        'center': 'david',
        'balance': '',
        'password': 'Temp1234',
        'confirm_password': 'Temp1234',
        'require_password_change': 'y',
        'is_admin': '',
        'is_active': 'y',
    }

    response = client.post('/admin/add_user', data=form_data, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/users')

    with app.app_context():
        created_user = User.query.filter_by(username='student-no-email').first()
        assert created_user is not None
        assert created_user.email is None
        assert created_user.must_change_password is True


def test_admin_rejects_duplicate_email_case_insensitive(client, app):
    login_as_admin(client)

    with app.app_context():
        existing_user = User(username='student', email='student@example.com', center='david', is_active=True)
        existing_user.set_password('Password123')
        db.session.add(existing_user)
        db.session.commit()

    form_data = {
        'username': 'student-duplicate-email',
        'email': 'Student@Example.COM',
        'center': 'david',
        'balance': '',
        'password': 'Temp1234',
        'confirm_password': 'Temp1234',
        'require_password_change': 'y',
        'is_admin': '',
        'is_active': 'y',
    }

    response = client.post('/admin/add_user', data=form_data, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/users')

    with app.app_context():
        assert User.query.filter_by(username='student-duplicate-email').first() is None
        assert User.query.count() == 2  # admin + existing user


def test_admin_normalizes_email_before_save(client, app):
    login_as_admin(client)

    form_data = {
        'username': 'student-normalized-email',
        'email': 'NewStudent@Example.COM ',
        'center': 'david',
        'balance': '',
        'password': 'Temp1234',
        'confirm_password': 'Temp1234',
        'require_password_change': 'y',
        'is_admin': '',
        'is_active': 'y',
    }

    response = client.post('/admin/add_user', data=form_data, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers['Location'].endswith('/admin/users')

    with app.app_context():
        created_user = User.query.filter_by(username='student-normalized-email').first()
        assert created_user is not None
        assert created_user.email == 'newstudent@example.com'
