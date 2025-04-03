from datetime import datetime, timedelta
import os
from flask import Blueprint, abort, current_app, flash, session, jsonify, redirect, render_template, request, url_for
from flask_login import login_required, current_user, logout_user
from models.user import KYC, Chat, Deposit, Investment, InvestmentPlan, Loan, Message, Notification, Transaction, User, PaymentMethods
from extensions import db
from werkzeug.utils import secure_filename


user = Blueprint('user', __name__)


@user.route('/dashboard')
@login_required
def dashboard():
    # Delete all records in Investment table
    # user = current_user
    user = current_user  # Get the logged-in user
    if user is None: # handle the case where somehow current_user is None
        return redirect(url_for('login')) # Redirect to login page
    # investment = Investment.query.filter_by(user_id=current_user.id).first()
    # print(investment.profit_per_day, investment.profit_per_hour, investment.profit_per_min)

    # profit_per_day=round(user.profit_per_day if user.profit_per_day else 0, 6)
    # profit_per_hour=round(user.profit_per_hour if user.profit_per_hour else 0, 6)
    # profit_per_min=round(user.profit_per_min if user.profit_per_min else 0, 6)
    # estimated_profit=round(user.estimated_profit if user.estimated_profit else 0, 6)
    # total_profit=round(user.total_profit if user.total_profit else 0, 6)
        
    # Get the active investment of the logged-in user
    investment = Investment.query.filter_by(user_id=current_user.id, status='active').first()
    print(f"{user.referral_earnings}")

    # Check which records are affected

    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
    # user = User.query.all()
    # register_url = url_for('register', _external=True)  # Get full URL
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.created_at.desc()).all()

    return render_template('user/user_dashboard.html', user=user, investment=investment, notifications=notifications, unread_count=unread_count, chats=chats)
    


