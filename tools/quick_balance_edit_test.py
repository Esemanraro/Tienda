import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    c = app.test_client()
    c.post('/auth/login', data={'username':'admin','password':'admin123'})
    r = c.post('/admin/users/9/balance', json={'balance': 77.25})
    print('BAL', r.status_code, r.get_json())
