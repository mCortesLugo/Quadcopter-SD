from flask import Flask, redirect, url_for, render_template

from flask_googlemaps import GoogleMaps
from flask_googlemaps import Map

app = Flask(__name__)

#api_key = "AIzaSyAB7MbKvVHLspmx_69G-eTAUtCHwJqJlgY"
#app.config['GOOGLEMAPS_KEY'] = "AIzaSyAB7MbKvVHLspmx_69G-eTAUtCHwJqJlgY"
#GoogleMaps(app)

@app.route("/")
def home():
#    mymap = Map(
#        identifier="view-side",
#       lat=37.4419,
#        lng=-122.1419,
#        markers=[(37.4419, -122.1419)]
##    )
#    sndmap = Map(
#        identifier="sndmap",
#        lat=37.4419,
#        lng=-122.1419,
#        markers=[
#          {
#             'icon': 'http://maps.google.com/mapfiles/ms/icons/green-dot.png',
#             'lat': 37.4419,
#             'lng': -122.1419,
#             'infobox': "<b>Hello World</b>"
#          },
#          {
#             'icon': 'http://maps.google.com/mapfiles/ms/icons/blue-dot.png',
#             'lat': 37.4300,
#             'lng': -122.1400,
#             'infobox': "<b>Hello World from other place</b>"
#          }
#        ]
#    )
    return render_template("index.html")

@app.route("/coordinateInput")
def coordinateInput():
    return render_template("coordniatePage.html")

@app.route("/controlOverride")
def overrideControls():
    return render_template("controlOverride.html")

if __name__ == "__main__":
    app.run(debug = True)
