from .main import socketio, notify_user
from database import db, User, Attachment, Messages
from flask_login import current_user, login_required
from flask_socketio import emit, join_room, leave_room, rooms
from datetime import datetime
from flask import request
from functools import wraps
import html
from sqlalchemy import func, case, or_

# Online users tracking
online_users = {}

def authenticated_only(f):
    """Decorator to only allow authenticated users"""
    @wraps(f)
    def wrapped(*args, **kwargs):
        if not current_user.is_authenticated:
            emit('error', {'message': 'Not authenticated'})
            return
        return f(*args, **kwargs)
    return wrapped

@socketio.on('connect')
def handle_connect(auth):
    """Handle user connection"""
    if current_user.is_authenticated:
        user_id = current_user.id
        online_users[user_id] = {
            'sid': request.sid,
            'username': current_user.username,
            'name': current_user.name
        }
        # Join private room for this user
        join_room(f'user_{user_id}')
        print(f'User {current_user.username} (ID: {user_id}) connected')
    else:
        print('Unauthenticated connection attempt')

@socketio.on('disconnect')
def handle_disconnect():
    """Handle user disconnection"""
    if current_user.is_authenticated:
        user_id = current_user.id
        if user_id in online_users:
            del online_users[user_id]
        leave_room(f'user_{user_id}')
        print(f'User {current_user.username} (ID: {user_id}) disconnected')

@socketio.on('get_conversations')
@authenticated_only
def handle_get_conversations():
    """Get all conversations for the current user"""
    user_id = current_user.id
    
    conversation_list = []
    
    # ============== SYSTEM CHAT ==============
    # Alapértelmezett rendszer-chat üdvözlő üzenettel
    system_welcome_message = "Üdvözlünk az Elveszett Tárgyak Közösségében! 🎉\n\nEbben a csatornában információkat találsz a platformról. Ha bármilyen kérdésed van, írj bátran!"
    
    conversation_list.append({
        'id': 0,  # Special ID for system chat
        'name': 'Rendszer',
        'pic': '/static/attachments/system.png',
        'lastMsg': system_welcome_message[:30] + '...',
        'time': current_user.created_at.strftime('%H:%M'),
        'status': 'online',
        'unread': 0,
        'is_system': True,
        'last_msg_time': current_user.created_at  # Always first when sorting
    })
    # ============== END SYSTEM CHAT ==============
    
    # Get unique partners from messages where user is sender or receiver
    # Gather all partner IDs
    sent_to = db.session.query(Messages.receiver_id).filter(Messages.sender_id == user_id).distinct().all()
    received_from = db.session.query(Messages.sender_id).filter(Messages.receiver_id == user_id).distinct().all()
    
    partner_ids = set([row[0] for row in sent_to] + [row[0] for row in received_from])

    for partner_id in partner_ids:
        partner = User.query.get(partner_id)
        if not partner:
            continue
        
        # Get last message
        last_msg = Messages.query.filter(
            db.or_(
                db.and_(Messages.sender_id == user_id, Messages.receiver_id == partner_id),
                db.and_(Messages.sender_id == partner_id, Messages.receiver_id == user_id)
            )
        ).order_by(Messages.created_at.desc()).first()
        
        # Count unread messages
        unread_count = Messages.query.filter(
            Messages.sender_id == partner_id,
            Messages.receiver_id == user_id,
            Messages.seen == False
        ).count()
        
        conversation_list.append({
            'id': partner.id,
            'name': partner.name or partner.username,
            'pic': f'/static/attachments/{Attachment.query.get(partner.profile_picture).filename}' if partner.profile_picture else '/static/default-avatar.png',
            'lastMsg': html.escape(last_msg.content[:30]) if last_msg else '',
            'time': last_msg.created_at.strftime('%H:%M') if last_msg else '',
            'status': 'online' if partner.id in online_users else 'offline',
            'unread': unread_count,
            'last_msg_time': last_msg.created_at if last_msg else None
        })
    
    # Rendezés az utolsó üzenet ideje szerint
    conversation_list.sort(key=lambda x: x['last_msg_time'] if x['last_msg_time'] else datetime.min, reverse=True)
    
    # Eltávolítsa az ideiglenes 'last_msg_time' mezőt
    for conv in conversation_list:
        del conv['last_msg_time']
    
   
    
    emit('conversations', conversation_list)

