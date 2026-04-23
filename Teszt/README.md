# Elveszett Tárgyak – Teszt mappa

Ez a mappa tartalmazza az automatikus tesztelő szkriptet, amely az **Elveszett Tárgyak** Flask alkalmazás lehető legtöbb funkcióját ellenőrzi, és a futás végén egy részletes sima szöveges dokumentumban foglalja össze az eredményeket.

## Fájlok

| Fájl | Leírás |
| --- | --- |
| `teszt_futtato.py` | A komplex teszt szkript (Python, `requests` alapú). |
| `riport/teszt_riport.txt` | Részletes, sima szöveges riport (futtatás után). |
| `riport/teszt_riport.json` | Gépi feldolgozható, teljes eredménylista. |

## Használat

1. **Indítsd el az alkalmazást** egy külön terminálban a projekt gyökeréből:

   ```powershell
   python main.py
   ```

   Alapértelmezetten a `http://127.0.0.1:5000` címen fut.

2. **Futtasd a teszt szkriptet:**

   ```powershell
   python Teszt/teszt_futtato.py
   ```

   A szkript szükség esetén automatikusan telepíti a `requests` csomagot.

3. **Nyisd meg a riportot:**

   ```powershell
   notepad Teszt/riport/teszt_riport.txt
   ```

## Cím módosítása

Ha a szerver másik címen fut (pl. éles környezet), állítsd be az `ELVESZETT_URL` környezeti változót:

```powershell
$env:ELVESZETT_URL = "http://example.com"
python Teszt/teszt_futtato.py
```

## Mit tesztel a szkript?

A forgatókönyv egy teljes felhasználói utat jár be:

- **Alaprendszer**: főoldal, `/varmegyek.json`, login oldal, 404, térkép.
- **Autentikáció**: két új felhasználó regisztrációja, bejelentkezés, kijelentkezés, duplikált név kiszűrése, túl hosszú jelszó elutasítása, rossz jelszó elutasítása.
- **Profil**: profil kitöltése, profil és szerkesztő oldal elérhetősége.
- **2FA**: QR kód generálás végpont válasza.
- **Poszt**: létrehozás (szöveggel és képpel is), adatok lekérése, lezárás/visszanyitás, idegen szerkesztés tiltása, nem létező poszt redirect, végül a poszt törlése.
- **Bejelentés**: saját poszt bejelentés tiltva, idegen bejelentés sikeres, duplikált bejelentés kiszűrve.
- **Jelszó visszaállítás**: létező és nem létező felhasználó.
- **Üzenetkezelés**: oldal elérhető bejelentkezve, védett guest mód alatt.
- **Jogosultság**: admin panel nem érhető el sima felhasználónak, admin API 403-at ad vissza, bejelentkezés nélkül nem törölhető poszt.

A riportban minden teszt külön-külön is megjelenik, a hibás tesztek részletes hibainformációval (HTTP státusz, JSON válasz, szükség esetén Python stacktrace).
