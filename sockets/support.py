from .main import socketio
from flask_socketio import emit
from .support_chat import SupportAI


AI_DISABLED = False

# Initialize Support AI
try:
    with open('ai.txt', 'r', encoding='utf-8') as f:
        AI_DOCS = f.read()
    support_ai = SupportAI(AI_DOCS)
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
    
    user_message = data.get('message', '').strip()
    if not user_message:
        return
    
    try:
        for token in support_ai.ask(user_message):
            emit('support_token', {'token': token})
        
        emit('support_response_end', {'status': 'complete'})
    except Exception as e:
        print(f"Error in support AI: {str(e)}")
        emit('support_response', {'error': str(e)})
