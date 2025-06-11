"""
This webserver will pretend to be a backend to an Ecommerce site. Its endpoints will simulate necessary actions like fetching data or looking up account information.
Additionally this webserver will integrate with Slack API to simulate a way to contact a real person.
"""

from flask import Flask, request, jsonify
from utils import validateUsername, validateTrackingNumber, getPackage
app = Flask(__name__)

"""
this endpoint will verify if account information is valid
"""
@app.route('/val/username')
def doRoute():
    username = request.args.get('username')
    if validateUsername(username):
        return 'Username is valid', 200
    else:
        return 'Username is invalid', 400

"""
this endpoint will verify if a tracking number is valid
"""
@app.route('/val/tracking')
def doRoute():
    number = request.args.get('number')
    if validateTrackingNumber(number):
        return 'Tracking Number is valid', 200
    else:
        return 'Tracking Number is invalid', 400
    
"""
this endpoint will get information about someone's package
"""
@app.route('/package')
def doRoute():
    username, trackingNumber = request.args.get('auth')
    package = getPackage(username, trackingNumber)

    if package is None:
        return 'Error with getting package', 500
    else:
        return jsonify(package), 200
    
"""
this endpoint will see if an item description is in inventory
"""
@app.route('/lookup/:item')
def doRoute():
    itemDescription = request.args.get()
