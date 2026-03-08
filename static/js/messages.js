

// Initialize Socket.IO
const socket = io();

// Storage for conversations and messages
let conversations = [];
let messagesData = {};
let currentActiveConversation = null;
let typingTimeout = null;

// DOM elemek
const convListEl    = document.getElementById("conversation-list");
const chatBody      = document.getElementById("chat-body");
const noChat        = document.getElementById("no-chat-placeholder");
const chatInterface = document.getElementById("chat-interface");
const partnerPic    = document.getElementById("chat-partner-pic");
const partnerName   = document.getElementById("chat-partner-name");
const partnerStatus = document.getElementById("chat-partner-status");
const input         = document.getElementById("chat-input");
const sendBtn       = document.getElementById("send-message-btn");



socket.on('conversations', (data) => {
    conversations = data;
    renderConversations();
});

socket.on('messages', (data) => {
    console.log('Messages received:', data, 'Current conversation:', currentActiveConversation);
    if (currentActiveConversation !== null && currentActiveConversation !== undefined) {
        messagesData[currentActiveConversation] = data;
        console.log('Messages stored:', messagesData[currentActiveConversation]);
        renderMessages();
    }
});

socket.on('message_sent', (data) => {
    if (currentActiveConversation) {
        if (!messagesData[currentActiveConversation]) {
            messagesData[currentActiveConversation] = [];
        }
        messagesData[currentActiveConversation].push(data);
        renderMessages();
    }
});

socket.on('new_message', (data) => {
    const partner_id = data.sender_id;
    
    // Add to conversation if not exists
    if (!messagesData[partner_id]) {
        messagesData[partner_id] = [];
    }
    
    messagesData[partner_id].push({
        id: data.message_id,
        type: 'other',
        text: data.text,
        time: data.time,
        seen: false
    });
    
    // Update conversation list
    const conv = conversations.find(c => c.id === partner_id);
    if (conv) {
        conv.lastMsg = data.text;
        conv.time = data.time;
    }
    
    // If this partner is open, render messages
    if (currentActiveConversation === partner_id) {
        renderMessages();
    }
    
    // Always update conversation list
    renderConversations();
    
    // Mark as seen if conversation is open
    if (currentActiveConversation === partner_id) {
        setTimeout(() => {
            const lastMsg = messagesData[partner_id][messagesData[partner_id].length - 1];
            if (lastMsg && lastMsg.type === 'other' && lastMsg.id) {
                socket.emit('mark_message_seen', { message_id: lastMsg.id });
            }
        }, 500);
    }
});

socket.on('message_seen', (data) => {
    if (currentActiveConversation) {
        const msgs = messagesData[currentActiveConversation];
        if (msgs) {
            const msg = msgs.find(m => m.id === data.message_id);
            if (msg) {
                msg.seen = true;
                renderMessages();
            }
        }
    }
});

socket.on('user_typing', (data) => {
    const typingIndicator = document.getElementById('typing-indicator');
    if (!typingIndicator) {
        const indicator = document.createElement('div');
        indicator.id = 'typing-indicator';
        indicator.className = 'typing-indicator';
        indicator.textContent = `${data.sender_name} gépel...`;
        chatBody.appendChild(indicator);
    }
});

socket.on('user_stop_typing', (data) => {
    const typingIndicator = document.getElementById('typing-indicator');
    if (typingIndicator) {
        typingIndicator.remove();
    }
});

