# 🏦 Tracksy Backend

FastAPI + MySQL backend for **Tracksy** — your smart expense & budget manager.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 JWT Auth | Signup / Login with bcrypt password hashing |
| 💸 Expenses | Full CRUD with category tagging |
| 🎯 Budgets | Monthly + per-category budgets |
| ⚠️ Smart Email Alerts | Warning at 80% spent, alert when exceeded (via Gmail SMTP) |
| 📍 Food Spots | Nearby affordable restaurants via OpenStreetMap (no API key!) |
| 🔔 Notifications | In-app log of all budget alerts |
| ⏰ Scheduler | Hourly background job to catch missed budget breaches |

---

## 📁 Project Structure

```
tracksy/
├── main.py                  ← FastAPI app + scheduler
├── requirements.txt
├── .env.example             ← Copy to .env and fill in values
│
├── core/
│   ├── config.py            ← Settings from .env
│   ├── database.py          ← SQLAlchemy engine + session
│   └── security.py          ← JWT + password helpers
│
├── models/
│   └── user.py              ← All SQLAlchemy ORM models
│
├── routers/
│   ├── auth.py              ← POST /auth/signup, /auth/login
│   ├── expenses.py          ← CRUD + monthly summary
│   ├── budgets.py           ← Monthly + category budgets
│   ├── categories.py        ← CRUD categories
│   ├── food_spots.py        ← GET /food-spots/nearby
│   ├── notifications.py     ← List + delete notifications
│   └── users.py             ← Profile + theme settings
│
└── services/
    ├── email_service.py     ← Gmail SMTP email sender + HTML templates
    ├── budget_service.py    ← Budget check logic + deduplication
    └── food_service.py      ← OpenStreetMap Overpass API client
```

---

## 🚀 Setup

### 1. Clone & install dependencies

```bash
cd tracksy
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pip install pydantic-settings   # needed for config
```

### 2. Create your MySQL database

```sql
CREATE DATABASE tracksy;
-- then run your full schema SQL
```

### 3. Configure environment variables

```bash
cp .env.example .env
# Edit .env with your values
```

**Key values to fill in:**

```env
DB_PASSWORD=your_mysql_password
SECRET_KEY=any-long-random-string
SMTP_USER=yourgmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password   # see below
```

### 4. Get a Gmail App Password

> Regular Gmail passwords won't work — you need an App Password.

1. Go to [myaccount.google.com](https://myaccount.google.com)
2. **Security** → enable **2-Step Verification**
3. **Security** → **App passwords** → create one for "Mail"
4. Copy the 16-character password into `.env` as `SMTP_PASSWORD`

### 5. Run the server

```bash
uvicorn main:app --reload
```

**API docs:** http://localhost:8000/docs  
**Health check:** http://localhost:8000/

---

## 📡 API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register + sends welcome email |
| POST | `/auth/login` | Login → returns JWT token |

**Signup body:**
```json
{ "username": "Arjun", "email": "arjun@example.com", "password": "secret123" }
```

**Login** uses form data (`OAuth2PasswordRequestForm`):
```
email=arjun@example.com&password=secret123
```

All protected routes need the header:
```
Authorization: Bearer <token>
```

---

### Expenses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses/` | Add expense → triggers budget check |
| GET | `/expenses/` | List (filter by month/year/category) |
| GET | `/expenses/summary?month=6&year=2025` | Monthly total + by-category breakdown |
| GET | `/expenses/{id}` | Single expense |
| PUT | `/expenses/{id}` | Update |
| DELETE | `/expenses/{id}` | Delete |

**Add expense body:**
```json
{
  "category_id": 2,
  "description": "Lunch at canteen",
  "amount": 120.00,
  "expense_date": "2025-06-15"
}
```

---

### Budgets

| Method | Endpoint | Description |
|---|---|---|
| POST | `/budgets/monthly` | Set/update monthly budget |
| GET | `/budgets/monthly?month=6&year=2025` | Budget vs spent + remaining |
| POST | `/budgets/category` | Set category budget |
| GET | `/budgets/category?month=6&year=2025` | All category budgets with spent |

---

### Food Spots 📍

**Frontend JS to get location + call API:**
```javascript
navigator.geolocation.getCurrentPosition(async (pos) => {
  const { latitude, longitude } = pos.coords;
  const res = await fetch(
    `/food-spots/nearby?lat=${latitude}&lon=${longitude}&radius=1500`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const data = await res.json();
  console.log(data.spots); // Array of nearby food places
});
```

**Response:**
```json
{
  "count": 12,
  "search_center": { "lat": 28.6139, "lon": 77.2090 },
  "radius_m": 1500,
  "spots": [
    {
      "name": "Raja Dhaba",
      "amenity": "Restaurant",
      "cuisine": "Indian",
      "price_level": "Budget",
      "opening_hours": "Mo-Su 08:00-22:00",
      "lat": 28.612,
      "lon": 77.208,
      "maps_link": "https://www.openstreetmap.org/?mlat=28.612&mlon=77.208&zoom=18"
    }
  ]
}
```

---

## 📧 Budget Alert Emails

Two emails are sent automatically — both go to the user's registered email:

### ⚠️ Warning Email (before exceeding)
- Fires when spending reaches **80%** of the monthly budget
- Sent only **once per month** (no spam)
- Configure threshold in `.env`: `BUDGET_WARNING_PERCENT=80`

### 🚨 Exceeded Email (after exceeding)
- Fires when total spending **goes over** the monthly budget
- Sent only **once per month**

**When are checks triggered?**
- ✅ Every time an expense is **added or updated** (real-time)
- ✅ Every **hour** via background scheduler (catches edge cases)

---

## 🔧 Customization

**Change warning threshold to 70%:**
```env
BUDGET_WARNING_PERCENT=70
```

**Change search radius default:**  
Pass `?radius=2000` in the API call (max 10,000 m)

**Change token expiry:**
```env
ACCESS_TOKEN_EXPIRE_MINUTES=1440   # 1 day
```

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `Authentication failed` on email | Use Gmail App Password, not your real password |
| `SMTP connection error` | Make sure 2FA is enabled on your Google account |
| `Can't connect to MySQL` | Check `DB_HOST`, `DB_PORT`, `DB_PASSWORD` in `.env` |
| Food spots return empty | Rare rural areas may have few OSM entries; increase `radius` |
| Budget email sent twice | Shouldn't happen — deduplication uses `Notifications` table |
