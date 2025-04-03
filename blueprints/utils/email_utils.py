from flask_mail import Message, Mail
from flask import current_app, url_for
import jwt
from datetime import datetime, timedelta

mail = Mail()

def send_verification_email(user_email, token):
    msg = Message('Verify Your Email',
                  sender=current_app.config['MAIL_USERNAME'],
                  recipients=[user_email])
    
    verify_url = url_for('auth.verify_email', token=token, _external=True)
    
    msg.body = f'''To verify your email, visit the following link:
{verify_url}

If you did not make this request then simply ignore this email.
'''
    mail.send(msg)

def generate_verification_token(user_id):
    return jwt.encode(
        {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(hours=24)
        },
        current_app.config['SECRET_KEY'],
        algorithm='HS256'
    )

def verify_token(token):
    try:
        data = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        return data['user_id']
    except:
        return None