@user.route('/chats/new', methods=['GET', 'POST'])
@login_required
def new_chat():
    if request.method == 'POST':
        subject = request.form.get('subject')
        message = request.form.get('message')
        
        if not subject or not message:
            flash('Both subject and message are required')
            return redirect(url_for('user.new_chat'))
        
        # Create a new chat
        chat = Chat(user_id=current_user.id, subject=subject)
        db.session.add(chat)
        db.session.flush()  # to get the chat.id
        
        # Add the first message
        new_message = Message(
            chat_id=chat.id,
            sender_id=current_user.id,
            content=message
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        flash('Your support request has been submitted')
        return redirect(url_for('user.view_chat', chat_id=chat.id))
    
    return render_template('user/new_chat.html')

@user.route('/chats/<int:chat_id>', methods=['GET', 'POST'])
@login_required
def view_chat(chat_id):
    chat = Chat.query.get_or_404(chat_id)
    
    # Security check - users can only view their own chats
    if chat.user_id != current_user.id and not current_user.is_admin:
        flash('You do not have permission to view this chat')
        return redirect(url_for('user.dashboard'))
    
    if request.method == 'POST':
        message_content = request.form.get('message')
        
        if not message_content:
            flash('Message cannot be empty')
            return redirect(url_for('user.view_chat', chat_id=chat_id))
        
        # Add new message
        new_message = Message(
            chat_id=chat.id,
            sender_id=current_user.id,
            content=message_content
        )
        
        db.session.add(new_message)
        db.session.commit()
        
        return redirect(url_for('user.view_chat', chat_id=chat_id))
    
    # Mark unread messages as read if the current user is not the sender
    unread_messages = Message.query.filter_by(
        chat_id=chat.id, 
        is_read=False
    ).filter(Message.sender_id != current_user.id).all()
    
    for message in unread_messages:
        message.is_read = True
    
    db.session.commit()
    
    return render_template('user/view_chat.html', chat=chat)

@user.route('/profile')
@login_required
def profile():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
        
    # user = User.query.all()    
    return render_template('user/profile.html', user=current_user, notifications=notifications, unread_count=unread_count)


@user.route('/update_pin', methods=['POST'])
@login_required
def update_pin():
    user = User.query.get_or_404(current_user.id)
    
    pin = request.form.get('pin')
    confirmpin = request.form.get('confirmpin')
    
    if pin != confirmpin:
        flash('Sorry Pin must match', 'error')
        
    if len(confirmpin) > 6 or len(confirmpin) < 6:
        flash('Sorry Pin must be 6 digits', 'error')
        
    else:
        user.transaction_pin = confirmpin
        db.session.commit()
        flash('Pin Updated Successfully', 'success')
        return redirect('profile')
        
    return render_template('user/profile.html', user=current_user)


@user.route('/update_profile', methods=['POST'])
@login_required
def update_profile():
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id is None:
        flash("User must be logged in to submit KYC", "error")
    
    user = User.query.get_or_404(current_user.id)
    
    user.fname = request.form.get('fname')
    user.username = request.form.get('username')
    user.mobile = request.form.get('mobile')
    user.line1 = request.form.get('line1')
    user.line2 = request.form.get('line2')
    user.postal = request.form.get('postal')
    user.email = request.form.get('email')
    user.dob = request.form.get('dob')
    user.country = request.form.get('country')
    user.region = request.form.get('region')
     
    
    # user.transaction_pin = confirmpin
    db.session.commit()
    flash('Pin Updated Successfully', 'success')
    return redirect('profile')
        


INTEREST_RATE = 0.08  # 8% per month

@user.route('/request_loan', methods=['POST'])
@login_required
def request_loan():
    user = User.query.get_or_404(current_user.id)

    user_id = current_user.id if current_user.is_authenticated else None
    existing_kyc = KYC.query.filter_by(user_id=user_id).first()
    if not existing_kyc or existing_kyc.status != "verified":
        flash("You must complete KYC verification before requesting a loan.", "error")
        return redirect(url_for('user.loan'))

    # Get form data
    amount = request.form.get('amount', type=float)
    duration = request.form.get('duration', type=int)

    if not amount or not duration or amount <= 0 or duration <= 0:
        flash("Invalid loan amount or duration.", "error")
        return redirect(url_for('user.loan'))

    # Ensure the user has at least 30% of the loan amount as balance
    required_balance = 0.30 * amount
    if user.balance < required_balance:
        flash(f"Insufficient balance. You need at least ${required_balance:.2f} as Insurance fee to request this loan.", "error")
        return redirect(url_for('user.loan'))

    # Check if the user has an existing unpaid loan
    existing_loan = Loan.query.filter_by(user_id=user.id, status='unpaid').first()
    if existing_loan:
        flash("You must repay your existing loan before requesting a new one.", "error")
        return redirect(url_for('user.loan'))

    # Calculate total repayment amount with interest
    interest = amount * INTEREST_RATE * duration  # Interest = Principal * Rate * Time
    total_repayment = amount + interest

    # Create a new loan request
    new_loan = Loan(
        user_id=user.id,
        amount=amount,
        duration=duration,
        interest_rate=interest,
        total_due=total_repayment,
        status="pending",
        created_at=datetime.utcnow()
    )

    db.session.add(new_loan)
    
    # Create a transaction record
    transaction = Transaction(
        user_id=user.id,
        transaction_type="Loan Payment",
        transaction_detail=f"Loan request of ",
        amount=loan.amount,
        status="completed",
        created_at=datetime.utcnow()
    )

    # Commit all changes
    db.session.add(transaction)
    db.session.commit()
    flash(f"Loan request submitted successfully! you will be contacted by our support team for further  instruction on how to recieve your ${amount:.2f}. Total repayment: ${total_repayment:.2f} after {duration}", "success")

    return redirect(url_for('user.loan'))


# @user.route('/transfer', methods=['POST'])
# def transfer():
#     data = request.get_json()

#     sender_wallet_id = data.get('sender_wallet_id')
#     receiver_wallet_id = data.get('receiver_wallet_id')
#     sender_email = data.get('sender_email')
#     amount = data.get('amount')

#     # Check if all required fields are provided
#     if not sender_wallet_id or not receiver_wallet_id or not sender_email or not amount:
#         return jsonify({'error': 'All fields are required'}), 400

#     # Find the sender by wallet ID and email
#     sender = User.query.filter_by(wallet_id=sender_wallet_id, email=sender_email).first()
#     if not sender:
#         return jsonify({'error': 'Sender not found'}), 404

#     # Check if sender has sufficient balance
#     if sender.balance < amount:
#         return jsonify({'error': 'Insufficient balance'}), 400

#     # Find the receiver by wallet ID
#     receiver = User.query.filter_by(wallet_id=receiver_wallet_id).first()
#     if not receiver:
#         return jsonify({'error': 'Receiver not found'}), 404

#     # Create a new transaction (status = 'pending' initially)
#     transaction = Transaction(
#         user_id=current_user.id,
#         transaction_type="Transfer",
#         transaction_detail="Transfer of ",
#         amount=amount,
#         status='pending',  # The transaction is pending until the admin approves
#         created_at=datetime.utcnow()
#     )

#     # Deduct the amount from sender's balance
#     sender.balance -= amount
#     db.session.add(transaction)
#     db.session.commit()

#     # Notify the sender and receiver (optional)
#     # Email or notification logic can be added here

#     return jsonify({
#         'message': 'Transaction initiated successfully',
#         'transaction_id': transaction.transaction_id,
#         'status': transaction.status
#     }), 200



# @user.route('/transfer', methods=['POST'])
# def transfer():
#     # Get form data
#     receiver_email = request.form.get('sender_email')
#     receiver_wallet_id = request.form.get('sender_wallet_id')
#     amount = request.form.get('amount').strip()  # Strip any extra spaces

#     # Validate input fields
#     if not receiver_wallet_id or not receiver_email or not amount:
#         flash('All fields are required.', 'error')
#         return redirect(url_for('user.dashboard'))

#     # Check if amount is valid
#     if not amount.replace('.', '', 1).isdigit():
#         flash('Invalid amount entered.', 'error')
#         return redirect(url_for('user.dashboard'))

#     # Convert amount to float
#     amount = float(amount)

#     # Find the sender by email and wallet ID
#     receiver = User.query.filter_by(wallet_id=receiver_wallet_id, email=receiver_email).first()
#     if not receiver:
#         flash('Sorry Sender not found.', 'error')
#         return redirect(url_for('user.dashboard'))

#     # Refresh the sender object to make sure we have the latest balance from the database
#     db.session.refresh(receiver)

#     # Check if sender has sufficient balance
#     sender = current_user
#     if sender.balance < amount:
#         flash('Insufficient balance.', 'error')
#         return redirect(url_for('user.dashboard'))

#     # Assuming the sender is both the sender and the receiver
#     # receiver = sender
#     if receiver == sender:
#         flash("Sorry You can't send money to your self.", 'error')
#         return redirect(url_for('user.dashboard'))

#     # Create a new transaction (status = 'pending' initially)
#     transaction = Transaction(
#         user_id=sender.id,
#         transaction_type="Transfer",
#         transaction_detail="Transfer of funds to the user",
#         amount=amount,
#         status='pending',  # The transaction is pending until the admin approves
#         created_at=datetime.utcnow(),
#         sender_id=sender.user_id,
#         receiver_id=receiver.id
#     )

#     # Deduct the amount from sender's balance
#     sender.balance -= amount
#     db.session.add(transaction)
#     db.session.commit()

#     flash('Transaction initiated successfully.', 'success')
#     return redirect(url_for('user.dashboard'))

@user.route('/transfer', methods=['POST'])
def transfer():
    # Get form data
    receiver_email = request.form.get('sender_email')
    receiver_wallet_id = request.form.get('sender_wallet_id')
    amount = request.form.get('amount').strip()  # Strip any extra spaces
    transaction_pin = request.form.get('transaction_pin')  # Get the entered pin
    print(f"{transaction_pin}")
    

    # Validate input fields
    if not receiver_wallet_id or not receiver_email or not amount:
        flash('All fields are required.', 'error')
        return redirect(url_for('user.dashboard'))

    # Check if amount is valid
    if not amount.replace('.', '', 1).isdigit():
        flash('Invalid amount entered.', 'error')
        return redirect(url_for('user.dashboard'))

    # Convert amount to float
    amount = float(amount)

    # Find the receiver by email and wallet ID
    receiver = User.query.filter_by(wallet_id=receiver_wallet_id, email=receiver_email).first()
    if not receiver:
        flash('Sorry Receiver not found.', 'error')
        return redirect(url_for('user.dashboard'))

    # Refresh the receiver object to make sure we have the latest balance from the database
    db.session.refresh(receiver)

    # Find the sender (current_user)
    sender = current_user

    # Check if sender has sufficient balance
    if sender.balance < amount:
        flash('Insufficient balance.', 'error')
        return redirect(url_for('user.dashboard'))

    print(f"{sender.transaction_pin}")
    # Check if the sender and receiver are the same person
    if receiver == sender:
        flash("Sorry You can't send money to yourself.", 'error')
        return redirect(url_for('user.dashboard'))

    # Check if the entered transaction pin is correct
    # if sender.transaction_pin != transaction_pin:
    #     flash('Incorrect transaction pin.', 'error')
    #     return redirect(url_for('user.dashboard'))

    # Create a new transaction (status = 'pending' initially)
    transaction = Transaction(
        user_id=sender.id,  # This should be sender.id
        transaction_type="Transfer",
        transaction_detail="Transfer of funds to the user",
        amount=amount,
        status='pending',  # The transaction is pending until the admin approves
        created_at=datetime.utcnow(),
        sender_id=sender.id,  # Correct sender_id (sender.id)
        receiver_id=receiver.id
    )

    # Deduct the amount from sender's balance
    sender.balance -= amount
    db.session.add(transaction)
    db.session.commit()

    flash('Transaction initiated successfully.', 'success')
    return redirect(url_for('user.dashboard'))


@user.route('/withdraw', methods=['POST'])
@login_required
def process_withdrawal():
    btc_wallet_address = request.form.get('btc_wallet')
    memo = request.form.get('memo')
    amount = request.form.get('amount')

    # Ensure all fields are provided
    if not btc_wallet_address or not amount:
        flash("All fields are required.", "error")
        return redirect(url_for('user.dashboard'))
    
    if not memo or not amount:
        flash("All fields are required.", "error")
        return redirect(url_for('user.dashboard'))

    try:
        amount = float(amount)
        if amount <= 0:
            flash("Invalid withdrawal amount.", "error")
            return redirect(url_for('user.dashboard'))
    except ValueError:
        flash("Invalid amount entered.", "error")
        return redirect(url_for('user.dashboard'))

    # Ensure user has enough balance
    if current_user.balance < amount:
        flash("Insufficient funds.", "error")
        return redirect(url_for('user.dashboard'))

    # Create a withdrawal transaction
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="Withdraw",
        transaction_detail=f"BTC Withdrawal to {btc_wallet_address}",
        amount=amount,
        status='pending',  # Set to pending for admin approval
        created_at=datetime.utcnow()
    )

    # Deduct balance (will only reflect if admin approves)
    current_user.balance -= amount

    db.session.add(transaction)
    db.session.commit()

    flash("Withdrawal request submitted successfully.", "success")
    return redirect(url_for('user.dashboard'))

