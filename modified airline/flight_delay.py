from flask import Flask, render_template, request, redirect, url_for, session
import pickle
import numpy as np
from database import init_db, add_user, verify_user

app = Flask(__name__)
app.secret_key = "flight_delay_secret_key"

# ---------------- INITIALIZE DATABASE ----------------
init_db()

# ---------------- LOAD ML MODEL ----------------
with open("lr_model.pkl", "rb") as f:
    lr_model = pickle.load(f)

# ---------------- ENCODING FUNCTIONS ----------------
def encode_airport(code):
    airport_map = {
        "DEL": 1, "BOM": 2, "BLR": 3, "MAA": 4, "HYD": 5, "CCU": 6,
        "JFK": 7, "LAX": 8, "ORD": 9, "LHR": 10, "DXB": 11, "SIN": 12
    }
    return airport_map.get(code, 0)

def encode_carrier(code):
    carrier_map = {
        "AI": 1, "6E": 2, "UK": 3,
        "UA": 4, "AA": 5, "DL": 6
    }
    return carrier_map.get(code, 0)

# ---------------- HOME ----------------
@app.route("/", methods=["GET"])
def home():
    return redirect(url_for("signin"))

# ---------------- AUTH ROUTES ----------------
@app.route("/signup", methods=["GET", "POST"])
def signup():
    error = None
    if request.method == "POST":
        if add_user(request.form["username"], request.form["password"]):
            return redirect(url_for("signin"))
        else:
            error = "Username already exists"
    return render_template("signup.html", error=error)

@app.route("/signin", methods=["GET", "POST"])
def signin():
    error = None
    if request.method == "POST":
        if verify_user(request.form["username"], request.form["password"]):
            session["user"] = request.form["username"]
            return redirect(url_for("predict"))
        else:
            error = "Invalid username or password"
    return render_template("signin.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("signin"))

# ---------------- FLIGHT PREDICTION ----------------
@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("signin"))

    if request.method == "POST":
        origin = encode_airport(request.form["origin"])
        dest = encode_airport(request.form["dest"])
        carrier = encode_carrier(request.form["carrier"])
        temperature = float(request.form["temperature"])
        wind_speed = float(request.form["wind_speed"])
        flight_date = request.form["flight_date"]

        # Model input
        input_data = np.array([[origin, dest, carrier, temperature, wind_speed]])
        predicted_delay = float(lr_model.predict(input_data)[0])

        # ================== DYNAMIC DELAY LOGIC ==================
        # Convert model score → minutes (dynamic)
        delay_minutes = int(predicted_delay * 20)

        if delay_minutes <= 0:
            delay_message = "✅ Flight is Not Delayed"
            delay_text = "On Time"
        else:
            delay_message = "⚠️ Flight is Delayed"

            if delay_minutes < 60:
                delay_text = f"{delay_minutes} minutes delay"
            else:
                hours = delay_minutes // 60
                minutes = delay_minutes % 60
                delay_text = f"{hours} hour(s) {minutes} minute(s) delay"

        # DEBUG (check terminal)
        print("Model Output:", predicted_delay)
        print("Delay Minutes:", delay_minutes)
        print("Displayed:", delay_text)

        return render_template(
            "result.html",
            delay_message=delay_message,
            delay_text=delay_text,
            flight_date=flight_date
        )

    return render_template("index.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)
