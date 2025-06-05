from flask import Flask, request, jsonify

app = Flask(__name__)
auth = None

@app.route('/auth')
def storeAuth():
    global auth
    code = request.args.get('code')
    state = request.args.get('state')
    if code:
        auth = {'url': request.url,
                'code': code,
                'state': state }
        return 'Authorization received', 200
    else:
        return 'Failed to save auth', 400

@app.route('/get')
def retrieveUrl():
    global auth
    if auth:
        temp = auth
        auth = None
        return jsonify(temp), 200
    else:
        return jsonify({'error': 'No auth yet'}), 404
