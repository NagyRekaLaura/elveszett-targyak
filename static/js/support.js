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
    }

    function autoReply(body) {
        setTimeout(function () {
            appendMessage(body, 'Köszönjük az üzenetet! Hamarosan válaszolunk.', 'bot');
        }, 800);
    }

    function handleSend(input, body) {
        var text = input.value.trim();
        if (!text) return;
        appendMessage(body, text, 'user');
        input.value = '';
        autoReply(body);
    }

    sendDesktop.addEventListener('click', function () {
        handleSend(inputDesktop, bodyDesktop);
    });

    sendMobile.addEventListener('click', function () {
        handleSend(inputMobile, bodyMobile);
    });

    inputDesktop.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
            e.preventDefault();
            handleSend(inputDesktop, bodyDesktop);
        }
    });

    inputMobile.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') {
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
