

async function requestPasswordResetCheck(username) {
    const response = await fetch('/reset_password_req', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username })
    });

    if (!response.ok) {
        throw new Error('A kiszolgalo nem valaszolt megfeleloen.');
    }

    return response.json();
}

async function handlePasswordResetRequest(event) {
    if (event) {
        event.preventDefault();
    }

    const usernameInput = document.getElementById('username');
    if (!usernameInput) {
        return;
    }

    const username = usernameInput.value.trim();
    if (username === '') {
        showToast('Kerem, adja meg a felhasznalonevet!');
        return;
    }

    try {
        const exists = await requestPasswordResetCheck(username);

        if (exists === true) {
            showToast('Jelszó visszaállító email elküldve.', 'success');
        } else {
            showToast('Nincs ilyen felhasznalo.', 'error');
        }
    } catch (error) {
        showToast(error.message || 'Varatlan hiba tortent.');
    }
}



const resetPasswordRequestLink = document.getElementById('reset_passwd_req');
if (resetPasswordRequestLink) {
    resetPasswordRequestLink.addEventListener('click', handlePasswordResetRequest);
}