from flask import Flask, render_template, request, redirect, url_for, session, flash, g
import sqlite3
import re
from datetime import datetime
import smtplib

from helpers import apology, lookup, usd
import os

app = Flask(__name__)

app.config["TEMPLATES_AUTO_RELOAD"] = True
app.secret_key = 'your secret key'

DATABASE = 'trading.db'


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE)
    db.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT NOT NULL,
        password TEXT NOT NULL,
        email TEXT NOT NULL,
        cash REAL DEFAULT 10000.00
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS details (
        symbol TEXT,
        shares INTEGER,
        current_price REAL,
        name TEXT,
        bought_on TEXT,
        user_id INTEGER,
        total REAL
    )''')
    db.execute('''CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        symbol TEXT,
        shares INTEGER,
        price REAL,
        transacted_on TEXT,
        user_id INTEGER
    )''')
    db.commit()
    db.close()


init_db()


@app.route("/")
def front():
    return render_template('front.html')


@app.route('/home/login', methods=['GET', 'POST'])
def login():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        account = db.execute(
            'SELECT * FROM users WHERE username = ? AND password = ?', (username, password)
        ).fetchone()
        if account:
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']
            return redirect(url_for('home'))
        else:
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)


@app.route('/home/logout')
def logout():
    session.pop('loggedin', None)
    session.pop('id', None)
    session.pop('username', None)
    return redirect(url_for('login'))


@app.route('/home/register', methods=['GET', 'POST'])
def register():
    msg = ''
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        db = get_db()
        account = db.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            db.execute('INSERT INTO users(username, password, email) VALUES (?, ?, ?)', (username, password, email))
            db.commit()
            flash('Thank you for registering')
            msg = 'You have successfully registered!'
            return render_template('login.html', msg=msg)
        return render_template('register.html', msg=msg)
    elif request.method == 'POST':
        msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg)
    else:
        return render_template('register.html', msg=msg)


@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', username=session['username'], name=session['username'])
    return redirect(url_for('login'))


@app.route('/home/profile')
def profile():
    if 'loggedin' in session:
        db = get_db()
        account = db.execute('SELECT * FROM users WHERE id = ?', (session['id'],)).fetchone()
        return render_template('profile.html', account=account, name=session['username'])


@app.route('/home/profile/changepassword', methods=["POST", "GET"])
def changepwd():
    if request.method == "POST":
        if 'loggedin' in session:
            msg = ''
            db = get_db()
            account = db.execute('SELECT * FROM users WHERE id = ?', (session['id'],)).fetchone()
            oldpwd = request.form['oldpwd']
            newpwd = request.form['newpwd']
            renewpwd = request.form['renewpwd']
            if oldpwd != account['password']:
                msg = "Your old password is incorrect :("
            elif newpwd != renewpwd:
                msg = "Your passwords does not match ! Try again"
            else:
                db.execute("UPDATE users SET password = ? WHERE id = ?", (newpwd, session['id']))
                db.commit()
                flash('Password changed :)')
                return redirect(url_for('profile'))
            return render_template("changepwd.html", msg=msg, name=session['username'])
    else:
        return render_template("changepwd.html", name=session['username'])


@app.route("/home/buy", methods=["GET", "POST"])
def buy():
    """Buy shares of stock"""
    if request.method == "POST":
        symb = request.form.get("symbol")
        if not symb:
            return apology("must provide symbol", 400)

        stock_lookup = lookup(symb)
        if not stock_lookup:
            return apology("must provide valid stock symbol", 400)

        shares_input = request.form.get("shares")
        if "." in shares_input or "/" in shares_input or "," in shares_input:
            return apology("Number of shares must be a positive integer!")
        if not shares_input.isnumeric():
            return apology("Number of shares must be a positive integer")

        share_num = float(shares_input)
        if share_num <= 0:
            return apology("must provide positive share number", 400)

        db = get_db()
        user_details = db.execute("SELECT cash, username FROM users WHERE id = ?", (session['id'],)).fetchone()
        user_cash = user_details["cash"]
        price = stock_lookup["price"]
        name = stock_lookup["name"]
        est_cost = price * share_num

        if est_cost > user_cash:
            return apology("Sorry! You don't have enough cash to purchase", 400)

        total = est_cost
        today = datetime.today().isoformat()

        db.execute(
            "INSERT INTO details VALUES(?, ?, ?, ?, ?, ?, ?)",
            (symb, int(share_num), price, name, today, session['id'], total)
        )
        db.execute("UPDATE users SET cash = ? WHERE id = ?", (float(user_cash) - float(est_cost), session['id']))
        db.execute(
            "INSERT INTO history(symbol, shares, price, transacted_on, user_id) VALUES(?, ?, ?, ?, ?)",
            (symb, int(share_num), price, today, session['id'])
        )
        db.commit()
        return redirect("/home/dashboard")
    else:
        return render_template("buy.html", name=session['username'])


@app.route("/home/quote", methods=["GET", "POST"])
def quote():
    """Get stock quote."""
    if request.method == "POST":
        stock_lookup = lookup(request.form.get("symbol"))
        if not stock_lookup:
            return apology("must provide valid symbol", 400)
        price = usd(stock_lookup["price"])
        return render_template("quoted.html", stock_lookup=stock_lookup, price=price, name=session['username'])
    else:
        return render_template("quote.html", name=session['username'])


@app.route("/home/quoted", methods=["GET", "POST"])
def quoted():
    if request.method == "POST":
        symb = request.form.get("symb")
        stock_lookup = lookup(symb)
        if not stock_lookup:
            return apology("must provide valid symbol", 400)
        price = usd(stock_lookup["price"])
        return render_template("quoted.html", stock_lookup=stock_lookup, price=price, name=session['username'])
    else:
        return render_template("quote.html", name=session['username'])


@app.route("/home/history")
def history():
    """Show history of transactions"""
    db = get_db()
    history = db.execute("SELECT * FROM history WHERE user_id = ?", (session['id'],)).fetchall()
    return render_template("history.html", history=history, usd=usd, name=session['username'])


@app.route("/home/sell", methods=["GET", "POST"])
def sell():
    """Sell shares of stock"""
    db = get_db()
    detail = db.execute("SELECT * FROM details WHERE user_id = ?", (session['id'],)).fetchall()
    l = set(row["symbol"] for row in detail)

    if request.method == "POST":
        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        if not shares:
            return apology("must provide the number of shares", 400)
        if not symbol:
            return apology("must choose a symbol", 400)
        elif symbol not in l:
            return apology("Sorry! You do not have this symbol", 400)
        if shares <= 0:
            return apology("must provide positive share number", 400)

        detail = db.execute(
            "SELECT * FROM details WHERE user_id = ? AND symbol = ?", (session['id'], symbol)
        ).fetchall()

        for row in detail:
            user_cur_share = row["shares"]

        if user_cur_share < shares:
            return apology("Sorry! You do not have required number of shares", 400)

        stock_lookup = lookup(symbol)
        price = stock_lookup["price"]
        today = datetime.today().isoformat()

        cash = db.execute("SELECT cash FROM users WHERE id = ?", (session['id'],)).fetchone()["cash"]
        est_cost = price * float(shares)
        final_cash = float(cash) + float(est_cost)

        cur_share = user_cur_share - shares
        if cur_share == 0:
            db.execute("DELETE FROM details WHERE symbol = ? AND user_id = ?", (symbol, session['id']))
        else:
            db.execute(
                "UPDATE details SET shares = ? WHERE symbol = ? AND user_id = ?",
                (cur_share, symbol, session['id'])
            )

        total = float(cur_share) * price
        db.execute("UPDATE details SET total = ? WHERE symbol = ? AND user_id = ?", (total, symbol, session['id']))
        db.execute("UPDATE users SET cash = ? WHERE id = ?", (final_cash, session['id']))
        db.execute(
            "INSERT INTO history(symbol, shares, price, transacted_on, user_id) VALUES(?, ?, ?, ?, ?)",
            (symbol, (-1) * shares, price, today, session['id'])
        )
        db.commit()
        return redirect("/home/dashboard")
    else:
        return render_template("sell.html", list_symbols=l, name=session['username'])


@app.route("/home/dashboard")
def dashboard():
    """Show portfolio of stocks"""
    s = 0
    db = get_db()
    details = db.execute("SELECT * FROM details WHERE user_id = ?", (session['id'],)).fetchall()

    for r in details:
        symb = r["symbol"]
        stock_lookup = lookup(symb)
        price = stock_lookup["price"]
        total = price * r["shares"]
        s += total
        db.execute(
            "UPDATE details SET current_price = ? WHERE symbol = ? AND user_id = ?",
            (price, symb, session['id'])
        )
        db.execute(
            "UPDATE details SET total = ? WHERE symbol = ? AND user_id = ?",
            (total, symb, session['id'])
        )
    db.commit()

    # Re-fetch after updates
    details = db.execute("SELECT * FROM details WHERE user_id = ?", (session['id'],)).fetchall()
    cash = db.execute("SELECT cash FROM users WHERE id = ?", (session['id'],)).fetchone()["cash"]
    s = float(s) + float(cash)
    return render_template("dashboard.html", details=details, usd=usd, cash=cash, s=s, name=session['username'])


@app.route("/home/contact_us", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        name = request.form.get('name')
        email = request.form.get('email')
        subject = request.form.get('subject')
        msg = request.form.get('message')
        msg1 = f"Hello {name}. Thanks for contacting us. This is your message :\n" + msg
        message = 'Subject: {}\n\n{}'.format(subject, msg1)

        smtp_user = os.environ.get("SMTP_USER", "")
        smtp_pass = os.environ.get("SMTP_PASS", "")
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.sendmail(smtp_user, email, message)
        msg = "Mail sent successfully"
        server.quit()
        return render_template('contact-us.html', name=session['username'], msg=msg)
    else:
        return render_template('contact-us.html', name=session['username'], msg='')
