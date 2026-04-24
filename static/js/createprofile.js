const ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif'];
const MAX_FILE_SIZE_MB = 5;

const profilePicInput = document.getElementById('profilePic');
if (profilePicInput) {
    profilePicInput.addEventListener('change', function (e) {
        const file = e.target.files[0];
        if (file) {
            const ext = file.name.split('.').pop().toLowerCase();
            if (!ALLOWED_EXTENSIONS.includes(ext)) {
                showToast(`Nem támogatott fájlformátum! Engedélyezett: ${ALLOWED_EXTENSIONS.join(', ')}`);
                this.value = '';
                return;
            }
            if (file.size > MAX_FILE_SIZE_MB * 1024 * 1024) {
                showToast(`A fájl mérete nem haladhatja meg az ${MAX_FILE_SIZE_MB} MB-ot!`);
                this.value = '';
                return;
            }
            const reader = new FileReader();
            reader.onload = function (event) {
                const preview = document.getElementById('profilePicPreview');
                if (!preview) {
                    return;
                }
                preview.innerHTML = `<img src="${event.target.result}" alt="Profilkép" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
                preview.style.background = 'none';
            };
            reader.onerror = function () {
                showToast('Hiba történt a kép beolvasása közben!');
            };
            reader.readAsDataURL(file);
        }
    });
}
document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById('createProfileForm');
    if (form) {
        const enable2FA = document.getElementById('enable2FA');
        let initial2FAState = null;
        if (enable2FA) {
            initial2FAState = enable2FA.dataset['2faEnabled'] === 'true';
        }

        form.addEventListener('submit', async function (e) {
            e.preventDefault();
            const submitUrl = form.getAttribute('action') || '/createprofile';

            const displayName = document.getElementById('displayName').value.trim();
            const birthdate = document.getElementById('birthdate').value.trim();
            const address = document.getElementById('address').value.trim();
            const phoneNumber = document.getElementById('phoneNumber').value.trim();

            // Kliens oldali validáció
            if (!displayName) {
                showToast('A megjelenítendő név megadása kötelező!');
                document.getElementById('displayName').focus();
                return;
            }
            if (displayName.length < 2 || displayName.length > 100) {
                showToast('A megjelenítendő név 2 és 100 karakter között legyen!');
                document.getElementById('displayName').focus();
                return;
            }
            if (!birthdate) {
                showToast('A születési idő megadása kötelező!');
                document.getElementById('birthdate').focus();
                return;
            }
            const birthdateObj = new Date(birthdate);
            if (isNaN(birthdateObj.getTime())) {
                showToast('Érvénytelen születési idő!');
                document.getElementById('birthdate').focus();
                return;
            }
            if (birthdateObj > new Date()) {
                showToast('A születési idő nem lehet a jövőben!');
                document.getElementById('birthdate').focus();
                return;
            }
            if (!address) {
                showToast('A lakhely megadása kötelező!');
                document.getElementById('address').focus();
                return;
            }
            if (phoneNumber && !/^\+?[0-9\s\-()]{6,20}$/.test(phoneNumber)) {
                showToast('Érvénytelen telefonszám formátum!');
                document.getElementById('phoneNumber').focus();
                return;
            }

            const submitBtn = document.getElementById('submitBtn');
            const originalBtnHTML = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Feldolgozás...';

            const formData = new FormData();
            formData.append('name', displayName);
            formData.append('phone_number', phoneNumber);
            formData.append('phone_number_is_private', document.getElementById('phoneNumberPrivate').checked);
            formData.append('birthdate', birthdate);
            formData.append('address', address);
            formData.append('address_is_private', document.getElementById('addressPrivate').checked);
            
            // Handle 2FA action based on current state vs initial state
            const enable2FA = document.getElementById('enable2FA');
            if (enable2FA && initial2FAState !== null) {
                const isCurrentlyChecked = enable2FA.checked;
                
                // User verified 2FA during this session (was off, now on and verified)
                if (isCurrentlyChecked && !initial2FAState && enable2FA.dataset.verified === 'true') {
                    formData.append('2fa_action', 'enable');
                }
                // User disabled 2FA during this session (was on, now off)
                else if (!isCurrentlyChecked && initial2FAState) {
                    formData.append('2fa_action', 'disable');
                }
            }
            
            const profilePicFile = document.getElementById('profilePic').files[0];
            if (profilePicFile) {
                formData.append('profile_picture', profilePicFile);
            }

            try {
                const response = await fetch(submitUrl, {
                    method: 'POST',
                    body: formData
                });

                let data;
                try {
                    data = await response.json();
                } catch {
                    throw new Error('Szerverhiba: érvénytelen válasz.');
                }

                if (!response.ok || !data.success) {
                    showToast(data.error || 'Ismeretlen hiba történt a profil mentésekor.');
                } else {
                    showToast(data.message || 'Profil sikeresen létrehozva!', 'success');
                    setTimeout(() => {
                        window.location.href = '/profile';
                    }, 1500);
                }
            } catch (error) {
                if (error.name === 'TypeError') {
                    showToast('Hálózati hiba! Ellenőrizd az internetkapcsolatod.');
                } else {
                    showToast(error.message || 'Váratlan hiba történt.');
                }
            } finally {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnHTML;
            }
        });
    }

    document.querySelectorAll('.privacy-toggle input[type="checkbox"]').forEach(checkbox => {
        const label = checkbox.closest('.privacy-toggle');
        const icon = checkbox.nextElementSibling;
        if (!label || !icon) return;
        if (checkbox.id === 'enable2FA') return;

        updatePrivacyUI(checkbox, icon, label);
        checkbox.addEventListener('change', function() {
            updatePrivacyUI(this, icon, label);
        });
    });

    function updatePrivacyUI(checkbox, icon, label) {
        const isPrivate = checkbox.checked;
        if (isPrivate) {
            icon.classList.remove('fa-lock-open');
            icon.classList.add('fa-lock');
        } else {
            icon.classList.remove('fa-lock');
            icon.classList.add('fa-lock-open');
        }
        const textSpan = label.querySelector('[data-i18n]');
        if (textSpan) {
            if (isPrivate) {
                textSpan.setAttribute('data-i18n', 'profile.private');
                textSpan.textContent = 'Privát';
            } else {
                textSpan.setAttribute('data-i18n', 'profile.public');
                textSpan.textContent = 'Nyilvános';
            }
        }
    }
}); 