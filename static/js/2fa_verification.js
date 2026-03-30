document.addEventListener("DOMContentLoaded", function () {
    const otpDigits = document.querySelectorAll(".otp-digit");
    const otpCodeInput = document.getElementById("otpCode");
    const otpError = document.getElementById("otpError");
    const twoFAForm = document.getElementById("twoFAForm");

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

    if (twoFAForm) {
        twoFAForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const code = Array.from(otpDigits).map(d => d.value).join('');
            
            if (code.length !== 6 || !/^\d{6}$/.test(code)) {
                if (otpError) {
                    otpError.setAttribute('data-i18n', '2fa.incomplete');
                    otpError.textContent = 'Kérlek add meg mind a 6 számjegyet!';
                    otpError.style.display = 'block';
                }
                return;
            }
            
            otpCodeInput.value = code;
            
            if (otpError) otpError.style.display = 'none';
            
            this.submit();
        });
    }
});
