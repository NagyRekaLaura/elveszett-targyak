// Teszt adatok, remélem ezzel már majd tud dolgozni a backend (hajrá bozsikk)
const conversations = [
    {
        id: 1,
        name: "Működj lécci",
        pic: "/static/attachments/cat.jpg",
        lastMsg: "asdf",
        time: "14:22",
        status: "online",
    },
    {
        id: 2,
        name: "Admin",
        pic: "/static/attachments/cat2.jpg",
        lastMsg: "Üdvözlünk az Elveszett Tárgyak Közösségében! Ha bármilyen kérdésed van, írj bátran.",
        time: "tegnap",
        status: "offline",
        unread: 0
    }
];

const messagesData = {
    1: [
        { type: "other", text: "asd", time: "14:05" },
        { type: "user",  text: "Aztakurva", time: "14:08", seen: false },
        { type: "other", text: "WAPPPP", time: "14:10" }
    ],
    2: [
        { type: "other", text: "Üdvözlünk az Elveszett Tárgyak Közösségében! Ha bármilyen kérdésed van, írj bátran.", time: "09:45" },
        { type: "user",  text: "Köszönöm!", time: "09:50", seen: true }
    ]
};

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

function renderConversations() {
    convListEl.innerHTML = "";
    conversations.forEach(conv => {
        const item = document.createElement("div");
        item.className = "conversation-item";
        item.dataset.convId = conv.id;

        let unreadHtml = conv.unread > 0
            ? `<span class="unread-badge">${conv.unread}</span>`
            : "";

        item.innerHTML = `
            <div class="conv-profile-pic">
                <img src="${conv.pic}" alt="${conv.name}">
            </div>
            <div class="conv-info">
                <div class="conv-name">${conv.name}</div>
                <div class="conv-last-msg">${conv.lastMsg}</div>
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
    const conv = conversations.find(c => c.id === convId);
    if (!conv) return;

    document.querySelectorAll(".conversation-item").forEach(el => el.classList.remove("active"));
    document.querySelector(`[data-conv-id="${convId}"]`)?.classList.add("active");

    partnerPic.src = conv.pic;
    partnerName.textContent = conv.name;

    // Státusz
    const statusEl = partnerStatus;
    statusEl.textContent = conv.status === "online" ? "Elérhető" : "Nem elérhető";
    statusEl.className = "chat-header-status"; // reset
    if (conv.status === "online") {
        statusEl.classList.add("online");
    } else {
        statusEl.classList.add("offline");
    }

    noChat.style.display = "none";
    chatInterface.style.display = "flex";

    chatBody.innerHTML = "";
    const msgs = messagesData[convId] || [];

    msgs.forEach(msg => {
        const div = document.createElement("div");
        div.className = `chat-message ${msg.type}`;

        let seenHtml = "";
        if (msg.type === "user") {
            const seenClass = msg.seen ? "seen" : "";
            const seenText  = msg.seen ? "Látta" : "Kézbesítve";
            seenHtml = `<span class="message-seen ${seenClass}">${seenText}</span>`;
        }

        div.innerHTML = `
            <div class="message-bubble">${msg.text}</div>
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
    if (!text) return;

    const active = document.querySelector(".conversation-item.active");
    if (!active) return;

    const convId = parseInt(active.dataset.convId);
    const now = new Date().toLocaleTimeString("hu-HU", { hour: "2-digit", minute: "2-digit" });

    const msgDiv = document.createElement("div");
    msgDiv.className = "chat-message user";
    msgDiv.innerHTML = `
        <div class="message-bubble">${text}</div>
        <div class="message-meta">
            <span class="message-time">${now}</span>
            <span class="message-seen">Kézbesítve</span>
        </div>
    `;

    chatBody.appendChild(msgDiv);
    chatBody.scrollTop = chatBody.scrollHeight;

    if (!messagesData[convId]) messagesData[convId] = [];
    const newMsg = { type: "user", text, time: now, seen: false };
    messagesData[convId].push(newMsg);

    const conv = conversations.find(c => c.id === convId);
    if (conv) {
        conv.lastMsg = text;
        conv.time = "Most";
        conv.unread = 0;
        renderConversations();
    }

    input.value = "";

    setTimeout(() => {
        if (!newMsg.seen) {
            newMsg.seen = true;
            const seenEl = msgDiv.querySelector(".message-seen");
            if (seenEl) {
                seenEl.textContent = "Látta";
                seenEl.classList.add("seen");
            }
        }
    }, 2800 + Math.random() * 2200);
}

sendBtn.addEventListener("click", sendMessage);
input.addEventListener("keypress", e => {
    if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
});

// Indítás
document.addEventListener("DOMContentLoaded", () => {
    renderConversations();
    if (conversations.length > 0) {
        openConversation(conversations[0].id);
    }
});