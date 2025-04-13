from datetime import datetime, timedelta
import os
from flask import Blueprint, abort, current_app, jsonify, session, render_template, redirect, flash, url_for, request
from flask_login import login_required, current_user
from utils.decorators import admin_required, get_or_create_chat
from models.user import KYC, Chat, Deposit, Investment, InvestmentPlan, Loan, Message, Notification, Transaction, User, PaymentMethods, Settings
from extensions import db
from werkzeug.utils import secure_filename
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func


admin = Blueprint('admin', __name__)


@admin.route('/dashboard')
@login_required
@admin_required
def dashboard():
    # users = User.query.all()
    payment_methods = PaymentMethods.query.all()
    
    transactions = Transaction.query.all()

    users_with_kyc = User.query.join(KYC).filter(KYC.status != 'pending').all()
    
    # $ Total Invests
    total_invests = db.session.query(func.sum(Investment.amount)).scalar() or 0.0

    # $ Total Pending Deposit
    total_pending_deposit = db.session.query(func.sum(Deposit.amount)).filter(Deposit.status == "Pending").scalar() or 0.0

    # $ Total Transactions
    total_transactions = db.session.query(func.sum(Transaction.amount)).filter(Transaction.status == "approved").scalar() or 0.0

    # $ Total Withdrawals
    total_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'Withdraw',
        Transaction.status == 'approved'
    ).scalar() or 0.0

    # $ Pending Withdrawals
    pending_withdrawals = db.session.query(func.sum(Transaction.amount)).filter(
        Transaction.transaction_type == 'Withdraw',
        Transaction.status == 'pending'
    ).scalar() or 0.0
    
    # Total Users
    total_users = db.session.query(User).count()

    # Active Users
    active_users = db.session.query(User).filter(User.status == 'active').count()

    # Deactivated Users
    deactivated_users = db.session.query(User).filter(User.status != 'active').count()

    dashboard_stats = {
        "total_invests": round(total_invests, 6),
        "pending_deposit": round(total_pending_deposit, 6),
        "total_transactions": round(total_transactions, 6),
        "total_withdrawals": round(total_withdrawals, 6),
        "pending_withdrawals": round(pending_withdrawals, 6),
        "total_users": total_users,
        "active_users": active_users,
        "deactivated_users": deactivated_users
    }


    return render_template('admin/admin_dashboard.html', user=current_user, payment_methods=payment_methods, user_kyc=users_with_kyc, transactions=transactions, data=dashboard_stats)


