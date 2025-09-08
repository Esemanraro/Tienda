import os, sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app, db

app = create_app()
app.config['TESTING'] = True
app.config['WTF_CSRF_ENABLED'] = False

with app.app_context():
    db.create_all()
    client = app.test_client()

    # Unique data per run
    import time
    suffix = str(int(time.time()))
    username = f"user_{suffix}"
    email = f"user_{suffix}@example.com"

    first = client.post('/auth/register', data={
        'username': username,
        'email': email,
        'password': 'StrongPass1',
        'center': 'costa del este'
    }, follow_redirects=False)

    print('FIRST', first.status_code, first.headers.get('Location'))

    # Try duplicate email with different username
    dup = client.post('/auth/register', data={
        'username': username + 'x',
        'email': email,
        'password': 'StrongPass1',
        'center': 'costa del este'
    }, follow_redirects=False)

    print('DUP', dup.status_code)
    # Show a snippet to confirm form returned (not a 500)
    print(dup.data[:120])
