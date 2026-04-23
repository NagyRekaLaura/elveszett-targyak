# Lost & Found – Elveszett Tárgyak

A **Lost & Found** egy Flask alapú webes alkalmazás, amely segít az elveszett és megtalált tárgyak bejelentésében, nyilvántartásában és a tulajdonosukhoz való visszajuttatásában. A felhasználók feltölthetik az elveszett vagy talált tárgyak adatait, böngészhetnek a bejegyzések között, valós idejű csevegésen keresztül léphetnek kapcsolatba egymással, és a beépített mesterséges intelligencia gondoskodik az automatikus fordításról, valamint az ügyfélszolgálati támogatásról.

---

## Készítette

| Név | Szerep |
| --- | --- |
| **Nagy Réka Laura** | fejlesztő |
| **Bozsik Ádám Botond** | fejlesztő |
| **Tomor Noel** | fejlesztő |

---

## Telepítés

### Előfeltételek

- **Python 3.10+**
- **pip** és **virtualenv** (a Pythonhoz mellékelt `venv` is megfelelő)
- Opcionálisan: Ollama API kulcs (AI fordításhoz és ügyfélszolgálati chathez)
- Opcionálisan: Mailgun API kulcs (jelszó-visszaállító emailek küldéséhez)

### Lépések

1. **Klónozd a repót:**

   ```bash
   git clone https://github.com/NagyRekaLaura/elveszett-targyak.git
   cd elveszett-targyak
   ```

2. **Hozd létre és aktiváld a virtuális környezetet** (Windows-on a mellékelt batch fájlok használhatók):

   ```bat
   create-venv.bat
   ```

   A szkript létrehozza a `lost-and-found` nevű virtuális környezetet és telepíti a függőségeket az `r.txt` fájlból.

   Manuálisan:

   ```bash
   python -m venv lost-and-found
   # Windows:
   lost-and-found\Scripts\activate
   # Linux/Mac:
   source lost-and-found/bin/activate
   pip install -r r.txt
   ```

3. **API kulcsok beállítása** (opcionális, de AI és email funkciókhoz szükséges):

   Hozz létre egy `tokens.json` fájlt a projekt gyökerében:

   ```json
   {
     "ollama_api_key": "A_TE_OLLAMA_KULCSOD",
     "mailgun_api_key": "A_TE_MAILGUN_KULCSOD"
   }
   ```

   Ha a fájl hiányzik, az alkalmazás első indításkor automatikusan létrehoz egy üres sablont.

4. **Indítsd el az alkalmazást:**

   ```bash
   python main.py
   ```

   Az alkalmazás alapértelmezetten a `http://127.0.0.1:5000` címen érhető el.

   Első indításkor automatikusan létrejön:
   - a SQLite adatbázis (`instance/app.db`),
   - egy alapértelmezett admin felhasználó (`admin` / `admin`) – **éles környezetben azonnal cseréld le!**

---

## Használat

### Regisztráció és bejelentkezés

1. Nyisd meg a `http://127.0.0.1:5000/login` oldalt.
2. A regisztrációs űrlapon hozz létre egy új fiókot (felhasználónév, email, jelszó).
3. Bejelentkezés után az alkalmazás a profil kitöltésére irányít (név, lakcím, születési dátum).
4. Opcionálisan engedélyezheted a **kétlépcsős hitelesítést (2FA)** egy authenticator alkalmazással (Google Authenticator, Authy stb.).

### Tárgy bejelentése

1. A főoldalon kattints az **„Új bejegyzés”** gombra.
2. Válaszd ki a típust: **Elveszett** vagy **Talált**.
3. Add meg a tárgy nevét, leírását, kategóriáját, helyszínét (vármegye + település) és tölts fel képeket.
4. A bejegyzés feltöltése után a rendszer a háttérben automatikusan lefordítja a leírást magyarra/angolra.

### Keresés és szűrés

- A főoldal keresőmezőjében szabad szöveggel kereshetsz név, leírás, kategória vagy helyszín alapján.
- A kategóriacsempékkel gyorsan szűrheted a bejegyzéseket (állat, elektronika, ruházat, ékszer, dokumentum, egyéb).

### Kapcsolatfelvétel és üzenetküldés

- Egy poszt részletein belül elindíthatsz privát beszélgetést a feltöltővel.
- Az **Üzenetek** oldal valós időben (Socket.IO) mutatja a beszélgetéseket, olvasottság-visszajelzéssel és értesítésekkel.

### Nyelvváltás

- A fejlécben található **HU / EN** gombokkal válthatsz magyar és angol nyelv között.
- A választott nyelv a böngésződ `localStorage`-ában tárolódik.

### Admin felület

