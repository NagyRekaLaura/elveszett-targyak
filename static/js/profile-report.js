/**
 * Profile Report Handler
 * Handles user report functionality in profile page
 */

document.addEventListener('DOMContentLoaded', function() {
    const submitReportBtn = document.getElementById('submit-report-btn');
    const reportModal = document.getElementById('reportModal');
    
    if (!submitReportBtn) return;
    
    submitReportBtn.addEventListener('click', function() {
        const selectedReason = document.querySelector('input[name="report-reason"]:checked');
        
        if (!selectedReason) {
            showToast('Válassz egy indoklást!', 'error');
            return;
        }
        
        const reason = selectedReason.value;
        let content = '';
        
        // Ha "other" van kiválasztva, szükséges a szöveg
        if (reason === 'other') {
            content = document.getElementById('other-reason-text').value.trim();
            if (!content) {
                showToast('Írd be a részleteket az "Egyéb" opcióhoz!', 'error');
                return;
            }
        }
        
        const userId = document.querySelector('[data-report-user-id]')?.getAttribute('data-report-user-id');
        const postId = document.querySelector('[data-report-post-id]')?.getAttribute('data-report-post-id') ||
                       window.location.pathname.split('/post/')[1];
        
        if (userId) {
            submitUserReport(userId, reason, content);
        } else if (postId) {
            submitPostReport(postId, reason, content);
        } else {
            showToast('Nem található bejelentendő elem!', 'error');
        }
    });
    
    // Handle "other" reason text area visibility
    const otherReasonRadio = document.getElementById('reason5');
    const otherReasonTextarea = document.getElementById('other-reason-text');
    
    if (otherReasonRadio && otherReasonTextarea) {
        document.querySelectorAll('input[name="report-reason"]').forEach(radio => {
            radio.addEventListener('change', function() {
                if (this.value === 'other') {
                    otherReasonTextarea.style.display = 'block';
                } else {
                    otherReasonTextarea.style.display = 'none';
                    otherReasonTextarea.value = '';
                }
            });
        });
    }
});

async function submitUserReport(userId, reason, content) {
    try {
        const formData = new FormData();
        formData.append('reason', reason);
        formData.append('content', content);
        
        const response = await fetch(`/profile/report-user/${userId}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast(data.message, 'success');
            
            // Close the modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('reportModal'));
            if (modal) modal.hide();
            
            // Reset the form
            document.querySelector('form[name="report-form"]')?.reset() || 
            Array.from(document.querySelectorAll('input[name="report-reason"]')).forEach(r => r.checked = false);
            document.getElementById('other-reason-text').value = '';
            
        } else {
            showToast(data.error || 'Hiba a bejelentés feldolgozása során', 'error');
        }
    } catch (error) {
        console.error('Report error:', error);
        showToast('Hiba a bejelentés küldése során', 'error');
    }
}

async function submitPostReport(postId, reason, content) {
    try {
        const formData = new FormData();
        formData.append('reason', reason);
        formData.append('content', content);
        
        const response = await fetch(`/post/report-post/${postId}`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok && data.success) {
            showToast(data.message, 'success');
            
            const modal = bootstrap.Modal.getInstance(document.getElementById('reportModal'));
            if (modal) modal.hide();
            
            document.querySelector('form[name="report-form"]')?.reset() || 
            Array.from(document.querySelectorAll('input[name="report-reason"]')).forEach(r => r.checked = false);
            document.getElementById('other-reason-text').value = '';
            
        } else {
            showToast(data.error || 'Hiba a bejelentés feldolgozása során', 'error');
        }
    } catch (error) {
        console.error('Report error:', error);
        showToast('Hiba a bejelentés küldése során', 'error');
    }
}
