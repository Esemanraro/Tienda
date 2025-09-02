import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from app import create_app

app = create_app()

def main():
    with app.test_client() as c:
        r = c.get('/search')
        print('status', r.status_code)
        print(r.data[:200])

if __name__ == '__main__':
    main()