# Admin required decorator
@admin.route('/chats/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    if request.method == 'POST':
        message_content = request.form.get('message')
        
        if not message_content:
            flash('Message cannot be empty')
            return redirect(url_for('admin.view_chat', chat_id=chat_id))
        
        # Add admin response
        new_message = Message(
            chat_id=chat.id,
            sender_id=current_user.id,
            content=message_content
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return redirect(url_for('admin.view_chat', chat_id=chat_id))
    
    # Mark unread messages as read
    unread_messages = Message.query.filter_by(
        chat_id=chat.id, 
        is_read=False
    ).filter(Message.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    return render_template('admin/view_chat.html', chat=chat)

@admin.route('/chats/<int:chat_id>/resolve', methods=['POST'])
@login_required
def resolve_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    chat.is_resolved = not chat.is_resolved  # Toggle resolved status
    db.session.commit()
    
    return redirect(url_for('admin.view_chat', chat_id=chat_id))

@admin.route('/userslist')
@login_required
def user_list():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/user_list.html', users=users)
    
@admin.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    # Fetch investments for all users (or specific users if needed)
    
    return render_template('admin/users.html', user=current_user, users=users)

@admin.route('/search_users', methods=['GET'])
@login_required
@admin_required
def search_users():
    query = request.args.get('q', '').strip()
    
    from sqlalchemy import cast, String
    
    users_query = db.session.query(User).filter(User.is_admin == False)
    
    if query:
        search_query = f"%{query}%"
        users_query = users_query.filter(
            (User.username.ilike(search_query)) |
            (User.email.ilike(search_query)) |
            (cast(User.user_id, String).ilike(search_query))
        )
    
    users = users_query.all()
    
    # Render the table rows as HTML
    html_content = render_template('user_table_rows.html', users=users)
    return html_content

@admin.route('/search_transactions', methods=['GET'])
@login_required
@admin_required
def search_transactions():
    query = request.args.get('q', '').strip()
    
    from sqlalchemy import cast, String
    
    transactions_query = db.session.query(Transaction)
    
    if query:
        search_query = f"%{query}%"
        transactions_query = transactions_query.filter(
            (cast(Transaction.transaction_id, String).ilike(search_query))
        )
    
    transactions = transactions_query.all()
    
    # Render just the table rows HTML
    html_content = render_template('transaction_table_rows.html', transactions=transactions)
    return html_content


# @admin.route('/update_user/<int:user_id>', methods=['POST'])
# @login_required
# @admin_required
# def update_user(user_id):
#     user = User.query.get_or_404(user_id)
#     User.query.filter(User.pending_bonus.is_(None)).update({User.pending_bonus: 0.0})
#     db.session.commit()

#     user.fullname = request.form['fullname']
#     user.username = request.form['username']
#     user.email = request.form['email']
#     user.mobile = request.form['mobile']
#     user.dateofbirth = request.form['dateofbirth']
#     user.gender = request.form['gender']
#     user.status = request.form['status']

#     # Handle pending bonus addition
#     new_bonus = request.form.get('bonus', type=float)
#     if new_bonus and new_bonus > 0:
#         user.pending_bonus += new_bonus
#         notification = Notification(user_id=user.id, message=f'You received a bonus of ${new_bonus}. Claim it now!')
#         db.session.add(notification)
#         flash(f'Bonus of ${new_bonus} added to pending bonus for {user.username}', 'success')

#     # Handle balance update
#     # new_balance = request.form.get('balance', type=float)
#     # total_profit = request.form.get('total_profit', type=float)
#     # estimated_profit = request.form.get('estimated_profit', type=float)
#     # profit_per_day = request.form.get('profit_per_day', type=float)
#     # profit_per_hour = request.form.get('profit_per_hour', type=float)
#     # profit_per_min = request.form.get('profit_per_min', type=float)
#     # profit_per_sec = request.form.get('profit_per_sec', type=float)
#     # if new_balance is not None:
#     #     user.balance = new_balance
        
        
#     # if total_profit is not None:
#     #     user.total_profit = total_profit
            
#     # if estimated_profit is not None:
#     #     user.estimated_profit = estimated_profit
            
#     # if profit_per_day is not None:
#     #     user.profit_per_day = profit_per_day
            
#     # if profit_per_hour is not None:
#     #     user.profit_per_hour = profit_per_hour
            
#     # if profit_per_min is not None:
#     #     user.profit_per_min = profit_per_min
            
#     # if profit_per_sec is not None:
#     #     user.profit_per_sec = profit_per_sec
        
#     # flash(f'User balance updated ', 'success')

#     # db.session.commit()
    
#     # Handle balance update
#     numeric_fields = ['balance', 'total_profit', 'estimated_profit', 'profit_per_day', 'profit_per_hour', 'profit_per_min', 'profit_per_sec', 'revenue_today']
#     for field in numeric_fields:
#         new_value = request.form.get(field)
#         if new_value:
#             try:
#                 setattr(user, field, float(new_value))  # Convert and assign
#             except ValueError:
#                 flash(f'Invalid value for {field}.', 'danger')
    
   

#     db.session.commit()
#     flash(f'User {user.username} updated successfully!', 'success')
#     return redirect(url_for('admin.users'))


@admin.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    User.query.filter(User.pending_bonus.is_(None)).update({User.pending_bonus: 0.0})
    db.session.commit()

    # Update user details
    user.fullname = request.form['fullname']
    user.username = request.form['username']
    user.email = request.form['email']
    user.mobile = request.form['mobile']
    user.dateofbirth = request.form['dateofbirth']
    user.gender = request.form['gender']
    user.status = request.form['status']

    # Handle pending bonus addition
    new_bonus = request.form.get('bonus', type=float)
    if new_bonus and new_bonus > 0:
        user.pending_bonus += new_bonus
        notification = Notification(user_id=user.id, message=f'You received a bonus of ${new_bonus}. Claim it now!')
        db.session.add(notification)
        flash(f'Bonus of ${new_bonus} added to pending bonus for {user.username}', 'success')

    # Handle balance and profits update
    numeric_fields = ['balance', 'total_profit', 'estimated_profit', 'profit_per_day', 'profit_per_hour', 'profit_per_min', 'profit_per_sec', 'revenue_today']
    for field in numeric_fields:
        new_value = request.form.get(field)
        if new_value:
            try:
                setattr(user, field, float(new_value))  # Convert and assign
            except ValueError:
                flash(f'Invalid value for {field}.', 'danger')

    # Add user's total profit to each of their investments
    for investment in user.investments:
        investment.total_profit = user.total_profit  # Add user's profit to each investment's total profit
        investment.estimated_profit = user.estimated_profit  # Add user's profit to each investment's total profit
        investment.profit_per_day = user.profit_per_day  # Add user's profit to each investment's total profit
        investment.profit_per_hour = user.profit_per_hour  # Add user's profit to each investment's total profit
        investment.profit_per_min = user.profit_per_min  # Add user's profit to each investment's total profit
        investment.profit_per_sec = user.profit_per_sec  # Add user's profit to each investment's total profit
        investment.revenue_today = user.revenue_today  # Add user's profit to each investment's total profit
        db.session.commit()  # Commit after updating each investment's total profit

    db.session.commit()
    flash(f'User {user.username} updated successfully!', 'success')
    return redirect(url_for('admin.users'))



@admin.route('/send_notification', methods=['POST'])
@login_required
def send_notification():
    if not current_user.is_admin:
        flash("You do not have permission to send notifications.", "danger")
        return redirect(url_for('admin.dashboard'))

    message = request.form.get('message')
    if not message:
        flash("Notification message cannot be empty!", "warning")
        return redirect(url_for('admin.dashboard'))

    # Send notification to all users
    users = User.query.all()
    for user in users:
        notification = Notification(user_id=user.id, message=message, is_read=False)
        db.session.add(notification)

    db.session.commit()
    flash("Notification sent successfully!", "success")
    return redirect(url_for('admin.users'))


@admin.route('/admin/referral-bonus', methods=['GET', 'POST'])
@login_required
def update_referral_bonus():
    if not current_user.is_admin:  # Ensure only admins can access this
        flash("Access denied!", "danger")
        return redirect(url_for('auth.dashboard'))

    bonus_setting = Settings.query.filter_by(key="referral_bonus").first()

    if request.method == 'POST':
        new_bonus = float(request.form.get("bonus"))
        
        if bonus_setting:
            bonus_setting.value = new_bonus
        else:
            bonus_setting = Settings(key="referral_bonus", value=new_bonus)
            db.session.add(bonus_setting)
        
        db.session.commit()
        flash("Referral bonus updated successfully!", "success")
        return redirect(url_for('auth.update_referral_bonus'))

    return render_template('admin/referral_bonus.html', bonus=bonus_setting.value if bonus_setting else 10.0)


# Ensure upload folder exists inside a request context
@admin.before_app_request
def create_upload_folder():
    os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)



@admin.route('/add-payment-method', methods=['POST'])
@login_required
@admin_required
def add_payment_method():
    method = request.form.get('method')

    if not method:
        flash('Payment method is required!', 'danger')

    else:
        # 🔍 Check if the method already exists
        existing_method = PaymentMethods.query.filter_by(method=method).first()
        if existing_method:
            flash('This payment method already exists! try adding another method', 'danger')

        # Proceed with adding a new payment method
        details = request.form.get('details')
        account_number = request.form.get('account_number')
        bank_name = request.form.get('bank_name')
        account_name = request.form.get('account_name')
        sub_type = request.form.get('sub_type')
        wallet_address = request.form.get('wallet_address')
        memo = request.form.get('memo')
        network_address = request.form.get('network_address')
        image = request.files.get('qr_code')
        
        image_filename = None  # Default value

        if image:
            filename = secure_filename(image.filename)
            image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            image.save(image_path)
    
            # Store only the filename, NOT the full path
            image_filename = filename  
    
        try:
            payment = PaymentMethods(
                method=method,
                details=details,
                account_number=account_number,
                bank_name=bank_name,
                account_name=account_name,
                sub_type=sub_type,
                wallet_address=wallet_address,
                memo=memo,
                network_address=network_address,
                image_url=image_filename  # Store only the filename
            )

            db.session.add(payment)
            db.session.commit()
            flash('Payment method added successfully!', 'success')

        except IntegrityError:
            db.session.rollback()
            flash('Error: Duplicate payment method!', 'danger')

    return redirect(url_for('admin.dashboard'))



# Route to edit a payment method
@admin.route('/edit-payment-method', methods=['POST'])
@login_required
@admin_required
def edit_payment_method():
    payment_id = request.form.get('payment_id')
    method = request.form.get('method')
    details = request.form.get('details')
    account_number = request.form.get('account_number')
    bank_name = request.form.get('bank_name')
    account_name = request.form.get('account_name')
    wallet_address = request.form.get('wallet_address')
    memo = request.form.get('memo')
    network_address = request.form.get('network_address')
    image = request.files.get('image')

    # Fetch existing payment method
    payment = PaymentMethods.query.get(payment_id)
    if not payment:
        flash("Payment method not found!", "danger")
        return redirect(url_for('admin.dashboard'))

    # 🔍 Check if the new method name already exists in another record
    existing_method = PaymentMethods.query.filter(PaymentMethods.method == method, PaymentMethods.id != payment.id).first()
    if existing_method:
        flash("This payment method name already exists!", "danger")
        return redirect(url_for('admin.dashboard'))

    # Update fields
    payment.method = method
    payment.details = details
    payment.account_number = account_number
    payment.bank_name = bank_name
    payment.account_name = account_name
    payment.wallet_address = wallet_address
    payment.memo = memo
    payment.network_address = network_address

    if image:
        # Delete old image if it exists
        if payment.image_url:
            old_image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(payment.image_url))
            if os.path.exists(old_image_path):
                os.remove(old_image_path)

        # Save new image
        filename = secure_filename(image.filename)
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        image.save(image_path)

        # Store only the filename, not the full path
        payment.image_url = filename

    try:
        db.session.commit()
        flash("Payment method updated successfully!", "success")
    except IntegrityError:
        db.session.rollback()
        flash("Sorry you can't change payment method from here! ", "danger")

    return redirect(url_for('admin.dashboard'))



@admin.route('/admin/payment-methods/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_payment_method(id):
    payment = PaymentMethods.query.get_or_404(id)

    # Delete the image file if it exists
    if payment.image_url:
        image_path = os.path.join(current_app.config['UPLOAD_FOLDER'], payment.image_url)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Delete the payment method from the database
    db.session.delete(payment)
    db.session.commit()

    flash('Payment method deleted successfully!', 'success')
    return redirect(url_for('admin.dashboard'))  # Make sure this is the correct route

# Example function to get all payments
@admin.route('/get_all_payment_method')
def get_all_payment_method():
    return {payment.method: payment.details for payment in PaymentMethods.query.all()}


@admin.route('/investment')
@login_required
def investment():
    plans = InvestmentPlan.query.all()
    return render_template('admin/investment.html', user=current_user, plans=plans)


@admin.route('/add-plan', methods=['POST'])
@login_required
@admin_required
def add_plan():
    try:
        name = request.form.get('name')
        roi = float(request.form.get('roi'))
        min_amount = float(request.form.get('min_amount'))
        max_amount = float(request.form.get('max_amount'))
        duration = int(request.form.get('duration'))
        capital_back = request.form.get('capital_back')

        if not name or not roi or not min_amount or not max_amount or not duration:
            flash("All fields are required!", "danger")
            return redirect(url_for('dashboard'))

        new_plan = InvestmentPlan(
            name=name,
            roi=roi,
            min_amount=min_amount,
            max_amount=max_amount,
            duration=duration,
            capital_back=capital_back
        )

        db.session.add(new_plan)
        db.session.commit()
        flash("Investment plan added successfully!", "success")
        return redirect(url_for('admin.investment'))

    except Exception as e:
        db.session.rollback()
        flash(f"Error: {str(e)}", "danger")

    return redirect(url_for('admin.investment'))


@admin.route('/edit_plan/<int:plan_id>', methods=['POST'])
@login_required
@admin_required
def edit_plan(plan_id):
    plan = InvestmentPlan.query.get(plan_id)
    if not plan:
        flash("Plan not found!", "danger")
        return redirect(url_for('admin.view_plans'))

    try:
        # Get form data
        plan.name = request.form.get('name')
        plan.roi = float(request.form.get('roi'))
        plan.min_amount = float(request.form.get('min_amount'))
        plan.max_amount = float(request.form.get('max_amount'))
        plan.duration = int(request.form.get('duration'))
        plan.capital_back = request.form.get('capital_back')

        db.session.commit()
        flash("Investment plan updated successfully!", "success")

    except Exception as e:
        db.session.rollback()
        flash(f"Error updating plan: {str(e)}", "danger")

    return redirect(url_for('admin.investment'))



# @admin.route('/delete-plan/<int:plan_id>', methods=['POST'])
# @login_required
# @admin_required
# def delete_plan(plan_id):
#     plan = InvestmentPlan.query.get(plan_id)
#     if not plan:
#         flash("Plan not found!", "danger")
#         return redirect(url_for('admin.investment'))

#     db.session.delete(plan)
#     db.session.commit()
#     flash("Investment plan deleted successfully!", "success")
#     return redirect(url_for('admin.investment'))

@admin.route('/delete_plan/<int:plan_id>', methods=['GET', 'POST'])
@login_required
@admin_required
def delete_plan(plan_id):
    plan = InvestmentPlan.query.get(plan_id)
    if not plan:
        flash("Plan not found!", "danger")
        return redirect(url_for('admin.investment'))

    db.session.delete(plan)
    db.session.commit()
    flash("Investment plan deleted successfully!", "success")
    
    return redirect(url_for('admin.investment'))



@admin.route('/loan')
@login_required
def loan():
    loans = Loan.query.all()
    return render_template('admin/loan.html', user=current_user, loans=loans)

@admin.route('/update_loan_status/<int:loan_id>', methods=['POST'])
@login_required
def update_loan_status(loan_id):
    if not current_user.is_admin:
        flash("Unauthorized action.", "danger")
        return redirect(url_for('admin.loan')) 

    loan = Loan.query.get_or_404(loan_id)
    new_status = request.form.get('status')

    if new_status not in ['pending', 'approved', 'unpaid', 'paid', 'due', 'overdue', 'cancelled']:
        flash("Invalid status selection.", "danger")
        return redirect(url_for('admin.loan'))

    loan.status = new_status
    db.session.commit()

    flash("Loan status updated successfully!", "success")
    return redirect(url_for('admin.loan'))



# <----------------------------------- Starting Of Transaction Section <------------------------------- #
@admin.route('/transactions')
def transactions():
    transactions = Transaction.query.all()  # Fetch all transactions from DB
    return render_template('admin/transactions.html', user=current_user, transactions=transactions)


@admin.route('/delete_transaction/<int:transaction_id>', methods=['DELETE'])
def delete_transaction(transaction_id):
    transaction = Transaction.query.get(transaction_id)
    
    if transaction:
        db.session.delete(transaction)
        db.session.commit()
        
        flash("Transaction Deleted Successfully", "success")  # Flash message
        return jsonify({"success": True, "message": "Transaction Deleted Successfully"}), 200  # JSON response
    
    flash("Transaction not found", "danger")  # Flash error message
    return jsonify({"success": False, "error": "Transaction not found"}), 404



# @admin.route("/update_transaction_status/<int:transaction_id>", methods=["POST"])
# def update_transaction_status(transaction_id):
#     data = request.get_json()
#     transaction = Transaction.query.get(transaction_id)
    
#     if transaction:
#         transaction.status = data["status"]
#         db.session.commit()
        
#         flash("Transaction Edited Successfully", "success")  # Flash message
#         return jsonify({"success": True, "message": "Transaction Edited Successfully"}), 200  # JSON response for AJAX
    
#     flash("Transaction not found", "danger")  # Flash error message
#     return jsonify({"success": False, "error": "Transaction not found"}), 404

@admin.route("/update_transaction_status/<int:transaction_id>", methods=["POST"])
def update_transaction_status(transaction_id):
    data = request.get_json()
    transaction = Transaction.query.get(transaction_id)
    receiver = User.query.get(transaction.receiver_id)  # Fetch the receiver user related to the transaction
    
    if transaction:
        transaction.status = data["status"]
        user = User.query.get(transaction.user_id)  # Fetch the user related to the transaction

        if user:
            print(f"User ID: {user.id}, Balance Before: {user.balance}")  # Debugging
            print(f"Transaction Status: {transaction.status}, Type: {transaction.transaction_type}, Amount: {transaction.amount}")  # Debugging

            if transaction.status == "completed":
                if transaction.transaction_type.lower() == "deposit":
                    user.balance += transaction.amount  # Add the amount to the user's balance
                    
                   
                elif transaction.transaction_type.lower() == "transfer":
                    receiver.balance += transaction.amount  # Add the amount to the receiver's balance
                
                elif transaction.transaction_type.lower() == "withdraw":
                    if user.balance >= transaction.amount:
                        user.balance -= transaction.amount  # Deduct the amount
                    else:
                        flash("Insufficient balance for withdrawal", "danger")
                        return jsonify({"success": False, "error": "Insufficient balance"}), 400
            
            db.session.commit()  # Save changes
            db.session.refresh(user)  # Refresh to verify changes
            print(f"User ID: {user.id}, Balance After: {user.balance}")  # Debugging
            
            flash("Transaction Edited Successfully", "success")
            return jsonify({"success": True, "message": "Transaction Edited Successfully"}), 200

    flash("Transaction not found", "danger")
    return jsonify({"success": False, "error": "Transaction not found"}), 404


# <----------------------------------- Ending Of Transaction Section <------------------------------- #




# <----------------------------------- Starting Of Kyc Section <------------------------------- #
@admin.route('/kyc')
@login_required
def kyc():
    # Fetch all KYC records with status 'pending', 'failed', or 'completed'
    kyc_records = KYC.query.filter(KYC.status.in_(['pending', 'failed', 'verified', 'success'])).all()
    return render_template('admin/kyc.html', user=current_user, kyc_records=kyc_records)


@admin.route('/update_kyc_status/<int:kyc_id>', methods=['POST'])
@login_required
def update_kyc_status(kyc_id):
    if not current_user.is_admin:  # Ensure only admins can update
        flash("Unauthorized action", "error")
        return redirect(request.referrer)

    kyc_record = KYC.query.get_or_404(kyc_id)

    new_status = request.form.get('status')
    if new_status not in ['pending', 'failed', 'verified']:
        flash("Invalid status value", "error")
        return redirect(request.referrer)

    kyc_record.status = new_status
    db.session.commit()

    flash("KYC status updated successfully", "success")
    return redirect(request.referrer)


# <----------------------------------- End Of Kyc Section <------------------------------- #
# @admin.route('/support')
# # @login_required
# def support():
#     return render_template('admin/support.html')


@admin.route('/chat')
@login_required
def chat():
    if current_user.is_admin:
        # Get list of users who have messages for admin
        users_with_messages = db.session.query(User).join(
            Message, Message.sender_id == User.id
        ).filter(
            Message.recipient_id == current_user.id
        ).group_by(User.id).all()
        
        # Also get all users for admin to initiate chats
        all_users = User.query.filter(User.id != current_user.id).all()
        
        return render_template('admin/support.html', users=all_users, users_with_messages=users_with_messages)
    else:
        # For regular users, get their conversation with admin
        admin = User.query.filter_by(is_admin=True).first()
        messages = Message.query.filter(
            ((Message.sender_id == current_user.id) & (Message.recipient_id == admin.id)) |
            ((Message.sender_id == admin.id) & (Message.recipient_id == current_user.id))
        ).order_by(Message.timestamp).all()
        
        return render_template('user/support.html', messages=messages, admin=admin)
    
    

# @admin.route('/api/messages/<int:user_id>')
# @login_required
# def get_messages(user_id):
#     if not current_user.is_admin and user_id != current_user.id:
#         return jsonify({'error': 'Unauthorized'}), 403
    
#     # For admin viewing user messages
#     if current_user.is_admin:
#         user = User.query.get_or_404(user_id)
#         messages = Message.query.filter(
#             ((Message.sender_id == user.id) & (Message.recipient_id == current_user.id)) |
#             ((Message.sender_id == current_user.id) & (Message.recipient_id == user.id))
#         ).order_by(Message.timestamp).all()
#     else:
#         # Regular user viewing their messages with admin
#         admin = User.query.filter_by(is_admin=True).first()
#         messages = Message.query.filter(
#             ((Message.sender_id == current_user.id) & (Message.recipient_id == admin.id)) |
#             ((Message.sender_id == admin.id) & (Message.recipient_id == current_user.id))
#         ).order_by(Message.timestamp).all()
    
#     # Mark unread messages as read
#     unread_messages = [m for m in messages if not m.is_read and m.recipient_id == current_user.id]
#     for message in unread_messages:
#         message.is_read = True
    
#     if unread_messages:
#         db.session.commit()
    
#     return jsonify({
#         'messages': [
#             {
#                 'id': message.id,
#                 'content': message.content,
#                 'sender_id': message.sender_id,
#                 'recipient_id': message.recipient_id,
#                 'is_read': message.is_read,
#                 'timestamp': message.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
#                 'is_self': message.sender_id == current_user.id
#             } for message in messages
#         ]
#     })

@admin.route('/api/unread_count')
@login_required
def unread_count():
    count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'count': count})


