# ColdReached AI - Project Documentation v1.0

## 01 — Overview & Core Objective
A Flask-based web application that scrapes local business contacts from Google Maps, finds their emails, writes AI-personalized pitches, and sends them—all from one dashboard.

### Problem Solved
Automates the manual, time-consuming pipeline of finding leads, hunting emails, writing pitches, and tracking replies.

### Targeted Features
- **Targeted Scraping**: Search by keyword + city or paste a Google Maps URL.
- **Email Discovery**: Regex scraping from websites with Hunter.io fallback.
- **AI Personalization**: Unique emails via `gpt4free` (not template blasts).
- **Tracking Dashboard**: Manage scrapes, emails, and status in a clean UI.

---

## 02 — Data Flow
The entire pipeline runs inside Flask, triggered via the browser:
`Maps URL / Keyword` → `Playwright Scraper` → `Email Finder` → `AI Writer` → `Gmail SMTP` → `SQLite Log`

---

## 03 — Build Phases
1. **Phase 1: Project Scaffold + Database**: Flask app, SQLite schema (SQLAlchemy), and config file.
2. **Phase 2: Google Maps Scraper**: Playwright (headless) extraction of name, address, phone, website, and rating.
3. **Phase 4: Email Finder**: Homestead/Contact page scraping (BS4/Regex) + Hunter.io API fallback.
4. **Phase 4: AI Email Writer**: `gpt4free` personalization (Subject + Body) based on business data.
5. **Phase 5: Mailer + Rate Limiter**: Gmail SMTP (App Password) with 30/day cap and dry-run mode.
6. **Phase 6: Flask UI Dashboard**: 4 screens (Scrape, List, Preview, Logs) using Jinja2 + TailwindCSS + HTMX.

---

## 04 — File Structure
```text
cold-outreach-tool/
├── app.py              # Flask routes + entry point
├── config.py           # API keys, SMTP creds, limits
├── models.py           # SQLAlchemy DB models
├── requirements.txt
├── modules/
│   ├── scraper.py      # Playwright Google Maps scraper
│   ├── email_finder.py # Website email extraction
│   ├── ai_writer.py    # GPT4Free personalised emails
│   └── mailer.py       # Gmail SMTP + rate limiter
├── templates/
│   ├── base.html       # Layout with nav
│   ├── index.html      # Dashboard / scrape trigger
│   ├── businesses.html # Scraped results table
│   ├── preview.html    # Email preview + approve
│   └── logs.html       # Sent email log
├── static/
│   └── style.css
├── outreach.db         # Auto-created SQLite file
└── .env                # Sensitive credentials
```

---

## 05 — Database Schema
| Table | Key Columns | Purpose |
| :--- | :--- | :--- |
| **businesses** | id, name, address, phone, website, rating, scraped_at | Raw data from Google Maps |
| **emails** | id, business_id, email, source, email_body, subject, status, generated_at | Found emails + AI content |
| **send_log** | id, email_id, sent_at, status, error_msg | History of every send attempt |

---

## 06 — Tech Stack
- **Web**: Flask, Jinja2, TailwindCSS CDN, HTMX.
- **Scraping**: Playwright, BeautifulSoup4.
- **Automation**: `requests`, `re` (regex), `asyncio`.
- **AI**: `gpt4free` (g4f).
- **Database**: SQLite, SQLAlchemy.
- **Mailing**: `smtplib` (Gmail SMTP).

---

## 07 — Limits & Notes
- **Gmail**: Cap at 30 emails/day (safety margin). Warm up gradually.
- **Scraping**: Use delays to avoid blocks. Google Places API is a fallback.
- **AI Stability**: `gpt4free` can be unstable; keep Jinja2 template fallbacks.
- **Setup**: `playwright install chromium` required.