@user.route('/get_payment_details', methods=['POST'])
def get_payment_details():
    data = request.get_json()
    method = data.get('method')
    
    if not method:
        return jsonify({'error': 'Payment method is required'}), 400

    # Query the database for the payment method details
    payment_method = PaymentMethods.query.filter_by(method=method).first()
    if not payment_method:
        return jsonify({'error': 'Payment method not found'}), 404

    # Generate the correct image URL
    image_url = url_for('static', filename=f'uploads/{payment_method.image_url}') if payment_method.image_url else ''

    # Return the relevant details as JSON
    return jsonify({
        'details': payment_method.details,
        'account_number': payment_method.account_number,
        'bank_name': payment_method.bank_name,
        'account_name': payment_method.account_name,
        'sub_type': payment_method.sub_type,
        'wallet_address': payment_method.wallet_address,
        'memo': payment_method.memo,
        'network_address': payment_method.network_address,
        'image_url': image_url  # Ensure correct static path
    })

    
    
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@user.route("/deposit", methods=["POST"])
@login_required
def deposit():
    print("Deposit route hit")  # Debugging log

    if not current_user.is_authenticated:
        flash("Unauthorized access. Please log in first.", "danger")
        return jsonify({"success": False, "message": "Unauthorized"}), 401

    amount = request.form.get('amount')
    payment_method = request.form.get('payment_method')
    proof_image = request.files.get('proof_image')

    print(f"Amount: {amount}, Payment Method: {payment_method}, Proof Image: {proof_image}")  # Debugging

    if not amount or float(amount) <= 0 or not payment_method:
        flash("Invalid request. Please check your input.", "danger")
        return jsonify({"success": False, "message": "Invalid request"}), 400

    filename = None
    if proof_image and allowed_file(proof_image.filename):
        filename = save_file(proof_image)

    try:
        # new_deposit = Deposit(
        #     user_id=current_user.id,
        #     amount=float(amount),
        #     payment_method=payment_method,
        #     proof_image=filename
        # )
        # db.session.add(new_deposit)

        new_transaction = Transaction(
            user_id=current_user.id,
            transaction_type="Deposit",
            transaction_detail="Deposit initiated",
            image_url = filename,
            amount=float(amount),
            status="pending",
            created_at=datetime.utcnow()
        )
        db.session.add(new_transaction)
        db.session.commit()

        flash('Your deposit has been queued successfully!', 'success')

        # Redirect to the user's dashboard after success
        return redirect(url_for('user.dashboard'))

    except Exception as e:
        db.session.rollback()  # In case of an error, rollback the transaction
        flash(f"An error occurred while processing your deposit: {str(e)}", "danger")
        return jsonify({"success": False, "message": "Failed to process deposit"}), 500



@user.route('/loan')
@login_required
def loan():
    main_user = User.query.get_or_404(current_user.id)
    user_id = current_user.id if current_user.is_authenticated else None
    existing_kyc = KYC.query.filter_by(user_id=user_id).first()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()
    user_loans = Loan.query.filter_by(user_id=current_user.id).all()
    # if existing_kyc:
    #     flash('Pin Updated Successfully', 'success')
    # return redirect('loan')
    return render_template('user/loan.html', user=current_user, existing_kyc=existing_kyc, notifications=notifications, unread_count=unread_count, loans=user_loans)


@user.route('/update_loan_status/<int:loan_id>', methods=['POST'])
@login_required
def update_loan_status(loan_id):
    loan = Loan.query.filter_by(id=loan_id, user_id=current_user.id).first()
    user = User.query.get(current_user.id)  # Get the current user

    if not loan:
        flash("Loan not found!", "error")
        return redirect(url_for('user.loan'))

    new_status = request.form.get('status')

    # Allow only 'cancelled' and 'paid' as valid statuses
    if new_status not in ["cancelled", "paid"]:
        flash("Invalid loan status update!", "error")
        return redirect(url_for('user.loan'))

    # Only allow cancellation if the loan is still pending
    if new_status == "cancelled" and loan.status != "pending":
        flash("You can only cancel a pending loan.", "error")
        return redirect(url_for('user.loan'))

    # Ensure the total_due is calculated before checking user balance
    if not loan.total_due:
        loan.calculate_interest()
        db.session.commit()

    # Allow payment only if the user has enough balance
    if new_status == "paid":
        if user.balance < loan.total_due:
            flash(f"Insufficient balance. You need at least ${loan.total_due:.2f} to pay off this loan.", "error")
            return redirect(url_for('user.loan'))

        # Deduct total_due from user balance
        user.balance -= loan.total_due
        loan.status = "paid"
        loan.updated_at = datetime.utcnow()

        # Create a transaction record
        transaction = Transaction(
            user_id=user.id,
            transaction_type="Loan Payment",
            transaction_detail=f"Loan repayment of ",
            amount=loan.total_due,
            status="completed",
            created_at=datetime.utcnow()
        )

        # Commit all changes
        db.session.add(transaction)
        flash("Loan paid successfully!", "success")
        return redirect(url_for('user.loan'))

    # If cancelling, update status
    loan.status = new_status
    loan.updated_at = datetime.utcnow()
    db.session.commit()

    flash("Loan status updated successfully!", "success")
    return redirect(url_for('user.loan'))


