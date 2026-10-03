"""Create the first administrator account on a fresh installation."""
from getpass import getpass

from sqlalchemy import select

from app.database import Base, SessionLocal, engine
from app.models import User
from app.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    if db.scalar(select(User.id).limit(1)):
        raise SystemExit("An account already exists. Ask an administrator to create staff accounts via POST /auth/users.")
    name = input("Administrator full name: ").strip()
    email = input("Administrator email: ").strip().lower()
    password = getpass("Password (at least 8 characters): ")
    if len(name) < 2 or "@" not in email or len(password) < 8:
        raise SystemExit("Please enter a name, valid-looking email, and password of at least 8 characters.")
    db.add(User(full_name=name, email=email, password_hash=hash_password(password), role="admin"))
    db.commit()
    print(f"Administrator created: {email}")
finally:
    db.close()
