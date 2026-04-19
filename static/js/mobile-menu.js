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
});