@user.route('/transactions')
@login_required
def transactions():
    transactions = Transaction.query.filter_by(user_id=current_user.id).order_by(Transaction.created_at.desc()).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('user/transactions.html', user=current_user, transactions=transactions, notifications=notifications, unread_count=unread_count)


@user.route('/claim_bonus', methods=['POST'])
@login_required
def claim_bonus():
    user = User.query.get_or_404(current_user.id)

    if user.pending_bonus > 0:
        user.balance += user.pending_bonus
        db.session.commit()

        # Update notification message for claimed bonus
        notification = Notification.query.filter_by(user_id=user.id, message=f'You received a bonus of ${user.pending_bonus}. Claim it now!').first()
        if notification:
            notification.message = f'Bonus of ${user.pending_bonus} has been claimed!'
            db.session.commit()

        transaction = Transaction(
            user_id=user.id,
            transaction_type="Loan Payment",
            transaction_detail=f"Bonus claim of ",
            amount=user.pending_bonus,
            status="completed",
            created_at=datetime.utcnow()
        )

        # Commit all changes
        db.session.add(transaction)
        flash(f'You have successfully claimed ${user.pending_bonus}!', 'success')
        user.pending_bonus = 0  # Reset pending bonus after claim
        db.session.commit()
    else:
        flash('No bonus available to claim.', 'warning')

    return redirect(url_for('user.dashboard'))


