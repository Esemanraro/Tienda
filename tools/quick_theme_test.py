import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models import User

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    c = app.test_client()
    # ensure admin login
    u = User.query.filter_by(username='admin').first()
    if not u:
        u = User(username='admin', email='admin@example.com', is_admin=True)
        u.set_password('admin123')
        db.session.add(u); db.session.commit()
    c.post('/auth/login', data={'username':'admin','password':'admin123'})
    r = c.post('/user/update_theme', json={'theme':'patriotic'})
    print('update theme', r.status_code, r.get_json())
    # reload user
    u2 = User.query.filter_by(username='admin').first()
    print('stored theme:', u2.theme)
