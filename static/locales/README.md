# i18js - Internationalization Setup

## Configuration

The project now supports **Hungarian (hu)** and **English (en)** languages using the **i18js** library.

### Translation Files

- **en.json** - English translations
- **hu.json** - Hungarian translations

These files are located in `static/locales/` directory.

### JavaScript Integration

The **i18js.js** script manages language switching and translation rendering:
- Loads translation JSON files automatically
- Applies translations to HTML elements using `data-i18n` attributes
- Stores language preference in localStorage
- Supports language switching with visual feedback

## How to Use

### In HTML Templates

#### Simple Text Translation
```html
<button data-i18n="home.createPost">Create Post</button>
```

#### Placeholder Text (Input/Textarea)
```html
<input data-i18n-attr="placeholder:nav.search" placeholder="Search">
```

#### With Replacements/Variables
```html
<p data-i18n="home.welcome" data-i18n-username="John">Welcome, John!</p>
```

#### HTML Content
```html
<span data-i18n-html="profile.agreeTerms">Accept <a href="#">privacy policy</a></span>
```

#### Multiple Attributes
```html
<button data-i18n-attr="aria-label:common.close;title:common.settings">Settings</button>
```

### Adding New Translations

1. Open `static/locales/hu.json` for Hungarian or `static/locales/en.json` for English
2. Add your keys following the nested structure:
```json
{
  "page": {
    "button": "Button Text",
    "message": "Message with {placeholder}"
  }
}
```

3. Use it in HTML with the dot notation: `data-i18n="page.button"`

### Language Switcher

The language switcher buttons are in the navbar (HU/EN):
```html
<div class="language-switcher">
  <button onclick="switchLanguage('hu')">HU</button>
  <button onclick="switchLanguage('en')">EN</button>
</div>
```

The active language button is highlighted with the `.active` class.

## Features

✅ Automatic language detection from localStorage
✅ Default language: Hungarian (hu)
✅ Support for text placeholders with dynamic values
✅ Responsive language switching with page reload
✅ Clean HTML markup with data attributes
✅ Easy to extend with new languages

## Adding a New Language

1. Create a new JSON file in `static/locales/` (e.g., `fr.json` for French)
2. Copy the structure from `en.json` or `hu.json`
3. Translate all values
4. Update the i18js initialization in the language switcher to include the new language

## Notes

- The active language is saved in browser localStorage with key `lang`
- First visit defaults to Hungarian (hu)
- Pages reload when switching languages to apply all translations
- All template pages (base.html, home.html, login.html, etc.) have been updated with i18js support
