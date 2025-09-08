import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models import User

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    client = app.test_client()
    rv = client.post('/auth/login', data={'username':'tempuser1','password':'Temp1234'}, follow_redirects=True)
    print('LOGIN-USER', rv.status_code)
    print(rv.data[:120])
