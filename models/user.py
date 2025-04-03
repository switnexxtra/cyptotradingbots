import random
from extensions import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import string
import random



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def generate_referral_code():
    """Generate a unique 8-character alphanumeric referral code"""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))

def generate_unique_id(model, field):
    """Generate a unique 6-digit ID for a given model and field."""
    while True:
        unique_id = random.randint(100000, 999999)
        exists = model.query.filter(getattr(model, field) == unique_id).first()
        if not exists:
            return unique_id

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, unique=True)
    fullname = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(35), unique=True, nullable=False)
    mobile = db.Column(db.String(15), unique=True, nullable=True)    # Mobile phone number
    dateofbirth = db.Column(db.String(15), nullable=False)               # Country field
    gender = db.Column(db.String(100), nullable=False)
    line1 = db.Column(db.String(100), nullable=False)               # line1 field
    line2 = db.Column(db.String(100), nullable=False)               # line2 field
    country = db.Column(db.String(100), nullable=False)               # Country field
    city = db.Column(db.String(100), nullable=False)               # city field
    region = db.Column(db.String(100), nullable=False)               # region field
    postal = db.Column(db.String(10), nullable=False)               # postal field
    password_hash = db.Column(db.String(255), nullable=False)  # Use password_hash instead of password
    is_admin = db.Column(db.Boolean, default=False)
    wallet_id = db.Column(db.String(100), unique=True, default=lambda: f"WALLET-{random.randint(100000,999999)}")
    balance = db.Column(db.Float, default=0.0)
    total_investment = db.Column(db.Float, default=0.0)
    total_profit = db.Column(db.Float, default=0.0)
    estimated_profit = db.Column(db.Float, default=0.0)
    profit_per_day = db.Column(db.Float, default=0.0)
    profit_per_hour = db.Column(db.Float, default=0.0)
    profit_per_min = db.Column(db.Float, default=0.0)
    profit_per_sec = db.Column(db.Float, default=0.0)
    bonus = db.Column(db.Float, default=0.0)
    pending_bonus = db.Column(db.Float, default=0.0)  # Bonuses pending claim
    revenue_today = db.Column(db.Float, default=0.0)
    current_plan = db.Column(db.String(50), default='None')
    transaction_pin = db.Column(db.Integer, unique=True,  nullable=True)
    status = db.Column(db.String(20), default='active')
    referral_code = db.Column(db.String(50), unique=True, default=generate_referral_code)  # Generate a random referral code
    referral_earnings = db.Column(db.Float, default=0.0)
    referral_tree = db.Column(db.String(255))
    kyc_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Define the relationship to KYC
    kyc = db.relationship('KYC', back_populates='user', uselist=False, cascade="all, delete-orphan")


    def __init__(self, *args, **kwargs):
        if 'user_id' not in kwargs or kwargs['user_id'] is None:
            kwargs['user_id'] = generate_unique_id(User, 'user_id')
        super().__init__(*args, **kwargs)
        
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    # Flask-Login requires these properties/methods:
    @property
    def is_active(self):
        return True  # Set this to False if you want to disable the user

    @property
    def is_authenticated(self):
        return True  # Return True if the user is logged in

    @property
    def is_anonymous(self):
        return False  # Return False since this is a real user

    # Add get_id method required by Flask-Login
    def get_id(self):
        return str(self.id)
    
    
class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    subject = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    messages = db.relationship('Message', backref='chat', lazy='dynamic', order_by='Message.timestamp')

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('chat.id'))
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    sender = db.relationship('User', backref='sent_messages')
    
    
class Deposit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    amount = db.Column(db.Float, nullable=False)
    payment_method = db.Column(db.String(50), nullable=False)
    proof_image = db.Column(db.String(200), nullable=True)  # Store image filename
    status = db.Column(db.String(20), default="Pending")  # Pending, Approved, Rejected
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Deposit {self.id} - {self.amount} - {self.status}>"


class PaymentMethods(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    method = db.Column(db.String(50), unique=True, nullable=False)  # e.g., 'paypal', 'google_pay'
    details = db.Column(db.String(255), nullable=False)  # e.g., email, account number, etc.
    account_number = db.Column(db.String(100), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)
    account_name = db.Column(db.String(100), nullable=True)
    sub_type = db.Column(db.String(50), nullable=True)  # USDT, BTC, etc.
    wallet_address = db.Column(db.String(255), nullable=True)
    memo = db.Column(db.String(255), nullable=True)
    network_address = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)  # Stores path to payment method image (e.g., QR code, bank logo)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)


# class Transaction(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     transaction_id = db.Column(db.Integer, unique=True)
#     user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
#     user = db.relationship('User', backref='transactions')  # Define the relationship
#     transaction_type = db.Column(db.String(50), nullable=False)  # Deposit, Withdraw, Transfer
#     transaction_detail = db.Column(db.String(100), nullable=False)  # Deposit, Withdraw, Transfer
#     image_url = db.Column(db.String(255), nullable=True)  # Stores path to payment method image (e.g., QR code, bank logo)
    
