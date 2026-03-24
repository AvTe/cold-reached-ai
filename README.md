# ColdReached AI

ColdReached AI is a Flask-based automation platform designed to streamline Local B2B outreach. The application autonomously scrapes highly targeted business leads from Google Maps, cross-references corporate websites to extract valid contact emails, utilizes AI to generate personalized initial pitches based on specific business data, and coordinates delivery through an integrated Gmail SMTP workflow.

## Features

- **Automated Directory Scraping:** Headless Playwright integration that supports extracting extensive business metadata such as organizational name, address, phone number, website link, and Google review ratings.
- **Multi-layered Email Discovery:** Employs concurrent BeautifulSoup4 parsing for on-site contact extraction (from Home/Contact pages) and automatically falls back to the Hunter.io Domain Search API if surface-level extraction fails.
- **AI-Driven Personalization:** Seamlessly interfaces with GPT-4 (via g4f) to draft succinct, hyper-personalized email subject lines and body copy that resonate directly with each unique local business profile.
- **Delivery Workflow & Rate Handling:** Integrates natively with Gmail SMTP. It strictly adheres to customizable daily sending limits, incorporates an intelligent Dry-Run diagnostic mode to prevent unintentional outbound emails during setup, and captures every interaction in the Outreach History logs.
- **Full-Stack Interface:** HTMX-powered UI structured entirely around Tailwind CSS, offering a clean, hardware-inspired, and professional dashboard containing zero page refreshes during operational tasks.

## Technical Architecture

- **Backend Logic:** Python 3.10+, Flask 3.0
- **Database Architecture:** SQLite coordinated via SQLAlchemy Object-Relational Mapping (ORM)
- **Scraping Engine:** Playwright (Chromium), BeautifulSoup4
- **Generative AI:** `gpt4free` (g4f)
- **Email Protocol:** Python `smtplib`

## Installation

### Prerequisites
- Python 3.10 or higher
- Git
- Google Chrome/Chromium installation (managed via Playwright)

### Setup Instructions

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/coldreached-ai.git
   cd coldreached-ai
   ```

2. **Initialize a Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows, use: venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   playwright install chromium
   ```

4. **Environment Configuration:**
   Create a `.env` file in the root directory mirroring the following variables:
   ```env
   SECRET_KEY=generate_a_secure_random_key_here
   HUNTER_API_KEY=your_hunter_io_api_key
   GMAIL_USER=your_email@gmail.com
   GMAIL_APP_PASSWORD=your_16_digit_app_password
   DAILY_EMAIL_LIMIT=30
   DRY_RUN=True
   EMAIL_SIGNATURE=Best regards,\nYour Name\nYour Company
   ```

5. **Initialize Database:**
   The SQLite database (`outreach.db`) and schema structure will automatically initialize on the first application launch.

## Usage

1. **Launch the Application:**
   ```bash
   python app.py
   ```
2. Navigate to `http://localhost:5000` via your web browser.
3. Access the **Dashboard/Scrape** view to input a target keyword and city or paste a raw Google Maps URL.
4. Evaluate leads under the **Businesses List** tab and initiate the **Find Emails** workflow.
5. Review AI-generated outreach copy inside the **Email Preview** view.
6. Observe status logs and delivery diagnostics within the **Send Log** section.

## Security Warning

This application requires SMTP App Passwords. Never commit your `.env` configuration file or `outreach.db` SQLite database to version control. Maintain stringent access control over your Hunter API tokens.

## License

This architecture is provided strictly under the MIT License framework.
