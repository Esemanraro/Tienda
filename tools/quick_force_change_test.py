import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app, db

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    client = app.test_client()
    client.post('/auth/login', data={'username':'tempuser1','password':'Temp1234'})
    r = client.get('/user/profile', follow_redirects=False)
    print('PROFILE status', r.status_code, 'Location:', r.headers.get('Location'))
    # Now change password
    r2 = client.post('/auth/force_password_change', data={'new_password':'NewStrong1','confirm_password':'NewStrong1'}, follow_redirects=True)
    print('CHANGE status', r2.status_code)
