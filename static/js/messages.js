
// Initialize Socket.IO
const socket = io();

// Storage for conversations and messages
let conversations = [];
let messagesData = {};
let currentActiveConversation = null;
let typingTimeout = null;
let autoOpenHandled = false;

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
const backBtn       = document.getElementById("chat-back-btn");
const sidebar       = document.getElementById("conversations-sidebar");
const mainChat      = document.getElementById("main-chat");

if (backBtn) {
  backBtn.addEventListener('click', () => {
    sidebar.classList.remove('hidden');
    mainChat.classList.add('hidden');
    currentActiveConversation = null;
  });
}

function showChatMobile() {
  if (window.innerWidth <= 576) {
    sidebar.classList.add('hidden');
    mainChat.classList.remove('hidden');
  }
}

window.addEventListener('resize', () => {
  if (window.innerWidth > 576) {
    sidebar.classList.remove('hidden');
    mainChat.classList.remove('hidden');
  }
});



socket.on('conversations', (data) => {
    // Ha van aktív beszélgetés ami nem szerepel a szerver adatokban, megőrizzük
    if (currentActiveConversation !== null && currentActiveConversation !== undefined) {
        const activeInNew = data.find(c => c.id === currentActiveConversation);
        if (!activeInNew) {
            const activeInOld = conversations.find(c => c.id === currentActiveConversation);
            if (activeInOld) {
                data.push(activeInOld);
            }
        }
    }
    conversations = data;
    renderConversations();
    
    // ============== AUTO-OPEN FROM URL PARAM ==============
    const urlParams = new URLSearchParams(window.location.search);
    const partnerId = urlParams.get('partner');
    if (partnerId && !autoOpenHandled) {
        autoOpenHandled = true;
        const pid = parseInt(partnerId);
        const existingConv = conversations.find(c => c.id === pid);
        if (existingConv) {
            openConversation(pid);
        } else {
            // Új beszélgetés indítása - partner adatok lekérése
            socket.emit('get_partner_info', { partner_id: pid });
        }
        // URL param eltávolítása
        window.history.replaceState({}, '', window.location.pathname);
    }
    // ============== END AUTO-OPEN FROM URL PARAM ==============
    
    // ============== UPDATE ACTIVE CHAT HEADER ==============
    // Ha egy chat van megnyitva, frissítsd az online/offline státuszát
    if (currentActiveConversation !== null && currentActiveConversation !== undefined) {
        const currentConv = conversations.find(c => c.id === currentActiveConversation);
        if (currentConv) {
            const statusEl = document.getElementById('chat-partner-status');
            if (statusEl) {
                statusEl.textContent = currentConv.status === "online" ? "Elérhető" : "Nem elérhető";
                statusEl.className = "chat-header-status";
                if (currentConv.status === "online") {
                    statusEl.classList.add("online");
                    statusEl.classList.remove("offline");
                } else {
                    statusEl.classList.add("offline");
                    statusEl.classList.remove("online");
                }
            }
        }
    }
    // ============== END UPDATE ACTIVE CHAT HEADER ==============
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



socket.on('error', (data) => {
    showToast(data.message, 'error');
});

socket.on('partner_info', (data) => {
    // Új beszélgetés hozzáadása a listához
    const newConv = {
        id: data.id,
        name: data.name,
        pic: data.pic,
        lastMsg: '',
        time: '',
        status: data.status,
        unread: 0,
        is_system: false
    };
    conversations.push(newConv);
    renderConversations();
    openConversation(data.id);
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('connect', () => {
    console.log('Connected to server');
    loadConversations();
});


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
        
        const profilePic = conv.pic || '/static/placeholders/user.png';

        let unreadHtml = conv.unread > 0
            ? `<span class="unread-badge">${conv.unread}</span>`
            : "";

        item.innerHTML = `
            <div class="conv-profile-pic">
                <img src="${profilePic}" alt="${conv.name}" onerror="this.src='/static/placeholders/user.png'">
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
    
    showChatMobile();
    
    const conv = conversations.find(c => c.id === convId);
    if (!conv) {
        console.error('Conversation not found:', convId);
        return;
    }

    console.log('Found conversation:', conv);

    currentActiveConversation = convId;

    document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
    document.querySelector(`[data-conv-id="${convId}"]`)?.classList.add("active");

    partnerPic.src = conv.pic || '/static/placeholders/user.png';
    partnerPic.onerror = function() { this.src = '/static/placeholders/user.png'; };
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
        if (msg.type === "user" && msgs.indexOf(msg) === msgs.length - 1) {
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
    
}



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
    
    // ============== STATUS REFRESH ==============
    // Frissítsd az online státuszokat 5 másodpercenként
    setInterval(() => {
        console.log('Refreshing conversations status...');
        socket.emit('get_conversations');
    }, 5000);
    // ============== END STATUS REFRESH ==============
});