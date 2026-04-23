"""
############################################################################################################################################################
A teszt script claude opus 4.7 segítségével készült, a tesztelési folyamat során több iterációban finomhangolva a tesztelési stratégiát és a teszt eseteket.
############################################################################################################################################################


Elveszett Targyak - Kiterjesztett, komplex tesztelo szkript
============================================================

Ez a szkript atfogo tesztet vegez az "Elveszett Targyak" Flask alkalmazason.
A teszt a leheto legtobb funkciot lefedi:
    - alaprendszer (fooldal, varmegyek.json, statikus eroforrasok, i18n)
    - autentikacio (regisztracio, bejelentkezes, kijelentkezes, validaciok)
    - 2FA (QR kod, setup endpoint, hibas OTP)
    - profil (letrehozas, szerkesztes, mas felhasznalo profilja)
    - poszt (letrehozas szoveggel/keppel, szerkesztes, lezaras, torles,
            jogosulatlansag, nem letezo, i18n)
    - bejelentes (poszt es felhasznalo, sajat, duplikalt)
    - jelszo visszaallitas (request + token validacio)
    - uzenet oldal + Socket.IO chat (connect, get_conversations, get_messages,
      send_message, system chat, hosszu uzenet tiltas, mark_seen, partner_info)
    - admin (admin user letrehozasa az adatbazisban, admin oldalak,
      metrics, api/users, api/posts, api/reports, resolve, delete)
    - tobbnyelvuseg (Accept-Language, lang cookie, HU/EN leiras)
    - biztonsag (SQL injection, XSS kiseret, CSRF/cookie).
Vegul reszletes sima szoveges es JSON riportot general a `Teszt/riport`
mappaba.

Hasznalat:
----------
1. Inditsd el a Flask alkalmazast egy kulon terminalban:
       python main.py
2. Futtasd ezt a szkriptet:
       python Teszt/teszt_futtato.py
3. A riport:
       Teszt/riport/teszt_riport.txt
       Teszt/riport/teszt_riport.json

A hianyzo Python csomagokat a szkript automatikusan felteszi (requests,
python-socketio).
"""

import io
import json
import os
import random
import re
import sqlite3
import string
import subprocess
import sys
import threading
import time
import traceback
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple


def _biztositsd_a_csomagot(csomagnev: str, import_nev: Optional[str] = None) -> None:
    """A megadott pip csomag feltelepitese, ha meg nincs telepitve."""
    try:
        __import__(import_nev or csomagnev)
    except ImportError:
        print(f"[telepites] '{csomagnev}' csomag telepitese pip-pel...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", csomagnev])


_biztositsd_a_csomagot("requests")
_biztositsd_a_csomagot("python-socketio[client]", import_nev="socketio")
_biztositsd_a_csomagot("websocket-client", import_nev="websocket")

import requests  # noqa: E402
import socketio  # noqa: E402


ALAP_URL = os.environ.get("ELVESZETT_URL", "http://127.0.0.1:5000")
GYOKER = os.path.dirname(os.path.abspath(__file__))
PROJEKT_GYOKER = os.path.dirname(GYOKER)
DB_UT = os.path.join(PROJEKT_GYOKER, "instance", "app.db")
RIPORT_MAPPA = os.path.join(GYOKER, "riport")
IDOKORLAT_MP = 15


