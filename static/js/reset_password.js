document.addEventListener("DOMContentLoaded", function () {
    const resetPasswordForm = document.getElementById("resetPasswordForm");
    const newPasswordInput = document.getElementById("newPassword");
    const confirmPasswordInput = document.getElementById("confirmPassword");
    const passwordError = document.getElementById("passwordError");

    if (resetPasswordForm) {
        resetPasswordForm.addEventListener('submit', function (e) {
            e.preventDefault();
            
            const newPassword = newPasswordInput.value.trim();
            const confirmPassword = confirmPasswordInput.value.trim();

            if (!newPassword || !confirmPassword) {
                if (passwordError) {
                    passwordError.querySelector('small').textContent = 'Kérlek töltsd ki mindkét jelszó mezőt!';
                    passwordError.style.display = 'block';
                }
                return;
            }

            if (newPassword !== confirmPassword) {
                if (passwordError) {
                    passwordError.querySelector('small').setAttribute('data-i18n', 'resetPassword.passwordMismatch');
                    passwordError.querySelector('small').textContent = 'A jelszavak nem egyeznek!';
                    passwordError.style.display = 'block';
                }
                return;
            }

            if (passwordError) passwordError.style.display = 'none';
            
            this.submit();
        });
    }
});
