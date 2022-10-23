# Ross P. Coron || # GPS50 - a simple online GPS viewer || Created: March 2019

import os

from cs50 import SQL
from flask import Flask, flash, jsonify, redirect, render_template, request, session, abort
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError    # Hash passwords
from werkzeug.security import check_password_hash, generate_password_hash
import json

from haversine import haversine    # Calculate distance on a sphere
from xml.dom import minidom    # Access data in XML file
from copy import copy    # Hack for working with Python lists
import datetime    # Manipulate datatime objects

from helpers import apology, login_required, time_calc, time_format, date_format    # Defined in 'helpers.py'

# Configure CS50 Library to use SQLite database 'gps50.db'
db = SQL("sqlite:///gps50.db")

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)


@app.route("/")
@login_required
def index():
    """Index - displays simple Google Maps interface"""

    return render_template("index.html")


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    """Upload and read XML file from form"""

    if request.method == "GET":
        return render_template("upload.html")

    elif request.method == "POST":

        # Obtain file from 'upload.html' and access data
        file = request.files["file"]
        xmldoc = minidom.parse(file)
        items = xmldoc.getElementsByTagName("trkpt")

        # Create empty lists for lat, lon, and time data
        lat_list = []
        lon_list = []
        time_list = []

        # Create empty lists for pertinant values ('temp') and list of 'temp' lists ('data')
        temp = []
        data = []

        # Set counters
        entry = 1    # Data entry number (for diagnostic print purposes only)
        distance = 0    # Set distance to 0 - for cumulative distance total
        km = 0    # Set km to 0 - acts as reference point

        # Set index counters
        n = 0
        m = 1
        z = 0

        # Iterate through XML file obtaining 'lat', 'lon', and 'time' values, and append to respective lists
        for item in items:

            lat = item.attributes['lat'].value
            lon = item.attributes['lon'].value
            time = item.getElementsByTagName("time")[0].firstChild.data

            lat_list.append(float(lat))
            lon_list.append(float(lon))
            time_list.append(time)

        # Merge lists ('lat_list' and 'lon_list') into single list, 'coordinates'
        coordinates = [{'lat': a, 'lng': b} for a, b in zip(lat_list, lon_list)]

        """For reference point km 0 (note: list popped at end of route)"""

        # List element 0 of 7 - current km (set to 0)
        temp.append(km)

        # List element 1 of 7 - distance from previous entry entry (typically 1 Km)
        temp.append(temp[0]-temp[0])

        # List element 2 of 7 - date stamp formatted using date_format() function
        temp.append(date_format(time_list[n]))

        # List element 3 of 7 - time stamp formatted using time() function
        temp.append(time_format(time_list[n]))

        # List element 4 of 7 - current time expressed as seconds (calculated using custom time_calc() function)
        deltaSec = time_calc(time_list[n])
        temp.append(deltaSec)

        # List element 5 of 7 - time from last entry in seconds (set to 0 for km 0)
        temp.append(0)

        # List element 6 of 7 - time from last entry MM:SS (set to 0 for km 0)
        temp.append(0)

        # List element 7 of 7 - pace (assigned 0 for km 0)
        pace = 0
        temp.append(pace)

        # Append 'temp' list to 'data' list (list of lists)
        data.append(copy(temp))

        # Clear 'temp' list
        temp.clear()

        # Increment km tracker by 1
        km = km + 1

        """For int km > 1"""

        # For all elements in 'lat_list' (preventing going out of index range with while loop)
        for x in lat_list:
            while (m < len(lat_list)):

                # Extract pair of coordinates
                pair1 = (lat_list[n], lon_list[n])
                pair2 = (lat_list[m], lon_list[m])

                # Calculate distance between pair of coordinates using haversine() function
                distance_between_points = haversine(pair1, pair2)

                # Update 'distance' tracker
                distance = distance+distance_between_points

                # Iterate until last calculated distance exceeds int km then populate 'temp' list
                if distance > km:

                    # List element 0 of 7 - current km
                    temp.append(km)

                    # List element 1 of 6 - distance from previous entry (typically 1 km)
                    temp.append(temp[0]-data[z][0])

                    # List element 2 of 6 - date stamp formatted using date_format() function
                    temp.append(date_format(time_list[n]))

                    # List element 3 of 6 - time stamp formatted using time() function
                    temp.append(time_format(time_list[n]))

                    # List element 4 of 6 - current time expressed as seconds (calculated using custom time_calc() function)
                    deltaSec = time_calc(time_list[n])
                    temp.append(deltaSec)

                    # List element 5 of 7 - time from last entry in seconds
                    temp.append(deltaSec - data[z][4])

                    # List element 6 of 7 - time from last entry MM:SS
                    time_elapsed = deltaSec - data[z][4]
                    time_elapsed = str(datetime.timedelta(seconds=time_elapsed))
                    time_elapsed = time_elapsed[2:7]
                    temp.append(time_elapsed)

                    # List element 7 of 7 - pace
                    pace = temp[5]/(distance - data[z][0])
                    pace = str(datetime.timedelta(seconds=pace))
                    pace = pace[2:7]
                    temp.append(pace)

                    # Append 'temp' list to 'data' list and clear 'temp'
                    data.append(copy(temp))
                    temp.clear()

                    # Increment 'km' tracker and 'z' index counter
                    km = km+1
                    z = z+1

                # Increment index counters ('n' and 'm') and 'entry' tracker
                n = n+1
                m = m+1
                entry = entry + 1

       # Prevent users from uploading activities > 45 km
        if km >= 45:
            return apology("Distance too long!", 400)

        """For remaining distance > prev. int"""

        temp.append(round(distance, 2))

        temp.append(round(((distance+1)-km), 2))

        temp.append(date_format(time_list[n]))

        temp.append(time_format(time_list[n]))

        deltaSec = time_calc(time_list[n])
        temp.append(deltaSec)

        temp.append(deltaSec - data[z][4])

        time_elapsed = deltaSec - data[z][4]
        time_elapsed = str(datetime.timedelta(seconds=time_elapsed))
        time_elapsed = time_elapsed[2:]
        temp.append(time_elapsed)

        pace = temp[5]/(distance - data[z][0])
        pace = str(datetime.timedelta(seconds=pace))
        pace = pace[2:7]
        temp.append(pace)

        data.append(copy(temp))
        temp.clear()

        """Calculate final data (duration, pace, etc.)"""

        # Calculate duration of activity (final timepoint - first timepoint)
        duration = data[-1][4] - data[0][4]
        duration = str(datetime.timedelta(seconds=duration))
        duration = duration[0:7]

        # Remove first list from data (km 0 reference data)
        data.pop(0)

        # Calculate average pace
        avg_pace = 0
        n = 0
        for x in data:
            avg_pace = avg_pace + data[n][5]
            n = n+1
        avg_pace = (avg_pace/distance)
        avg_pace = str(datetime.timedelta(seconds=avg_pace))
        avg_pace = avg_pace[2:7]

        # Prevent adding previously uploaded file to database (activity still rendered) - checks date and time against database
        results = db.execute("SELECT date, time FROM records WHERE username = :id", id=session["user_id"])
        for items in results:
            if data[0][2] in items.values() and data[0][3] in items.values():
                # Render activity passing in coordinates, table values (data), and activity statistics (distance, duration, and average pace)
                return render_template("activity.html", points=json.dumps(coordinates), data=data, distance=round(distance, 2), duration=duration, avg_pace=avg_pace)

        # If new activity, insert data into database and render activity
        result = db.execute("INSERT INTO records (username, date, time, distance, duration, pace, coordinates, data) VALUES (:username, :date, :time, :distance, :duration, :pace, :coordinates, :data)",
                            username=session["user_id"], date=data[0][2], time=data[0][3], distance=round(distance, 2), duration=duration, pace=avg_pace, coordinates=str(lat_list), data=str(data))
        return render_template("activity.html", points=json.dumps(coordinates), data=data, distance=round(distance, 2), duration=duration, avg_pace=avg_pace)


