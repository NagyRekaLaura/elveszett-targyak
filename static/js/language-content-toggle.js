function applyLanguageContentVisibility(lang) {
  const normalized = (lang || 'hu').toLowerCase().startsWith('en') ? 'en' : 'hu';
  document.querySelectorAll('[data-lang-content]').forEach((element) => {
    const elementLang = (element.getAttribute('data-lang-content') || '').toLowerCase();
    element.style.display = elementLang === normalized ? '' : 'none';
  });
}

document.addEventListener('DOMContentLoaded', () => {
  const initialLanguage = (window.i18 && typeof window.i18.getLanguage === 'function')
    ? window.i18.getLanguage()
    : (localStorage.getItem('lang') || document.documentElement.lang || 'hu');
  applyLanguageContentVisibility(initialLanguage);
});

document.addEventListener('app-language-changed', (event) => {
  const changedLanguage = event?.detail?.lang || 'hu';
  applyLanguageContentVisibility(changedLanguage);
});