@user.route('/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    return jsonify([{'id': n.id, 'message': n.message, 'created_at': n.created_at.strftime('%Y-%m-%d %H:%M')} for n in notifications])


@user.route('/mark_notification_read/<int:notif_id>')
@login_required
def mark_notification_read(notif_id):
    notification = Notification.query.get_or_404(notif_id)

    if notification.user_id != current_user.id:
        abort(403)

    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    return redirect(url_for('user.dashboard'))

# <----------------------------------- Starting Of Kyc Section <------------------------------- #
@user.route('/kyc')
@login_required
def kyc():
    kyc_records = KYC.query.filter(KYC.status.in_(['pending', 'failed', 'verified'])).all()
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    return render_template('user/kyc.html', user=current_user, kyc_records=kyc_records, notifications=notifications, unread_count=unread_count)


# @user.route('/submit_kyc', methods=['POST'])
# @login_required
# def submit_kyc():
#     user_id = current_user.id if current_user.is_authenticated else None
    
#     if user_id is None:
#         flash("User must be logged in to submit KYC", "error")
#     # Check if KYC record already exists
#     existing_kyc = KYC.query.filter_by(user_id=user_id).first()
#     if existing_kyc:
#         flash('KYC record already exists', 'error')
#         return redirect(request.referrer)

#     # Validate and parse date of birth (dob)
#     dob_str = request.form.get('dob')  # Now it comes as 'YYYY-MM-DD'

#     # Debugging: Print received DOB
#     print(f"Received dob: {dob_str}")

#     # Validate date format
#     try:
#         dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
#     except ValueError:
#         flash("Invalid date format. Please use YYYY-MM-DD.", "error")
#         return redirect(request.referrer)


#     # Create a new KYC record
#     new_kyc = KYC(
#         user_id=user_id,
#         first_name=request.form.get('fName'),
#         last_name=request.form.get('lName'),
#         nationality=request.form.get('Nationality'),
#         dob=dob,  # Correct date format
#         country=request.form.get('country'),
#         state=request.form.get('state'),
#         address=request.form.get('address'),
#         address2=request.form.get('address2'),
#         city=request.form.get('city'),
#         postcode=request.form.get('postcode'),
#         gender=request.form.get('gender'),
#         document_type=request.form.get('document_type'),
#         status='pending'  # Default status
#     )

#     # Save uploaded files if provided
#     # if 'document_front' in request.files:
#     #     new_kyc.document_front = save_file(request.files['document_front'])
#     # if 'document_back' in request.files:
#     #     new_kyc.document_back = save_file(request.files['document_back'])
#     # if 'selfie_with_document' in request.files:
#     #     new_kyc.selfie_with_document = save_file(request.files['selfie_with_document'])
    
    
#     if 'document_front' in request.files and request.files['document_front'].filename:
#         new_kyc.document_front = save_file(request.files['document_front'])

#     if 'document_back' in request.files and request.files['document_back'].filename:
#         new_kyc.document_back = save_file(request.files['document_back'])

#     if 'selfie_with_document' in request.files and request.files['selfie_with_document'].filename:
#         new_kyc.selfie_with_document = save_file(request.files['selfie_with_document'])


#     # Add and commit to database
#     db.session.add(new_kyc)
#     db.session.commit()

#     flash('KYC submitted successfully', 'success')
#     return redirect(request.referrer)


# @user.route('/submit_kyc', methods=['POST'])
# @login_required
# def submit_kyc():
#     user_id = current_user.id if current_user.is_authenticated else None

#     if user_id is None:
#         flash("User must be logged in to submit KYC", "error")
#         return redirect(request.referrer)

#     existing_kyc = KYC.query.filter_by(user_id=user_id).first()

#     if existing_kyc:
#         update_kyc()
#         # flash('KYC record already exists', 'error')
#         return redirect(request.referrer)

#     try:
#         dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d").date()
#     except ValueError:
#         flash("Invalid date format. Please use YYYY-MM-DD.", "error")
#         return redirect(request.referrer)

#     # Create or update KYC record
#     new_kyc = KYC(
#         user_id=user_id,
#         first_name=request.form.get('fName'),
#         last_name=request.form.get('lName'),
#         nationality=request.form.get('Nationality'),
#         dob=dob,
#         country=request.form.get('country'),
#         state=request.form.get('state'),
#         address=request.form.get('address'),
#         address2=request.form.get('address2'),
#         city=request.form.get('city'),
#         postcode=request.form.get('postcode'),
#         gender=request.form.get('gender'),
#         document_type=request.form.get('document_type'),
#         status='pending'
#     )

#     # Save and replace old images if new ones are uploaded
#     new_kyc.document_front = save_file(request.files.get('document_front'), new_kyc.document_front)
#     new_kyc.document_back = save_file(request.files.get('document_back'), new_kyc.document_back)
#     new_kyc.selfie_with_document = save_file(request.files.get('selfie_with_document'), new_kyc.selfie_with_document)

#     db.session.add(new_kyc)
#     db.session.commit()

#     flash('KYC submitted successfully', 'success')
#     return redirect(request.referrer)


# @user.route('/update_kyc', methods=['POST'])
# @login_required
# def update_kyc():
#     print("update_kyc function is being called")  # Debugging print
#     user_id = current_user.id if current_user.is_authenticated else None
    
#     if user_id is None:
#         flash("User must be logged in to update KYC", "error")
#         return redirect(request.referrer)

#     existing_kyc = KYC.query.filter_by(user_id=user_id).first()
#     if not existing_kyc:
#         flash("No KYC record found. Please submit KYC first.", "error")
#         return redirect(request.referrer)
    
#     # Update KYC details
#     existing_kyc.first_name = request.form.get('fName')
#     existing_kyc.last_name = request.form.get('lName')
#     existing_kyc.nationality = request.form.get('Nationality')
#     existing_kyc.country = request.form.get('country')
#     existing_kyc.state = request.form.get('state')
#     existing_kyc.address = request.form.get('address')
#     existing_kyc.address2 = request.form.get('address2')
#     existing_kyc.city = request.form.get('city')
#     existing_kyc.postcode = request.form.get('postcode')
#     existing_kyc.gender = request.form.get('gender')
#     existing_kyc.document_type = request.form.get('document_type')
    
#     # Validate and update date of birth
#     dob_str = request.form.get('dob')
#     if dob_str:
#         try:
#             existing_kyc.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
#         except ValueError:
#             flash("Invalid date format. Please use YYYY-MM-DD.", "error")
#             return redirect(request.referrer)
    
#     # Handle file uploads, keeping existing files if no new ones are uploaded

#     if 'document_front' in request.files and request.files['document_front'].filename:
#         print(request.files['document_front'].filename)
#         existing_kyc.document_front = save_file(request.files['document_front'])

#     if 'document_back' in request.files and request.files['document_back'].filename:
#         print(request.files['document_back'].filename)
#         existing_kyc.document_back = save_file(request.files['document_back'])

#     if 'selfie_with_document' in request.files and request.files['selfie_with_document'].filename:
#         print(request.files['selfie_with_document'].filename)
#         existing_kyc.selfie_with_document = save_file(request.files['selfie_with_document'])

#     db.session.commit()
#     flash("KYC updated successfully", "success")
#     return redirect(request.referrer)


# def save_file(file, old_filename=None):
#     if not file or file.filename == "":
#         print("No new file uploaded, keeping old file:", old_filename)
#         return old_filename  

#     UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']
#     print("UPLOAD_FOLDER:", UPLOAD_FOLDER)  # Debugging step

#     filename = secure_filename(file.filename)
#     file_path = os.path.join(UPLOAD_FOLDER, filename)
    
#     # Ensure the folder exists
#     if not os.path.exists(UPLOAD_FOLDER):
#         os.makedirs(UPLOAD_FOLDER)

#     # Delete old file if it exists
#     if old_filename:
#         old_file_path = os.path.join(UPLOAD_FOLDER, old_filename)
#         if os.path.exists(old_file_path):
#             os.remove(old_file_path)
#             print("Deleted old file:", old_file_path)

#     # Save new file
#     file.save(file_path)
#     print("Saved new file:", file_path)

#     return filename  

@user.route('/submit_kyc', methods=['POST'])
@login_required
def submit_kyc():
    user_id = current_user.id if current_user.is_authenticated else None

    if user_id is None:
        flash("User must be logged in to submit KYC", "error")
        return redirect(request.referrer)

    existing_kyc = KYC.query.filter_by(user_id=user_id).first()

    if existing_kyc:
        update_kyc()
        return redirect(request.referrer)

    try:
        dob = datetime.strptime(request.form.get('dob'), "%Y-%m-%d").date()
    except ValueError:
        flash("Invalid date format. Please use YYYY-MM-DD.", "error")
        return redirect(request.referrer)

    new_kyc = KYC(
        user_id=user_id,
        first_name=request.form.get('fName'),
        last_name=request.form.get('lName'),
        nationality=request.form.get('Nationality'),
        dob=dob,
        country=request.form.get('country'),
        state=request.form.get('state'),
        address=request.form.get('address'),
        address2=request.form.get('address2'),
        city=request.form.get('city'),
        postcode=request.form.get('postcode'),
        gender=request.form.get('gender'),
        document_type=request.form.get('document_type'),
        status='pending'
    )

    # Save and replace old images if new ones are uploaded
    new_kyc.document_front = save_file(request.files.get('document_front'), new_kyc.document_front)
    new_kyc.document_back = save_file(request.files.get('document_back'), new_kyc.document_back)
    new_kyc.selfie_with_document = save_file(request.files.get('selfie_with_document'), new_kyc.selfie_with_document)
    
    # Store driver's license and national ID
    new_kyc.driver_license_front = save_file(request.files.get('driver_license_front'))
    new_kyc.driver_license_back = save_file(request.files.get('driver_license_back'))
    new_kyc.national_id_front = save_file(request.files.get('national_id_front'))
    new_kyc.national_id_back = save_file(request.files.get('national_id_back'))

    db.session.add(new_kyc)
    db.session.commit()

    flash('KYC submitted successfully', 'success')
    return redirect(request.referrer)


@user.route('/update_kyc', methods=['POST'])
@login_required
def update_kyc():
    print("update_kyc function is being called")  # Debugging print
    user_id = current_user.id if current_user.is_authenticated else None
    
    if user_id is None:
        flash("User must be logged in to update KYC", "error")
        return redirect(request.referrer)

    existing_kyc = KYC.query.filter_by(user_id=user_id).first()
    if not existing_kyc:
        flash("No KYC record found. Please submit KYC first.", "error")
        return redirect(request.referrer)
    
    # Update KYC details
    existing_kyc.first_name = request.form.get('fName')
    existing_kyc.last_name = request.form.get('lName')
    existing_kyc.nationality = request.form.get('Nationality')
    existing_kyc.country = request.form.get('country')
    existing_kyc.state = request.form.get('state')
    existing_kyc.address = request.form.get('address')
    existing_kyc.address2 = request.form.get('address2')
    existing_kyc.city = request.form.get('city')
    existing_kyc.postcode = request.form.get('postcode')
    existing_kyc.gender = request.form.get('gender')
    existing_kyc.document_type = request.form.get('document_type')
    
    # Validate and update date of birth
    dob_str = request.form.get('dob')
    if dob_str:
        try:
            existing_kyc.dob = datetime.strptime(dob_str, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format. Please use YYYY-MM-DD.", "error")
            return redirect(request.referrer)
    
    # Handle file uploads, keeping existing files if no new ones are uploaded

    if 'document_front' in request.files and request.files['document_front'].filename:
        existing_kyc.document_front = save_file(request.files['document_front'])

    if 'document_back' in request.files and request.files['document_back'].filename:
        existing_kyc.document_back = save_file(request.files['document_back'])

    if 'selfie_with_document' in request.files and request.files['selfie_with_document'].filename:
        existing_kyc.selfie_with_document = save_file(request.files['selfie_with_document'])
    
    # Handle driver's license and national ID
    if 'driver_license_front' in request.files and request.files['driver_license_front'].filename:
        existing_kyc.driver_license_front = save_file(request.files['driver_license_front'])
    
    if 'driver_license_back' in request.files and request.files['driver_license_back'].filename:
        existing_kyc.driver_license_back = save_file(request.files['driver_license_back'])
    
    if 'national_id_front' in request.files and request.files['national_id_front'].filename:
        existing_kyc.national_id_front = save_file(request.files['national_id_front'])
    
    if 'national_id_back' in request.files and request.files['national_id_back'].filename:
        existing_kyc.national_id_back = save_file(request.files['national_id_back'])

    db.session.commit()
    flash("KYC updated successfully", "success")
    return redirect(request.referrer)


def save_file(file, old_filename=None):
    if not file or file.filename == "":
        return old_filename  

    UPLOAD_FOLDER = current_app.config['UPLOAD_FOLDER']

    filename = secure_filename(file.filename)
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

    if old_filename:
        old_file_path = os.path.join(UPLOAD_FOLDER, old_filename)
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    file.save(file_path)
    return filename

# <----------------------------------- End Of Kyc Section <------------------------------- #

@user.route('/support')
@login_required
def support():
    return render_template('user/support.html')


# @user.route("/deposit", methods=["POST"])
# @login_required
# def deposit():
#     if not current_user.is_authenticated:
#         return jsonify({"success": False, "message": "Unauthorized"}), 401

#     data = request.json
#     amount = data.get("amount")
#     method = data.get("method")

#     if not amount or amount <= 0 or not method:
#         return jsonify({"success": False, "message": "Invalid request"}), 400

#     new_transaction = Transaction(
#         user_id=current_user.user_id,
#         transaction_type="Deposit",
#         amount=amount,
#         status="pending",
#         created_at=datetime.utcnow()
#     )
#     db.session.add(new_transaction)
#     db.session.commit()

#     return jsonify({"success": True, "message": "Deposit submitted"})

# @user.route('/investment')
# @login_required
# def investment():
#     plans = InvestmentPlan.query.all()
#     user_investments = Investment.query.filter_by(user_id=current_user.id).all()  # Fetch user investments
#     return render_template('user/investment.html', user=current_user, plans=plans, user_investments=user_investments)


# @user.route('/investment')
# @login_required
# def investment():
#     plans = InvestmentPlan.query.all()
#     user_investments = Investment.query.filter_by(user_id=current_user.id).all()
    
#     # Create a dictionary to map plan_id to investment objects
#     plan_investments = {}
#     for inv in user_investments:
#         if inv.plan_id in plan_investments:
#             plan_investments[inv.plan_id].append(inv)
#         else:
#             plan_investments[inv.plan_id] = [inv]
    
#     # Calculate the highest plan that the user is eligible for
#     from sqlalchemy.sql import func
#     max_investment = db.session.query(func.max(Investment.amount)).filter_by(user_id=current_user.id).scalar()
#     max_investment = max_investment if max_investment is not None else 0
    
#     # Get the highest eligible investment plan based on the user's max investment
#     highest_plan = InvestmentPlan.query.filter(
#         InvestmentPlan.min_amount <= max_investment,
#         InvestmentPlan.max_amount >= max_investment
#     ).order_by(InvestmentPlan.max_amount.desc()).first()
    
#     highest_plan_id = highest_plan.id if highest_plan else 0
    
#     return render_template(
#         'user/investment.html', 
#         user=current_user, 
#         plans=plans, 
#         user_investments=user_investments,
#         plan_investments=plan_investments,
#         highest_plan=highest_plan_id,
#         max_investment=max_investment
#     )

@user.route('/investment')
@login_required
def investment():
    from datetime import datetime  # Add this import
    
    plans = InvestmentPlan.query.all()
    user_investments = Investment.query.filter_by(user_id=current_user.id).all()
    
    # Create a dictionary to map plan_id to investment objects
    plan_investments = {}
    for inv in user_investments:
        if inv.plan_id in plan_investments:
            plan_investments[inv.plan_id].append(inv)
        else:
            plan_investments[inv.plan_id] = [inv]
    
    # Calculate the highest plan that the user is eligible for
    from sqlalchemy.sql import func
    max_investment = db.session.query(func.max(Investment.amount)).filter_by(user_id=current_user.id).scalar()
    max_investment = max_investment if max_investment is not None else 0
    
    # Get the highest eligible investment plan based on the user's max investment
    # Determine the user's highest enrolled plan based on min_amount
    user_highest_plan = (
        db.session.query(InvestmentPlan)
        .join(Investment, Investment.plan_id == InvestmentPlan.id)
        .filter(Investment.user_id == current_user.id)
        .order_by(InvestmentPlan.min_amount.desc())
        .first()
    )
    user_highest_min_amount = user_highest_plan.min_amount if user_highest_plan else 0

    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current_user.id, is_read=False).count()

    
    return render_template(
        'user/investment.html', 
        user=current_user, 
        plans=plans, 
        user_investments=user_investments,
        plan_investments=plan_investments,
        highest_plan=user_highest_plan,
        user_highest_min_amount=user_highest_min_amount,
        max_investment=max_investment,
        now=datetime.now(),
        notifications=notifications, 
        unread_count=unread_count
    )
    
    
# @user.route('/subscribe/<int:plan_id>', methods=['POST'])
# @login_required
# def subscribe(plan_id):
#     plan = InvestmentPlan.query.get_or_404(plan_id)
#     amount = float(request.form.get('amount'))

#     if amount < plan.min_amount or amount > plan.max_amount:
#         flash("Amount must be within the plan limits!", "danger")
#         return redirect(url_for('user.investment'))

#     if current_user.balance < amount:
#         flash("Insufficient balance! Please fund your wallet.", "danger")
#         return redirect(url_for('user.investment'))

#     # Deduct the amount from the user's balance
#     current_user.balance -= amount
#     current_user.total_investment += amount

#     # Investment duration in days
#     duration_days = plan.duration * 30  

#     # Calculate profits based on ROI
#     total_profit = (plan.roi / 100 * amount) + amount  # Including initial investment
#     estimated_profit = total_profit
#     profit_per_day = (total_profit - amount) / duration_days
#     profit_per_hour = profit_per_day / 24
#     profit_per_min = profit_per_hour / 60
#     profit_per_sec = profit_per_min / 60  # Profit per second

#     # Track investment start time
#     start_time = datetime.utcnow()

#     # Calculate revenue for today so far
#     seconds_elapsed_today = (datetime.utcnow() - start_time.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
#     daily_revenue = profit_per_sec * seconds_elapsed_today

#     # Create a new investment record
#     end_date = datetime.utcnow() + timedelta(days=duration_days)
#     start_date = datetime.utcnow()
#     investment = Investment(
#         user_id=current_user.id,
#         plan_id=plan.id,
#         amount=amount,
#         roi=plan.roi,
#         start_date=start_date,
#         end_date=end_date,
#         total_profit=total_profit, 
#         estimated_profit=estimated_profit,
#         profit_per_day=profit_per_day,
#         profit_per_hour=profit_per_hour,
#         profit_per_min=profit_per_min,
#         profit_per_sec=profit_per_sec,
#         start_time=start_time,
#         revenue_today=daily_revenue
#     )
#     db.session.add(investment)

#     # Create a transaction history record
#     transaction = Transaction(
#         user_id=current_user.id,
#         transaction_type="Investment",
#         transaction_detail=f"Subscribed to {plan.name}",
#         amount=amount,
#         status="completed"
#     )
#     db.session.add(transaction)

#     # Commit the changes
#     db.session.commit()

#     flash("Investment successful! Transaction recorded.", "success")
#     return redirect(url_for('user.dashboard'))

# @user.route('/upgrade/<int:plan_id>', methods=['POST'])
# @login_required
# def upgrade(plan_id):
#     from sqlalchemy.sql import func
#     plan = InvestmentPlan.query.get_or_404(plan_id)
#     current_plan_id = request.form.get("current_plan")  # Get selected plan to upgrade
#     current_investment = Investment.query.filter_by(user_id=current_user.id, plan_id=current_plan_id, status='active').first()

#     # Get the user's highest investment amount
#     max_investment = db.session.query(func.max(Investment.amount)).filter_by(user_id=current_user.id).scalar()
#     max_investment = max_investment if max_investment is not None else 0

#     # Get the highest eligible investment plan based on the user's max investment
#     highest_plan = InvestmentPlan.query.filter(
#         InvestmentPlan.min_amount <= max_investment,
#         InvestmentPlan.max_amount >= max_investment
#     ).order_by(InvestmentPlan.max_amount.desc()).first()
    
#     highest_plan_id = highest_plan.id if highest_plan else 0  # Default to 0 if no plan found

#     if not current_investment:
#         flash("You must have an active investment to upgrade.", "danger")
#         return redirect(url_for('user.investment'))

#     if plan.min_amount <= current_investment.amount:
#         flash("You must upgrade to a higher plan!", "danger")
#         return redirect(url_for('user.investment'))

#     additional_amount = plan.min_amount - current_investment.amount

#     if current_user.balance < additional_amount:
#         flash("Insufficient balance to upgrade!", "danger")
#         return redirect(url_for('user.investment'))

#     # Deduct upgrade amount
#     current_user.balance -= additional_amount

#     # Update investment details
#     current_investment.plan_id = plan.id
#     current_investment.amount = plan.min_amount
#     current_investment.roi = plan.roi
#     current_investment.end_date = datetime.utcnow() + timedelta(days=plan.duration * 30)

#     # Recalculate profits
#     total_profit = (plan.roi / 100 * plan.min_amount) + plan.min_amount  
#     duration_days = plan.duration * 30
#     profit_per_day = (total_profit - plan.min_amount) / duration_days
#     profit_per_sec = profit_per_day / 24 / 60 / 60

#     # Update investment record
#     current_investment.total_profit = total_profit
#     current_investment.profit_per_day = profit_per_day
#     current_investment.profit_per_sec = profit_per_sec
#     current_investment.start_time = datetime.utcnow()
    
#     # Transaction history
#     transaction = Transaction(
#         user_id=current_user.id,
#         transaction_type="Upgrade",
#         transaction_detail=f"Upgraded to {plan.name}",
#         amount=additional_amount,
#         status="completed"
#     )
#     db.session.add(transaction)

#     db.session.commit()

#     flash("Upgrade successful!", "success")
#     return redirect(url_for('user.dashboard'))

@user.route('/subscribe/<int:plan_id>', methods=['POST']) 
@login_required
def subscribe(plan_id):
    plan = InvestmentPlan.query.get_or_404(plan_id)
    amount = float(request.form.get('amount'))

    if amount < plan.min_amount or amount > plan.max_amount:
        flash("Amount must be within the plan limits!", "danger")
        return redirect(url_for('user.investment'))

    if current_user.balance < amount:
        flash("Insufficient balance! Please fund your wallet.", "danger")
        return redirect(url_for('user.investment'))

    # Check if the user already has an active investment in this plan
    existing_investment = Investment.query.filter_by(user_id=current_user.id, plan_id=plan.id, status='active').first()

    if existing_investment:
        # Update existing investment balance and profit calculations
        existing_investment.amount += amount
        current_user.total_investment += amount
        
        # Recalculate profits based on the new amount
        total_profit = (plan.roi / 100 * existing_investment.amount) + existing_investment.amount
        duration_days = plan.duration * 30  # Convert months to days
        
        existing_investment.total_profit = total_profit
        existing_investment.estimated_profit = total_profit
        existing_investment.profit_per_day = (total_profit - existing_investment.amount) / duration_days
        existing_investment.profit_per_hour = existing_investment.profit_per_day / 24
        existing_investment.profit_per_min = existing_investment.profit_per_hour / 60
        existing_investment.profit_per_sec = existing_investment.profit_per_min / 60
        
    else:
        # Deduct the amount from the user's balance
        current_user.balance -= amount
        current_user.total_investment += amount

        # Investment duration in days
        duration_days = plan.duration * 30  

        # Calculate profits based on ROI
        total_profit = (plan.roi / 100 * amount) + amount  # Including initial investment
        estimated_profit = total_profit
        profit_per_day = (total_profit - amount) / duration_days
        profit_per_hour = profit_per_day / 24
        profit_per_min = profit_per_hour / 60
        profit_per_sec = profit_per_min / 60  # Profit per second

        # Track investment start time
        start_time = datetime.utcnow()

        # Calculate revenue for today so far
        now = datetime.utcnow()
        seconds_elapsed_today = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
        revenue_today = profit_per_sec * seconds_elapsed_today

        # Create a new investment record
        end_date = datetime.utcnow() + timedelta(days=duration_days)
        start_date = datetime.utcnow()
        investment = Investment(
            user_id=current_user.id,
            plan_id=plan.id,
            amount=amount,
            roi=plan.roi,
            start_date=start_date,
            end_date=end_date,
            total_profit=total_profit, 
            estimated_profit=estimated_profit,
            profit_per_day=profit_per_day,
            profit_per_hour=profit_per_hour,
            profit_per_min=profit_per_min,
            profit_per_sec=profit_per_sec,
            start_time=start_time,
            revenue_today=revenue_today
        )
        db.session.add(investment)

    # Deduct the amount from the user's balance
    current_user.balance -= amount

    # Create a transaction history record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="Investment",
        transaction_detail=f"Subscribed to {plan.name}",
        amount=amount,
        status="completed"
    )
    db.session.add(transaction)

    # Commit the changes
    db.session.commit()

    flash("Investment successful! Transaction recorded.", "success")
    return redirect(url_for('user.dashboard'))




