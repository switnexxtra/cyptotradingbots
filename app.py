import os
from flask import Flask
from flask_socketio import SocketIO
from config import Config
from extensions import db, login_manager, migrate, mail
from models.user import Investment, Loan, Settings
from blueprints.main.routes import main
from blueprints.auth.routes import auth
from blueprints.user.routes import user
from blueprints.admin.routes import admin
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

# Initialize SocketIO (if you are using WebSockets)
socketio = SocketIO()

def create_upload_folder(app):
    """Ensure the upload folder exists before the app starts."""
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    mail.init_app(app)
    socketio.init_app(app)  # Initialize Flask-SocketIO if needed

    # Create upload folder before registering blueprints
    create_upload_folder(app)

    # Register blueprints
    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(admin, url_prefix='/admin')

    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # Database initialization
    with app.app_context():
        db.create_all()

        bonus_setting = Settings.query.filter_by(key="referral_bonus").first()
        if not bonus_setting:
            new_setting = Settings(key="referral_bonus", value=10.0)
            db.session.add(new_setting)
            db.session.commit()

    def check_overdue_loans():
        """Check for overdue loans and apply penalties."""
        with app.app_context():
            today = datetime.utcnow()
            overdue_loans = Loan.query.filter(Loan.status == "unpaid").all()

            for loan in overdue_loans:
                loan_due_date = loan.created_at + timedelta(days=loan.duration * 30)  # Convert months to days
                if today > loan_due_date:
                    loan.status = "overdue"
                    penalty_interest = loan.amount * 0.10  # 10% penalty
                    loan.total_due += penalty_interest

            db.session.commit()

    def calculate_profits(investment):
        """Calculate investment profits based on ROI and duration."""
        total_investment = investment.amount
        total_profit = (investment.amount * investment.roi) / 100
        estimated_profit = total_investment + total_profit
        duration_days = (investment.end_date - investment.start_date).days

        if duration_days > 0:
            profit_per_day = total_profit / duration_days
        else:
            profit_per_day = 0

        return {
            "total_investment": total_investment,
            "total_profit": total_profit,
            "estimated_profit": estimated_profit,
            "profit_per_day": profit_per_day,
        }

    def update_user_balances():
        """Update user balances based on active investments."""
        with app.app_context():
            today = datetime.utcnow()
            active_investments = Investment.query.filter(Investment.status == 'active').all()

            for investment in active_investments:
                profits = calculate_profits(investment)
                user = investment.user

                # Check if the investment has ended
                if today >= investment.end_date:
                    investment.status = 'completed'

                # Update user balance
                user.balance += profits["profit_per_day"]
                user.total_profit += profits["profit_per_day"]

            db.session.commit()

    # Initialize Scheduler **Outside Function Calls**
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_overdue_loans, 'interval', days=1)
    scheduler.add_job(update_user_balances, 'interval', days=1)
    scheduler.start()

    return app


if __name__ == '__main__':
    app = create_app()
    socketio.run(app, debug=True)
