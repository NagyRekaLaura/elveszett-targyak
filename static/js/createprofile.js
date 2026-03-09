const ALLOWED_EXTENSIONS = ['png', 'jpg', 'jpeg', 'gif'];
const MAX_FILE_SIZE_MB = 5;

document.getElementById('profilePic').addEventListener('change', function (e) {
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
            preview.innerHTML = `<img src="${event.target.result}" alt="Profilkép" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
            preview.style.background = 'none';
        };
        reader.onerror = function () {
            showToast('Hiba történt a kép beolvasása közben!');
        };
        reader.readAsDataURL(file);
    }
});
document.addEventListener("DOMContentLoaded", function () {

    const enable2FA = document.getElementById("enable2FA");
    const modalEl = document.getElementById("twoFAModal");
    const modal = new bootstrap.Modal(modalEl);
    const cancelBtn = document.getElementById("cancel2FA");
    const verifyBtn = document.getElementById("verify2FA");
    const otpDigits = document.querySelectorAll(".otp-digit");
    const otpError = document.getElementById("otpError");

    if (enable2FA) {
        const label = enable2FA.closest('.privacy-toggle');
        const icon = enable2FA.nextElementSibling;

        if (label && icon) {
            update2FAUI(enable2FA, icon, label);

            enable2FA.addEventListener('change', function() {
                if (this.checked) {
                    modal.show();
                    clearOtpInputs();
                    if (otpError) otpError.style.display = 'none';
                }
                update2FAUI(this, icon, label);
            });
        }
    }

    function update2FAUI(checkbox, icon, label) {
        const isEnabled = checkbox.checked;

        if (isEnabled) {
            icon.classList.remove('fa-lock-open');
            icon.classList.add('fa-lock');
        } else {
            icon.classList.remove('fa-lock');
            icon.classList.add('fa-lock-open');
        }

        const textSpan = label.querySelector('[data-i18n]');
        if (textSpan) {
            if (isEnabled) {
                textSpan.setAttribute('data-i18n', 'profile.enabledStatus');
                textSpan.textContent = 'Bekapcsolva';
            } else {
                textSpan.setAttribute('data-i18n', 'profile.disabledStatus');
                textSpan.textContent = 'Kikapcsolva';
            }
        }
    }

    if (cancelBtn) {
        cancelBtn.addEventListener("click", function () {
            if (enable2FA) {
                enable2FA.checked = false;
                const label = enable2FA.closest('.privacy-toggle');
                const icon = enable2FA.nextElementSibling;
                if (label && icon) {
                    update2FAUI(enable2FA, icon, label);
                }
            }
            modal.hide();
            if (otpError) otpError.style.display = 'none';
            clearOtpInputs();
        });
    }

    if (modalEl) {
        modalEl.addEventListener('hidden.bs.modal', function () {
            if (enable2FA && !verifyBtn.dataset.verified) {
                enable2FA.checked = false;
                const label = enable2FA.closest('.privacy-toggle');
                const icon = enable2FA.nextElementSibling;
                if (label && icon) {
                    update2FAUI(enable2FA, icon, label);
                }
            }
            if (otpError) otpError.style.display = 'none';
            clearOtpInputs();
        });
    }

    if (otpDigits.length > 0) {
        otpDigits.forEach((input, index) => {
            input.addEventListener('input', function () {
                this.value = this.value.replace(/[^0-9]/g, '');
                if (this.value.length === 1 && index < 5) {
                    otpDigits[index + 1].focus();
                }
            });

            input.addEventListener('keydown', function (e) {
                if (e.key === "Backspace" && this.value === "" && index > 0) {
                    otpDigits[index - 1].focus();
                }
            });

            input.addEventListener('paste', function (e) {
                e.preventDefault();
                const paste = (e.clipboardData || window.clipboardData).getData('text');
                const digits = paste.replace(/[^0-9]/g, '').slice(0, 6);
                digits.split('').forEach((d, i) => {
                    if (otpDigits[index + i]) otpDigits[index + i].value = d;
                });
                const next = index + digits.length;
                if (next < 6) otpDigits[next].focus();
            });
        });
    }

    function clearOtpInputs() {
        otpDigits.forEach(el => el.value = '');
    }

    if (verifyBtn) {
        verifyBtn.addEventListener("click", function () {
            const code = Array.from(otpDigits).map(d => d.value).join('');
            if (code.length !== 6 || !/^\d{6}$/.test(code)) {
                if (otpError) {
                    otpError.textContent = 'Kérlek add meg mind a 6 számjegyet!';
                    otpError.style.display = 'block';
                }
                return;
            }
            if (otpError) otpError.style.display = 'none';
            if (enable2FA) {
                verifyBtn.dataset.verified = 'true';
            }
            modal.hide();
            showToast('Kétlépcsős azonosítás sikeresen bekapcsolva!', 'success');
        });
    }

    const form = document.getElementById('createProfileForm');
    if (form) {
        form.addEventListener('submit', async function (e) {
            e.preventDefault();

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
            formData.append('2fa_enabled', enable2FA ? enable2FA.checked : false);

            const profilePicFile = document.getElementById('profilePic').files[0];
            if (profilePicFile) {
                formData.append('profile_picture', profilePicFile);
            }

            try {
                const response = await fetch('/createprofile', {
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