socket.on('error', (data) => {
    showToast(data.message, 'error');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('connect', () => {
    console.log('Connected to server');
    loadConversations();
});


// Load initial conversations
// Load initial conversations
function loadConversations() {
    socket.emit('get_conversations');
}

function renderConversations() {
    convListEl.innerHTML = "";
    conversations.forEach(conv => {
        const item = document.createElement("div");
        item.className = "conversation-item";
        item.dataset.convId = conv.id;
        
        // ============== VISUAL INDICATORS ==============
        // Teszt felhasználók és system chat jelölése
        if (conv.is_system) {
            item.classList.add("system-chat");
        }
        if (conv.is_test) {
            item.classList.add("test-user");
        }
        // ============== END VISUAL INDICATORS ==============

        let unreadHtml = conv.unread > 0
            ? `<span class="unread-badge">${conv.unread}</span>`
            : "";

        item.innerHTML = `
            <div class="conv-profile-pic">
                <img src="${conv.pic}" alt="${conv.name}">
                <div class="status-indicator ${conv.status}"></div>
            </div>
            <div class="conv-info">
                <div class="conv-name">${escapeHtml(conv.name)}</div>
                <div class="conv-last-msg">${escapeHtml(conv.lastMsg)}</div>
                <div class="conv-meta">
                    <span class="conv-time">${conv.time}</span>
                    ${unreadHtml}
                </div>
            </div>
        `;

        item.addEventListener("click", () => openConversation(conv.id));
        convListEl.appendChild(item);
    });
}

function openConversation(convId) {
    console.log('Opening conversation:', convId, 'Available conversations:', conversations);
    const conv = conversations.find(c => c.id === convId);
    if (!conv) {
        console.error('Conversation not found:', convId);
        return;
    }

    console.log('Found conversation:', conv);

    currentActiveConversation = convId;

    document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
    document.querySelector(`[data-conv-id="${convId}"]`)?.classList.add("active");

    partnerPic.src = conv.pic;
    partnerName.textContent = escapeHtml(conv.name);

    // Státusz
    const statusEl = partnerStatus;
    statusEl.textContent = conv.status === "online" ? "Elérhető" : "Nem elérhető";
    statusEl.className = "chat-header-status";
    if (conv.status === "online") {
        statusEl.classList.add("online");
    } else {
        statusEl.classList.add("offline");
    }

    noChat.style.display = "none";
    chatInterface.style.display = "flex";
    
    // ============== SYSTEM CHAT HANDLING ==============
    // Ha a system chat-t nyitjuk meg, letiltjuk az input mezőt
    const chatFooter = document.querySelector(".chat-footer");
    if (conv.is_system) {
        // System chat - input disabled
        input.disabled = true;
        sendBtn.disabled = true;
        chatFooter.style.opacity = '0.5';
        input.placeholder = 'Nem küldhetsz üzenetet a Rendszer csatornához';
    } else {
        // Normal chat - input enabled
        input.disabled = false;
        sendBtn.disabled = false;
        chatFooter.style.opacity = '1';
        input.placeholder = 'Írj üzenetet...';
    }
    // ============== END SYSTEM CHAT HANDLING ==============

    // Load messages from server
    socket.emit('get_messages', { partner_id: convId });
}

function renderMessages() {
    console.log('renderMessages called for conversation:', currentActiveConversation);
    chatBody.innerHTML = "";
    const msgs = messagesData[currentActiveConversation] || [];
    console.log('Messages to render:', msgs);

    msgs.forEach(msg => {
        const div = document.createElement("div");
        div.className = `chat-message ${msg.type}`;

        let seenHtml = "";
        if (msg.type === "user") {
            const seenClass = msg.seen ? "seen" : "";
            const seenText = msg.seen ? "Látta" : "Kézbesítve";
            seenHtml = `<span class="message-seen ${seenClass}">${seenText}</span>`;
        }

        div.innerHTML = `
            <div class="message-bubble">${escapeHtml(msg.text)}</div>
            <div class="message-meta">
                <span class="message-time">${msg.time}</span>
                ${seenHtml}
            </div>
        `;

        chatBody.appendChild(div);
    });

    chatBody.scrollTop = chatBody.scrollHeight;
}

function sendMessage() {
    const text = input.value.trim();
    if (!text || !currentActiveConversation) return;

    socket.emit('send_message', {
        partner_id: currentActiveConversation,
        text: text
    });

    input.value = "";
    socket.emit('stop_typing', { partner_id: currentActiveConversation });
}

// Handle typing
input.addEventListener('input', () => {
    if (!currentActiveConversation) return;
    
    socket.emit('typing', { partner_id: currentActiveConversation });
    
    clearTimeout(typingTimeout);
    typingTimeout = setTimeout(() => {
        socket.emit('stop_typing', { partner_id: currentActiveConversation });
    }, 3000);
});

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// HTML escaping for security with newline handling
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    let escaped = div.innerHTML;
    // Replace newlines with <br> tags for multiline messages
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
}

// Initialize on page load
document.addEventListener("DOMContentLoaded", () => {
    loadConversations();
    
    // ============== AUTO-OPEN SYSTEM CHAT ==============
    // Az oldal betöltésekor nyissa meg az alapértelmezett system chatot
    setTimeout(() => {
        console.log('Auto-open timeout, conversations:', conversations);
        const systemChat = conversations.find(c => c.id === 0);
        if (systemChat) {
            console.log('System chat found, opening...');
            openConversation(0);
        } else {
            console.warn('System chat not found in conversations');
        }
    }, 1000);  // Növelt timeout a biztos betöltéshez
    // ============== END AUTO-OPEN SYSTEM CHAT ==============
});