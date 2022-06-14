from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import MySQLdb.cursors
import re
from datetime import datetime
import cherrypy

import pyttsx3

from flask_mail import  Mail, Message
from random import * 
import smtplib

from helpers import apology,  lookup, usd
# # import mail.py
import os
app = Flask(__name__)


# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Change this to your secret key (can be anything, it's for extra protection)
app.secret_key = 'your secret key'

# Enter your database connection details below
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'ae8df63b'
app.config['MYSQL_DB'] = 'onlinetrading'


# Intialize MySQL
mysql = MySQL(app)



@app.route("/")
def front():
    return render_template('front.html')

@app.route('/home/login', methods=['GET', 'POST'])
def login():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username" and "password" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s AND password = %s', (username, password,))
        # Fetch one record and return result
        account = cursor.fetchone()
        # If account exists in users table in out database
        if account:
            # Create session data, we can access this data in other routes
            session['loggedin'] = True
            session['id'] = account['id']
            session['username'] = account['username']

            return redirect(url_for('home'))
        else:
            # Account doesnt exist or username/password incorrect
            msg = 'Incorrect username/password!'
    return render_template('login.html', msg=msg)

# http://localhost:5000/python/logout - this will be the logout page
@app.route('/home/logout')
def logout():
    # Remove session data, this will log the user out
   session.pop('loggedin', None)
   session.pop('id', None)
   session.pop('username', None)
   # Redirect to login page
   return redirect(url_for('login'))


# http://localhost:5000/pythinlogin/register - this will be the registration page, we need to use both GET and POST requests
@app.route('/home/register', methods=['GET', 'POST'])
def register():
    # Output message if something goes wrong...
    msg = ''
    # Check if "username", "password" and "email" POST requests exist (user submitted form)
    if request.method == 'POST' and 'username' in request.form and 'password' in request.form and 'email' in request.form:
        # Create variables for easy access
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        # Check if account exists using MySQL
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        account = cursor.fetchone()
        # If account exists show error and validation checks
        if account:
            msg = 'Account already exists!'
        elif not re.match(r'[^@]+@[^@]+\.[^@]+', email):
            msg = 'Invalid email address!'
        elif not re.match(r'[A-Za-z0-9]+', username):
            msg = 'Username must contain only characters and numbers!'
        elif not username or not password or not email:
            msg = 'Please fill out the form!'
        else:
            # Account doesnt exists and the form data is valid, now insert new account into users table
            cursor.execute('INSERT INTO users(id,username, password, email) VALUES (null,%s, %s, %s)', (username, password, email,))
            mysql.connection.commit()
            flash('Thank you for registering')
            msg = 'You have successfully registered!'
            return render_template('login.html', msg=msg)
        return render_template('register.html', msg=msg)
    elif request.method == 'POST':
        # Form is empty... (no POST data)
        msg = 'Please fill out the form!'
        return render_template('register.html', msg=msg)
    else:
    # Show registration form with message (if any)
        return render_template('register.html', msg=msg)

# http://localhost:5000/pythinlogin/home - this will be the home page, only accessible for loggedin users
@app.route('/home')
def home():
    # Check if user is loggedin
    if 'loggedin' in session:
        
        # User is loggedin show them the home page
        return render_template('home.html', username=session['username'],name=session['username'])
    # User is not loggedin redirect to login page
    return redirect(url_for('login'))

@app.route('/home/profile')
def profile():
    if 'loggedin' in session:
        # We need all the account info for the user so we can display it on the profile page
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
        account = cursor.fetchone()
        # Show the profile page with account info
        return render_template('profile.html', account=account,name=session['username'])
    
        


@app.route('/home/profile/changepassword',methods=["POST","GET"])
def changepwd():
    if request.method == "POST":
       if 'loggedin' in session:
            msg = ''
            # We need all the account info for the user so we can display it on the profile page
            cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
            cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
            account = cursor.fetchone()
            oldpwd = request.form['oldpwd']
            newpwd = request.form['newpwd']
            renewpwd = request.form['renewpwd']

            if oldpwd != account['password']:
                msg = "Your old password is incorrect :("
            elif newpwd != renewpwd:
                msg = "Your passwords does not match ! Try again"
            else:
                cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
                cursor.execute("UPDATE users SET password= %s WHERE id= %s",(newpwd, session['id'],))
                mysql.connection.commit()
                # cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
                # account = cursor.fetchone()
                # for i in account:
                    # cursor.execute("UPDATE users SET password= %s WHERE id= %s",(newpwd, session['id'],))
                # cursor.execute('SELECT * FROM users WHERE id = %s', (session['id'],))
                # account = cursor.fetchone()
                # print(account['password'])
                print(newpwd)
                flash('Password changed :)')

                return redirect(url_for('profile'))
            return render_template("changepwd.html", msg = msg ,name=session['username'])
    else:
        return render_template("changepwd.html",name=session['username'])


