import os
from flask import Flask
from config import Config
from extensions import db, login_manager, migrate, mail
from models.user import Investment, Loan, Settings
from blueprints.main.routes import main
from blueprints.auth.routes import auth
from blueprints.user.routes import user
from blueprints.admin.routes import admin
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from events import socketio
import threading
import time
import requests



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
    mail.init_app(app)  # Initialize Flask-Mail
    socketio.init_app(app)
    
    # Create upload folder before registering blueprints
    create_upload_folder(app)
    
    # Register blueprints inside the function to avoid circular imports
    from blueprints.main.routes import main
    from blueprints.auth.routes import auth
    from blueprints.user.routes import user
    from blueprints.admin.routes import admin

    app.register_blueprint(main)
    app.register_blueprint(auth, url_prefix='/auth')
    app.register_blueprint(user, url_prefix='/user')
    app.register_blueprint(admin, url_prefix='/admin')
    from sqlalchemy import text
    app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

    # Create database tables
    with app.app_context():
        # db.session.execute(text("DELETE FROM Investment;"))
        # print("'Investment Table' deleted")
        # db.session.commit()
        # db.session.execute(text("DELETE FROM alembic_version WHERE version_num = 'a3788d1a4a1a';"))
        # print("'a3788d1a4a1a' deleted")
        # db.session.commit()
        db.create_all()
        bonus_setting = Settings.query.filter_by(key="referral_bonus").first()
        if not bonus_setting:
            new_setting = Settings(key="referral_bonus", value=10.0)
            db.session.add(new_setting)
            db.session.commit()

    def check_overdue_loans():
        with app.app_context():  # Ensure function runs inside Flask's app context
            today = datetime.utcnow()
            overdue_loans = Loan.query.filter(Loan.status == "unpaid").all()

            for loan in overdue_loans:
                loan_due_date = loan.created_at + timedelta(days=loan.duration * 30)  # Convert months to days
                if today > loan_due_date:
                    loan.status = "overdue"

                    # Apply penalty interest (e.g., 10% extra for overdue loans)
                    penalty_interest = loan.amount * 0.10  # 10% penalty
                    loan.total_due += penalty_interest

                    db.session.commit()
                   
                   
    def calculate_profits(investment):
        """
        Calculate investment profits based on ROI and duration.
        """
        total_investment = investment.amount
        total_profit = (investment.amount * investment.roi) / 100
        estimated_profit = total_investment + total_profit  # Capital + Profit
        duration_days = (investment.end_date - investment.start_date).days

        if duration_days > 0:
            profit_per_day = total_profit / duration_days
            profit_per_hour = profit_per_day / 24
            profit_per_min = profit_per_hour / 60
            profit_per_sec = profit_per_min / 60
        else:
            profit_per_day = profit_per_hour = profit_per_min = profit_per_sec = 0

        return {
            "total_investment": total_investment,
            "total_profit": total_profit,
            "estimated_profit": estimated_profit,
            "profit_per_day": profit_per_day,
            "profit_per_hour": profit_per_hour,
            "profit_per_min": profit_per_min,
            "profit_per_sec": profit_per_sec,
        }

    def update_user_balances():
        """
        This function updates all active investments daily.
        """
        today = datetime.utcnow()
        active_investments = Investment.query.filter(Investment.status == 'active').all()

        for investment in active_investments:
            profits = calculate_profits(investment)
            user = investment.user

            # Check if the investment is still valid
            if today >= investment.end_date:
                investment.status = 'completed'

            # Update user balance with daily profit
            user.balance += profits["profit_per_day"]
            user.total_profit += profits["profit_per_day"]

            db.session.commit()

    # Set up the scheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(check_overdue_loans, 'interval', days=1)  # Run every 24 hours
    scheduler.add_job(update_user_balances, 'interval', days=1)
    scheduler.start()
            
    # Replace before_first_request with a more modern approach
    @app.before_request
    def before_request_func():
        # This only needs to run once when the app starts
        if not getattr(app, '_ping_thread_started', False):
            app._ping_thread_started = True
            threading.Thread(target=ping_self, daemon=True).start()
            print("Ping thread started")

    def ping_self():
        # Your app URL - make sure this is correct
        app_url = "https://cyptotradingbots.onrender.com/ping"
        
        while True:
            try:
                print(f"Pinging {app_url} to keep it awake...")
                response = requests.get(app_url, timeout=10)
                print(f"Ping successful: {response.status_code}")
            except Exception as e:
                print(f"Ping failed: {e}")
            
            # Sleep for 12 minutes (5500 seconds)
            time.sleep(5500)

        
    return app

app = create_app()  # Ensure this line is at the bottom

if __name__ == '__main__':
    socketio.run(app)
    