@admin.route('/admin/messages', methods=['GET'])
def get_all_chats():
    admin_id = session.get('user_id')
    admin = User.query.get(admin_id)

    if not admin or not admin.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chats = Chat.query.all()
    results = []

    for chat in chats:
        last_message = chat.messages.order_by(Message.timestamp.desc()).first()
        results.append({
            'chat_id': chat.id,
            'user_id': chat.user_id,
            'subject': chat.subject,
            'last_message': last_message.content if last_message else "",
            'unread_count': chat.messages.filter_by(is_read=False).count()
        })

    return jsonify(results)


@admin.route('/send_message', methods=['POST'])
def admin_send_message():
    admin_id = current_user.id
    admin = User.query.get(admin_id)

    if not admin or not admin.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat_id = request.json.get('chat_id')
    content = request.json.get('content')

    if not content:
        return jsonify({'error': 'Message is empty'}), 400

    chat = Chat.query.get(chat_id)
    if not chat:
        return jsonify({'error': 'Chat not found'}), 404

    message = Message(chat_id=chat.id, sender_id=admin_id, content=content)
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent'})


@admin.route('/support')
@login_required
def support():
    user = current_user
    if not current_user.is_admin:
        return redirect(url_for('index'))

    # Get users who have sent messages (excluding the admin)
    user_ids = db.session.query(Message.sender_id).filter(Message.sender_id != current_user.id).distinct()
    users = User.query.filter(User.id.in_(user_ids)).all()

    return render_template('admin/admin_messages.html', user=user, users=users)

@admin.route('/get_messages/<int:user_id>')
@login_required
def get_messages(user_id):
    if not current_user.is_admin:
        return jsonify({'error': 'Unauthorized'}), 403

    chat = Chat.query.filter_by(user_id=user_id).first()
    if not chat:
        return jsonify({'messages': []})

    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.timestamp.asc()).all()

    return jsonify({
        'messages': [
            {
                'sender_id': msg.sender_id,
                'recipient_id': user_id if msg.sender_id == 1 else 1,
                'content': msg.content
            } for msg in messages
        ]
    })

@admin.route('/chat_history/<int:user_id>')
@login_required
def chat_history(user_id):
    if not current_user.is_admin:
        abort(403)

    chat = Chat.query.filter_by(user_id=user_id).first()
    if not chat:
        return jsonify([])

    messages = Message.query.filter_by(chat_id=chat.id).order_by(Message.created_at).all()
    return jsonify([{
        'sender_id': msg.sender_id,
        'content': msg.content,
        'timestamp': msg.created_at.strftime('%Y-%m-%d %H:%M:%S')
    } for msg in messages])
