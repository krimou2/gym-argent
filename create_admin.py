from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            full_name='Admin User',
            role='admin',
            specialty=None
        )
        admin.set_password('krimou1234')  # Change this!
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    else:
        print("Admin user already exists")