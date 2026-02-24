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
});
