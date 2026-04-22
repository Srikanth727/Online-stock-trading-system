# Online Stock Trading System

A web-based stock trading simulation platform built with **Flask** and **SQLite**. Users can register, log in, look up real stock prices, buy and sell shares, and track their portfolio and transaction history — all with a starting virtual balance of $10,000.

---

## Features

- **User Authentication** — Register, log in, log out, and change password
- **Stock Quotes** — Look up live-ish stock prices fetched from a Kaggle dataset (5-year historical data)
- **Buy Stocks** — Purchase shares using your virtual cash balance
- **Sell Stocks** — Sell owned shares and receive cash back into your account
- **Portfolio Dashboard** — View all current holdings with live price updates and total value
- **Transaction History** — Full log of all buy/sell transactions
- **Contact Form** — Send a message via email using SMTP
- **Responsive UI** — Clean frontend with Bootstrap and custom CSS

---

## Tech Stack

| Layer      | Technology              |
|------------|-------------------------|
| Backend    | Python, Flask           |
| Database   | SQLite3                 |
| Frontend   | HTML, CSS, Bootstrap, Jinja2 |
| Data       | Kaggle Dataset (5yr stock prices) |
| Email      | SMTP via Gmail          |

---

## Project Structure

```
.
├── app.py              # Main Flask application with all routes
├── helpers.py          # Utility functions: stock lookup, USD formatting, apology renderer
├── requirements.txt    # Python dependencies
├── static/
│   ├── style.css       # Custom stylesheet
│   └── 1.jpg           # Background image
└── templates/
    ├── layout.html     # Base layout template
    ├── front.html      # Landing page
    ├── home.html       # Home page (after login)
    ├── login.html      # Login page
    ├── register.html   # Registration page
    ├── dashboard.html  # Portfolio dashboard
    ├── buy.html        # Buy stocks form
    ├── sell.html       # Sell stocks form
    ├── quote.html      # Stock quote lookup
    ├── quoted.html     # Stock quote result
    ├── history.html    # Transaction history
    ├── profile.html    # User profile
    ├── changepwd.html  # Change password
    ├── contact-us.html # Contact form
    └── apology.html    # Error display page
```

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Srikanth727/Online-stock-trading-system.git
   cd Online-stock-trading-system
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**

   Create a `.env` file or export variables in your shell:

   ```bash
   export SMTP_USER="your_email@gmail.com"
   export SMTP_PASS="your_app_password"
   ```

   > For Gmail, use an [App Password](https://support.google.com/accounts/answer/185833) rather than your main password.

4. **Run the application**

   ```bash
   # On Mac/Linux
   export FLASK_APP=app.py
   export FLASK_DEBUG=1
   flask run

   # On Windows
   set FLASK_APP=app.py
   set FLASK_DEBUG=1
   flask run
   ```

5. **Open in browser**

   Navigate to `http://127.0.0.1:5000`

---

## How It Works

- On first run, the app automatically creates a `trading.db` SQLite database with three tables:
  - `users` — stores user accounts with a default $10,000 virtual cash balance
  - `details` — tracks each user's current stock holdings
  - `history` — logs all buy/sell transactions

- Stock prices are sourced from the [Kaggle "All Stocks 5yr" dataset](https://www.kaggle.com/datasets/rohitjain454/all-stocks-5yr) loaded via `kagglehub`. The most recent available closing price is used for each symbol.

---

## Database Schema

```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    email TEXT NOT NULL,
    cash REAL DEFAULT 10000.00
);

CREATE TABLE details (
    symbol TEXT,
    shares INTEGER,
    current_price REAL,
    name TEXT,
    bought_on TEXT,
    user_id INTEGER,
    total REAL
);

CREATE TABLE history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT,
    shares INTEGER,
    price REAL,
    transacted_on TEXT,
    user_id INTEGER
);
```

---

## Notes

- Passwords are stored in plain text in this version — suitable for educational/demo purposes only. For production use, hash passwords with `werkzeug.security` or `bcrypt`.
- The contact form requires valid SMTP credentials set via environment variables.
- The stock dataset covers S&P 500 companies over a 5-year period; not all ticker symbols may be available.

---

## License

This project is open-source and available under the [MIT License](LICENSE).
