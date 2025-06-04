from flask import Flask, request, jsonify

app = Flask(__name__)

authURL = None

@app.route('/auth')
def storeUrl():
    global authURL
    authURL = request.url
    return '', 200

@app.route('/get')
def retrieveUrl():
    global authURL
    if authURL:
        url = authURL
        authURL = None
        return jsonify({'data': url}), 200
    else:
        return jsonify({'error': 'No auth URL yet'}), 401