@app.route("/home/buy",  methods=["GET",  "POST"])
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symb = request.form.get("symbol")
        print(symb)
        if not symb:
            return apology("must provide symbol",  400)

        # check for invalid symbol
        stock_lookup = lookup(symb)
        if not stock_lookup:
            return apology("must provide valid stock symbol",  400)

        # check share number
        share_num = (request.form.get("shares"))
        print(type(share_num))
        if "." in request.form.get("shares") or "/" in request.form.get("shares") or "," in request.form.get("shares"):
            return apology("Number of shares must be a positive integer!")

        if not share_num.isnumeric():
            return apology("Number of shares must be a positive integer")

        # error checking
        if not share_num:
            return apology("must provide the number of shares",  400)
        # if not isinstance(share_num,int):
        #     return apology("must provide a positive share number",  400)
        share_num = float(share_num)
        if share_num <= 0:
            return apology("must provide positive share number",  400)
        # print("hi")
        # share_num = float(share_num)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("select cash, username from users where id = %s",( session['id'],))
        # user_details = cursor.fetchall()
        user_details = cursor.fetchone()
        # for row in user_details:
        #     user_cash = row["cash"]
        user_cash = user_details["cash"]
        price = stock_lookup["price"]
        name = stock_lookup["name"]
        # print("ko")
        est_cost = price * share_num
        
        if est_cost > user_cash:
            return apology("Sorry! You don't have enough cash to purchase",  400)

        total = est_cost
        today = datetime.today()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        # print("lo")
        cursor.execute("insert into details values(%s, '%s', '%s', %s, %s, %s, '%s')",( symb,
                   int(share_num), price, name, today, session['id'], total,))
        cursor.execute("update users set cash = '%s' where id = %s", (float(user_cash)-float(est_cost), session['id'],))
        mysql.connection.commit()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("insert into history(symbol, shares, price, transacted_on, user_id) values(%s, '%s', '%s', %s, %s)",
                   (symb, int(share_num), price, today, session['id'],))
        mysql.connection.commit()
        # print("ho")
        return redirect("/home/dashboard")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html",name=session['username'])

    # return apology("TODO")




k="pp"


@app.route("/home/quote",  methods=["GET",  "POST"])

def quote():
    """Get stock quote."""
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        symb = request.form.get("symbol")
        k=symb
        stock_lookup = lookup(request.form.get("symbol"))
        print(stock_lookup)
        # if symbol does not exist
        if not stock_lookup:
            return apology("must provide valid symbol",  400)
        price =usd (stock_lookup["price"])
        uname = stock_lookup["name"]
        sym = stock_lookup["symbol"]
        # engine = pyttsx3.init()
        # engine.say(f" A share of {name} {sym} costs {price}")
        # engine.runAndWait()        
        return render_template("quoted.html", stock_lookup=stock_lookup, price=price,name=session['username'])
        # return redirect(url_for('quoted',price=price,uname=uname,sym=sym))

    else:
        return render_template("quote.html",name=session['username'])



@app.route("/home/quoted" , methods=["GET",  "POST"])
def quoted():    
    if request.method == "POST":
        symb = request.form.get("symb")      
        print(symb) 
        stock_lookup = lookup(symb)
        print(k)
        # if symbol does not exist
        if not stock_lookup:
            return apology("must provide valid symbol",  400)
        price =usd (stock_lookup["price"])
        uname = stock_lookup["name"]
        sym = stock_lookup["symbol"]

        voice_id = "HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0"
        engine = pyttsx3.init()
        # Use female voice
        engine.setProperty('voice', voice_id)

        
        engine.say(f" A share of {uname} {sym} costs {price}")
        engine.runAndWait()

        return render_template("quoted.html", stock_lookup=stock_lookup, price=price,name=session['username'])

    else:
        return render_template("quote.html")


