import os, sys
sys.path.insert(0, os.getcwd())
from app import create_app, db
from app.models import User, Order, OrderItem, Toy
from datetime import datetime

app = create_app()
app.config['TESTING']=True
app.config['WTF_CSRF_ENABLED']=False

with app.app_context():
    db.create_all()
    # Ensure admin exists
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', email='admin@example.com', is_admin=True, center='david', is_active=True)
        admin.set_password('admin123')
        db.session.add(admin)
        db.session.commit()

    client = app.test_client()
    client.post('/auth/login', data={'username':'admin','password':'admin123'}, follow_redirects=True)

    # Ensure at least one order exists
    toy = Toy.query.first()
    if not toy:
        toy = Toy(name='Dummy', description='Test', price=5.0, stock=10)
        db.session.add(toy); db.session.commit()
    order = Order(user_id=admin.id, order_date=datetime.now(), total_price=5.0, status='completada')
    db.session.add(order); db.session.flush()
    db.session.add(OrderItem(order_id=order.id, toy_id=toy.id, quantity=1, price=5.0))
    db.session.commit()

    r = client.get('/admin/orders')
    print('ORDERS', r.status_code)
    print(r.data[:120])

    # Test receipt
    r2 = client.get(f'/admin/orders/{order.id}/receipt')
    print('RECEIPT', r2.status_code, r2.headers.get('Content-Disposition'))