@user.route('/upgrade/<int:plan_id>', methods=['POST'])
@login_required
def upgrade(plan_id):
    from sqlalchemy.sql import func
    plan = InvestmentPlan.query.get_or_404(plan_id)
    current_plan_id = request.form.get("current_plan")  # Get selected plan to upgrade
    current_investment = Investment.query.filter_by(user_id=current_user.id, plan_id=current_plan_id, status='active').first()

    if not current_investment:
        flash("You must have an active investment to upgrade.", "danger")
        return redirect(url_for('user.investment'))

    if plan.min_amount <= current_investment.amount:
        flash("You must upgrade to a higher plan!", "danger")
        return redirect(url_for('user.investment'))

    additional_amount = plan.min_amount - current_investment.amount

    if current_user.balance < additional_amount:
        flash("Insufficient balance to upgrade!", "danger")
        return redirect(url_for('user.investment'))

    # Deduct upgrade amount
    current_user.balance -= additional_amount

    # Update investment details
    current_investment.plan_id = plan.id
    current_investment.amount = plan.min_amount
    current_investment.roi = plan.roi
    current_investment.end_date = datetime.utcnow() + timedelta(days=plan.duration * 30)

    # Recalculate profits
    total_profit = (plan.roi / 100 * plan.min_amount) + plan.min_amount  
    duration_days = plan.duration * 30
    profit_per_day = (total_profit - plan.min_amount) / duration_days
    profit_per_sec = profit_per_day / 24 / 60 / 60

    # Calculate revenue for today
    now = datetime.utcnow()
    seconds_elapsed_today = (now - now.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
    revenue_today = profit_per_sec * seconds_elapsed_today

    # Update investment record
    current_investment.total_profit = total_profit
    current_investment.profit_per_day = profit_per_day
    current_investment.profit_per_sec = profit_per_sec
    current_investment.start_time = datetime.utcnow()
    current_investment.revenue_today = revenue_today

    # Transaction history
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="Upgrade",
        transaction_detail=f"Upgraded to {plan.name}",
        amount=additional_amount,
        status="completed"
    )
    db.session.add(transaction)

    db.session.commit()

    flash("Upgrade successful!", "success")
    return redirect(url_for('user.dashboard'))


