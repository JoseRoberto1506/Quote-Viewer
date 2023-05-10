import os
import requests
import urllib.parse
from flask import redirect, session
from functools import wraps


# Incorporated from finance pset
def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


# Incorporated from finance pset
def quote_stock(symbol):
    """Quote stock"""

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={YOUR API KEY HERE}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "symbol": quote["symbol"],
            "price": float(quote["latestPrice"]),
            "change": float(quote["change"]),
            "changePercentage": float(quote["changePercent"]) * 100,
            "marketCap": float(quote["marketCap"])
        }
    except (KeyError, TypeError, ValueError):
        return None


def quote_crypto(symbol):
    """Quote crypto"""

    # Contact API
    try:
        url = f"https://api.coincap.io/v2/assets/?search={urllib.parse.quote_plus(symbol)}&limit=1"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        return None

    # Parse response
    try:
        quote = response.json()
        return {
            "symbol": quote["data"][0]["symbol"],
            "name": quote["data"][0]["name"],
            "price": float(quote["data"][0]["priceUsd"]),
            "marketCap": float(quote["data"][0]["marketCapUsd"]),
            "volume": float(quote["data"][0]["volumeUsd24Hr"]),
            "24h": float(quote["data"][0]["changePercent24Hr"]),
            "currentSupply": float(quote["data"][0]["supply"])
        }
    except (KeyError, TypeError, ValueError, IndexError):
        return None


# Incorporated from finance pset
def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def percentage(value):
    """Format values as %"""
    return f"{value:.2f}"


def supply(value):
    """Format supply value"""
    return f"{int(value):,}"