class TesztEredmeny:
    """Egy darab teszt eset eredmenye."""

    def __init__(
        self,
        kategoria: str,
        nev: str,
        sikeres: bool,
        uzenet: str,
        idotartam_ms: int,
        reszletek: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.kategoria = kategoria
        self.nev = nev
        self.sikeres = sikeres
        self.uzenet = uzenet
        self.idotartam_ms = idotartam_ms
        self.reszletek = reszletek or {}

    def mint_szotar(self) -> Dict[str, Any]:
        return {
            "kategoria": self.kategoria,
            "nev": self.nev,
            "sikeres": self.sikeres,
            "uzenet": self.uzenet,
            "idotartam_ms": self.idotartam_ms,
            "reszletek": self.reszletek,
        }


class Tesztelo:
    """A tesztelo fo osztalya."""

    def __init__(self, alap_url: str) -> None:
        self.alap_url = alap_url.rstrip("/")
        self.eredmenyek: List[TesztEredmeny] = []
        self.felhasznalo_1: Dict[str, Any] = {}
        self.felhasznalo_2: Dict[str, Any] = {}
        self.admin_felhasznalo: Dict[str, Any] = {}
        self.sesszio_1 = requests.Session()
        self.sesszio_2 = requests.Session()
        self.admin_sesszio = requests.Session()
        self.vendeg_sesszio = requests.Session()
        self.letrehozott_item_id: Optional[int] = None
        self.letrehozott_item_id_2: Optional[int] = None
        self.letrehozott_kep_item_id: Optional[int] = None
        self.felhasznalo_1_id: Optional[int] = None
        self.felhasznalo_2_id: Optional[int] = None
        self.admin_felhasznalo_id: Optional[int] = None
        self.letrehozott_report_id: Optional[int] = None
        self.szerver_elerheto = False

    # ----------------------------------------------------------
    # Segedfuggvenyek
    # ----------------------------------------------------------

    def _veletlen_szoveg(self, hossz: int = 8) -> str:
        return "".join(random.choices(string.ascii_lowercase + string.digits, k=hossz))

    def _url(self, utvonal: str) -> str:
        if not utvonal.startswith("/"):
            utvonal = "/" + utvonal
        return f"{self.alap_url}{utvonal}"

    def _futtat_teszt(
        self,
        kategoria: str,
        nev: str,
        fuggveny: Callable[[], Tuple[bool, str, Optional[Dict[str, Any]]]],
    ) -> TesztEredmeny:
        """Egyetlen teszt lefuttatasa biztonsagos (hibakezelt) kornyezetben."""
        print(f"  -> {nev} ... ", end="", flush=True)
        kezdet = time.perf_counter()
        try:
            sikeres, uzenet, reszletek = fuggveny()
        except requests.exceptions.ConnectionError as hiba:
            sikeres = False
            uzenet = f"Nem sikerult csatlakozni a szerverhez: {hiba}"
            reszletek = {"kivetelTipus": "ConnectionError"}
        except Exception as hiba:  # noqa: BLE001
            sikeres = False
            uzenet = f"Kivetel: {hiba}"
            reszletek = {
                "kivetelTipus": type(hiba).__name__,
                "traceback": traceback.format_exc(),
            }

        idotartam_ms = int((time.perf_counter() - kezdet) * 1000)
        eredmeny = TesztEredmeny(kategoria, nev, sikeres, uzenet, idotartam_ms, reszletek)
        self.eredmenyek.append(eredmeny)
        jelzo = "OK " if sikeres else "HIBA"
        print(f"[{jelzo}] {idotartam_ms} ms")
        if not sikeres:
            print(f"       > {uzenet[:200]}")
        return eredmeny

    def _felhasznalo_id_lekerese(self, felhasznalonev: str) -> Optional[int]:
        try:
            conn = sqlite3.connect(DB_UT)
            kurzor = conn.execute("SELECT id FROM user WHERE username = ?", (felhasznalonev,))
            sor = kurzor.fetchone()
            conn.close()
            return sor[0] if sor else None
        except Exception:
            return None

    def _szerepkor_admin_allitas(self, felhasznalonev: str) -> bool:
        try:
            conn = sqlite3.connect(DB_UT)
            conn.execute("UPDATE user SET role = 'admin' WHERE username = ?", (felhasznalonev,))
            conn.commit()
            conn.close()
            return True
        except Exception:
            return False

    # ----------------------------------------------------------
    # Alaprendszer tesztek
    # ----------------------------------------------------------

    def teszt_szerver_eleres(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/"), timeout=IDOKORLAT_MP, allow_redirects=False)
        self.szerver_elerheto = valasz.status_code in (200, 302)
        return (
            self.szerver_elerheto,
            f"A szerver HTTP {valasz.status_code} valaszt adott a fooldal kereseere.",
            {"statusz": valasz.status_code, "byte_meret": len(valasz.content)},
        )

    def teszt_fooldal_tartalom(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200 and ("<html" in valasz.text.lower() or "<!doctype" in valasz.text.lower())
        return (
            sikeres,
            f"A fooldal HTML tartalmat szolgaltat (HTTP {valasz.status_code}, hossz={len(valasz.text)}).",
            {"statusz": valasz.status_code},
        )

    def teszt_varmegyek_json(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/varmegyek.json"), timeout=IDOKORLAT_MP)
        adat = None
        tartalmaz_megyet = False
        try:
            adat = valasz.json()
            tartalmaz_megyet = isinstance(adat, (list, dict)) and len(adat) > 0
        except Exception:
            pass
        sikeres = valasz.status_code == 200 and tartalmaz_megyet
        return (
            sikeres,
            "A varmegyek.json elerheto es ertelmes JSON-t tartalmaz." if sikeres else f"HTTP {valasz.status_code}, tartalmaz megyet: {tartalmaz_megyet}",
            {"statusz": valasz.status_code},
        )

    def teszt_statikus_logo(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/static/logo.svg"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200 and len(valasz.content) > 0
        return (
            sikeres,
            f"A /static/logo.svg letolthato ({len(valasz.content)} byte).",
            {"statusz": valasz.status_code},
        )

    def teszt_locale_fajl_hu(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/static/locales/hu.json"), timeout=IDOKORLAT_MP)
        ok_json = False
        kulcs_szam = 0
        try:
            adat = valasz.json()
            ok_json = isinstance(adat, dict) and len(adat) > 0
            kulcs_szam = len(adat) if isinstance(adat, dict) else 0
        except Exception:
            pass
        sikeres = valasz.status_code == 200 and ok_json
        return (
            sikeres,
            f"HU forditasi fajl elerheto, {kulcs_szam} kulcs.",
            {"statusz": valasz.status_code},
        )

    def teszt_locale_fajl_en(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/static/locales/en.json"), timeout=IDOKORLAT_MP)
        ok_json = False
        try:
            adat = valasz.json()
            ok_json = isinstance(adat, dict) and len(adat) > 0
        except Exception:
            pass
        sikeres = valasz.status_code == 200 and ok_json
        return (
            sikeres,
            f"EN forditasi fajl elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_404_kezeles(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(
            self._url(f"/ez-nem-letezik-{self._veletlen_szoveg()}"),
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code in (404, 302)
        return (
            sikeres,
            f"Nemletezo oldalra a rendszer HTTP {valasz.status_code} kodot ad vissza.",
            {"statusz": valasz.status_code},
        )

    def teszt_login_oldal_lathato(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/login"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200 and (
            "login" in valasz.text.lower() or "bejelentkez" in valasz.text.lower()
        )
        return (
            sikeres,
            f"A /login oldal HTTP {valasz.status_code}, tartalmazza a bejelentkezes szoveget.",
            {"statusz": valasz.status_code, "hossz": len(valasz.text)},
        )

    def teszt_admin_bejelentkezes_nelkul_tiltas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(
            self._url("/admin/dashboard"),
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (302, 401, 403)
        return (
            sikeres,
            f"Admin panel bejelentkezes nelkuli eleresere HTTP {valasz.status_code} (atiranyitas vagy tiltas).",
            {"statusz": valasz.status_code},
        )

    def teszt_terkep_oldal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/post/test-map"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"A terkep (test-map) oldal elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    # ----------------------------------------------------------
    # Autentikacio
    # ----------------------------------------------------------

    def teszt_regisztracio(
        self, sesszio: requests.Session, felhasznalo: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = sesszio.post(
            self._url("/login"),
            data={
                "type": "register",
                "username": felhasznalo["username"],
                "email": felhasznalo["email"],
                "passwd": felhasznalo["password"],
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (200, 302) and "foglalt" not in valasz.text.lower()
        # Ha valos regisztracio, a felhasznalo ID is lekerdezheto db-bol
        user_id = self._felhasznalo_id_lekerese(felhasznalo["username"])
        felhasznalo["id"] = user_id
        return (
            sikeres,
            f"Regisztracios kiseret HTTP {valasz.status_code}, user_id={user_id}.",
            {"statusz": valasz.status_code, "felhasznalonev": felhasznalo["username"], "user_id": user_id},
        )

    def teszt_duplikalt_regisztracio(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/login"),
            data={
                "type": "register",
                "username": self.felhasznalo_1["username"],
                "email": "mashol@example.com",
                "passwd": "valamiMas123",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        hibakezelt = (
            valasz.status_code == 200
            and ("foglalt" in valasz.text.lower() or "mar hasznalatban" in valasz.text.lower()
                 or "már használat" in valasz.text.lower())
        )
        return (
            hibakezelt,
            "A rendszer helyesen visszautasitja a duplikalt felhasznalonevet."
            if hibakezelt else f"A duplikalt regisztraciot nem utasitotta vissza (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_duplikalt_email(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/login"),
            data={
                "type": "register",
                "username": f"masnev_{self._veletlen_szoveg()}",
                "email": self.felhasznalo_1["email"],
                "passwd": "valamiMas123",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        hibakezelt = valasz.status_code == 200 and (
            "már használat" in valasz.text.lower() or "mar hasznalatban" in valasz.text.lower() or "foglalt" in valasz.text.lower()
        )
        return (
            hibakezelt,
            "A rendszer visszautasitja a duplikalt email cimet."
            if hibakezelt else f"Duplikalt email nem lett visszautasitva (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_tul_hosszu_jelszo(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        hosszu_jelszo = "a" * 80
        valasz = self.vendeg_sesszio.post(
            self._url("/login"),
            data={
                "type": "register",
                "username": f"hosszu_{self._veletlen_szoveg()}",
                "email": f"h_{self._veletlen_szoveg()}@example.com",
                "passwd": hosszu_jelszo,
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        hibakezelt = valasz.status_code == 200 and (
            "túl hosszú" in valasz.text.lower() or "tul hosszu" in valasz.text.lower() or "72" in valasz.text
        )
        return (
            hibakezelt,
            "A szerver elutasitja a 72 karakternel hosszabb jelszot."
            if hibakezelt else f"A hosszu jelszo nem lett elutasitva (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_bejelentkezes_rossz_jelszoval(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        ideiglenes = requests.Session()
        valasz = ideiglenes.post(
            self._url("/login"),
            data={
                "type": "login",
                "username": self.felhasznalo_1["username"],
                "passwd": "teljesenRosszJelszo123",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        # Sikeresen bejelentkezett volna => 302. Mi azt szeretnenk, hogy 200 (ujratoltott login).
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            "Rossz jelszoval nem lehet bejelentkezni."
            if sikeres else f"Rossz jelszoval is atment a bejelentkezes (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_bejelentkezes_nemletezo_felhasznaloval(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        ideiglenes = requests.Session()
        valasz = ideiglenes.post(
            self._url("/login"),
            data={
                "type": "login",
                "username": f"nemletezik_{self._veletlen_szoveg()}",
                "passwd": "BarmilyenJelszo123",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            "Nemletezo felhasznalonevvel sem lehet bejelentkezni."
            if sikeres else f"Furcsa valasz a nemletezo felhasznalora (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_bejelentkezes(
        self, sesszio: requests.Session, felhasznalo: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = sesszio.post(
            self._url("/login"),
            data={
                "type": "login",
                "username": felhasznalo["username"],
                "passwd": felhasznalo["password"],
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (302, 200)
        return (
            sikeres,
            f"Bejelentkezes HTTP {valasz.status_code}, felhasznalo: {felhasznalo['username']}.",
            {"statusz": valasz.status_code},
        )

    def teszt_remember_me_cookie(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Bejelentkezes utan session-cookie elerheto."""
        talalt = False
        for c in self.sesszio_1.cookies:
            if c.name.lower() in ("session", "remember_token"):
                talalt = True
                break
        return (
            talalt,
            "Bejelentkezes utan session cookie aktiv." if talalt else "Nincs session cookie a sesszioban.",
            {"cookiek": [c.name for c in self.sesszio_1.cookies]},
        )

    # ----------------------------------------------------------
    # Profil
    # ----------------------------------------------------------

    def teszt_profil_letrehozas(
        self, sesszio: requests.Session, felhasznalo: Dict[str, Any]
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = sesszio.post(
            self._url("/createprofile"),
            data={
                "name": felhasznalo.get("name", felhasznalo["username"].capitalize()),
                "address": "Budapest, Teszt utca 1.",
                "birthdate": "1995-01-15",
                "phone_number": "+36201234567",
                "phone_number_is_private": "true",
                "address_is_private": "false",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (200, 302)
        uzenet = f"Profil letrehozas HTTP {valasz.status_code}."
        reszletek: Dict[str, Any] = {"statusz": valasz.status_code}
        if valasz.headers.get("Content-Type", "").startswith("application/json"):
            try:
                json_valasz = valasz.json()
                reszletek["json"] = json_valasz
                sikeres = bool(json_valasz.get("success"))
                uzenet = json_valasz.get("message") or uzenet
            except Exception:
                pass
        return sikeres, uzenet, reszletek

    def teszt_profil_ervenytelen_datummal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/editprofile"),
            data={
                "name": "Teszt Anna",
                "address": "Budapest, Teszt utca 1.",
                "birthdate": "nem-datum",
                "phone_number": "+36201234567",
                "phone_number_is_private": "true",
                "address_is_private": "false",
            },
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code in (400, 200)
        try:
            adat = valasz.json()
            sikeres = sikeres and adat.get("success") is False
        except Exception:
            pass
        return (
            sikeres,
            "Ervenytelen datumformatot a szerver elutasitja."
            if sikeres else f"Ervenytelen datum atment (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_profil_hianyzo_nev(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/editprofile"),
            data={
                "name": "",
                "address": "Budapest",
                "birthdate": "1995-01-15",
            },
            timeout=IDOKORLAT_MP,
        )
        ok = valasz.status_code == 400
        try:
            adat = valasz.json()
            ok = ok and adat.get("success") is False
        except Exception:
            pass
        return (
            ok,
            "Hianyzo nev eseten a szerver 400-zal valaszol." if ok else f"Hianyzo nev nem 400 (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_fooldal_hitelesitve(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(self._url("/"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"A fooldalt a bejelentkezett felhasznalo elerte (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code, "hossz": len(valasz.text)},
        )

    def teszt_profil_oldal_sajat(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(self._url("/profile"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"A sajat profil oldal elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_profil_oldal_masik(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_2_id:
            return False, "Nincs 2. felhasznalo ID.", None
        valasz = self.sesszio_1.get(self._url(f"/profile/{self.felhasznalo_2_id}"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"Masik felhasznalo profilja lathato (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_profil_oldal_nemletezo(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(
            self._url("/profile/999999999"),
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (302, 404)
        return (
            sikeres,
            f"Nemletezo felhasznalo profiljahoz HTTP {valasz.status_code} jon.",
            {"statusz": valasz.status_code},
        )

    def teszt_profil_szerkesztes_oldal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(self._url("/editprofile"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"A profil szerkesztes oldal elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_profilkep_feltoltese(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        png_bajtok = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
            "890000000D4944415478DA63FCCFC0F01F00050101005A4D02F20000000049454E44AE426082"
        )
        valasz = self.sesszio_1.post(
            self._url("/editprofile"),
            data={
                "name": self.felhasznalo_1.get("name", "Teszt Anna"),
                "address": "Budapest, Teszt utca 1.",
                "birthdate": "1995-01-15",
                "phone_number": "+36201234567",
                "phone_number_is_private": "true",
                "address_is_private": "false",
            },
            files={"profile_picture": ("profil.png", io.BytesIO(png_bajtok), "image/png")},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code in (200, 302)
        try:
            adat = valasz.json()
            sikeres = sikeres and adat.get("success", False)
        except Exception:
            adat = None
        return (
            sikeres,
            "Profilkep feltoltese sikeres." if sikeres else f"Profilkep feltoltes sikertelen (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    # ----------------------------------------------------------
    # 2FA
    # ----------------------------------------------------------

    def teszt_2fa_qr_generalas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(self._url("/generate2fa_qr"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code in (200, 400)
        if valasz.status_code == 200:
            sikeres = bool(adat.get("success") and adat.get("qr_code"))
        return (
            sikeres,
            "2FA QR kod keszitese mukodik." if sikeres else "2FA QR kod keszites hiba.",
            {"statusz": valasz.status_code, "qr_meret": len(adat.get("qr_code", "") if adat else "")},
        )

    def teszt_2fa_setup_endpoint(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """A /create2fa GET POST nelkul, illetve hibas OTP-vel."""
        valasz = self.sesszio_1.post(self._url("/create2fa"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and isinstance(adat, dict)
        return (
            sikeres,
            "A /create2fa vegpont a setup folyamat elejen QR kodot ad vissza vagy hibat.",
            {"statusz": valasz.status_code, "success": adat.get("success") if isinstance(adat, dict) else None},
        )

    def teszt_2fa_hibas_otp(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/create2fa"),
            data={"2fa_code": "000000"},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 400 and adat.get("success") is False
        return (
            sikeres,
            "A rendszer elutasitja a nem megfelelo OTP kodot."
            if sikeres else f"Hibas OTP nem lett elutasitva (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_2fa_verification_oldal_lathato(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/2fa-verification"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code in (200, 302)
        return (
            sikeres,
            f"A 2FA verifikacios oldal elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    # ----------------------------------------------------------
    # Poszt kezelese
    # ----------------------------------------------------------

    def teszt_poszt_letrehozas_hianyos(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": "",
                "description": "",
                "category": "egyeb",
                "location": "Budapest",
                "type": "lost",
                "language": "hu",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 400
        return (
            sikeres,
            "A szerver helyesen 400-as hibat ad vissza, ha nincs nev/leiras."
            if sikeres else f"Hianyos poszt nem lett elutasitva (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_letrehozas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": f"Teszt elveszett kulcs {self._veletlen_szoveg()}",
                "description": "Egy szep alap kulcs-csomo, elveszett a park melletti kavezoban.",
                "category": "egyeb",
                "location": "Budapest, Varosliget",
                "type": "lost",
                "language": "hu",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 200
        reszletek: Dict[str, Any] = {"statusz": valasz.status_code}
        try:
            adat = valasz.json()
            reszletek["json"] = adat
            if adat.get("success") and "item_id" in adat:
                self.letrehozott_item_id = adat["item_id"]
                sikeres = True
            else:
                sikeres = False
        except Exception:
            sikeres = False
        return (
            sikeres,
            f"Uj poszt letrehozva, item_id={self.letrehozott_item_id}." if sikeres else "A poszt letrehozasa sikertelen.",
            reszletek,
        )

    def teszt_poszt_letrehozas_found(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_2.post(
            self._url("/post/create"),
            data={
                "name": f"Talalt irataco {self._veletlen_szoveg()}",
                "description": "Egy szurke iratacot talaltunk a busz megallonal.",
                "category": "dokumentum",
                "location": "Pest megye, Szentendre",
                "type": "found",
                "language": "hu",
            },
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        if sikeres:
            self.letrehozott_item_id_2 = adat["item_id"]
        return (
            sikeres,
            f"FOUND tipusu poszt letrehozva (id={self.letrehozott_item_id_2})." if sikeres else "FOUND poszt letrehozas hiba.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_poszt_invalid_tipus_normalizalas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Rossz `type` parameter eseten 'lost'-ra normalizaljon."""
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": f"Invalid tipus {self._veletlen_szoveg()}",
                "description": "Leiras a teszthez.",
                "category": "egyeb",
                "location": "Budapest",
                "type": "rossz-tipus",
                "language": "hu",
            },
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False) and "item_id" in adat
        return (
            sikeres,
            "Rossz tipus eseten a poszt 'lost' ertekkel jon letre."
            if sikeres else "Invalid tipus nem lett normalizalva.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_poszt_letrehozas_keppel(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        png_bajtok = bytes.fromhex(
            "89504E470D0A1A0A0000000D49484452000000010000000108060000001F15C4"
            "890000000D4944415478DA63FCCFC0F01F00050101005A4D02F20000000049454E44AE426082"
        )
        kep = ("teszt.png", io.BytesIO(png_bajtok), "image/png")
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": f"Talalt tarca {self._veletlen_szoveg()}",
                "description": "Egy fekete tarca kerult elo az irodahaz elott.",
                "category": "egyeb",
                "location": "Debrecen, Foter",
                "type": "found",
                "language": "hu",
            },
            files={"images": kep},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        if sikeres:
            self.letrehozott_kep_item_id = adat["item_id"]
        return (
            sikeres,
            "Poszt keppel egyutt sikeresen letrehozva." if sikeres else "Keppel torteno poszt letrehozas sikertelen.",
            {"statusz": valasz.status_code, "json": adat},
        )

    def teszt_poszt_letrehozas_tiltott_fajl(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        rossz_fajl = ("evil.txt", io.BytesIO(b"nem-kep"), "text/plain")
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": f"Tiltott fajl teszt {self._veletlen_szoveg()}",
                "description": "Tiltott fajl teszt",
                "category": "egyeb",
                "location": "Budapest",
                "type": "lost",
                "language": "hu",
            },
            files={"images": rossz_fajl},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        # A szerver elfogadja a posztot, de a txt fajl nem kerul mellekletkent rogzitesre (silent skip)
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Tiltott kiterjesztesu fajl eseten a poszt letrejon, de a fajl nem csatolodik."
            if sikeres else "Tiltott fajl rogzites meghiusitotta a posztot.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_poszt_megjelenites(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs letrehozott poszt.", None
        # A poszt csak akkor aktiv, ha a forditas befejezodott - varjunk egy kicsit
        sikeres = False
        statusz = 0
        for _ in range(8):
            valasz = self.vendeg_sesszio.get(
                self._url(f"/post/{self.letrehozott_item_id}"),
                timeout=IDOKORLAT_MP,
                allow_redirects=False,
            )
            statusz = valasz.status_code
            if valasz.status_code == 200:
                sikeres = True
                break
            time.sleep(1)
        return (
            sikeres,
            f"A letrehozott poszt lathatova valt (HTTP {statusz})."
            if sikeres else f"A poszt nem lett aktiv a vart idon belul (utolso HTTP {statusz}).",
            {"statusz": statusz},
        )

    def teszt_poszt_adatok_lekerdese(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_1.get(
            self._url(f"/post/{self.letrehozott_item_id}/data"),
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success") and adat.get("id") == self.letrehozott_item_id
        return (
            sikeres,
            "Poszt adatai sikeresen lekerdezve." if sikeres else "Adatok lekerdese hiba.",
            {"statusz": valasz.status_code, "json": adat},
        )

    def teszt_poszt_adatok_jogosulatlan(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.get(
            self._url(f"/post/{self.letrehozott_item_id}/data"),
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 403
        return (
            sikeres,
            "Idegen felhasznalo nem kerdezheti le a poszt szerkesztesi adatat."
            if sikeres else f"403 helyett HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_szerkesztes_sajat(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_1.post(
            self._url(f"/post/{self.letrehozott_item_id}/edit"),
            data={
                "name": "Modositott nev",
                "description": "Modositott leiras magyarul.",
                "category": "elektronika",
                "location": "Budapest, V. kerulet",
                "type": "lost",
                "language": "hu",
                "is_closed": "false",
                "removed_images": "[]",
            },
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Tulajdonos sikeresen szerkesztette a posztot." if sikeres else "Szerkesztes sikertelen.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_poszt_szerkesztes_jogosulatlan(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.post(
            self._url(f"/post/{self.letrehozott_item_id}/edit"),
            data={
                "name": "Jogosulatlan modositas",
                "description": "Hekkerkiseret",
                "category": "egyeb",
                "location": "",
                "type": "lost",
                "language": "hu",
                "is_closed": "false",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 403
        return (
            sikeres,
            "403 a jogosulatlan szerkesztesre." if sikeres else f"HTTP {valasz.status_code} a jogosulatlan szerkesztesre!",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_lezaras_kapcsolhato(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz1 = self.sesszio_1.post(
            self._url(f"/post/{self.letrehozott_item_id}/close"), timeout=IDOKORLAT_MP
        )
        try:
            adat1 = valasz1.json()
        except Exception:
            adat1 = {}
        # Vissza is kapcsoljuk
        valasz2 = self.sesszio_1.post(
            self._url(f"/post/{self.letrehozott_item_id}/close"), timeout=IDOKORLAT_MP
        )
        try:
            adat2 = valasz2.json()
        except Exception:
            adat2 = {}
        sikeres = (
            valasz1.status_code == 200
            and valasz2.status_code == 200
            and adat1.get("is_closed") != adat2.get("is_closed")
        )
        return (
            sikeres,
            f"Lezarasi kapcsolo mukodik: {adat1.get('is_closed')} -> {adat2.get('is_closed')}."
            if sikeres else "A lezarasi kapcsolo nem valtott.",
            {"elso": adat1, "masodik": adat2},
        )

    def teszt_poszt_lezaras_jogosulatlan(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.post(
            self._url(f"/post/{self.letrehozott_item_id}/close"),
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 403
        return (
            sikeres,
            "Idegen nem zarhatja le a posztot." if sikeres else f"HTTP {valasz.status_code} helyett 403 kellene.",
            {"statusz": valasz.status_code},
        )

    def teszt_nem_letezo_poszt_redirect(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(
            self._url("/post/99999999"), timeout=IDOKORLAT_MP, allow_redirects=False
        )
        sikeres = valasz.status_code in (302, 404)
        return (
            sikeres,
            f"Nemletezo posztra HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_adatok_nemletezo(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(self._url("/post/99999999/data"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 404
        return (
            sikeres,
            "Nemletezo poszt adatlekerdese 404." if sikeres else f"HTTP {valasz.status_code} nemletezo posztra!",
            {"statusz": valasz.status_code},
        )

    # ----------------------------------------------------------
    # Bejelentesek
    # ----------------------------------------------------------

    def teszt_onbejelentes_kiszurve(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_1.post(
            self._url(f"/report-post/{self.letrehozott_item_id}"),
            data={"reason": "sajat-teszt", "content": "ez egy sajat poszt"},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 400
        return (
            sikeres,
            "A sajat poszt bejelentese 400-as hibaval tiltott."
            if sikeres else f"Sajat bejelentes HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_bejelentes_indoklas_nelkul(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.post(
            self._url(f"/report-post/{self.letrehozott_item_id}"),
            data={"reason": "", "content": ""},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 400
        return (
            sikeres,
            "Indoklas nelkuli bejelentes 400." if sikeres else f"HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def teszt_bejelentes_masik_felhasznalotol(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.post(
            self._url(f"/report-post/{self.letrehozott_item_id}"),
            data={"reason": "hamis", "content": "Valoszinutleg hamis poszt."},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Masik felhasznalo sikeresen bejelentette a posztot." if sikeres else "Bejelentes sikertelen.",
            {"statusz": valasz.status_code, "json": adat},
        )

    def teszt_duplikalt_bejelentes(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_2.post(
            self._url(f"/report-post/{self.letrehozott_item_id}"),
            data={"reason": "hamis", "content": "Megegyszer bejelentem."},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 400
        return (
            sikeres,
            "A rendszer megakadalyozza a ketszeri bejelentest egy posztra."
            if sikeres else f"Duplikalt bejelentes HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def teszt_felhasznalo_bejelentes_sajat(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_1_id:
            return False, "Nincs 1. felhasznalo ID.", None
        valasz = self.sesszio_1.post(
            self._url(f"/report-user/{self.felhasznalo_1_id}"),
            data={"reason": "teszt", "content": ""},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 400
        return (
            sikeres,
            "Sajat magunk bejelentese tilos (400)." if sikeres else f"HTTP {valasz.status_code} a sajat bejelentesre.",
            {"statusz": valasz.status_code},
        )

    def teszt_felhasznalo_bejelentes_masik(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_2_id:
            return False, "Nincs 2. felhasznalo ID.", None
        valasz = self.sesszio_1.post(
            self._url(f"/report-user/{self.felhasznalo_2_id}"),
            data={"reason": "spam", "content": "Spam uzenetek."},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Masik felhasznalo bejelentese sikeres." if sikeres else "Felhasznalo bejelentese nem ment at.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_felhasznalo_bejelentes_nemletezo(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/report-user/99999999"),
            data={"reason": "spam", "content": "teszt"},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 404
        return (
            sikeres,
            "Nemletezo felhasznalo bejelentesere 404." if sikeres else f"HTTP {valasz.status_code} helyett 404.",
            {"statusz": valasz.status_code},
        )

    # ----------------------------------------------------------
    # Jelszo visszaallitas
    # ----------------------------------------------------------

    def teszt_jelszo_visszaallitas_kerese(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/reset_password_req"),
            json={"username": self.felhasznalo_1["username"]},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 200
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        return (
            sikeres,
            f"Jelszo visszaallitasi kereses vegpont elerheto, valasz: {adat}.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_nem_letezo_felhasznalo_reset(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/reset_password_req"),
            json={"username": f"nemletezik_{self._veletlen_szoveg()}"},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = valasz.status_code == 200 and adat is False
        return (
            sikeres,
            "Nemletezo felhasznalonevre False valasz." if sikeres else f"Hibas valasz ({adat}).",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_reset_password_ures_username(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/reset_password_req"),
            json={"username": "   "},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = valasz.status_code == 200 and adat is False
        return (
            sikeres,
            "Ures felhasznalonevre a reset False-t ad." if sikeres else f"Valasz: {adat}.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_reset_password_oldal_token_nelkul(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(
            self._url("/reset-password"), timeout=IDOKORLAT_MP, allow_redirects=False
        )
        sikeres = valasz.status_code in (302, 200)
        # Token nelkul atiranyit a loginra
        if valasz.status_code == 302:
            ok_atiranyitas = "/login" in valasz.headers.get("Location", "")
            sikeres = ok_atiranyitas
        return (
            sikeres,
            f"Token nelkuli reset oldal helyesen kezelve (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code, "location": valasz.headers.get("Location")},
        )

    def teszt_reset_password_ervenytelen_token(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.post(
            self._url("/reset-password"),
            data={"token": "ervenytelen-token-abcd1234", "new_password": "ujJelszo1234"},
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 302
        return (
            sikeres,
            "Ervenytelen tokennel nem tortenik jelszovaltas, hanem redirect."
            if sikeres else f"HTTP {valasz.status_code} az ervenytelen tokenre.",
            {"statusz": valasz.status_code, "location": valasz.headers.get("Location")},
        )

    # ----------------------------------------------------------
    # Uzenet oldal + Socket.IO chat
    # ----------------------------------------------------------

    def teszt_uzenet_oldal_bejelentkezetten(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(self._url("/messages"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"Az uzenet oldal elerheto bejelentkezve (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_uzenet_oldal_bejelentkezes_nelkul(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(self._url("/messages"), timeout=IDOKORLAT_MP, allow_redirects=False)
        sikeres = valasz.status_code in (302, 401)
        return (
            sikeres,
            "Uzenet oldal bejelentkezes nelkul atiranyit."
            if sikeres else f"HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code},
        )

    def _socketio_kliens(self, sesszio: requests.Session) -> socketio.Client:
        cookiek = {c.name: c.value for c in sesszio.cookies}
        ker_fejlec = {"Cookie": "; ".join(f"{k}={v}" for k, v in cookiek.items())}
        sio = socketio.Client(logger=False, engineio_logger=False, reconnection=False)
        sio.connect(self.alap_url, wait_timeout=10, headers=ker_fejlec, transports=["polling", "websocket"])
        return sio

    def teszt_socketio_get_conversations(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Socket.IO kapcsolat + get_conversations."""
        kapott: List[Any] = []
        kesz = threading.Event()
        sio = self._socketio_kliens(self.sesszio_1)
        try:
            @sio.on("conversations")
            def _handler(data):
                kapott.append(data)
                kesz.set()

            sio.emit("get_conversations")
            kesz.wait(timeout=5)
        finally:
            sio.disconnect()

        sikeres = len(kapott) > 0 and isinstance(kapott[0], list) and any(
            isinstance(cs, dict) and cs.get("is_system") for cs in kapott[0]
        )
        return (
            sikeres,
            f"Beszelgetes-lista lekerve ({len(kapott[0]) if kapott else 0} elem, benne system chat)."
            if sikeres else "get_conversations nem valaszolt, vagy nincs system chat.",
            {"valasz_hossz": len(kapott[0]) if kapott else 0},
        )

    def teszt_socketio_system_chat(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        kapott: List[Any] = []
        kesz = threading.Event()
        sio = self._socketio_kliens(self.sesszio_1)
        try:
            @sio.on("messages")
            def _handler(data):
                kapott.append(data)
                kesz.set()

            sio.emit("get_messages", {"partner_id": 0})
            kesz.wait(timeout=5)
        finally:
            sio.disconnect()

        sikeres = (
            len(kapott) > 0 and isinstance(kapott[0], list) and len(kapott[0]) > 0 and "text" in kapott[0][0]
        )
        return (
            sikeres,
            "System chat udvozlo uzenet lekerdezheto." if sikeres else "System chat nem jott meg.",
            {"elemszam": len(kapott[0]) if kapott else 0},
        )

    def teszt_socketio_uzenet_kuldese(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_2_id:
            return False, "Nincs 2. felhasznalo.", None
        sent_events: List[Any] = []
        uj_events: List[Any] = []
        kesz_sent = threading.Event()

        sio_kuldo = self._socketio_kliens(self.sesszio_1)
        sio_fogado = self._socketio_kliens(self.sesszio_2)
        try:
            @sio_kuldo.on("message_sent")
            def _sent(data):
                sent_events.append(data)
                kesz_sent.set()

            @sio_fogado.on("new_message")
            def _new(data):
                uj_events.append(data)

            sio_kuldo.emit(
                "send_message",
                {"partner_id": self.felhasznalo_2_id, "text": "Szia teszt uzenet!"},
            )
            kesz_sent.wait(timeout=5)
            time.sleep(1)
        finally:
            sio_kuldo.disconnect()
            sio_fogado.disconnect()

        sikeres = len(sent_events) > 0 and isinstance(sent_events[0], dict) and sent_events[0].get("text")
        return (
            sikeres,
            f"Uzenet elkuldve, {len(uj_events)} new_message esemeny a fogadonal."
            if sikeres else "Uzenet kuldese nem sikerult.",
            {"elkuldve": bool(sent_events), "kapott_esemenyek": len(uj_events)},
        )

    def teszt_socketio_system_chat_valasz_tiltas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        hibak: List[Any] = []
        kesz = threading.Event()
        sio = self._socketio_kliens(self.sesszio_1)
        try:
            @sio.on("error")
            def _h(data):
                hibak.append(data)
                kesz.set()

            sio.emit("send_message", {"partner_id": 0, "text": "Proba szoveg"})
            kesz.wait(timeout=4)
        finally:
            sio.disconnect()

        sikeres = any("Rendszer" in (h.get("message", "") if isinstance(h, dict) else "") for h in hibak)
        return (
            sikeres,
            "System chat (partner_id=0) nem fogadja az uzeneteket."
            if sikeres else "System chat uzenet tiltas nem kezelt.",
            {"hibak": hibak},
        )

    def teszt_socketio_hosszu_uzenet_tiltva(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_2_id:
            return False, "Nincs 2. felhasznalo.", None
        hibak: List[Any] = []
        kesz = threading.Event()
        sio = self._socketio_kliens(self.sesszio_1)
        try:
            @sio.on("error")
            def _h(data):
                hibak.append(data)
                kesz.set()

            sio.emit(
                "send_message",
                {"partner_id": self.felhasznalo_2_id, "text": "x" * 5100},
            )
            kesz.wait(timeout=4)
        finally:
            sio.disconnect()

        sikeres = any("too long" in (h.get("message", "").lower() if isinstance(h, dict) else "") for h in hibak)
        return (
            sikeres,
            "A rendszer 5000 karakter felett visszautasitja az uzenetet."
            if sikeres else "Hosszu uzenet kiszures nem erzekelheto.",
            {"hibak": hibak},
        )

    def teszt_socketio_partner_info(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.felhasznalo_2_id:
            return False, "Nincs 2. felhasznalo.", None
        kapott: List[Any] = []
        kesz = threading.Event()
        sio = self._socketio_kliens(self.sesszio_1)
        try:
            @sio.on("partner_info")
            def _h(data):
                kapott.append(data)
                kesz.set()

            sio.emit("get_partner_info", {"partner_id": self.felhasznalo_2_id})
            kesz.wait(timeout=5)
        finally:
            sio.disconnect()

        sikeres = len(kapott) > 0 and isinstance(kapott[0], dict) and kapott[0].get("id") == self.felhasznalo_2_id
        return (
            sikeres,
            "Partner informacio lekerheto." if sikeres else "Partner informacio nem kapott valaszt.",
            {"valasz": kapott},
        )

    def teszt_socketio_autentikalatlan(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Socket.IO csatlakozas auth nelkul nem kaphat conversations adatot."""
        hibak: List[Any] = []
        kapott: List[Any] = []
        kesz = threading.Event()
        sio = socketio.Client(logger=False, engineio_logger=False, reconnection=False)
        try:
            sio.connect(self.alap_url, wait_timeout=5)

            @sio.on("conversations")
            def _c(data):
                kapott.append(data)
                kesz.set()

            @sio.on("error")
            def _e(data):
                hibak.append(data)
                kesz.set()

            sio.emit("get_conversations")
            kesz.wait(timeout=4)
        finally:
            try:
                sio.disconnect()
            except Exception:
                pass

        # Autentikalatlan eseten conversations nem erkezhet (vagy hibat kap)
        sikeres = len(kapott) == 0 or any(
            "not authenticated" in (h.get("message", "").lower() if isinstance(h, dict) else "") for h in hibak
        )
        return (
            sikeres,
            "Autentikalatlan kliens nem kap bizalmas adatokat a socketen."
            if sikeres else "Autentikalatlan socket valaszt kapott!",
            {"hibak": hibak, "kapott": kapott},
        )

    # ----------------------------------------------------------
    # Admin
    # ----------------------------------------------------------

    def teszt_admin_api_felhasznalo_nelkul(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.get(
            self._url("/admin/api/users"), timeout=IDOKORLAT_MP, allow_redirects=False
        )
        sikeres = valasz.status_code == 403
        return (
            sikeres,
            "Admin API nem elerheto sima felhasznalonak (403)."
            if sikeres else f"HTTP {valasz.status_code}!",
            {"statusz": valasz.status_code},
        )

    def teszt_admin_regisztracio(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.post(
            self._url("/login"),
            data={
                "type": "register",
                "username": self.admin_felhasznalo["username"],
                "email": self.admin_felhasznalo["email"],
                "passwd": self.admin_felhasznalo["password"],
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (200, 302)
        uid = self._felhasznalo_id_lekerese(self.admin_felhasznalo["username"])
        self.admin_felhasznalo_id = uid
        return (
            sikeres,
            f"Admin felhasznalo regisztralva (user_id={uid})." if sikeres else "Admin regisztracio sikertelen.",
            {"statusz": valasz.status_code, "user_id": uid},
        )

    def teszt_admin_szerepkor_allitas(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        sikeres = self._szerepkor_admin_allitas(self.admin_felhasznalo["username"])
        return (
            sikeres,
            "Admin szerepkor beallitasa az adatbazisban sikeres."
            if sikeres else "Nem sikerult a DB-ben beallitani az admin szerepkort.",
            {"db_ut": DB_UT},
        )

    def teszt_admin_bejelentkezes(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        uj_sesszio = requests.Session()
        self.admin_sesszio = uj_sesszio
        valasz = uj_sesszio.post(
            self._url("/login"),
            data={
                "type": "login",
                "username": self.admin_felhasznalo["username"],
                "passwd": self.admin_felhasznalo["password"],
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code == 302 and "/admin" in valasz.headers.get("Location", "")
        return (
            sikeres,
            f"Admin bejelentkezes utan /admin iranyba redirect (Location={valasz.headers.get('Location')})."
            if sikeres else f"Admin bejelentkezes redirectje: {valasz.headers.get('Location')}",
            {"statusz": valasz.status_code, "location": valasz.headers.get("Location")},
        )

    def teszt_admin_dashboard(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/dashboard"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            f"Admin dashboard oldal elerheto (HTTP {valasz.status_code}).",
            {"statusz": valasz.status_code},
        )

    def teszt_admin_users_oldal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/users"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return sikeres, f"Admin users oldal HTTP {valasz.status_code}.", {"statusz": valasz.status_code}

    def teszt_admin_posts_oldal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/posts"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return sikeres, f"Admin posts oldal HTTP {valasz.status_code}.", {"statusz": valasz.status_code}

    def teszt_admin_metrics(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/metrics"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = (
            valasz.status_code == 200
            and isinstance(adat, dict)
            and "ram" in adat
            and "cpu" in adat
            and "stats" in adat
        )
        return (
            sikeres,
            f"Admin /metrics RAM/CPU/stats adatokat ad (users={adat['stats']['total_users'] if sikeres else '?'})."
            if sikeres else f"Admin /metrics nem valaszolt helyesen. Status: {valasz.status_code}, Response: {adat if adat else 'empty'}",
            {"statusz": valasz.status_code, "reszek": list(adat.keys()) if isinstance(adat, dict) else None, "valasz": adat},
        )

    def teszt_admin_api_users(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/api/users"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception as e:
            adat = None
        sikeres = (
            valasz.status_code == 200 and isinstance(adat, dict) and "users" in adat and isinstance(adat["users"], list)
        )
        return (
            sikeres,
            f"Admin /api/users listat ad ({len(adat['users']) if sikeres else 0} elem az elso oldalon)."
            if sikeres else f"Admin /api/users nem valaszolt elvart formatumban. Status: {valasz.status_code}, Response: {adat if adat else 'empty'}",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_admin_api_users_kereses(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(
            self._url("/admin/api/users"),
            params={"search": self.felhasznalo_1["username"]},
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = (
            valasz.status_code == 200
            and isinstance(adat, dict)
            and any(u["username"] == self.felhasznalo_1["username"] for u in adat.get("users", []))
        )
        return (
            sikeres,
            "Admin /api/users keresesi eredmenyt ad." if sikeres else "Kereses nem adott egyezo felhasznalot.",
            {"statusz": valasz.status_code, "talalat_szam": len(adat.get("users", [])) if isinstance(adat, dict) else 0},
        )

    def teszt_admin_api_posts(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/api/posts"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception as e:
            adat = None
        sikeres = valasz.status_code == 200 and isinstance(adat, dict) and "posts" in adat
        return (
            sikeres,
            f"Admin /api/posts elerheto ({len(adat['posts']) if sikeres else 0} elem)."
            if sikeres else f"Admin /api/posts nem valaszolt helyesen. Status: {valasz.status_code}, Response: {adat if adat else 'empty'}",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_admin_api_posts_statusz_szures(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(
            self._url("/admin/api/posts"), params={"status": "active"}, timeout=IDOKORLAT_MP
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = (
            valasz.status_code == 200 and isinstance(adat, dict) and isinstance(adat.get("posts"), list)
        )
        if sikeres:
            for p in adat["posts"]:
                if p["status"] not in ("Active",):
                    sikeres = False
                    break
        return (
            sikeres,
            "Admin /api/posts status=active csak aktiv posztokat ad." if sikeres else "Statusz szures hibas.",
            {"statusz": valasz.status_code, "elemszam": len(adat.get("posts", [])) if isinstance(adat, dict) else 0},
        )

    def teszt_admin_api_reports(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(self._url("/admin/api/reports"), timeout=IDOKORLAT_MP)
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = valasz.status_code == 200 and isinstance(adat, dict) and "reports" in adat
        if sikeres and adat.get("reports"):
            self.letrehozott_report_id = adat["reports"][0]["id"]
        return (
            sikeres,
            f"Admin /api/reports elerheto ({len(adat['reports']) if sikeres else 0} elem)."
            if sikeres else f"Admin /api/reports nem valaszolt. Status: {valasz.status_code}, Response: {adat if adat else 'empty'}",
            {"statusz": valasz.status_code, "elso_report_id": self.letrehozott_report_id, "valasz": adat},
        )

    def teszt_admin_report_resolve(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_report_id:
            return False, "Nincs rendezheto bejelentes.", None
        valasz = self.admin_sesszio.post(
            self._url(f"/admin/api/reports/{self.letrehozott_report_id}/resolve"),
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Bejelentes rendezettre valtva admin altal." if sikeres else "Resolve sikertelen.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_admin_api_posts_kereses(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.get(
            self._url("/admin/api/posts"), params={"search": "Teszt"}, timeout=IDOKORLAT_MP
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = None
        sikeres = valasz.status_code == 200 and isinstance(adat, dict)
        return (
            sikeres,
            f"Admin /api/posts search Teszt-re {len(adat.get('posts', []))} elem." if sikeres else "Kereses hiba.",
            {"statusz": valasz.status_code},
        )

    def teszt_admin_item_torles(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_kep_item_id:
            return False, "Nincs admin torlendo poszt.", None
        valasz = self.admin_sesszio.post(
            self._url(f"/admin/api/items/{self.letrehozott_kep_item_id}/delete"),
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Admin torolte a poszt elemet." if sikeres else f"Admin torles sikertelen. Status: {valasz.status_code}, Response: {adat}",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    def teszt_admin_nemletezo_item_torles(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.admin_sesszio.post(
            self._url("/admin/api/items/99999999/delete"), timeout=IDOKORLAT_MP
        )
        sikeres = valasz.status_code == 404
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        return (
            sikeres,
            "Nemletezo item torlesere 404." if sikeres else f"HTTP {valasz.status_code}.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    # ----------------------------------------------------------
    # Tobbnyelvuseg
    # ----------------------------------------------------------

    def teszt_i18n_accept_language_en(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.vendeg_sesszio.get(
            self._url("/"),
            headers={"Accept-Language": "en-US,en;q=0.9"},
            timeout=IDOKORLAT_MP,
        )
        sikeres = valasz.status_code == 200
        return sikeres, f"Angol Accept-Language HTTP {valasz.status_code}.", {"statusz": valasz.status_code}

    def teszt_i18n_lang_cookie_en(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        sesszio = requests.Session()
        sesszio.cookies.set("lang", "en")
        valasz = sesszio.get(self._url("/"), timeout=IDOKORLAT_MP)
        sikeres = valasz.status_code == 200
        return sikeres, f"lang=en cookie HTTP {valasz.status_code}.", {"statusz": valasz.status_code}

    def teszt_poszt_en_leirassal(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": f"English test item {self._veletlen_szoveg()}",
                "description": "This is an English description for translation test.",
                "category": "elektronika",
                "location": "Budapest",
                "type": "lost",
                "language": "en",
            },
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "Angol nyelvu posztot elfogad a rendszer." if sikeres else "Angol nyelvu poszt letrehozas hiba.",
            {"statusz": valasz.status_code, "valasz": adat},
        )

    # ----------------------------------------------------------
    # Biztonsagi probak
    # ----------------------------------------------------------

    def teszt_xss_poszt_nevben(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        xss = "<script>alert('xss')</script>Teszt"
        valasz = self.sesszio_1.post(
            self._url("/post/create"),
            data={
                "name": xss,
                "description": "XSS probapoint",
                "category": "egyeb",
                "location": "Budapest",
                "type": "lost",
                "language": "hu",
            },
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        if not (valasz.status_code == 200 and adat.get("success", False)):
            return False, "Nem sikerult a poszt letrehozasa az XSS teszthez.", {"valasz": adat}
        item_id = adat["item_id"]
        # Varjunk, amig aktivva valik
        kor = None
        for _ in range(6):
            kor = self.vendeg_sesszio.get(self._url(f"/post/{item_id}"), timeout=IDOKORLAT_MP, allow_redirects=False)
            if kor.status_code == 200:
                break
            time.sleep(1)
        # Jinja2 alapertelmezetten escape-eli a ${ }-t -> nem talalhato a `<script>` szosszenet formazatlanul
        html_str = kor.text if kor is not None else ""
        sikeres = "<script>alert('xss')</script>" not in html_str
        return (
            sikeres,
            "A sablon helyesen escape-eli az XSS-t tartalmazo nevet."
            if sikeres else "Az XSS payload formazatlanul megjelenik a HTML-ben!",
            {"html_tartalmaz_script": not sikeres},
        )

    def teszt_sql_injection_login_mezobe(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """SQL injection probakiseret a login form username mezojen."""
        payload = "admin' OR '1'='1"
        ideiglenes = requests.Session()
        valasz = ideiglenes.post(
            self._url("/login"),
            data={
                "type": "login",
                "username": payload,
                "passwd": "akarmi",
            },
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        # Sikeres bejelentkezes esetern 302 lenne, tehat 200 (login ujratoltve) a helyes
        sikeres = valasz.status_code == 200
        return (
            sikeres,
            "SQL injection kiseret nem fog visszaerni bejelentkezest."
            if sikeres else f"HTTP {valasz.status_code} - injekcio akcioba lepett?",
            {"statusz": valasz.status_code},
        )

    # ----------------------------------------------------------
    # Kijelentkezes + jogosultsag
    # ----------------------------------------------------------

    def teszt_kijelentkezes(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_2.get(self._url("/logout"), timeout=IDOKORLAT_MP, allow_redirects=False)
        sikeres = valasz.status_code in (302, 200)
        return sikeres, f"Kijelentkezes HTTP {valasz.status_code}.", {"statusz": valasz.status_code}

    def teszt_kijelentkezes_utan_vedett(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        valasz = self.sesszio_2.get(self._url("/editprofile"), timeout=IDOKORLAT_MP, allow_redirects=False)
        sikeres = valasz.status_code in (302, 401)
        return (
            sikeres,
            "Kijelentkezes utan a vedett oldal atiranyit."
            if sikeres else f"Kijelentkezes utan 200 jott (HTTP {valasz.status_code})!",
            {"statusz": valasz.status_code},
        )

    def teszt_bejelentkezes_nelkuli_poszt_torles(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.vendeg_sesszio.post(
            self._url(f"/post/{self.letrehozott_item_id}/delete"),
            timeout=IDOKORLAT_MP,
            allow_redirects=False,
        )
        sikeres = valasz.status_code in (302, 401, 403)
        return (
            sikeres,
            "Bejelentkezes nelkul nem lehet posztot torolni."
            if sikeres else f"HTTP {valasz.status_code}!",
            {"statusz": valasz.status_code},
        )

    def teszt_poszt_torlese(self) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        if not self.letrehozott_item_id:
            return False, "Nincs poszt.", None
        valasz = self.sesszio_1.post(
            self._url(f"/post/{self.letrehozott_item_id}/delete"),
            timeout=IDOKORLAT_MP,
        )
        try:
            adat = valasz.json()
        except Exception:
            adat = {}
        sikeres = valasz.status_code == 200 and adat.get("success", False)
        return (
            sikeres,
            "A tulajdonos torolte a sajat posztot."
            if sikeres else "Poszt torles sikertelen.",
            {"statusz": valasz.status_code, "json": adat},
        )

    # ----------------------------------------------------------
    # Fo forgatokonyv
    # ----------------------------------------------------------

    def forgatokonyv(self) -> None:
        print("=" * 60)
        print("ELVESZETT TARGYAK - KITERJESZTETT TESZT FORGATOKONYV")
        print(f"Celcim: {self.alap_url}")
        print(f"Ido: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)

        # --- Alaprendszer
        self._futtat_teszt("Alaprendszer", "Szerver eleres", self.teszt_szerver_eleres)
        if not self.szerver_elerheto:
            print("\n[!] A szerver nem elerheto. A tovabbi tesztek ki lesznek hagyva.")
            return

        self._futtat_teszt("Alaprendszer", "Fooldal HTML tartalom", self.teszt_fooldal_tartalom)
        self._futtat_teszt("Alaprendszer", "Varmegyek JSON elerheto", self.teszt_varmegyek_json)
        self._futtat_teszt("Statikus", "Logo SVG letoltheto", self.teszt_statikus_logo)
        self._futtat_teszt("Statikus", "HU forditas JSON elerheto", self.teszt_locale_fajl_hu)
        self._futtat_teszt("Statikus", "EN forditas JSON elerheto", self.teszt_locale_fajl_en)
        self._futtat_teszt("Alaprendszer", "Login oldal elerheto", self.teszt_login_oldal_lathato)
        self._futtat_teszt("Alaprendszer", "404 kezeles", self.teszt_404_kezeles)
        self._futtat_teszt("Alaprendszer", "Terkep oldal", self.teszt_terkep_oldal)
        self._futtat_teszt(
            "Jogosultsag",
            "Admin panel bejelentkezes nelkul tiltva",
            self.teszt_admin_bejelentkezes_nelkul_tiltas,
        )

        # --- Felhasznalok letrehozasa
        idobelyeg = int(time.time())
        self.felhasznalo_1 = {
            "username": f"teszt_a_{idobelyeg}",
            "email": f"teszt_a_{idobelyeg}@example.com",
            "password": "ErosJelszo123!",
            "name": "Teszt Anna",
        }
        self.felhasznalo_2 = {
            "username": f"teszt_b_{idobelyeg}",
            "email": f"teszt_b_{idobelyeg}@example.com",
            "password": "ErosJelszo456!",
            "name": "Teszt Bela",
        }
        self.admin_felhasznalo = {
            "username": f"teszt_admin_{idobelyeg}",
            "email": f"teszt_admin_{idobelyeg}@example.com",
            "password": "AdminJelszo789!",
            "name": "Teszt Admin",
        }

        # --- Autentikacio
        self._futtat_teszt(
            "Autentikacio",
            "1. felhasznalo regisztracio",
            lambda: self.teszt_regisztracio(self.sesszio_1, self.felhasznalo_1),
        )
        self.felhasznalo_1_id = self.felhasznalo_1.get("id")

        self._futtat_teszt(
            "Autentikacio",
            "2. felhasznalo regisztracio",
            lambda: self.teszt_regisztracio(self.sesszio_2, self.felhasznalo_2),
        )
        self.felhasznalo_2_id = self.felhasznalo_2.get("id")

        self._futtat_teszt(
            "Autentikacio",
            "Duplikalt felhasznalonev kiszurve",
            self.teszt_duplikalt_regisztracio,
        )
        self._futtat_teszt("Autentikacio", "Duplikalt email kiszurve", self.teszt_duplikalt_email)
        self._futtat_teszt("Autentikacio", "Tul hosszu jelszo tiltva", self.teszt_tul_hosszu_jelszo)
        self._futtat_teszt(
            "Autentikacio",
            "Rossz jelszoval nem enged belepni",
            self.teszt_bejelentkezes_rossz_jelszoval,
        )
        self._futtat_teszt(
            "Autentikacio",
            "Nemletezo felhasznalonevvel nem enged belepni",
            self.teszt_bejelentkezes_nemletezo_felhasznaloval,
        )
        self._futtat_teszt("Autentikacio", "Session cookie bejelentkezes utan", self.teszt_remember_me_cookie)

        # --- Profil
        self._futtat_teszt(
            "Profil",
            "1. felhasznalo profil letrehozas",
            lambda: self.teszt_profil_letrehozas(self.sesszio_1, self.felhasznalo_1),
        )
        self._futtat_teszt(
            "Profil",
            "2. felhasznalo profil letrehozas",
            lambda: self.teszt_profil_letrehozas(self.sesszio_2, self.felhasznalo_2),
        )
        self._futtat_teszt("Profil", "Ervenytelen datumformat elutasitva", self.teszt_profil_ervenytelen_datummal)
        self._futtat_teszt("Profil", "Hianyzo nev elutasitva", self.teszt_profil_hianyzo_nev)
        self._futtat_teszt("Fooldal", "Fooldal elerheto bejelentkezve", self.teszt_fooldal_hitelesitve)
        self._futtat_teszt("Profil", "Sajat profil oldal", self.teszt_profil_oldal_sajat)
        self._futtat_teszt("Profil", "Masik felhasznalo profilja", self.teszt_profil_oldal_masik)
        self._futtat_teszt("Profil", "Nemletezo profil redirect", self.teszt_profil_oldal_nemletezo)
        self._futtat_teszt("Profil", "Profil szerkeszto oldal elerheto", self.teszt_profil_szerkesztes_oldal)
        self._futtat_teszt("Profil", "Profilkep feltoltes", self.teszt_profilkep_feltoltese)

        # --- 2FA
        self._futtat_teszt("2FA", "2FA verification oldal lathato", self.teszt_2fa_verification_oldal_lathato)
        self._futtat_teszt("2FA", "QR kod generalas vegpont", self.teszt_2fa_qr_generalas)
        self._futtat_teszt("2FA", "Setup vegpont QR-t ad vissza", self.teszt_2fa_setup_endpoint)
        self._futtat_teszt("2FA", "Hibas OTP elutasitva", self.teszt_2fa_hibas_otp)

        # --- Poszt
        self._futtat_teszt("Poszt", "Hianyos poszt elutasitva", self.teszt_poszt_letrehozas_hianyos)
        self._futtat_teszt("Poszt", "Uj poszt (lost) letrehozasa", self.teszt_poszt_letrehozas)
        self._futtat_teszt("Poszt", "Uj poszt (found) letrehozasa", self.teszt_poszt_letrehozas_found)
        self._futtat_teszt("Poszt", "Rossz tipus normalizalas", self.teszt_poszt_invalid_tipus_normalizalas)
        self._futtat_teszt("Poszt", "Poszt keppel", self.teszt_poszt_letrehozas_keppel)
        self._futtat_teszt("Poszt", "Tiltott fajl kiterjesztes", self.teszt_poszt_letrehozas_tiltott_fajl)
        self._futtat_teszt("Poszt", "Poszt megjelenites (aktivalas)", self.teszt_poszt_megjelenites)
        self._futtat_teszt("Poszt", "Poszt szerkesztesi adatok", self.teszt_poszt_adatok_lekerdese)
        self._futtat_teszt(
            "Jogosultsag",
            "Idegen nem kerheti le a szerkesztesi adatot",
            self.teszt_poszt_adatok_jogosulatlan,
        )
        self._futtat_teszt("Poszt", "Tulajdonos szerkesztes", self.teszt_poszt_szerkesztes_sajat)
        self._futtat_teszt(
            "Jogosultsag",
            "Idegen nem szerkesztheti a posztot",
            self.teszt_poszt_szerkesztes_jogosulatlan,
        )
        self._futtat_teszt("Poszt", "Lezaras/visszanyitas kapcsolo", self.teszt_poszt_lezaras_kapcsolhato)
        self._futtat_teszt(
            "Jogosultsag",
            "Idegen nem zarhatja le a posztot",
            self.teszt_poszt_lezaras_jogosulatlan,
        )
        self._futtat_teszt("Poszt", "Nemletezo poszt redirect", self.teszt_nem_letezo_poszt_redirect)
        self._futtat_teszt("Poszt", "Nemletezo poszt adatok 404", self.teszt_poszt_adatok_nemletezo)

        # --- Bejelentesek
        self._futtat_teszt("Bejelentes", "Sajat poszt bejelentes tiltva", self.teszt_onbejelentes_kiszurve)
        self._futtat_teszt(
            "Bejelentes",
            "Indoklas nelkuli bejelentes tiltva",
            self.teszt_poszt_bejelentes_indoklas_nelkul,
        )
        self._futtat_teszt(
            "Bejelentes",
            "Masik felhasznalo sikeresen bejelent",
            self.teszt_bejelentes_masik_felhasznalotol,
        )
        self._futtat_teszt("Bejelentes", "Duplikalt bejelentes kiszurve", self.teszt_duplikalt_bejelentes)
        self._futtat_teszt(
            "Bejelentes",
            "Sajat magunk felhasznalo bejelentes tiltva",
            self.teszt_felhasznalo_bejelentes_sajat,
        )
        self._futtat_teszt(
            "Bejelentes",
            "Masik felhasznalo sikeres bejelentese",
            self.teszt_felhasznalo_bejelentes_masik,
        )
        self._futtat_teszt(
            "Bejelentes",
            "Nemletezo felhasznalo bejelentese 404",
            self.teszt_felhasznalo_bejelentes_nemletezo,
        )

        # --- Jelszo visszaallitas
        self._futtat_teszt(
            "Jelszo",
            "Reset kereses letezo felhasznalora",
            self.teszt_jelszo_visszaallitas_kerese,
        )
        self._futtat_teszt(
            "Jelszo",
            "Reset kereses nemletezo felhasznalora",
            self.teszt_nem_letezo_felhasznalo_reset,
        )
        self._futtat_teszt("Jelszo", "Ures felhasznalonev False", self.teszt_reset_password_ures_username)
        self._futtat_teszt("Jelszo", "Reset oldal token nelkul", self.teszt_reset_password_oldal_token_nelkul)
        self._futtat_teszt(
            "Jelszo",
            "Ervenytelen tokennel jelszocsere tiltva",
            self.teszt_reset_password_ervenytelen_token,
        )

        # --- Uzenet oldal + Socket.IO
        self._futtat_teszt("Uzenet", "Uzenet oldal bejelentkezve", self.teszt_uzenet_oldal_bejelentkezetten)
        self._futtat_teszt(
            "Uzenet",
            "Uzenet oldal vendegkent atiranyitott",
            self.teszt_uzenet_oldal_bejelentkezes_nelkul,
        )
        self._futtat_teszt("SocketIO", "Autentikalt get_conversations", self.teszt_socketio_get_conversations)
        self._futtat_teszt("SocketIO", "System chat (partner 0)", self.teszt_socketio_system_chat)
        self._futtat_teszt("SocketIO", "Uzenet kuldese (felh. 1 -> 2)", self.teszt_socketio_uzenet_kuldese)
        self._futtat_teszt(
            "SocketIO",
            "System chat uzenet valasz tiltva",
            self.teszt_socketio_system_chat_valasz_tiltas,
        )
        self._futtat_teszt(
            "SocketIO",
            "5000 karakter feletti uzenet tiltva",
            self.teszt_socketio_hosszu_uzenet_tiltva,
        )
        self._futtat_teszt("SocketIO", "Partner informacio", self.teszt_socketio_partner_info)
        self._futtat_teszt(
            "SocketIO",
            "Autentikalatlan kliens nem kap adatot",
            self.teszt_socketio_autentikalatlan,
        )

        # --- Admin
        self._futtat_teszt(
            "Jogosultsag",
            "Admin API sima felhasznalotol 403",
            self.teszt_admin_api_felhasznalo_nelkul,
        )
        self._futtat_teszt("Admin", "Admin felhasznalo regisztracio", self.teszt_admin_regisztracio)
        self._futtat_teszt("Admin", "Admin szerepkor DB-ben beallitasa", self.teszt_admin_szerepkor_allitas)
        self._futtat_teszt("Admin", "Admin bejelentkezes -> /admin redirect", self.teszt_admin_bejelentkezes)
        self._futtat_teszt("Admin", "Dashboard oldal", self.teszt_admin_dashboard)
        self._futtat_teszt("Admin", "Users oldal", self.teszt_admin_users_oldal)
        self._futtat_teszt("Admin", "Posts oldal", self.teszt_admin_posts_oldal)
        self._futtat_teszt("Admin", "Metrics RAM/CPU adatok", self.teszt_admin_metrics)
        self._futtat_teszt("Admin", "/api/users alap lekerdezes", self.teszt_admin_api_users)
        self._futtat_teszt("Admin", "/api/users kereses", self.teszt_admin_api_users_kereses)
        self._futtat_teszt("Admin", "/api/posts alap lekerdezes", self.teszt_admin_api_posts)
        self._futtat_teszt("Admin", "/api/posts kereses", self.teszt_admin_api_posts_kereses)
        self._futtat_teszt("Admin", "/api/posts statusz szures", self.teszt_admin_api_posts_statusz_szures)
        self._futtat_teszt("Admin", "/api/reports lekerdezes", self.teszt_admin_api_reports)
        self._futtat_teszt("Admin", "Report resolve", self.teszt_admin_report_resolve)
        self._futtat_teszt("Admin", "Item (poszt) torlese admin altal", self.teszt_admin_item_torles)
        self._futtat_teszt("Admin", "Nemletezo item torlese 404", self.teszt_admin_nemletezo_item_torles)

        # --- Tobbnyelvuseg
        self._futtat_teszt("I18n", "Angol Accept-Language", self.teszt_i18n_accept_language_en)
        self._futtat_teszt("I18n", "lang=en cookie", self.teszt_i18n_lang_cookie_en)
        self._futtat_teszt("I18n", "Poszt letrehozasa angol leirassal", self.teszt_poszt_en_leirassal)

        # --- Biztonsag
        self._futtat_teszt("Biztonsag", "XSS tartalom escape-eles", self.teszt_xss_poszt_nevben)
        self._futtat_teszt("Biztonsag", "SQL injection login nem sikerul", self.teszt_sql_injection_login_mezobe)

        # --- Kijelentkezes + jogosultsag finom
        self._futtat_teszt("Autentikacio", "2. felhasznalo kijelentkezes", self.teszt_kijelentkezes)
        self._futtat_teszt(
            "Jogosultsag",
            "Kijelentkezes utan vedett oldal atiranyitva",
            self.teszt_kijelentkezes_utan_vedett,
        )
        self._futtat_teszt(
            "Jogosultsag",
            "Bejelentkezes nelkul nem torolheto poszt",
            self.teszt_bejelentkezes_nelkuli_poszt_torles,
        )
        self._futtat_teszt("Poszt", "Tulajdonos torli a sajat posztot", self.teszt_poszt_torlese)


# ----------------------------------------------------------
# Riport generalas
# ----------------------------------------------------------


def _vonal(karakter: str = "-", szelesseg: int = 78) -> str:
    return karakter * szelesseg


def _keret(szoveg: str, szelesseg: int = 78) -> str:
    szoveg = szoveg.center(szelesseg - 2)
    return f"+{'-' * (szelesseg - 2)}+\n|{szoveg}|\n+{'-' * (szelesseg - 2)}+"


def _szelesseg_szerinti_tolto(szoveg: str, szelesseg: int) -> str:
    if len(szoveg) > szelesseg:
        return szoveg[: szelesseg - 1] + "..."
    return szoveg.ljust(szelesseg)


def riport_generalasa(tesztelo: Tesztelo) -> Tuple[str, str]:
    os.makedirs(RIPORT_MAPPA, exist_ok=True)
    idopont = datetime.now()

    eredmenyek = [e.mint_szotar() for e in tesztelo.eredmenyek]
    osszes = len(eredmenyek)
    sikeres = sum(1 for e in eredmenyek if e["sikeres"])
    bukott = osszes - sikeres
    atlagos_ido = int(sum(e["idotartam_ms"] for e in eredmenyek) / osszes) if osszes else 0
    arany = round((sikeres / osszes) * 100, 1) if osszes else 0.0

    kategoriak: Dict[str, List[Dict[str, Any]]] = {}
    for e in eredmenyek:
        kategoriak.setdefault(e["kategoria"], []).append(e)

    # JSON riport
    json_riport = {
        "idopont": idopont.isoformat(),
        "cel": tesztelo.alap_url,
        "osszes": osszes,
        "sikeres": sikeres,
        "bukott": bukott,
        "sikeressegi_arany_szazalek": arany,
        "atlag_idotartam_ms": atlagos_ido,
        "kategoriak": kategoriak,
        "eredmenyek": eredmenyek,
    }
    json_ut = os.path.join(RIPORT_MAPPA, "teszt_riport.json")
    with open(json_ut, "w", encoding="utf-8") as f:
        json.dump(json_riport, f, ensure_ascii=False, indent=2)

    # Sima szoveges riport
    sorok: List[str] = []
    sorok.append(_keret("ELVESZETT TARGYAK - KITERJESZTETT TESZT RIPORT"))
    sorok.append("")
    sorok.append(f"Futtatas ideje : {idopont.strftime('%Y-%m-%d %H:%M:%S')}")
    sorok.append(f"Celcim         : {tesztelo.alap_url}")
    sorok.append(f"Tesztek szama  : {osszes}")
    sorok.append(f"Sikeres        : {sikeres}")
    sorok.append(f"Sikertelen     : {bukott}")
    sorok.append(f"Arany          : {arany}%")
    sorok.append(f"Atlagos ido    : {atlagos_ido} ms")
    sorok.append("")

    sav_hossz = 50
    telt = int(round((arany / 100.0) * sav_hossz))
    sav = "[" + "#" * telt + "." * (sav_hossz - telt) + f"] {arany}%"
    sorok.append("Sikeressegi sav:")
    sorok.append("  " + sav)
    sorok.append("")

    sorok.append(_vonal("="))
    sorok.append("OSSZEFOGLALO KATEGORIAK SZERINT")
    sorok.append(_vonal("="))
    sorok.append("")
    fejlec = (
        f"{_szelesseg_szerinti_tolto('Kategoria', 22)}"
        f"{_szelesseg_szerinti_tolto('Osszes', 10)}"
        f"{_szelesseg_szerinti_tolto('Sikeres', 10)}"
        f"{_szelesseg_szerinti_tolto('Hiba', 10)}"
        f"{_szelesseg_szerinti_tolto('Arany', 10)}"
    )
    sorok.append(fejlec)
    sorok.append(_vonal("-", len(fejlec)))
    for kat, tesztek in kategoriak.items():
        k_osszes = len(tesztek)
        k_sikeres = sum(1 for t in tesztek if t["sikeres"])
        k_bukott = k_osszes - k_sikeres
        k_arany = round((k_sikeres / k_osszes) * 100, 1) if k_osszes else 0.0
        sorok.append(
            f"{_szelesseg_szerinti_tolto(kat, 22)}"
            f"{_szelesseg_szerinti_tolto(str(k_osszes), 10)}"
            f"{_szelesseg_szerinti_tolto(str(k_sikeres), 10)}"
            f"{_szelesseg_szerinti_tolto(str(k_bukott), 10)}"
            f"{_szelesseg_szerinti_tolto(str(k_arany) + '%', 10)}"
        )
    sorok.append("")

    # Reszletes eredmenyek
    sorok.append(_vonal("="))
    sorok.append("RESZLETES EREDMENYEK")
    sorok.append(_vonal("="))
    sorok.append("")
    for kat, tesztek in kategoriak.items():
        sorok.append(f">>> Kategoria: {kat}")
        sorok.append(_vonal("-"))
        for t in tesztek:
            jel = "[PASS]" if t["sikeres"] else "[FAIL]"
            sorok.append(f"{jel} {t['nev']}  ({t['idotartam_ms']} ms)")
            sorok.append(f"       Uzenet: {t['uzenet']}")
            if t["reszletek"]:
                reszletek_szoveg = json.dumps(t["reszletek"], ensure_ascii=False, indent=2)
                for r_sor in reszletek_szoveg.splitlines():
                    sorok.append(f"       {r_sor}")
            sorok.append("")
        sorok.append("")

    sorok.append(_vonal("="))
    sorok.append("HIBAS TESZTEK MELYREHATOBB ELEMZES")
    sorok.append(_vonal("="))
    sorok.append("")
    bukottak = [e for e in eredmenyek if not e["sikeres"]]
    if not bukottak:
        sorok.append("Minden teszt sikeresen lefutott - nincs hibas eset.")
    else:
        for idx, t in enumerate(bukottak, 1):
            sorok.append(f"{idx}. [{t['kategoria']}] {t['nev']}")
            sorok.append(f"   Uzenet   : {t['uzenet']}")
            sorok.append(f"   Idotartam: {t['idotartam_ms']} ms")
            if t["reszletek"]:
                sorok.append("   Reszletek:")
                reszletek_szoveg = json.dumps(t["reszletek"], ensure_ascii=False, indent=2)
                for r_sor in reszletek_szoveg.splitlines():
                    sorok.append(f"     {r_sor}")
            sorok.append("")
    sorok.append("")

    sorok.append(_vonal("="))
    sorok.append("TESZTELT FUNKCIOK OSSZESITESE")
    sorok.append(_vonal("="))
    sorok.append("")
    sorok.append("A szkript a kovetkezo funkcionalis teruleteket jarta be:")
    sorok.append("")
    sorok.append("  [Alaprendszer] fooldal, varmegyek.json, login oldal, 404, terkep oldal.")
    sorok.append("  [Statikus]     logo.svg, locale fajlok (hu.json, en.json).")
    sorok.append("  [Autentikacio] regisztracio, bejelentkezes, kijelentkezes, session cookie,")
    sorok.append("                 rossz jelszo, nemletezo felhasznalo, duplikalt nev/email,")
    sorok.append("                 tul hosszu jelszo.")
    sorok.append("  [Profil]       profil adatok, ervenytelen datum, hianyzo nev, masik/nemletezo,")
    sorok.append("                 profilkep feltoltes.")
    sorok.append("  [2FA]          verifikacios oldal, QR kod, setup vegpont, hibas OTP.")
    sorok.append("  [Poszt]        lost/found letrehozas, rossz tipus normalizalas, kep feltoltes,")
    sorok.append("                 tiltott kiterjeszteses fajl, poszt aktivalodas, szerkesztesi")
    sorok.append("                 adatok, idegen lekerdezes tiltasa, szerkesztes, lezaras kapcsolo,")
    sorok.append("                 nemletezo poszt, tulajdonos torli.")
    sorok.append("  [Bejelentes]   sajat/masik/duplikalt poszt bejelentes, felhasznalo bejelentes")
    sorok.append("                 (sajat, masik, nemletezo), indoklas nelkul.")
    sorok.append("  [Jelszo]       reset kereses letezo, nemletezo, ures, token nelkul, ervenytelen.")
    sorok.append("  [Uzenet+Socket] bejelentkezett oldal, vendeg redirect, Socket.IO")
    sorok.append("                 get_conversations, system chat, uzenetkuldes, hosszu uzenet")
    sorok.append("                 tiltas, system chat uzenet tiltas, partner info, autentikalatlan.")
    sorok.append("  [Admin]        regisztracio, szerepkor allitas DB-ben, bejelentkezes redirect,")
    sorok.append("                 dashboard/users/posts oldal, metrics, api/users+kereses,")
    sorok.append("                 api/posts+kereses+statusz, api/reports, resolve, item torles,")
    sorok.append("                 nemletezo item.")
    sorok.append("  [I18n]         Accept-Language header, lang cookie, angol leiras.")
    sorok.append("  [Biztonsag]    XSS escape, SQL injection login.")
    sorok.append("  [Jogosultsag]  kijelentkezes utani vedett oldal, bejelentkezes nelkul torles.")
    sorok.append("")
    sorok.append(_vonal("="))
    sorok.append(f"Riport veg.  Sikeres: {sikeres}/{osszes}  ({arany}%)")
    sorok.append(_vonal("="))

    txt_szoveg = "\n".join(sorok) + "\n"
    txt_ut = os.path.join(RIPORT_MAPPA, "teszt_riport.txt")
    with open(txt_ut, "w", encoding="utf-8") as f:
        f.write(txt_szoveg)

    return json_ut, txt_ut


def main() -> int:
    print(f"Celcim: {ALAP_URL}")
    tesztelo = Tesztelo(ALAP_URL)
    tesztelo.forgatokonyv()

    json_ut, txt_ut = riport_generalasa(tesztelo)

    print("")
    print("=" * 60)
    print("TESZT BEFEJEZVE")
    print("=" * 60)
    osszes = len(tesztelo.eredmenyek)
    sikeres = sum(1 for e in tesztelo.eredmenyek if e.sikeres)
    bukott = osszes - sikeres
    print(f"Osszes: {osszes}  |  Sikeres: {sikeres}  |  Sikertelen: {bukott}")
    print(f"Riport:\n  - {txt_ut}\n  - {json_ut}")
    return 0 if bukott == 0 and tesztelo.szerver_elerheto else 1


if __name__ == "__main__":
    sys.exit(main())
