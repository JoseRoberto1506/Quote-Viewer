import os
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helpers import login_required, quote_stock, quote_crypto, usd, percentage, supply

# Configure application
app = Flask(__name__)

# Custom filter. Incorporated from finance pset
app.jinja_env.filters["usd"] = usd
app.jinja_env.filters["percentage"] = percentage
app.jinja_env.filters["supply"] = supply

# Configure session to use filesystem (instead of signed cookies). Incorporated from finance pset
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///project.db")

# Make sure API key is set. Incorporated from finance pset
if not os.environ.get("API_KEY"):
    raise RuntimeError("API_KEY not set")


# Incorporated from finance pset
@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Incorporated from finance pset
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return flash("Must provide username")

        # Ensure password was submitted
        elif not request.form.get("password"):
            return flash("Must provide password")

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return flash("Invalid username and/or password")

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


# Incorporated from finance pset
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")

        # Checks if input fields are filled
        if not username:
            return flash("You must type a username")
        elif not password:
            return flash("A password is required")
        elif not confirmation:
            return flash("You must confirm your password")

        rows = db.execute("SELECT * FROM users WHERE username = ?", username)
        # Checks if username exists
        if len(rows) == 0:
            # Checks if passwords submitted matches
            if password == confirmation:
                hashed_password = generate_password_hash(password)
                db.execute("INSERT INTO users (username, hash) VALUES(?, ?)", username, hashed_password)

                # Remember which user has logged in
                session["user_id"] = db.execute("SELECT id FROM users WHERE username = ?", username)[0]["id"]

                # Redirect user to home page
                flash("Registration sucessful")
                return redirect("/")
            else:
                return flash("Password and password confirmation doesn't match")
        else:
            return flash("Username already in use")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("register.html")


# Incorporated from finance pset
@app.route("/")
@login_required
def index():
    """Show favorite stocks and cryptocurrencies"""

    # Query for user's favorite stocks and cryptos
    stocks = db.execute("SELECT * FROM favorites WHERE user_id = ? AND class = ?", session["user_id"], 'stock')
    cryptos = db.execute("SELECT * FROM favorites WHERE user_id = ? AND class = ?", session["user_id"], 'cryptocurrency')

    # Gets info of each stock from user's favorites list
    fav_stocks = []
    for i in range(len(stocks)):
        stock_info = quote_stock(stocks[i]["asset"])
        fav_stocks.append([stock_info["name"], stock_info["symbol"], stock_info["price"], stock_info["change"],
                           stock_info["changePercentage"], stock_info["marketCap"]])

    # Gets info of each cryptocurrency from user's favorites list
    fav_cryptos = []
    for i in range(len(cryptos)):
        crypto_info = quote_crypto(cryptos[i]["asset"])
        fav_cryptos.append([crypto_info["name"], crypto_info["symbol"], crypto_info["price"], crypto_info["24h"],
                           crypto_info["marketCap"], crypto_info["volume"], crypto_info["currentSupply"]])

    return render_template("index.html", fav_stocks=fav_stocks, fav_cryptos=fav_cryptos)


@app.route("/stocks", methods=["GET", "POST"])
@login_required
def stocks():
    """Get stock quote"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        stock = request.form.get("symbol")
        quoted_stock = quote_stock(stock)

        # Checks if the stock symbol is valid
        if (not stock) or (not quoted_stock):
            flash("Invalid symbol")
            return render_template("stocks.html")
        else:
            return render_template("stocks.html", stock=quoted_stock)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("stocks.html")


@app.route("/crypto", methods=["GET", "POST"])
@login_required
def cryptos():
    """Get cryptocurrency quote"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        cryptocurrency = request.form.get("symbol")
        quoted_crypto = quote_crypto(cryptocurrency)

        # Checks if cryptocurrency symbol is valid
        if (not cryptocurrency) or (not quoted_crypto):
            flash("Invalid symbol")
            return render_template("crypto.html")
        else:
            return render_template("crypto.html", cryptocurrency=quoted_crypto)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("crypto.html")


@app.route("/add-fav-stock", methods=["GET", "POST"])
@login_required
def add_stock():
    """Add stock to favorites list"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        stock = request.form.get("symbol")
        chosen_stock = quote_stock(stock)

        # Checks if stock symbol is valid
        if (not stock) or (not chosen_stock):
            flash("Invalid symbol")
            return render_template("add-fav-stock.html")

        # Checks if chosen stock is already in favorites list or not
        favorite_stock = db.execute("SELECT * FROM favorites WHERE user_id = ? AND asset = ?", session["user_id"], stock)
        if len(favorite_stock) == 0:
            # Adds stock into favorites list
            db.execute("INSERT INTO favorites (user_id, asset, class) VALUES (?, ?, ?)", session["user_id"], stock, 'stock')
        else:
            flash(f"{stock.upper()} is already in your favorites list")
            return render_template("add-fav-stock.html")

        # Redirects user to home page
        flash("Added to favorites list!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add-fav-stock.html")


@app.route("/add-fav-crypto", methods=["GET", "POST"])
@login_required
def add_crypto():
    """Add cryptocurrency to favorites list"""

    # user reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        cryptocurrency = request.form.get("symbol")
        chosen_cryptocurrency = quote_crypto(cryptocurrency)

        # Checks if cryptocurrency symbol is valid
        if (not cryptocurrency) or (not chosen_cryptocurrency):
            flash("Invalid symbol")
            return render_template("add-fav-crypto.html")

        # Checks if chosen cryptocurrency is already in favorites list or not
        favorite_cryptocurrency = db.execute("SELECT * FROM favorites WHERE user_id = ? AND asset = ?", session["user_id"], cryptocurrency)
        if len(favorite_cryptocurrency) == 0:
            # Adds cryptocurrency into favorites list
            db.execute("INSERT INTO favorites (user_id, asset, class) VALUES (?, ?, ?)", session["user_id"], cryptocurrency, 'cryptocurrency')
        else:
            flash(f"{cryptocurrency.upper()} is already in your favorites list")
            return render_template("add-fav-crypto.html")

        # Redirects user to home page
        flash("Added to favorites list!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("add-fav-crypto.html")
