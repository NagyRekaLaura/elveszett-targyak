(function() {
    let isEditingPost = false;
    let currentEditPostId = null;
    let varmegyekData = {};
    let existingImages = [];
    let removedImages = [];
    
    const originalFetch = window.fetch;
    
    fetch('/varmegyek.json')
        .then(r => r.json())
        .then(data => {
            varmegyekData = data;
        })
        .catch(e => console.error('Failed to load varmegyek:', e));
    
    document.addEventListener('DOMContentLoaded', () => {
        document.addEventListener('click', (e) => {
            if (e.target.closest('.btn-edit')) {
                handleEditButtonClick(e);
            }
        });
        
        const modal = document.getElementById('staticBackdrop');
        if (modal) {
            modal.addEventListener('hidden.bs.modal', () => {
                isEditingPost = false;
                currentEditPostId = null;
                window.postUploadedFiles = [];
                existingImages = [];
                removedImages = [];
            });
        }
    });
    
    function handleEditButtonClick(e) {
        e.preventDefault();
        e.stopPropagation();
        
        const btn = e.target.closest('.btn-edit');
        const card = btn.closest('.card');
        const postId = card?.dataset.postId;
        
        if (!postId) {
            alert('Post ID not found');
            return;
        }
        
        fetch(`/post/${postId}/data`)
            .then(r => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then(data => {
                if (!data.success) throw new Error(data.error);
                
                isEditingPost = true;
                currentEditPostId = postId;
                window.postUploadedFiles = [];
                
                document.getElementById('post-name').value = data.name || '';
                document.getElementById('post-description').value = data.description || '';
                document.getElementById('post-category').value = data.category || 'egyeb';
                
                const megye = document.getElementById('megye');
                const telepules = document.getElementById('telepules');
                
                if (data.megye && varmegyekData[data.megye]) {
                    megye.value = data.megye;
                    
                    telepules.innerHTML = '<option value="">Válassz települést</option>';
                    Object.keys(varmegyekData[data.megye]).sort().forEach(town => {
                        const opt = document.createElement('option');
                        opt.value = town;
                        opt.textContent = town;
                        telepules.appendChild(opt);
                    });
                    
                    if (data.telepules) {
                        telepules.value = data.telepules;
                    }
                } else {
                    megye.selectedIndex = 0;
                    telepules.innerHTML = '<option value="">Válassz települést</option>';
                }
                
                document.querySelectorAll('.toggle-switch .toggle-btn').forEach(b => b.classList.remove('active'));
                const typeBtn = document.querySelector(`.toggle-switch .toggle-btn.${data.type}`);
                if (typeBtn) typeBtn.classList.add('active');
                
                const inner = document.getElementById('uploadInner');
                const indicators = document.getElementById('uploadIndicators');
                
                if (inner && indicators) {
                    inner.innerHTML = '';
                    indicators.innerHTML = '';
                    existingImages = [];
                    removedImages = [];
                    
                    if (data.attachments && data.attachments.length > 0) {
                        existingImages = [...data.attachments];
                        
                        data.attachments.forEach((filename, i) => {
                            const item = document.createElement('div');
                            item.className = `carousel-item ${i === 0 ? 'active' : ''}`;
                            item.dataset.filename = filename;
                            item.innerHTML = `
                                <img src="/static/attachments/${filename}" alt="${filename}">
                                <button class="remove-image-btn" type="button">&times;</button>
                            `;
                            
                            item.querySelector('.remove-image-btn').onclick = (e) => {
                                e.stopPropagation();
                                removeCarouselImage(item, filename);
                            };
                            
                            inner.appendChild(item);
                            
                            const indicator = document.createElement('button');
                            indicator.dataset.bsTarget = '#uploadCarousel';
                            indicator.dataset.bsSlideTo = i;
                            if (i === 0) {
                                indicator.classList.add('active');
                                indicator.setAttribute('aria-current', 'true');
                            }
                            indicators.appendChild(indicator);
                        });
                        
                        const carouselContainer = document.querySelector('.upload-carousel-container');
                        if (carouselContainer) {
                            carouselContainer.style.display = 'block';
                        }
                    }
                }
                
                const title = document.getElementById('staticBackdropLabel');
                if (title) title.textContent = 'Poszt szerkesztése';
                
                try {
                    const modal = new bootstrap.Modal(document.getElementById('staticBackdrop'));
                    modal.show();
                } catch (err) {
                    console.error('Failed to show modal:', err);
                }
            })
            .catch(err => {
                console.error('Error loading post data:', err);
                alert('Poszt adatok betöltése hibás: ' + err.message);
            });
    }
    
    function removeCarouselImage(item, filename) {
        const inner = document.getElementById('uploadInner');
        const indicators = document.getElementById('uploadIndicators');
        
        if (!inner || !indicators) return;
        
        if (!removedImages.includes(filename)) {
            removedImages.push(filename);
        }
        
        existingImages = existingImages.filter(f => f !== filename);
        
        const itemIndex = Array.from(inner.children).indexOf(item);
        item.remove();
        
        if (indicators.children[itemIndex]) {
            indicators.children[itemIndex].remove();
        }
        
        Array.from(inner.children).forEach((itm, i) => {
            if (i === 0) {
                itm.classList.add('active');
            } else {
                itm.classList.remove('active');
            }
        });
        
        Array.from(indicators.children).forEach((ind, i) => {
            ind.dataset.bsSlideTo = i;
            if (i === 0) {
                ind.classList.add('active');
                ind.setAttribute('aria-current', 'true');
            } else {
                ind.classList.remove('active');
                ind.removeAttribute('aria-current');
            }
        });
        
        if (inner.children.length === 0) {
            const carouselContainer = document.querySelector('.upload-carousel-container');
            if (carouselContainer) {
                carouselContainer.style.display = 'none';
            }
        }
    }
    
    window.fetch = function(...args) {
        if (isEditingPost && currentEditPostId && args[0] === '/post/create' && args[1]?.method === 'POST') {
            args[0] = `/post/${currentEditPostId}/edit`;
            
            if (args[1].body instanceof FormData) {
                args[1].body.append('is_closed', 'false');
                if (removedImages.length > 0) {
                    args[1].body.append('removed_images', JSON.stringify(removedImages));
                }
            }
        }
        
        return originalFetch.apply(this, args);
    };
    
    window.isEditingPost = () => isEditingPost;
    window.getCurrentEditPostId = () => currentEditPostId;
})();

const closePostBtns = document.querySelectorAll('.btn-close-post');
const deletePostBtns = document.querySelectorAll('.btn-delete');


closePostBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        
        const postId = btn.dataset.postId;

    })});


closePostBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        
        const postId = btn.dataset.postId;
        
        if (!postId) {
            console.error('Post ID nem található.');
            return;
        }
        
        try {
            const response = await fetch(`/post/${postId}/close`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                const card = btn.closest('.card');
                
                if (result.is_closed) {
                    card.style.opacity = '0.6';
                    btn.classList.add('btn-close-open');
                    btn.classList.remove('btn-close-post');
                    btn.innerHTML = '<i class="fas fa-lock-open"></i>';
                    btn.title = 'Poszt megnyitása';
                    showToast('Poszt lezárva', 'success');
                } else {
                    card.style.opacity = '1';
                    btn.classList.remove('btn-close-open');
                    btn.classList.add('btn-close-post');
                    btn.innerHTML = '<i class="fas fa-lock"></i>';
                    btn.title = 'Poszt lezárása';
                    showToast('Poszt megnyitva', 'success');
                }
            } else {
                alert(result.error || 'Hiba történt a lezárás során.');
            }
        } catch (err) {
            console.error('Poszt lezárási hiba:', err);
            alert('Hiba történt a lezárás során.');
        }
    });
});

deletePostBtns.forEach(btn => {
    btn.addEventListener('click', async (e) => {
        e.stopPropagation();
        e.preventDefault();
        
        const card = btn.closest('.card');
        const postId = card?.dataset.postId;
        
        if (!postId) {
            console.error('Post ID nem található.');
            return;
        }
        
        if (!confirm('Biztosan szeretnéd törölni ezt a posztot? Ez a művelet nem vonható vissza.')) {
            return;
        }
        
        try {
            const response = await fetch(`/post/${postId}/delete`, {
                method: 'POST'
            });
            
            const result = await response.json();
            
            if (result.success) {
                card.style.transition = 'opacity 0.3s ease';
                card.style.opacity = '0';
                
                setTimeout(() => {
                    card.remove();
                    showToast('Poszt törölve', 'success');
                    
                    const remainingCards = document.querySelectorAll('.card');
                    if (remainingCards.length === 0) {
                        location.reload();
                    }
                }, 300);
            } else {
                alert(result.error || 'Hiba történt a törlés során.');
            }
        } catch (err) {
            console.error('Poszt törlési hiba:', err);
            alert('Hiba történt a törlés során.');
        }
    });
});
