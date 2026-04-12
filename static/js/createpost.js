document.addEventListener('DOMContentLoaded', () => {
    const publishBtn = document.getElementById('post-publish-btn');
    const modal = document.getElementById('staticBackdrop');
    const megyeSelect = document.getElementById('megye');
    const telepulesSelect = document.getElementById('telepules');

    let varmegyekData = {};

    // Vármegyék betöltése
    fetch('/static/locales/hu.json')
        .catch(() => ({}));

    fetch('/varmegyek.json')
        .then(res => res.json())
        .then(data => {
            varmegyekData = data;
            Object.keys(data).sort().forEach(megye => {
                const option = document.createElement('option');
                option.value = megye;
                option.textContent = megye;
                megyeSelect.appendChild(option);
            });
        })
        .catch(err => console.error('Vármegyék betöltése sikertelen:', err));

    // Település betöltése megye választáskor
    megyeSelect.addEventListener('change', () => {
        const selectedMegye = megyeSelect.value;
        telepulesSelect.innerHTML = '<option value="" disabled selected>Válassz települést</option>';

        if (varmegyekData[selectedMegye]) {
            Object.keys(varmegyekData[selectedMegye]).sort().forEach(telepules => {
                const option = document.createElement('option');
                option.value = telepules;
                option.textContent = telepules;
                telepulesSelect.appendChild(option);
            });
        }
    });

    // Közzététel gomb
    publishBtn.addEventListener('click', async () => {
        const name = document.getElementById('post-name').value.trim();
        const description = document.getElementById('post-description').value.trim();
        const category = document.getElementById('post-category').value;
        const megye = megyeSelect.value;
        const telepules = telepulesSelect.value;

        // Típus (lost/found) meghatározása a toggle alapján
        const activeToggle = document.querySelector('.toggle-switch .toggle-btn.active');
        const type = activeToggle && activeToggle.classList.contains('found') ? 'found' : 'lost';
        const currentLanguage = (window.i18 && typeof window.i18.getLanguage === 'function')
            ? window.i18.getLanguage()
            : (localStorage.getItem('lang') || document.documentElement.lang || 'hu');

        // Validáció
        if (!name) {
            alert('Kérlek add meg a tárgy nevét!');
            return;
        }
        if (!description) {
            alert('Kérlek adj meg leírást!');
            return;
        }

        // Helyszín összeállítása
        let location = '';
        if (megye) {
            location = megye;
            if (telepules) {
                location += ', ' + telepules;
            }
        }

        // FormData összeállítása
        const formData = new FormData();
        formData.append('name', name);
        formData.append('description', description);
        formData.append('category', category);
        formData.append('location', location);
        formData.append('type', type);
        formData.append('language', currentLanguage);

        // Képek hozzáadása
        const imageInput = document.getElementById('image-upload');
        // A slider.js FileReader-t használ előnézethez, de az eredeti fájlok elvesznek
        // Ezért a feltöltött képeket külön tároljuk
        if (window.postUploadedFiles && window.postUploadedFiles.length > 0) {
            window.postUploadedFiles.forEach(file => {
                formData.append('images', file);
            });
        }

        publishBtn.disabled = true;

        try {
            const response = await fetch('/post/create', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.success) {
                if (result.processing) {
                    showToast(result.message || 'A poszt forditasa folyamatban van, hamarosan megjelenik.', 'success');
                }

                // Modal bezárása
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();

                // Oldal újratöltése, hogy az új poszt megjelenjen
                window.location.reload();
            } else {
                alert(result.error || 'Hiba történt a poszt létrehozásakor.');
            }
        } catch (err) {
            console.error('Poszt létrehozási hiba:', err);
            alert('Hiba történt a poszt létrehozásakor.');
        } finally {
            publishBtn.disabled = false;
        }
    });

    // Modal bezárásakor form ürítése
    modal.addEventListener('hidden.bs.modal', () => {
        document.getElementById('post-name').value = '';
        document.getElementById('post-description').value = '';
        document.getElementById('post-category').selectedIndex = 0;
        megyeSelect.selectedIndex = 0;
        telepulesSelect.innerHTML = '<option value="" disabled selected>Válassz települést</option>';
        window.postUploadedFiles = [];

        // Toggle visszaállítása "lost"-ra
        const buttons = document.querySelectorAll('.toggle-switch .toggle-btn');
        buttons.forEach(btn => btn.classList.remove('active'));
        const lostBtn = document.querySelector('.toggle-switch .toggle-btn.lost');
        if (lostBtn) lostBtn.classList.add('active');
    });
});
