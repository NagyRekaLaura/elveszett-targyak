function toggleStatus(clickedBtn) {
    const parent = clickedBtn.parentElement;
    const buttons = parent.querySelectorAll('.toggle-btn');

    buttons.forEach(btn => btn.classList.remove('active'));
    clickedBtn.classList.add('active');
}