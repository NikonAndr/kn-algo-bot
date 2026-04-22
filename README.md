# 🤖 KN Discord Bot

Bot Discord stworzony do zarządzania kołem naukowym (~30 osób).  
Obsługuje newslettery, przypomnienia, weekly notes oraz automatyczne wysyłki maili.

---

## 🚀 Funkcjonalności

- 📧 System newsletterów email (SMTP – Gmail)
- 📬 Wysyłka masowych maili
- ⏰ Scheduler (automatyczne zadania, przypomnienia)
- 📝 Weekly Notes (raporty tygodniowe członków)
- 🔐 System uprawnień (role Discord)
- 🎛️ UI na Discordzie (buttons, modals, dropdowns)

---

## 🧱 Architektura

Projekt oparty o podejście warstwowe:

```
commands → services → database
```

- **commands/** – interakcje Discord
- **services/** – logika biznesowa
- **database/** – operacje na SQLite
- **utils/** – helpery i walidacje

---

## 📁 Struktura projektu

```
kn-discord-bot/

bot.py
config.py
.env
requirements.txt

commands/
services/
database/
utils/

data/
  database.db
```

---

## ⚙️ Wymagania

- Python **3.10+**
- Konto Discord Developer
- Konto Gmail (SMTP)

---

## 🛠️ Instalacja

### 1. Klonowanie repo

```
git clone https://github.com/twoje-repo/kn-discord-bot.git
cd kn-discord-bot
```

---

### 2. Virtual environment

```
python -m venv venv
source venv/bin/activate      # Linux / Mac
venv\Scripts\activate         # Windows
```

---

### 3. Instalacja zależności

```
pip install -r requirements.txt
```

---

## 🔑 Konfiguracja

Utwórz plik `.env` w root projektu:

```
DISCORD_TOKEN=your_token_here

EMAIL_ADDRESS=your_email@gmail.com
EMAIL_PASSWORD=your_app_password

BOT_ADMIN_ROLE_ID=123456789
BOT_NOTES_ROLE_ID=123456789
MEMBER_ROLE_ID=123456789

NEWSLETTER_CHANNEL_ID=123456789
```

---

### ⚠️ Gmail SMTP

Musisz użyć **App Password**, nie zwykłego hasła.

1. Włącz 2FA
2. Wygeneruj App Password
3. Wklej do `.env`

---

## 🗄️ Baza danych

SQLite jest używany lokalnie.

Przy pierwszym uruchomieniu:
- plik `data/database.db` zostanie utworzony automatycznie  
*(lub dodaj migracje jeśli masz setup script)*

---

## ▶️ Uruchomienie bota

```
python bot.py
```

Po uruchomieniu:
- bot pojawi się online na Discordzie
- scheduler zacznie działać automatycznie

---

## 📝 Weekly Notes – jak działa

1. Użytkownik tworzy notatkę (`!note`)
2. Status: `draft`
3. Moderator zatwierdza → `approved`
4. Scheduler sprawdza:
   - czy `send_at <= now`
5. Mail zostaje wysłany automatycznie
6. Status zmienia się na `sent`

---

## ⏰ Scheduler

- działa co 30 sekund (`tasks.loop`)
- obsługuje:
  - wiadomości Discord
  - wysyłkę maili (weekly notes)

---

## 🔐 Uprawnienia

Role wymagane:

- `BOT_ADMIN`
- `NOTES_MANAGER`
- `MEMBER`

Sprawdzane przez:
- decorators (`@bot_admin_only`)
- UI (`interaction_check`)

---

## 📬 Email system

- SMTP (Gmail)
- wysyłka pojedyncza i bulk
- rate limiting (sleep między mailami)

---

## 📌 Status projektu

✔️ Stabilny  
✔️ Modularna architektura  
✔️ Gotowy do rozwoju  

---

## 🚧 TODO / Roadmap

- [ ] HTML email templates
- [ ] Panel moderatora (review notes)
- [ ] Auto-refresh UI
- [ ] Reminder dla draft notes
- [ ] Multi-server support (guild config)
- [ ] Cron-like scheduler (np. weekly send)

---

## 🤝 Contributing

Na razie projekt rozwijany prywatnie, ale można forkować i testować.

---

## 📄 License

MIT (lub dowolna, którą wybierzesz)