- Az admin fiókkal elérhető a `/admin/dashboard` oldal.
- Itt kezelhetők a felhasználók, posztok, bejelentések, valamint valós idejű rendszermetrikák (CPU, RAM, statisztikák).

---

## Funkciók

### Felhasználói fiókok

- Regisztráció és bejelentkezés Flask-Login-nal (jelszó hash: bcrypt).
- **Kétlépcsős hitelesítés (2FA)** TOTP alapon, QR kód generálással (pyotp + qrcode).
- Profilkép feltöltés, személyes adatok (név, lakcím, telefonszám, születési dátum).
- Adatvédelmi kapcsolók: a lakcím és a telefonszám egyénileg rejthető.
- Jelszó visszaállítás egyedi tokennel, Mailgun-on keresztül küldött HTML email.

### Tárgybejelentések

- Elveszett és talált tárgyak külön típusokkal.
- Kategorizálás (állat, elektronika, ruházat, ékszer, dokumentum, egyéb).
- Többképes feltöltés (PNG, JPG, JPEG, GIF, WEBP).
- Helyszín megadása vármegye + település bontásban (Magyarország teljes vármegyei adatbázisa a `varmegyek.json` fájlban).
- Saját posztok szerkesztése, lezárása (megtalálva!) és törlése.
- Automatikus két nyelvre (HU/EN) fordítás Ollama-val a háttérben.

### Keresés és megjelenítés

- Szabad szöveges keresés minden releváns mezőben.
- Kategóriák szerinti gyorsszűrés.
- Térkép nézet (`/post/test-map`), amely településenként csoportosítva mutatja a bejegyzéseket.
- Dinamikus kártya nézet képekkel és kapcsolati adatokkal.

### Üzenetek és értesítések

- Valós idejű chat Flask-SocketIO-val.
- Beszélgetéslista olvasatlan üzenetek számával.
- Látva-jelzés (seen), online/offline státusz.
- Rendszer-csatorna (üdvözlés, figyelmeztetések).
- Valós idejű böngésző értesítések új üzenet esetén.

### Ügyfélszolgálati AI

- Beépített támogató chat widget a felület alján.
- A `SupportAI` osztály Ollama modellt (gpt-oss:120b) használ a dokumentáció (`ai.txt`) alapján.
- Streamelt válaszok WebSocket-en keresztül, felhasználói sessiononként.

### Bejelentések (moderáció)

- Felhasználók bejelenthetnek posztokat vagy más felhasználókat.
- Dupla-bejelentés szűrés, saját poszt nem bejelenthető.
- Admin oldalon kezelhetők a bejelentések (feloldás, poszt/felhasználó törlése).

### Admin funkciók

- Dashboard rendszerinformációkkal (psutil: CPU, RAM).
- Felhasználók, posztok, bejelentések listázása, szűrése, lapozása.
- Felhasználói büntetések: figyelmeztetés, felfüggesztés, ban (időtartammal).
- Posztok és felhasználók végleges törlése kaszkádolva.

### Internacionalizáció (i18n)

- Saját könnyűsúlyú `i18js` JavaScript library.
- Magyar és angol teljes fordítás (`static/locales/hu.json`, `en.json`).
- Dinamikus szövegcsere `data-i18n` attribútumokkal, placeholder és HTML tartalom támogatással.
- Automatikus nyelvmentés `localStorage`-ban.
- Új nyelv hozzáadása egyszerű: új JSON fájl a `static/locales` mappába.

---

## Használt technológiák

### Backend

- **Python 3** – futtatókörnyezet
- **Flask 3.1** – webes keretrendszer
- **Flask-SQLAlchemy** – ORM (SQLite adatbázissal)
- **Flask-Login** – session kezelés
- **Flask-Bcrypt** – jelszó hash-elés
- **Flask-SocketIO** – valós idejű kommunikáció
- **pyotp** – TOTP alapú 2FA
- **qrcode + Pillow** – QR kódok generálása
- **psutil** – rendszerstatisztikák az admin felülethez
- **requests** – HTTP hívások (Mailgun)
- **ollama** – AI kliens a fordításhoz és ügyfélszolgálathoz

### Frontend

- **HTML5 + Jinja2** sablonok
- **Vanilla JavaScript** (minden funkció külön JS fájlban a `static/js` mappában)
- **Saját CSS** (`static/css/style.css`)
- **Socket.IO kliens** valós idejű üzenetekhez
- **Font Awesome** ikonok
- **Leaflet.js** (térkép nézethez)

### Külső szolgáltatások

- **Ollama Cloud API** (gpt-oss:120b modell) – automatikus fordítás + chatbot
- **Mailgun** – tranzakciós email küldés (jelszó visszaállítás)

---

## Projekt struktúra

