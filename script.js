document.addEventListener('DOMContentLoaded', () => {

    const imageInput = document.getElementById('image-upload');
    const modal = document.getElementById('staticBackdrop');
    const modalBody = modal.querySelector('.modal-body');

    const carouselWrapper = document.createElement('div');
    carouselWrapper.className = 'upload-carousel-container';

    carouselWrapper.innerHTML = `
        <div id="uploadCarousel" class="carousel slide">
            <div class="carousel-indicators" id="uploadIndicators"></div>
            <div class="carousel-inner" id="uploadInner"></div>

            <button class="carousel-control-prev" type="button" data-bs-target="#uploadCarousel" data-bs-slide="prev">
                <span class="carousel-control-prev-icon"></span>
            </button>

            <button class="carousel-control-next" type="button" data-bs-target="#uploadCarousel" data-bs-slide="next">
                <span class="carousel-control-next-icon"></span>
            </button>
        </div>
    `;

    modalBody.insertBefore(carouselWrapper, modalBody.children[1]);

    let images = [];
    let carouselInstance = null;

    imageInput.addEventListener('change', (e) => {
        const files = [...e.target.files].filter(f => f.type.startsWith('image/'));
        if (!files.length) return;

        files.forEach(file => {
            const reader = new FileReader();
            reader.onload = ev => {
                images.push({
                    src: ev.target.result,
                    name: file.name
                });
                rebuildCarousel(images.length - 1);
            };
            reader.readAsDataURL(file);
        });

        imageInput.value = '';
    });

    function rebuildCarousel(activeIndex = 0) {
        const inner = document.getElementById('uploadInner');
        const indicators = document.getElementById('uploadIndicators');

        inner.innerHTML = '';
        indicators.innerHTML = '';

        images.forEach((img, i) => {
            const item = document.createElement('div');
            item.className = `carousel-item ${i === activeIndex ? 'active' : ''}`;

            item.innerHTML = `
                <img src="${img.src}" alt="${img.name}">
                <button class="remove-image-btn" type="button">&times;</button>
            `;

            item.querySelector('.remove-image-btn').onclick = (e) => {
                e.stopPropagation();
                removeImage(i);
            };

            inner.appendChild(item);

            const indicator = document.createElement('button');
            indicator.dataset.bsTarget = '#uploadCarousel';
            indicator.dataset.bsSlideTo = i;
            if (i === activeIndex) {
                indicator.classList.add('active');
                indicator.setAttribute('aria-current', 'true');
            }
            indicators.appendChild(indicator);
        });

        carouselWrapper.style.display = 'block';
        initCarousel(activeIndex);
    }

    function initCarousel(startIndex) {
        const el = document.getElementById('uploadCarousel');

        if (carouselInstance) carouselInstance.dispose();

        carouselInstance = new bootstrap.Carousel(el, {
            interval: false,
            ride: false,
            wrap: true
        });

        carouselInstance.to(startIndex);
    }

    function removeImage(index) {
        images.splice(index, 1);

        if (!images.length) {
            carouselWrapper.style.display = 'none';
            return;
        }

        rebuildCarousel(Math.max(0, index - 1));
    }
    modal.addEventListener('hidden.bs.modal', () => {
        images = [];
        carouselWrapper.style.display = 'none';
        document.getElementById('uploadInner').innerHTML = '';
        document.getElementById('uploadIndicators').innerHTML = '';
    });

});
function toggleStatus(clickedBtn) {
    const parent = clickedBtn.parentElement;
    const buttons = parent.querySelectorAll('.toggle-btn');

    buttons.forEach(btn => btn.classList.remove('active'));
    clickedBtn.classList.add('active');
}