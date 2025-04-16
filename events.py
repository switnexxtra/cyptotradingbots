# from flask_mail import Message
from flask_socketio import emit, join_room
from extensions import socketio
from models.user import Chat, Message
from extensions import db


# @socketio.on("connect")
# def handle_connect():
#     print("Client connected")
    
    
# @socketio.on("user_join")
# def handle_user_join(username):
#     print(f"User {username} Joined!")
    
    
# @socketio.on("new_message")
# def handle_new_message(message):
#     print(f"{message}")

@socketio.on('join_room')
def handle_join(data):
    room = data['room']
    join_room(room)
    
@socketio.on('join')
def on_join(data):
    print('joined Chat')
    user_id = data['user_id']
    room = f"user_{user_id}"
    join_room(room)
    emit('joined', {'room': room})


# @socketio.on('send_message')
# def handle_send_message(data):
#     sender_id = data['sender_id']
#     recipient_id = data['recipient_id']
#     content = data['content']

#     # Get or create chat session
#     chat = Chat.query.filter_by(user_id=recipient_id if sender_id == 1 else sender_id).first()
#     if not chat:
#         chat = Chat(user_id=recipient_id if sender_id == 1 else sender_id)
#         db.session.add(chat)
#         db.session.commit()

#     # Save message
#     message = Message(chat_id=chat.id, sender_id=sender_id, content=content)
#     db.session.add(message)
#     db.session.commit()

#     # Only emit once to each unique room
#     message_data = {
#         'sender_id': sender_id,
#         'recipient_id': recipient_id,
#         'content': content
#     }
    
#     # Create a set of unique rooms to avoid duplicate messages
#     rooms = set([f"user_{recipient_id}", f"user_{sender_id}"])
    
#     # Emit to each unique room
#     for room in rooms:
#         emit('receive_message', message_data, room=room)


@socketio.on('send_message')
def handle_send_message(data):
    sender_id = data['sender_id']
    recipient_id = data['recipient_id']
    content = data['content']

    # Prepare message data to send (not saving to database)
    message_data = {
        'sender_id': sender_id,
        'recipient_id': recipient_id,
        'content': content
    }

    # Emit to both sender and recipient rooms
    rooms = set([f"user_{recipient_id}", f"user_{sender_id}"])
    for room in rooms:
        emit('receive_message', message_data, room=room)
