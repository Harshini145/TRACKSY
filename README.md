# 💰 Tracksy

A full-stack **expense & budget management app** — FastAPI backend + Vanilla JS frontend, powered by MySQL.

---

## ✨ Features

| Feature | Details |
|---|---|
| 🔐 JWT Auth | Signup / Login with bcrypt password hashing |
| 💸 Expenses | Full CRUD with category tagging, date filtering & monthly summary |
| 🎯 Budgets | Monthly budget + per-category budgets with live % tracking |
| ⚠️ Smart Email Alerts | Warning at 80% spent, alert when exceeded — sent once per month via Gmail SMTP |
| 📍 Nearby Food Spots | Affordable restaurants via OpenStreetMap Overpass API — no API key needed |
| 🔔 In-App Notifications | Persistent log of all budget alerts (warning & exceeded) |
| ⏰ Background Scheduler | Hourly APScheduler job catches missed budget breaches |
| 🎨 Theme Support | Light/dark mode preference saved per user |
| 📊 Charts & Dashboard | Chart.js powered spending breakdown by category |
| 🤖 Groq AI Budget Assistant | Powered by Groq + Ollama Version 3 (Llama 3) for ultra-fast AI responses, budget insights, expense analysis, and smart spending recommendations |
| 🛍️ Budget Shopping AI | Compares product prices across Flipkart, Amazon, Myntra, and Nykaa to help users find the best deals within their budget |


---

## 📁 Project Structure

```
tracksy/
├── main.py                  ← FastAPI app entry point + APScheduler setup
├── requirements.txt
├── database.sql             ← Full MySQL schema (run once to set up DB)
├── index.html               ← Frontend SPA (sidebar + all pages)
│
├── css/
│   └── style.css            ← Responsive styling, light/dark themes
│
├── js/
│   └── script.js            ← All frontend logic (auth, CRUD, charts, food spots)
│
├── img/
│   ├── ai_bot.png           ← AI bot avatar for budget chat UI
│   └── bg.png               ← App background
│
├── core/
│   ├── config.py            ← Pydantic settings loaded from .env
│   ├── database.py          ← SQLAlchemy engine + session factory
│   └── security.py          ← JWT creation/verification + bcrypt helpers
│
├── models/
│   └── user.py              ← All SQLAlchemy ORM models (User, Expense, Category,
│                               MonthlyBudget, CategoryBudget, UserSetting, Notification)
│
├── routers/
│   ├── auth.py              ← POST /auth/signup, /auth/login
│   ├── expenses.py          ← Full CRUD + monthly summary
│   ├── budgets.py           ← Monthly + category budget upsert & retrieval
│   ├── categories.py        ← CRUD for expense categories
│   ├── food_spots.py        ← GET /food-spots/nearby
│   ├── notifications.py     ← List + delete in-app notifications
│   └── users.py             ← Profile info + theme settings
│
└── services/
    ├── email_service.py     ← Gmail SMTP sender with styled HTML email templates
    ├── budget_service.py    ← Budget check logic + one-email-per-month deduplication
    └── food_service.py      ← OpenStreetMap Overpass API client (multi-mirror fallback)
```

---

## 🚀 Setup

### 1. Clone & install dependencies

```bash
git clone https://github.com/Harshini145/TRACKSY.git
cd TRACKSY
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Create your MySQL database

```sql
CREATE DATABASE tracksy;
USE tracksy;
-- Then run the full schema:
SOURCE database.sql;
```

### 3. Configure environment variables

Create a `.env` file in the project root:

```env
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=tracksy

# JWT
SECRET_KEY=any-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=10080   # 7 days

# Gmail SMTP
SMTP_USER=yourgmail@gmail.com
SMTP_PASSWORD=your-16-char-app-password

# Budget alert threshold (default 80%)
BUDGET_WARNING_PERCENT=80
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
**Frontend:** http://localhost:8000/app/index.html  
**Health check:** http://localhost:8000/

---

## 📡 API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| POST | `/auth/signup` | Register → seeds default categories + sends welcome email |
| POST | `/auth/login` | Login → returns JWT token |

**Signup body:**
```json
{ "username": "Arjun", "email": "arjun@example.com", "password": "secret123" }
```

**Login body:**
```json
{ "username": "arjun@example.com", "password": "secret123" }
```

All protected routes require:
```
Authorization: Bearer <token>
```

---

### Expenses

| Method | Endpoint | Description |
|---|---|---|
| POST | `/expenses/` | Add expense → triggers real-time budget check |
| GET | `/expenses/` | List all (filter by `month`, `year`, `category_id`) |
| GET | `/expenses/summary?month=6&year=2025` | Monthly total + per-category breakdown |
| GET | `/expenses/{id}` | Get single expense |
| PUT | `/expenses/{id}` | Update expense → re-runs budget check |
| DELETE | `/expenses/{id}` | Delete expense |