@user.route('/withdraw_from_plan/<int:plan_id>', methods=['POST'])
@login_required
def withdraw_from_plan(plan_id):
    # Get all of the user's investments for this plan
    investments = Investment.query.filter_by(
        user_id=current_user.id, 
        plan_id=plan_id,
        status='active'
    ).all()
    
    if not investments:
        flash("No active investments found for this plan!", "danger")
        return redirect(url_for('user.investment'))
    
    withdraw_amount = request.form.get("withdraw_amount", type=float)
    
    if withdraw_amount <= 0:
        flash("Invalid withdrawal amount!", "danger")
        return redirect(url_for('user.investment'))
    
    today = datetime.utcnow()
    
    # Calculate total available balance across all investments in this plan
    total_available = sum(inv.amount + inv.total_profit for inv in investments)
    
    if withdraw_amount > total_available:
        flash(f"Cannot withdraw more than available amount (${total_available:.2f})", "danger")
        return redirect(url_for('user.investment'))
    
    # Apply penalty if any investment is still within its term
    has_early_withdrawal = any(today < inv.end_date for inv in investments)
    
    if has_early_withdrawal:
        penalty = withdraw_amount * 0.30  # 30% penalty
        amount_to_receive = withdraw_amount - penalty
        transaction_detail = f"Early withdrawal of ${withdraw_amount:.2f} from {investments[0].plan.name} plan (30% penalty: ${penalty:.2f})"
    else:
        amount_to_receive = withdraw_amount
        transaction_detail = f"Withdrawal of ${withdraw_amount:.2f} from completed {investments[0].plan.name} plan"
    
    # Ensure user doesn't get a negative amount
    if amount_to_receive < 0:
        amount_to_receive = 0
    
    # Deduct the withdrawn amount from investments, starting with the oldest
    remaining_amount = withdraw_amount
    sorted_investments = sorted(investments, key=lambda inv: inv.start_date)
    
    for inv in sorted_investments:
        if remaining_amount <= 0:
            break
            
        available_in_this_inv = inv.amount + inv.total_profit
        amount_to_deduct = min(available_in_this_inv, remaining_amount)
        
        inv.amount -= amount_to_deduct
        remaining_amount -= amount_to_deduct
        
        if inv.amount <= 0:
            inv.status = 'completed'
    
    # Update user balance
    current_user.balance += amount_to_receive
    
    # Create transaction record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="Investment Withdrawal",
        transaction_detail=transaction_detail,
        amount=amount_to_receive,
        status="completed"
    )
    db.session.add(transaction)
    
    # Commit all changes
    db.session.commit()
    
    flash(f"Withdrawal successful! You received ${amount_to_receive:.2f}.", "success")
    return redirect(url_for('user.investment'))

