from typing import Optional

from flask_httpauth import HTTPBasicAuth

from .database import create_session
from .models import User

auth: HTTPBasicAuth = HTTPBasicAuth()


@auth.verify_password
def verify_password(username: str, password: str) -> bool:
    with create_session() as session:
        user: Optional[User] = session.query(User).filter_by(username=username).first()
        if not user or not user.verify_password(password):
            return False
        return True
