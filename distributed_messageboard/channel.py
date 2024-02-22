## channel.py - a simple message channel
##

from flask import Flask, request, render_template, jsonify
import json
import requests
import random as rd

# Class-based application configuration
class ConfigClass(object):
    """ Flask application config """

    # Flask settings
    SECRET_KEY = 'This is an INSECURE secret!! DO NOT use this in production!!'

# Create Flask app
app = Flask(__name__)
app.config.from_object(__name__ + '.ConfigClass')  # configuration
app.app_context().push()  # create an app context before initializing db

HUB_URL = 'http://localhost:5555'
HUB_AUTHKEY = '1234567890'
CHANNEL_AUTHKEY = '0987654321'
CHANNEL_NAME = "Guess the Number Channel"
CHANNEL_ENDPOINT = "http://localhost:5001" # don't forget to adjust in the bottom of the file
CHANNEL_FILE = 'messages.json'
MIN = 0
MAX = 5
NUMBER = rd.randint(MIN, MAX)

@app.cli.command('register')
def register_command():
    global CHANNEL_AUTHKEY, CHANNEL_NAME, CHANNEL_ENDPOINT

    # send a POST request to server /channels
    response = requests.post(HUB_URL + '/channels', headers={'Authorization': 'authkey ' + HUB_AUTHKEY},
                             data=json.dumps({
            "name": CHANNEL_NAME,
            "endpoint": CHANNEL_ENDPOINT,
            "authkey": CHANNEL_AUTHKEY}))

    if response.status_code != 200:
        print("Error creating channel: "+str(response.status_code))
        return

def check_authorization(request):
    global CHANNEL_AUTHKEY
    # check if Authorization header is present
    if 'Authorization' not in request.headers:
        return False
    # check if authorization header is valid
    if request.headers['Authorization'] != 'authkey ' + CHANNEL_AUTHKEY:
        return False
    return True

@app.route('/health', methods=['GET'])
def health_check():
    global CHANNEL_NAME
    if not check_authorization(request):
        return "Invalid authorization", 400
    return jsonify({'name':CHANNEL_NAME}),  200

# GET: Return list of messages
@app.route('/', methods=['GET'])
def home_page():
    if not check_authorization(request):
        return "Invalid authorization", 400
    # fetch channels from server
    return jsonify(read_messages())

# POST: Send a message
@app.route('/', methods=['POST'])
def send_message():
    # fetch channels from server
    # check authorization header
    if not check_authorization(request):
        return "Invalid authorization", 400
    # check if message is present
    message = request.json
    if not message:
        return "No message", 400
    if not 'content' in message:
        return "No content", 400
    if not 'sender' in message:
        return "No sender", 400
    if not 'timestamp' in message:
        return "No timestamp", 400
    # add message to messages
    messages = read_messages()
    messages.append({'content':message['content'], 'sender':message['sender'], 'timestamp':message['timestamp']})
    save_messages(messages)
    send_response(messages, message)
    save_messages(messages)
    return "OK", 200

def read_messages():
    global CHANNEL_FILE
    try:
        f = open(CHANNEL_FILE, 'r')
    except FileNotFoundError:
        return []
    try:
        messages = json.load(f)
    except json.decoder.JSONDecodeError:
        messages = []
    f.close()
    return messages

def save_messages(messages):
    global CHANNEL_FILE
    with open(CHANNEL_FILE, 'w') as f:
        json.dump(messages, f)

def send_response(messages, message):
    try:
        int(message['content'])
    except ValueError:
        return messages.append({'content':'Introduce a number, please!', 'sender':'Bot', 'timestamp':message['timestamp']})
    n = number_guessed(int(message['content']))

    if n == True:
        return messages.append({'content':'You guessed right!', 'sender':'Bot', 'timestamp':message['timestamp']})
    if n == 'greater':
        return messages.append({'content':'The number is greater', 'sender':'Bot', 'timestamp':message['timestamp']})
    if n == 'lower':
        return messages.append({'content':'The number is lower', 'sender':'Bot', 'timestamp':message['timestamp']})
    return messages.append({'content':'Try again', 'sender':'Bot', 'timestamp':message['timestamp']})
    
def number_guessed(x):
    global NUMBER, MIN, MAX
    if NUMBER == x:
        NUMBER = rd.randint(MIN, MAX)
        return True
    if NUMBER < x:
        return 'lower'
    if NUMBER > x:
        return 'greater'
    return False

# Start development web server
if __name__ == '__main__':
    app.run(port=5001, debug=True)