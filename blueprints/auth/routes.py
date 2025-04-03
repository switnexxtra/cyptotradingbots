from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, current_user, login_required, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from models.user import User, Referral, Settings
from utils.email_utils import send_verification_email, generate_verification_token, verify_token



auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')  # Get input from form
        password = request.form.get('password')

        # Find user by username or email
        user = User.query.filter((User.username == username) | (User.email == username)).first()
    
        # Check if user exists and password is correct
        if not user or not check_password_hash(user.password_hash, password):
            flash('Invalid username or password. Please try again.', 'danger')
            return redirect(url_for('auth.login'))  # Redirect to login on failure

        # Log in the user
        login_user(user)
        flash('Login Successful.', 'success')

        # Redirect based on user role
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('user.dashboard'))

    return render_template('auth/login.html')



@auth.route('/register_admin')
def register_admin():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        

    fullname = "Site Admin"
    username = "Site Admin"
    email = "siteadmin@gmail.com"
    mobile = "+2348890192"
    dateofbirth = "12-06-1995"
    gender = "male"
    line1 = "anonymous"
    line2 = "anonymous"
    country = "Nigeria"
    city = "Abuja"
    region = "nigeria"
    postal = "808069"
    # referrer_code = request.form.get('referral_code')  # Referral code from form

    password = "SiteAdminPass6058"
    confirm_password = "SiteAdminPass6058"
    
    # Form validation
    if not all([username, email, password, confirm_password]):
        flash('All fields are required.', 'error')
        return redirect(url_for('auth.register'))
        
    if password != confirm_password:
        flash('Passwords do not match.', 'error')
        return redirect(url_for('auth.register'))
        
    # Check if user already exists
    if User.query.filter_by(username=username).first():
        flash('Username already exists.', 'error')
        return redirect(url_for('auth.register'))
        
    if User.query.filter_by(email=email).first():
        flash('Email already registered.', 'error')
        return redirect(url_for('auth.register'))
    
    # Create new user
    new_user = User(
        fullname=fullname,
        username=username,
        email=email,
        mobile=mobile,
        dateofbirth=dateofbirth,
        gender=gender,
        line1=line1,
        line2=line2,
        country=country,
        city=city,
        region=region,
        postal=postal,
        is_admin=True
        # password=generate_password_hash(password, method='pbkdf2:sha256')
    )
    
    new_user.set_password(password)  # Use the set_password method
    
    try:
        db.session.add(new_user)
        db.session.commit()
                    
        # Handle referral logic
        # Get the latest referral bonus
        # Check for valid referral code
        # if referrer_code:
        #     referrer = User.query.filter_by(referral_code=referrer_code).first()
        #     if referrer:
        #         referral_bonus_setting = Settings.query.filter_by(key="referral_bonus").first()
        #         referral_bonus = float(referral_bonus_setting.value) if referral_bonus_setting else 10.0  # Default 10

        #         # Save referral record
        #         referral = Referral(referrer_id=referrer.user_id, referred_id=new_user.user_id, amount_earned=referral_bonus)
        #         db.session.add(referral)

        #         # Update referrer’s earnings & balance
        #         referrer.referral_earnings += referral_bonus
        #         referrer.balance += referral_bonus  # Also add to balance
        #         db.session.commit()

        #         flash(f"You were referred by {referrer.username}. They earned ${referral_bonus}!", "info")

            
        # Generate verification token and send email
        token = generate_verification_token(new_user.id)
        send_verification_email(new_user.email, token)
        
        flash('Registration successful. Please check your email to verify your account.', 'success')
        return redirect(url_for('auth.login'))
        
    except Exception as e:
        db.session.rollback()
        flash('An error occurred. Please try again.', 'error')
        print(f"Database error: {str(e)}")  # Debugging
        return redirect(url_for('auth.register'))

    # return render_template('auth/register.html')

@auth.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
        
    if request.method == 'POST':
         # Get form data
        fullname = request.form.get('fullname')
        username = request.form.get('userName')
        email = request.form.get('email')
        mobile = request.form.get('mobile')
        dateofbirth = request.form.get('dateofbirth')
        gender = request.form.get('gender')
        line1 = request.form.get('line1')
        line2 = request.form.get('line2')
        country = request.form.get('country')
        city = request.form.get('city')
        region = request.form.get('region')
        postal = request.form.get('postal')
        referrer_code = request.form.get('referral_code')  # Referral code from form

        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        # Form validation
        if not all([username, email, password, confirm_password]):
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.register'))
            
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('auth.register'))
            
        # Check if user already exists
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('auth.register'))
        
        # Create new user
        new_user = User(
            fullname=fullname,
            username=username,
            email=email,
            mobile=mobile,
            dateofbirth=dateofbirth,
            gender=gender,
            line1=line1,
            line2=line2,
            country=country,
            city=city,
            region=region,
            postal=postal,
            referral_code=username
            # password=generate_password_hash(password, method='pbkdf2:sha256')
        )
        
        new_user.set_password(password)  # Use the set_password method
        
        try:
            db.session.add(new_user)
            db.session.commit()
                        
            # Handle referral logic
            # Get the latest referral bonus
            # Check for valid referral code
            if referrer_code:
                referrer = User.query.filter_by(referral_code=referrer_code).first()
                if referrer:
                    referral_bonus_setting = Settings.query.filter_by(key="referral_bonus").first()
                    referral_bonus = float(referral_bonus_setting.value) if referral_bonus_setting else 10.0  # Default 10

                    # Save referral record
                    referral = Referral(referrer_id=referrer.user_id, referred_id=new_user.user_id, amount_earned=referral_bonus)
                    db.session.add(referral)

                    # Update referrer’s earnings & balance
                    referrer.referral_earnings += referral_bonus
                    referrer.balance += referral_bonus  # Also add to balance
                    db.session.commit()

                    flash(f"You were referred by {referrer.username}. They earned ${referral_bonus}!", "info")

                
            # Generate verification token and send email
            token = generate_verification_token(new_user.id)
            send_verification_email(new_user.email, token)
            
            flash('Registration successful. Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash('An error occurred. Please try again.', 'error')
            print(f"Database error: {str(e)}")  # Debugging
            return redirect(url_for('auth.register'))
    
    return render_template('auth/register.html')

@auth.route('/verify/<token>')
def verify_email(token):
    if current_user.is_authenticated and current_user.is_verified:
        return redirect(url_for('main.home'))
        
    user_id = verify_token(token)
    
    if user_id is None:
        flash('Invalid or expired verification link.', 'error')
        return redirect(url_for('auth.login'))
        
    user = User.query.get(user_id)
    
    if user is None:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))
        
    if user.is_verified:
        flash('Email already verified. Please login.', 'info')
        return redirect(url_for('auth.login'))
        
    user.is_verified = True
    user.verified_at = datetime.utcnow()
    db.session.commit()
    
    flash('Your email has been verified! You can now login.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    print("Logout Called")
    logout_user()
    flash("successfully logout", "success")
    return redirect(url_for('main.home'))