**Add expense body:**
```json
{
  "category_id": 2,
  "description": "Lunch at canteen",
  "amount": 120.00,
  "expense_date": "2025-06-15"
}
```

**Summary response:**
```json
{
  "month": 6,
  "year": 2025,
  "total_spent": 4500.00,
  "by_category": [
    { "category": "Food", "spent": 1800.00 },
    { "category": "Transport", "spent": 700.00 }
  ]
}
```

---

### Budgets

| Method | Endpoint | Description |
|---|---|---|
| POST | `/budgets/monthly` | Set or update monthly budget |
| GET | `/budgets/monthly?month=6&year=2025` | Budget vs spent + remaining + % used |
| POST | `/budgets/category` | Set or update a category budget |
| GET | `/budgets/category?month=6&year=2025` | All category budgets with spent & remaining |

**Monthly budget response:**
```json
{
  "month": 6,
  "year": 2025,
  "budget": 10000.00,
  "spent": 4500.00,
  "remaining": 5500.00,
  "percent_used": 45.0
}
```

---

### Categories

| Method | Endpoint | Description |
|---|---|---|
| POST | `/categories/` | Create a new category |
| GET | `/categories/` | List all user categories |
| PUT | `/categories/{id}` | Rename a category |
| DELETE | `/categories/{id}` | Delete a category |

> On signup, 8 default categories are seeded automatically: Food, Transport, Shopping, Health, Rent, Utilities, Education, Entertainment.

---

### Notifications

| Method | Endpoint | Description |
|---|---|---|
| GET | `/notifications/` | List last 50 alerts (newest first) |
| DELETE | `/notifications/{id}` | Delete a notification |

---

### Users

| Method | Endpoint | Description |
|---|---|---|
| GET | `/users/me` | Get current user profile |
| GET | `/users/settings` | Get theme preference |
| PUT | `/users/settings` | Update theme (`light` / `dark`) |

---

### Food Spots 📍

```
GET /food-spots/nearby?lat=28.6139&lon=77.2090&radius=1500&limit=10
```

No API key required — powered by OpenStreetMap.

**Frontend usage:**
```javascript
navigator.geolocation.getCurrentPosition(async (pos) => {
  const { latitude, longitude } = pos.coords;
  const res = await fetch(
    `/food-spots/nearby?lat=${latitude}&lon=${longitude}&radius=1500`,
    { headers: { Authorization: `Bearer ${token}` } }
  );
  const data = await res.json();
  console.log(data.spots);
});
```

**Response:**
```json
{
  "count": 5,
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
      "maps_link": "https://www.google.com/maps/search/?api=1&query=28.612,77.208"
    }
  ]
}
```

> Results are sorted budget-first. Falls back to sample spots if all Overpass mirrors are unreachable.

---

## 📧 Email Alerts

Two HTML emails are sent automatically to the user's registered address:

### ⚠️ Warning Email
- Fires when spending hits **80%** of the monthly budget
- Sent only **once per month** — no repeated emails
- Threshold configurable: `BUDGET_WARNING_PERCENT=70` in `.env`

### 🚨 Exceeded Email
- Fires when total spending **exceeds** the monthly budget
- Sent only **once per month**
- Shows exact overshoot amount

**When are checks triggered?**
- ✅ Every time an expense is **added or updated** (real-time)
- ✅ Every **hour** via background APScheduler job (catch-all for edge cases)

Deduplication works via the `Notifications` table — a tagged entry per `[year-month:type]` ensures emails are never sent twice for the same threshold in the same month.

---

## 🗃️ Database Schema

| Table | Purpose |
|---|---|
| `Users` | Auth — username, email, hashed password |
| `Categories` | Per-user expense categories |
| `Expenses` | Individual expense records |
| `Monthly_Budgets` | One budget per user per month/year |
| `Category_Budgets` | Per-category budgets per month/year |
| `User_Settings` | Theme preference per user |
| `Notifications` | In-app + email deduplication log |

---

## 🔧 Customization

**Change warning threshold to 70%:**
```env
BUDGET_WARNING_PERCENT=70
```

**Change food spot search radius:**
```
GET /food-spots/nearby?lat=...&lon=...&radius=3000
```
Max radius: 10,000 m

**Change JWT token expiry:**
```env
ACCESS_TOKEN_EXPIRE_MINUTES=1440   # 1 day
```

---

## 🛠 Troubleshooting

| Problem | Fix |
|---|---|
| `Authentication failed` on email | Use a Gmail App Password, not your account password |
| `SMTP connection error` | Ensure 2-Step Verification is enabled on your Google account |
| `Can't connect to MySQL` | Check `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD` in `.env` |
| Food spots return empty | Increase `radius` — rural/sparse areas may have limited OSM entries |
| Budget email sent twice | Shouldn't happen — check `Notifications` table for duplicate `[year-month:type]` tags |
| Frontend not loading | Make sure the server is running and visit `/app/index.html`, not `/` |
| `ModuleNotFoundError` for pydantic-settings | Run `pip install pydantic-settings` separately |

