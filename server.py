from flask import Flask, request, jsonify

app = Flask(__name__)
authCredentials = None

@app.route('/auth')
def storeAuth():
    global authCredentials
    code = request.args.get('code')
    state = request.args.get('state')

    if code:
        authCredentials = {'ok': True, 'code': code, 'state': state}
        return 'Authorization received', 200
    else:
        return 'Failed to save auth', 400

@app.route('/get')
def retrieveUrl():
    global authCredentials
    if authCredentials:
        data = authCredentials
        authCredentials = None
        return jsonify(data), 200
    else:
        return jsonify({'error': 'No auth URL yet'}), 404
