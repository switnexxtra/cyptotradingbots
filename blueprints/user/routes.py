@user.route('/dashboard')
@login_required
def dashboard():
    current = current_user  # store current_user in a separate variable

    if current is None:
        return redirect(url_for('login'))

    # Get all referrals made by the current user
    referrals = Referral.query.filter_by(referrer_id=current.user_id).all()

    # Fetch details of referred users + amount earned
    referred_users = []
    for referral in referrals:
        referred = User.query.filter_by(user_id=referral.referred_id).first()
        if referred:
            referred_users.append({
                'username': referred.username,
                'email': referred.email,
                'date': referred.created_at.strftime('%Y-%m-%d'),
                'amount_earned': referral.amount_earned
            })

    # Get the active investment of the logged-in user
    investment = Investment.query.filter_by(user_id=current.id, status='active').first()

    # Notifications
    notifications = Notification.query.filter_by(user_id=current.id, is_read=False).order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(user_id=current.id, is_read=False).count()

    # Chats
    chats = Chat.query.filter_by(user_id=current.id).order_by(Chat.created_at.desc()).all()

    # Total pending deposits for current user
    total_pending_deposit = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
        .filter_by(user_id=current.id, transaction_type='Deposit', status='pending').scalar()

    # Total pending withdrawals for current user
    total_pending_withdrawal = db.session.query(func.coalesce(func.sum(Transaction.amount), 0))\
        .filter_by(user_id=current.id, transaction_type='Withdraw', status='pending').scalar()

    return render_template(
        'user/user_dashboard.html',
        user=current,
        investment=investment,
        notifications=notifications,
        unread_count=unread_count,
        total_pending_deposit=total_pending_deposit,
        total_pending_withdrawal=total_pending_withdrawal,
        chats=chats,
        referred_users=referred_users
    )
