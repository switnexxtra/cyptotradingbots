from functools import wraps
from flask_login import current_user
from flask import abort
from extensions import db
from models.user import Chat

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# utils.py or in your routes
def get_or_create_chat(user_id):
    chat = Chat.query.filter_by(user_id=user_id).first()
    if not chat:
        chat = Chat(user_id=user_id, subject='General Chat')
        db.session.add(chat)
        db.session.commit()
    return chat
