document.addEventListener('DOMContentLoaded', function() {
    const mobileMenuToggle = document.getElementById('mobileMenuToggle');
    const mobileDropdownMenu = document.getElementById('mobileDropdownMenu');

    if (mobileMenuToggle && mobileDropdownMenu) {
        mobileMenuToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            mobileDropdownMenu.classList.toggle('open');
        });

        const dropdownItems = mobileDropdownMenu.querySelectorAll('.mobile-dropdown-item');
        dropdownItems.forEach(item => {
            item.addEventListener('click', function() {
                mobileDropdownMenu.classList.remove('open');
            });
        });

        document.addEventListener('click', function(e) {
            if (!mobileMenuToggle.contains(e.target) && !mobileDropdownMenu.contains(e.target)) {
                mobileDropdownMenu.classList.remove('open');
            }
        });
    }

    // Mobile search toggle - show input only when button is pressed
    const mobileSearchIcon = document.querySelector('.mobile-search-icon');
    const mobileSearchInput = document.querySelector('.mobile-navbar-search-input');

    if (mobileSearchIcon && mobileSearchInput) {
        mobileSearchIcon.addEventListener('click', (e) => {
            e.preventDefault();
            mobileSearchIcon.style.display = 'none';
            mobileSearchInput.style.display = 'flex';
            mobileSearchInput.focus();
        });

        // Hide input and show icon again when user leaves or presses escape
        mobileSearchInput.addEventListener('blur', () => {
            mobileSearchInput.style.display = 'none';
            mobileSearchIcon.style.display = 'flex';
        });

        mobileSearchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                mobileSearchInput.value = '';
                mobileSearchInput.style.display = 'none';
                mobileSearchIcon.style.display = 'flex';
            }
        });
    }
});
