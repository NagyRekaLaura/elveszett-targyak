document.addEventListener('DOMContentLoaded', function() {
    const categoryButtons = document.querySelectorAll('.category-container .btn.category');
    const cards = document.querySelectorAll('.card-container .card');
    const noPostsMessage = document.querySelector('.card-container .text-center');
    
    let selectedCategory = null;
    
    categoryButtons.forEach(button => {
        button.addEventListener('click', function() {
            const categoryName = this.querySelector('span').textContent.trim().toLowerCase();
            
            const categoryMap = {
                // Hungarian
                'állat': 'allat',
                'elektronika': 'elektronika',
                'ruházat': 'ruhazat',
                'ékszer': 'ekszer',
                'dokumentum': 'dokumentum',
                'egyéb': 'egyeb',
                // English
                'animal': 'allat',
                'electronics': 'elektronika',
                'clothing': 'ruhazat',
                'jewelry': 'ekszer',
                'document': 'dokumentum',
                'other': 'egyeb'
            };
            
            const categoryValue = categoryMap[categoryName];
            
            if (selectedCategory === categoryValue) {
                selectedCategory = null;
                this.classList.remove('active');
            } else {
                categoryButtons.forEach(btn => btn.classList.remove('active'));
                this.classList.add('active');
                selectedCategory = categoryValue;
            }
            
            filterCards();
        });
    });
    
    function filterCards() {
        let visibleCount = 0;
        
        cards.forEach(card => {
            const cardCategory = card.getAttribute('data-category');
            
            if (selectedCategory === null || cardCategory === selectedCategory) {
                card.style.display = '';
                visibleCount++;
            } else {
                card.style.display = 'none';
            }
        });
        
        if (noPostsMessage) {
            if (visibleCount === 0) {
                noPostsMessage.style.display = 'block';
            } else {
                noPostsMessage.style.display = 'none';
            }
        }
    }
});
