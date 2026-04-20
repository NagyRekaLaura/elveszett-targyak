import time

from .main import socketio
from flask_socketio import emit, disconnect
from flask import current_app, request
from .support_chat import SupportAI


AI_DISABLED = False

# Initialize Support AI
try:
    with open('ai.txt', 'r', encoding='utf-8') as f:
        AI_DOCS = f.read()
    support_ai = SupportAI(documentation=AI_DOCS)
except FileNotFoundError:
    support_ai = None
    print("Warning: ai.txt not found, support AI disabled")

def disable_ai():
    global AI_DISABLED
    AI_DISABLED = True

@socketio.on('support_message')
def handle_support_message(data):
    if AI_DISABLED:
        
        emit('support_token', {'token': 'AI is currently not available'})
        emit('support_response_end', {'status': 'complete'})
        return
    if not support_ai:
        emit('support_response', {'error': 'AI not available'})
        return
    
    # Get token from app config
    token = current_app.config.get('OLLAMA_API_KEY')
    if not token:
        emit('support_response', {'error': 'Support AI token not configured'})
        return
    
    # Set token on the support_ai instance
    support_ai.set_token(token)
    
    # Get session ID from the socket connection
    session_id = request.sid
    
    user_message = data.get('message', '').strip()
    if not user_message:
        return
    
    try:
        for token_text in support_ai.ask(user_message, session_id):
            emit('support_token', {'token': token_text})
            time.sleep(0.05)
        
        emit('support_response_end', {'status': 'complete'})
    except Exception as e:
        print(f"Error in support AI: {str(e)}")
        emit('support_response', {'error': str(e)})

@socketio.on('disconnect')
def handle_disconnect():
    """Clean up session when user disconnects"""
    session_id = request.sid
    if support_ai:
        support_ai.clear_session(session_id)
    print(f"Support session cleared for {session_id}")
