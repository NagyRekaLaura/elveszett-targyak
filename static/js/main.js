function showToast(message, type = 'error', customTitle = null) {
    // Toast container létrehozása, ha nem létezik
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = `
            position: fixed; top: 20px; right: 20px; z-index: 9999;
            display: flex; flex-direction: column; gap: 10px;
            pointer-events: none;
        `;
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.innerHTML = `<strong>${customTitle ? customTitle : (type === 'success' ? 'Siker!' : 'Hiba!')}</strong><br>${message}`;
    
    toast.style.cssText = `
        padding: 14px 24px; border-radius: 8px; color: #fff;
        font-size: 14px; font-weight: 500; max-width: 400px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        animation: slideIn 0.3s ease;
        background: ${customTitle ? '#007bff' : (type === 'success' ? '#28a745' : '#dc3545')};
        pointer-events: auto;
    `;

    if (customTitle) {
        toast.style.background = '#007bff'; 
    }
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transition = 'opacity 0.3s ease';
        setTimeout(() => {
            toast.remove();
            if (container.children.length === 0) {
                container.remove();
            }
        }, 300);
    }, 4000);
}