@socketio.on('get_messages')
@authenticated_only
def handle_get_messages(data):
    """Get all messages between current user and a partner"""
    user_id = current_user.id
    partner_id = data.get('partner_id')
    
    if not partner_id and partner_id != 0:
        emit('error', {'message': 'Partner ID required'})
        return
    
    messages_list = []
    
    # ============== SYSTEM CHAT ==============
    # Ha a partner_id 0, akkor a system chat-ről van szó
    if partner_id == 0:
        system_welcome_message = "Üdvözlünk az Elveszett Tárgyak Közösségében! 🎉\n\nEbben a csatornában információkat találsz a platformról. Ha bármilyen kérdésed van, írj bátran!"
        messages_list.append({
            'id': 0,
            'type': 'other',
            'text': system_welcome_message,
            'time': '09:00',
            'seen': True
        })
        emit('messages', messages_list)
        return
    # ============== END SYSTEM CHAT ==============
    
    # Verify partner exists
    partner = User.query.get(partner_id)
    if not partner:
        emit('error', {'message': 'Partner not found'})
        return
    
    # Get all messages
    messages = Messages.query.filter(
        db.or_(
            db.and_(Messages.sender_id == user_id, Messages.receiver_id == partner_id),
            db.and_(Messages.sender_id == partner_id, Messages.receiver_id == user_id)
        )
    ).order_by(Messages.created_at.asc()).all()
    
    # Mark all as seen
    for msg in messages:
        if msg.receiver_id == user_id and not msg.seen:
            msg.seen = True
    db.session.commit()
    
    for msg in messages:
        messages_list.append({
            'id': msg.id,
            'type': 'user' if msg.sender_id == user_id else 'other',
            'text': html.escape(msg.content),
            'time': msg.created_at.strftime('%H:%M'),
            'seen': msg.seen
        })
    
    emit('messages', messages_list)

@socketio.on('send_message')
@authenticated_only
def handle_send_message(data):
    """Send a message to a partner"""
    user_id = current_user.id
    partner_id = data.get('partner_id')
    content = data.get('text', '').strip()
    
    # ============== PREVENT SYSTEM CHAT ==============
    # Ne engedj üzenetet a system chathez
    if partner_id == 0:
        emit('error', {'message': 'Nem küldhetsz üzenetet a Rendszer csatornához'})
        return
    # ============== END PREVENT SYSTEM CHAT ==============
    
    # Validate
    if not partner_id or not content:
        emit('error', {'message': 'Partner ID and message content required'})
        return
    
    if len(content) > 5000:
        emit('error', {'message': 'Message too long'})
        return
    
    # Verify partner exists
    partner = User.query.get(partner_id)
    if not partner:
        emit('error', {'message': 'Partner not found'})
        return
    
    # Save message to database
    message = Messages(
        sender_id=user_id,
        receiver_id=partner_id,
        content=content,
        created_at=datetime.now()
    )
    db.session.add(message)
    db.session.commit()
    
    current_time = datetime.now().strftime('%H:%M')
    message_data = {
        'id': message.id,
        'type': 'user',
        'text': html.escape(content),
        'time': current_time,
        'seen': False
    }
    
    # Send to sender
    emit('message_sent', message_data)
    
    # Send to receiver if online
    emit('new_message', {
        'type': 'other',
        'text': html.escape(content),
        'time': current_time,
        'sender_name': current_user.name or current_user.username,
        'sender_id': user_id,
        'message_id': message.id
    }, room=f'user_{partner_id}')
    
    # Send notification to receiver
    notify_user(partner_id, f'{current_user.name or current_user.username} új üzenetet küldött', 'Új üzenet érkezett')

@socketio.on('mark_message_seen')
@authenticated_only
def handle_mark_message_seen(data):
    """Mark a message as seen"""
    user_id = current_user.id
    message_id = data.get('message_id')
    
    if not message_id:
        emit('error', {'message': 'Message ID required'})
        return
    
    message = Messages.query.get(message_id)
    if not message or message.receiver_id != user_id:
        emit('error', {'message': 'Message not found or unauthorized'})
        return
    
    message.seen = True
    db.session.commit()
    
    # Notify sender that message was seen
    emit('message_seen', {
        'message_id': message.id
    }, room=f'user_{message.sender_id}')

@socketio.on('get_partner_info')
@authenticated_only
def handle_get_partner_info(data):
    """Get partner info for starting a new conversation"""
    partner_id = data.get('partner_id')
    if not partner_id:
        emit('error', {'message': 'Partner ID required'})
        return
    
    partner = User.query.get(partner_id)
    if not partner:
        emit('error', {'message': 'Partner not found'})
        return
    
    pic = '/static/default-avatar.png'
    if partner.profile_picture:
        att = Attachment.query.get(partner.profile_picture)
        if att:
            pic = f'/static/attachments/{att.filename}'
    
    emit('partner_info', {
        'id': partner.id,
        'name': partner.name or partner.username,
        'pic': pic,
        'status': 'online' if partner.id in online_users else 'offline'
    })