#     # Correct the ForeignKey references
#     sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
#     receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
#     amount = db.Column(db.Float, nullable=False)
#     status = db.Column(db.String(20), default='pending')
#     created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    
#     # Correct relationships for sender and receiver
#     sender = db.relationship('User', foreign_keys=[sender_id])
#     receiver = db.relationship('User', foreign_keys=[receiver_id])


#     def __init__(self, *args, **kwargs):
#         if 'transaction_id' not in kwargs or kwargs['transaction_id'] is None:
#             kwargs['transaction_id'] = generate_unique_id(Transaction, 'transaction_id')
#         super().__init__(*args, **kwargs)
        
class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.Integer, unique=True)
    
    # Specify the foreign key for 'user' relationship (using 'user_id')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Define the relationship with explicit foreign key for 'user_id'
    user = db.relationship('User', backref='transactions', foreign_keys=[user_id])  # Define the relationship with 'user_id'
    
    transaction_type = db.Column(db.String(50), nullable=False)  # Deposit, Withdraw, Transfer
    transaction_detail = db.Column(db.String(100), nullable=False)  # Deposit, Withdraw, Transfer
    image_url = db.Column(db.String(255), nullable=True)  # Stores path to payment method image (e.g., QR code, bank logo)
    
    # Correct the ForeignKey references for sender and receiver
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    
    amount = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Specify the relationships for sender and receiver with the correct foreign keys
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])

    def __init__(self, *args, **kwargs):
        if 'transaction_id' not in kwargs or kwargs['transaction_id'] is None:
            kwargs['transaction_id'] = generate_unique_id(Transaction, 'transaction_id')
        super().__init__(*args, **kwargs)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Loan duration in months
    status = db.Column(db.String(20), default='pending')  # pending, approved, unpaid, paid
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    interest_rate = db.Column(db.Float, default=5.0)  # Default 5% interest
    total_due = db.Column(db.Float, nullable=True)  # Amount + interest

    user = db.relationship('User', backref='loans')

    def calculate_interest(self):
        interest = (self.amount * self.interest_rate / 100) * (self.duration / 12)  # Interest formula
        self.total_due = self.amount + interest


class InvestmentPlan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    roi = db.Column(db.Float, nullable=False)  # ROI percentage
    min_amount = db.Column(db.Float, nullable=False)
    max_amount = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, nullable=False)  # Duration in months
    capital_back = db.Column(db.String(10), nullable=False, default='No')

    def __repr__(self):
        return f"<InvestmentPlan {self.name}>"


class Investment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    plan_id = db.Column(db.Integer, db.ForeignKey('investment_plan.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    roi = db.Column(db.Float, nullable=False)
    start_date = db.Column(db.DateTime, default=datetime.utcnow)
    end_date = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    
    # New fields for calculated profits
    total_profit = db.Column(db.Float, nullable=False, default=0.0)
    estimated_profit = db.Column(db.Float, nullable=False, default=0.0)
    profit_per_day = db.Column(db.Float, nullable=False, default=0.0)
    profit_per_hour = db.Column(db.Float, nullable=False, default=0.0)
    profit_per_min = db.Column(db.Float, nullable=False, default=0.0)
    profit_per_sec = db.Column(db.Float, nullable=False, default=0.0)
    revenue_today = db.Column(db.Float, default=0.0)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('investments', lazy=True))
    plan = db.relationship('InvestmentPlan', backref=db.backref('investments', lazy=True))

    def __repr__(self):
        return f"<Investment {self.id} - {self.user_id} - {self.plan_id}>"

    
class Referral(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Who referred
    referred_id = db.Column(db.Integer, db.ForeignKey('user.user_id'), nullable=False)  # Who was referred
    amount_earned = db.Column(db.Float, default=0.0)  # Store the amount earned per referral
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class KYC(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)  # Foreign Key to User
    user = db.relationship('User', back_populates='kyc', uselist=False)  # Relationship to User
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    gender = db.Column(db.String(10), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    address = db.Column(db.String(255), nullable=False)
    address2 = db.Column(db.String(255), nullable=True)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    nationality = db.Column(db.String(100), nullable=False)
    postcode = db.Column(db.String(100), nullable=False)
    document_type = db.Column(db.String(50), nullable=False)
    document_front = db.Column(db.String(255), nullable=True)
    document_back = db.Column(db.String(255), nullable=True)
    selfie_with_document = db.Column(db.String(255), nullable=True)
    status = db.Column(db.String(20), default='pending')  # pending, verified, rejected

    
class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    message = db.Column(db.String(255), nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    
    
class Settings(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.Float, nullable=False)

