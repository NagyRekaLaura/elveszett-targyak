document.addEventListener('DOMContentLoaded', function () {
    var fab = document.getElementById('supportBtn');
    var chatDesktop = document.getElementById('supportChatDesktop');
    var chatMobile = document.getElementById('supportChatMobile');
    var closeBtnDesktop = document.getElementById('closeChatDesktop');
    var closeBtnMobile = document.getElementById('closeChatMobile');
    var inputDesktop = document.getElementById('chatInputDesktop');
    var inputMobile = document.getElementById('chatInputMobile');
    var sendDesktop = document.getElementById('chatSendDesktop');
    var sendMobile = document.getElementById('chatSendMobile');
    var bodyDesktop = document.getElementById('chatBodyDesktop');
    var bodyMobile = document.getElementById('chatBodyMobile');

    var MOBILE_BREAKPOINT = 768;
    var HIDE_DELAY = 3000; 

    var desktopOpen = false;
    var mobileOpen = false;
    var fabVisible = false;
    var hideTimer = null;
    var socket = null;
    var currentResponseElement = null;
    var isWaitingForResponse = false;

    function initSocket() {
        if (!socket) {
            socket = io();
            
            socket.on('connect', function() {
                console.log('Connected to support server');
            });
            
            socket.on('support_token', function(data) {
                if (currentResponseElement) {
                    currentResponseElement.textContent += data.token;
                    if (currentResponseElement.parentElement) {
                        currentResponseElement.parentElement.scrollTop = 
                            currentResponseElement.parentElement.scrollHeight;
                    }
                }
            });
            
            socket.on('support_response_end', function(data) {
                isWaitingForResponse = false;
                currentResponseElement = null;
            });
            
            socket.on('support_response', function(data) {
                if (data.error) {
                    appendMessage(
                        document.body.contains(chatDesktop) && desktopOpen ? bodyDesktop : bodyMobile,
                        'Hiba történt: ' + data.error,
                        'bot'
                    );
                    isWaitingForResponse = false;
                }
            });
            
            socket.on('disconnect', function() {
                console.log('Disconnected from support server');
            });
        }
    }

    function isMobile() {
        return window.innerWidth <= MOBILE_BREAKPOINT;
    }

    function slideFabOff() {
        fab.classList.add('half-hidden');
        fabVisible = false;
    }

    function slideFabOn() {
        fab.classList.remove('half-hidden');
        fabVisible = true;
        scheduleHide();
    }

    function scheduleHide() {
        clearTimeout(hideTimer);
        hideTimer = setTimeout(function () {
            if (isMobile() && fabVisible && !mobileOpen) {
                slideFabOff();
            }
        }, HIDE_DELAY);
    }

    if (isMobile()) {
        slideFabOff();
    }

    window.addEventListener('resize', function () {
        if (isMobile()) {
            if (!mobileOpen && !fabVisible) {
                slideFabOff();
            }
        } else {
            fab.classList.remove('half-hidden');
            fab.style.display = '';
            fabVisible = false;
            clearTimeout(hideTimer);
        }
    });

    fab.addEventListener('click', function () {
        if (isMobile()) {
            if (!fabVisible) {
                slideFabOn();
            } else {
                clearTimeout(hideTimer);
                openMobileChat();
            }
        } else {
            if (desktopOpen) {
                closeDesktopChat();
            } else {
                openDesktopChat();
            }
        }
    });

    function openDesktopChat() {
        initSocket();
        chatDesktop.classList.add('open');
        chatDesktop.setAttribute('aria-hidden', 'false');
        desktopOpen = true;
        inputDesktop.focus();
    }

    function closeDesktopChat() {
        chatDesktop.classList.remove('open');
        chatDesktop.setAttribute('aria-hidden', 'true');
        desktopOpen = false;
    }

    closeBtnDesktop.addEventListener('click', function () {
        closeDesktopChat();
    });

    function openMobileChat() {
        initSocket();
        chatMobile.classList.add('open');
        chatMobile.setAttribute('aria-hidden', 'false');
        mobileOpen = true;
        fab.style.display = 'none';
        inputMobile.focus();
    }

    function closeMobileChat() {
        chatMobile.classList.remove('open');
        chatMobile.setAttribute('aria-hidden', 'true');
        mobileOpen = false;
        fab.style.display = '';
        slideFabOff();
    }

    closeBtnMobile.addEventListener('click', function () {
        closeMobileChat();
    });

    function appendMessage(body, text, sender) {
        var welcome = body.querySelector('.support-chat-welcome');
        if (welcome) welcome.remove();

        var msg = document.createElement('div');
        msg.className = 'support-msg ' + sender;
        msg.textContent = text;
        body.appendChild(msg);
        body.scrollTop = body.scrollHeight;
        
        return msg;
    }

    function handleSend(input, body) {
        var text = input.value.trim();
        if (!text || isWaitingForResponse) return;
        
        appendMessage(body, text, 'user');
        input.value = '';
        
        isWaitingForResponse = true;
        currentResponseElement = document.createElement('div');
        currentResponseElement.className = 'support-msg bot';
        currentResponseElement.textContent = '';
        body.appendChild(currentResponseElement);
        body.scrollTop = body.scrollHeight;
        
        if (socket && socket.connected) {
            socket.emit('support_message', { message: text });
        }
    }

    sendDesktop.addEventListener('click', function () {
        handleSend(inputDesktop, bodyDesktop);
    });

    sendMobile.addEventListener('click', function () {
        handleSend(inputMobile, bodyMobile);
    });

    inputDesktop.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(inputDesktop, bodyDesktop);
        }
    });

    inputMobile.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSend(inputMobile, bodyMobile);
        }
    });

    document.addEventListener('keydown', function (e) {
        if (e.key === 'Escape') {
            if (desktopOpen) closeDesktopChat();
            if (mobileOpen) closeMobileChat();
        }
    });
});