@app.route("/home/history")
def history():
    """Show history of transactions"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("select * from history where user_id = %s", (session['id'],))
    history = cursor.fetchall()
    print(history)
    return render_template("history.html", history=history, usd=usd,name=session['username'])

    # return apology("TODO")

@app.route("/home/sell",  methods=["GET",  "POST"])
def sell():
    """Sell shares of stock"""
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)       
    cursor.execute("select * from details where user_id = %s",( session['id'],))
    detail = cursor.fetchall()

    l = set()
    for row in detail:
        l.add(row["symbol"])
    # print("111")
    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        symbol = request.form.get("symbol")
        shares = int(request.form.get("shares"))

        # error checking
        if not shares:
            return apology("must provide the number of shares",  400)
        if not symbol:
            return apology("must choose a symbol",  400)
        elif symbol not in l:
            return apology("Sorry! You do not have this symbol",  400)

        if shares <= 0:
            return apology("must provide positive share number",  400)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("select * from details where user_id = %s and symbol = %s",( session['id'], symbol,))
        detail = cursor.fetchall()

        # check for share required
        for row in detail:
            user_cur_share = row["shares"]
        if user_cur_share < shares:
            return apology("Sorry! You do not have required number of shares",  400)

        # view current price
        stock_lookup = lookup(symbol)
        price = stock_lookup["price"]

        # today's date
        today = datetime.today()

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        
        cursor.execute("select cash from users where id = %s", (session['id'],))
        rows = cursor.fetchall()

        for row in rows:
            cash = row["cash"]

        est_cost = price * float(shares)
        final_cash = float(cash) + float(est_cost)

        # change share status
        cur_share = user_cur_share - shares
        print(cur_share)
        if cur_share == 0:
            cursor.execute("delete from details where  symbol = %s and user_id = %s",( symbol, session['id'],))
        else:
            cursor.execute("update details SET shares = '%s' where  symbol =%s and user_id = %s", (cur_share, symbol, session['id'],))
            mysql.connection.commit()

        total = float(cur_share) * price
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("update details set total = '%s' where symbol = %s and user_id = %s", (total, symbol, session['id'],))
        mysql.connection.commit()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("update users set cash = '%s' where id = %s",( final_cash, session['id'],))
        mysql.connection.commit()
        print((-1) * shares)
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("insert into history(symbol, shares, price, transacted_on, user_id) values(%s, '%s', '%s', %s, %s)",
                   (symbol, (-1) * shares, price, today, session['id'],))
        mysql.connection.commit()
        # print("777")
        return redirect("/home/dashboard")
    else:
        return render_template("sell.html", list_symbols=l,name=session['username'])
    # return apology("TODO")


@app.route("/home/dashboard")
def dashboard():

    """Show portfolio of stocks"""
    # calc total price
    s = 0
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("select * from details where user_id = %s", (session['id'],))
    # evaluate for each symbol
    details = cursor.fetchall()
    for r in details:
        symb = r["symbol"]
        stock_lookup = lookup(symb)
        price = (stock_lookup["price"])
        total = price * r["shares"]
        s += total
        # print(total, price, r["shares"])
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
       
        cursor.execute("update details set current_price = '%s' where symbol = %s and user_id = %s", (price, symb, session['id'],))
        mysql.connection.commit()
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("update details set total = '%s' where symbol = %s and user_id = %s", (total, symb, session['id'],))
        mysql.connection.commit()

    # select current user cash
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("select cash from users where id = %s",(session['id'],))
    rows = cursor.fetchall()
    for row in rows:
        cash = row["cash"]
    s = float(s)+ float(cash)
    return render_template("dashboard.html", details=details,  usd=usd,  cash=cash, s=s,name=session['username'])



@app.route("/home/contact_us", methods=["GET",  "POST"])
def contact():
    if request.method == "POST":
        name= request.form.get('name')
        email = request.form.get('email')
        subject= request.form.get('subject')
        msg = request.form.get('message')
        msg1 = f"Hello {name}. Thanks for contacting us. This is your message :\n" + msg
        message = 'Subject: {}\n\n{}'.format(subject, msg1)
        
        server = smtplib.SMTP("smtp.gmail.com",587)
        server.starttls()
        server.login("19z339@psgtech.ac.in","POORNI123")
        # from who ,  to who, msg
        server.sendmail("19z339@psgtech.ac.in",email,message)
        msg = "Mail sent successfully"
        server.quit()
        return render_template('contact-us.html',name=session['username'],msg=msg)


    else:
        return render_template('contact-us.html',name=session['username'],msg='')
