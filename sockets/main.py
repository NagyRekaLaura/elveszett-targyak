from flask_socketio import SocketIO
socketio = SocketIO()

def notify_user(user_id, message, title):
    socketio.emit('notification', {'message': message, 'title': title}, room=f'user_{user_id}')
