// i18js Configuration and Functions
class i18js {
  constructor() {
    this.currentLanguage = localStorage.getItem('lang') || 'hu';
    this.translations = {};
    this.initialized = false;
  }

  // Initialize i18js with translations
  async init(languages = ['hu', 'en']) {
    try {
      const baseUrl = document.currentScript?.dataset.staticUrl || '/static/';
      for (const lang of languages) {
        const response = await fetch(`${baseUrl}locales/${lang}.json`);
        this.translations[lang] = await response.json();
      }
      this.initialized = true;
      this.applyLanguage(this.currentLanguage);
    } catch (error) {
      console.error('Error loading translations:', error);
    }
  }

  // Get translated text
  t(key, defaultValue = '', replacements = {}) {
    const keys = key.split('.');
    let value = this.translations[this.currentLanguage];

    for (const k of keys) {
      if (value && typeof value === 'object') {
        value = value[k];
      } else {
        return defaultValue;
      }
    }

    if (typeof value !== 'string') {
      return defaultValue;
    }

    // Replace placeholders like {username} with actual values
    return value.replace(/\{(\w+)\}/g, (match, key) => {
      return replacements[key] !== undefined ? replacements[key] : match;
    });
  }

  // Set current language
  setLanguage(lang) {
    if (this.translations[lang]) {
      this.currentLanguage = lang;
      localStorage.setItem('lang', lang);
      this.applyLanguage(lang);
      document.documentElement.lang = lang;
    }
  }

  // Get current language
  getLanguage() {
    return this.currentLanguage;
  }

  // Apply language to all elements with data-i18n attribute
  applyLanguage(lang) {
    document.documentElement.lang = lang;
    document.querySelectorAll('[data-i18n]').forEach(element => {
      const key = element.getAttribute('data-i18n');
      const replacements = this.getReplacementsFromElement(element);
      const translated = this.t(key, element.textContent, replacements);
      
      if (element.tagName === 'INPUT' || element.tagName === 'TEXTAREA') {
        element.placeholder = translated;
      } else {
        element.textContent = translated;
      }
    });

    document.querySelectorAll('[data-i18n-html]').forEach(element => {
      const key = element.getAttribute('data-i18n-html');
      const replacements = this.getReplacementsFromElement(element);
      const translated = this.t(key, element.innerHTML, replacements);
      element.innerHTML = translated;
    });

    document.querySelectorAll('[data-i18n-attr]').forEach(element => {
      const attrConfig = element.getAttribute('data-i18n-attr');
      const configs = attrConfig.split(';');
      
      configs.forEach(config => {
        const [attr, key] = config.trim().split(':');
        if (attr && key) {
          const translated = this.t(key, element.getAttribute(attr) || '');
          element.setAttribute(attr, translated);
        }
      });
    });
  }

  // Get replacements from element's data attributes
  getReplacementsFromElement(element) {
    const replacements = {};
    const attributes = element.attributes;

    for (let attr of attributes) {
      if (attr.name.startsWith('data-i18n-')) {
        const key = attr.name.replace('data-i18n-', '');
        if (key !== 'html' && key !== 'attr') {
          replacements[key] = attr.value;
        }
      }
    }

    return replacements;
  }
}

function persistLanguageCookie(lang) {
  document.cookie = `lang=${lang}; path=/; max-age=31536000; SameSite=Lax`;
}

function notifyLanguageChanged(lang) {
  document.dispatchEvent(new CustomEvent('app-language-changed', {
    detail: { lang }
  }));
}

// Create global instance
const i18 = new i18js();
window.i18 = i18;

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
  i18.init(['hu', 'en']);
  persistLanguageCookie(i18.getLanguage());
  notifyLanguageChanged(i18.getLanguage());
});

// Language switcher function
function switchLanguage(lang) {
  i18.setLanguage(lang);
}

// Update language button styles
function updateLanguageButtons() {
  const currentLang = i18.getLanguage();
  document.querySelectorAll('.language-switcher button').forEach(btn => {
    btn.classList.remove('active', 'btn-secondary');
    btn.classList.add('btn-outline-secondary');
  });
  const activeBtn = document.getElementById(`lang-${currentLang}`);
  if (activeBtn) {
    activeBtn.classList.remove('btn-outline-secondary');
    activeBtn.classList.add('btn-secondary', 'active');
  }
}

// Update buttons on page load
document.addEventListener('DOMContentLoaded', () => {
  i18.init(['hu', 'en']).then(() => {
    updateLanguageButtons();
  });
});

// Update buttons when language changes (before reload)
const originalSetLanguage = i18js.prototype.setLanguage;
i18js.prototype.setLanguage = function(lang) {
  if (this.translations[lang]) {
    this.currentLanguage = lang;
    localStorage.setItem('lang', lang);
    persistLanguageCookie(lang);
    updateLanguageButtons();
    this.applyLanguage(lang);
    document.documentElement.lang = lang;
    notifyLanguageChanged(lang);
    }
};
