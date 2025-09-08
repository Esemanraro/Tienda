import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models import User

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    db.create_all()
    # Ensure admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True, center='David', is_active=True, balance=100.0)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    client = app.test_client()
    # Login
    rv = client.post('/auth/login', data={'username':'admin','password':'admin123'}, follow_redirects=True)
    print('LOGIN', rv.status_code)

    # Add user via AJAX
    data = {
        'username':'tempuser1','email':'temp1@example.com','center':'david','balance':'12.5','password':'Temp1234','confirm_password':'Temp1234','require_password_change':'y','is_admin':'','is_active':'y'
    }
    add = client.post('/admin/add_user', data=data, headers={'X-Requested-With':'XMLHttpRequest'})
    print('ADD', add.status_code, add.is_json, add.get_json())

    # New user must change password flag?
    u = User.query.filter_by(username='tempuser1').first()
    print('USER', bool(getattr(u,'must_change_password', False)), u.balance)