# Keep the original withdrawal function for backward compatibility or direct investment withdrawals
@user.route('/withdraw_investment/<int:investment_id>', methods=['POST'])
@login_required
def withdraw_investment(investment_id):
    investment = Investment.query.get_or_404(investment_id)

    if investment.user_id != current_user.id:
        flash("Unauthorized withdrawal attempt!", "danger")
        return redirect(url_for('user.dashboard'))

    withdraw_amount = request.form.get("withdraw_amount", type=float)

    if withdraw_amount <= 0:
        flash("Invalid withdrawal amount!", "danger")
        return redirect(url_for('user.investment'))

    today = datetime.utcnow()

    # Check if the user has enough funds in this investment
    total_withdrawable = investment.amount + investment.total_profit  # Total available balance
    if withdraw_amount > total_withdrawable:
        flash(f"Cannot withdraw more than available amount (${total_withdrawable:.2f})", "danger")
        return redirect(url_for('user.investment'))

    # Apply penalty if withdrawing early
    if today < investment.end_date:
        penalty = withdraw_amount * 0.30  # 30% of the requested withdrawal amount
        amount_to_receive = withdraw_amount - penalty
        transaction_detail = f"Early withdrawal of ${withdraw_amount:.2f} (30% penalty applied: ${penalty:.2f})"
    else:
        amount_to_receive = withdraw_amount
        transaction_detail = f"Withdrawal of ${withdraw_amount:.2f} from completed investment"

    # Ensure user does not get a negative amount
    if amount_to_receive < 0:
        amount_to_receive = 0  # Set to zero to prevent issues

    # Deduct the withdrawn amount from the investment
    investment.amount -= withdraw_amount
    if investment.amount <= 0:
        investment.status = 'completed'  # Mark investment as completed if fully withdrawn

    # Update user balance
    current_user.balance += amount_to_receive

    # Create a transaction history record
    transaction = Transaction(
        user_id=current_user.id,
        transaction_type="Investment Withdrawal",
        transaction_detail=transaction_detail,
        amount=amount_to_receive,
        status="completed"
    )
    db.session.add(transaction)

    # Commit the changes
    db.session.commit()

    flash(f"Withdrawal successful! You received ${amount_to_receive:.2f}. Transaction recorded.", "success")
    return redirect(url_for('user.investment'))