```
elveszett-targyak/
│
├── main.py                    # Flask alkalmazás belépési pontja
├── database.py                # SQLAlchemy adatmodellek
├── r.txt                      # Python függőségek (pip requirements)
├── create-venv.bat            # Windows venv + pip install segédszkript
├── start-venv.bat             # Venv aktiválás segédszkript
├── tokens.json                # Ollama + Mailgun API kulcsok (nem tárolódik gitben)
├── varmegyek.json             # Magyar vármegyei adatbázis
├── ai.txt                     # Dokumentáció az ügyfélszolgálati AI-nak
│
├── routes/                    # Flask Blueprintek
│   ├── auth.py                # Bejelentkezés, regisztráció, 2FA, jelszó reset
│   ├── main.py                # Főoldal, keresés
│   ├── post.py                # Posztok CRUD, bejelentés
│   ├── profile.py             # Profil, 2FA beállítás
│   ├── messages.py            # Üzenetek oldal
│   ├── admin.py               # Admin dashboard + API
│   ├── send_mail.py           # Mailgun integráció
│   └── translate.py           # Ollama fordító osztály
│
├── sockets/                   # Flask-SocketIO eseménykezelők
│   ├── main.py                # SocketIO példány + értesítések
│   ├── chat.py                # Privát chat
│   ├── support.py             # AI támogató chat csatornák
│   └── support_chat.py        # SupportAI osztály (Ollama kliens)
│
├── templates/                 # Jinja2 HTML sablonok
│   ├── base.html              # Alap sablon (navbar, footer, chat widget)
│   ├── home.html              # Főoldal
│   ├── login.html             # Be- és regisztráció
│   ├── 2fa_verification.html  # 2FA ellenőrző oldal
│   ├── reset_password.html    # Jelszó visszaállító oldal
│   ├── createprofile.html     # Profil létrehozása
│   ├── editprofile.html       # Profil szerkesztése
│   ├── profile.html           # Profil megtekintése
│   ├── post.html              # Poszt részletei
│   ├── messages.html          # Üzenetek / chat
│   ├── admin.html              # Admin felület
│   ├── test_map.html          # Térkép nézet
│   └── error404.html          # 404 hibaoldal
│
├── static/                    # Statikus állományok
│   ├── css/style.css
│   ├── js/                    # Kliensoldali JavaScript
│   ├── locales/               # i18n fordítások (hu.json, en.json)
│   ├── attachments/           # Feltöltött képek
│   └── placeholders/          # Placeholder képek
│
├── instance/                  # SQLite adatbázis helye (automatikusan létrejön)
│
└── Teszt/                     # Automatizált végponti tesztek
    ├── teszt_futtato.py       # Komplex integrációs teszt szkript
    ├── README.md              # Teszt leírás
    └── riport/                # Generált tesztriportok
```

---

## Tesztelés

A projekt tartalmaz egy átfogó automatizált tesztelő szkriptet a `Teszt` mappában:

```bash
# Külön terminálban indítsd el a szervert
python main.py

# Másik terminálban futtasd a teszteket
python Teszt/teszt_futtato.py
```

A tesztek a teljes felhasználói utat lefedik: regisztráció, bejelentkezés, 2FA, profil, poszt létrehozás/szerkesztés/törlés, bejelentés, üzenetek, jogosultságkezelés. Az eredmények a `Teszt/riport/` mappába kerülnek szöveges és JSON formátumban.

Részletes leírás: [Teszt/README.md](Teszt/README.md).

---

## Adatbázis modellek

A `database.py` által definiált főbb entitások:

- **User** – felhasználói fiók (jelszó hash, 2FA, szerepkör, adatvédelmi kapcsolók)
- **Item** – elveszett/talált tárgy (név, leírás HU + EN, típus, kategória, helyszín, státusz)
- **Attachment** – képek és egyéb csatolmányok
- **Category** – kategóriák ikonokkal
- **Messages** – privát üzenetek
- **TwoFactorAuth** – TOTP kulcsok
- **PasswordResetToken** – egyszer használatos jelszó-visszaállító tokenek
- **Reports** – bejelentések (poszt vagy felhasználó)
- **Punishments** – admin büntetések (ban, felfüggesztés, figyelmeztetés)

---

## Jövőbeli fejlesztések

- Mobilapplikáció (iOS/Android)
- Push értesítések böngészőn kívül is
- Térkép alapú kereső interaktív markerekkel
- Automatikus képfelismerés a talált tárgyak kategorizálásához
- Több nyelv támogatása (német, román, szlovák)
- Social login (Google, Facebook)
- Nyilvános REST API a külső integrációkhoz

---

## Licenc

Ez a projekt oktatási célokra készült. A további felhasználásról egyeztess a készítőkkel.
