from flask import Flask, redirect, url_for, render_template

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/coordinateInput")
def coordinateInput():
    return render_template("coordniatePage.html")

@app.route("/controlOverride")
def overrideControls():
    return render_template("controlOverride.html")

if __name__ == "__main__":
    app.run(debug = True)
