from backend.app import app
from backend.extensions import db
from backend.models import User
from werkzeug.security import generate_password_hash as g

with app.app_context():
    db.create_all()
    if not User.query.filter_by(email="admin@example.com").first():
        db.session.add(
            User(name="Admin",
                 email="admin@example.com",
                 password_hash=g("examplepass"))
        )
        db.session.commit()
        print("seeded")
    else:
        print("user already exists")
