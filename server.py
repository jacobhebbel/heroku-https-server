from flask import Flask, request, jsonify

app = Flask(__name__)
authURL = None

@app.route('/auth')
def storeAuth():
    global authURL
    code = request.args.get('code')
    if code:
        authURL = request.url
        return 'Authorization received', 200
    else:
        return 'Failed to save auth', 400

@app.route('/get')
def retrieveUrl():
    global authURL
    if authURL:
        return jsonify({'url': authURL}), 200
    else:
        return jsonify({'error': 'No auth URL yet'}), 404