@app.route("/history")
@login_required
def history():
    """Show previously uploaded activities"""

    data = db.execute("SELECT date, time, distance, duration, pace FROM records WHERE username = :id", id=session["user_id"])

    return render_template("history.html", data=data)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Please provide a username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("Please provide a password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          username=request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("Invalid username and / or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


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

    if request.method == "GET":
        return render_template("register.html")

    elif request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("Please provide a username", 403)

        # Ensure password was submitted
        elif not request.form.get("password1"):
            return apology("Please provide a password", 403)

        # Ensure password confirmation was submitted
        elif not request.form.get("password2"):
            return apology("Please confirm your password", 403)

        # Ensures passwords match
        if request.form.get("password1") != request.form.get("password2"):
            return apology("Passwords do not match", 403)

        # Hash password for database
        hash = generate_password_hash(request.form.get("password1"))

        # Insert 'username' and 'hash' into database 'users' table
        result = db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                            username=request.form.get("username"), hash=hash)

        # Error-check for SQL error (e.g. 'username' already exists in table)
        if not result:
            return apology("SQL Error!", 400)

        # Store ID in session
        session["user_id"] = result

        return render_template("index.html")


@app.route("/check", methods=["GET"])
def check():
    """Return true if username available, else false, in JSON format"""

    # jQuery $.get function request to server at /check?username= route
    username = request.args.get("username")

    # Extract all users from SQLite table
    users = db.execute("SELECT username FROM users")

    # Check if username in table - if present, return false
    for usernames in users:
        if username in usernames.values():
            result = [False]
            return jsonify(result[0])

    # If not present, return true
    result = [True]
    return jsonify(result[0])


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
