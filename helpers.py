# Ross P. Coron || # GPS50 - a simple online GPS viewer || Created: March 2019

import requests
import urllib.parse
import datetime

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user"""

    def escape(s):
        """Escape special characters. https://github.com/jacebrowning/memegen#special-characters"""

        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """Decorate routes to require login. http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/"""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def time_calc(string):
    """Convert time to seconds"""

    # Format datetime
    time = datetime.datetime.strptime(string, "%Y-%m-%dT%H:%M:%SZ")

    # Extract hours, minutes, and seconds
    hour = int(time.hour)
    minute = int(time.minute)
    second = int(time.second)

    # Calculate seconds in time
    time = int(((hour*3600)+(minute*60)+(second)))

    return(time)


def date_format(datetime):
    """Format datetime string to date only"""

    for char in datetime:
        copy = datetime.replace('T', ' ')
        copy = copy.replace('Z', '')
        copy = copy[:10]

    return(copy)


def time_format(datetime):
    """Format datetime string to time only"""

    for char in datetime:
        copy = datetime.replace('T', ' ')
        copy = copy.replace('Z', '')
        copy = copy[11:]

    return(copy)
