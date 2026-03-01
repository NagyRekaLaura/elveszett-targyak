document.getElementById('profilePic').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function (event) {
            const preview = document.getElementById('profilePicPreview');
            preview.innerHTML = `<img src="${event.target.result}" alt="Profilkép" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
            preview.style.background = 'none';
        }
        reader.readAsDataURL(file);
    } 
    document.getElementById('profilePicPreview').style.cursor = 'pointer';

});
document.addEventListener("DOMContentLoaded", function () {
    const checkbox = document.getElementById("enable2FA");
    const modal = new bootstrap.Modal(document.getElementById("twoFAModal"));

    checkbox.addEventListener("change", function () {
        if (this.checked) {
            modal.show();
        }
    });

    // Form submit kezelése
    const form = document.getElementById('createProfileForm');
    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        
        // Adatok gyűjtése
        const formData = new FormData();
        formData.append('name', document.getElementById('displayName').value);
        formData.append('phone_number', document.getElementById('phoneNumber').value);
        formData.append('phone_number_is_private', document.getElementById('phoneNumberPrivate').checked);
        formData.append('birthdate', document.getElementById('birthdate').value);
        formData.append('address', document.getElementById('address').value);
        formData.append('address_is_private', document.getElementById('addressPrivate').checked);
        formData.append('2fa_enabled', checkbox.checked);
        
        // Profilkép hozzáadása, ha van
        const profilePicFile = document.getElementById('profilePic').files[0];
        if (profilePicFile) {
            formData.append('profile_picture', profilePicFile);
        }
        
        try {
            const response = await fetch('/createprofile', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (response.ok) {
                alert(data.message || 'Profil sikeresen frissítve!');
                window.location.href = '/profile';
            } else {
                alert(data.error || 'Hiba a profil frissítéséhez!');
            }
        } catch (error) {
            console.error('Hiba:', error);
            alert('Hiba az adatküldéshez!');
        }
    });
});
