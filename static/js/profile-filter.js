document.addEventListener('DOMContentLoaded', function () {
    const filterButtons = document.querySelectorAll('.filter-btn');
    const posts = document.querySelectorAll('.card');

    function filterPosts(filterValue) {
        posts.forEach(post => {
            const status = post.dataset.status;

            if (filterValue === 'all' || filterValue === status) {
                post.style.display = 'flex';
            } else {
                post.style.display = 'none';
            }
        });
    }

    filterButtons.forEach(button => {
        button.addEventListener('click', function () {
            filterButtons.forEach(btn => btn.classList.remove('active'));
            this.classList.add('active');

            const filterValue = this.dataset.filter;
            filterPosts(filterValue);
        });
    });
});

function resetFilter() {
    const allButton = document.querySelector('.filter-btn[data-filter="all"]');
    if (allButton) {
        allButton.click();
    }
}