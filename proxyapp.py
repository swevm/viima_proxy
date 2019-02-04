from flask import Flask, flash, request, url_for, redirect, render_template, request, session, abort, Response
import os
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import json
import logging
import sys

app = Flask(__name__)

client_id = ""
client_secret = ""
redirect_uri = 'https://your.registered/callback' # Not used by Viima afaik

# Setup logging capabilities
log = logging.getLogger('Flaskapp')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)
logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s')

# OAuth2 given in the Viima API documentation
authorization_base_url = "https://app.viima.com/oauth2/token/"
api_base_url = "app.viima.com/api/customers/3730/" # 3730 correspond to specific Viima Board ID
token_url = "https://app.viima.com/oauth2/token/" # Not really used by Viima but act as base API URL
refresh_url = "https://app.viima.com/oauth2/token/" # This one is used for Viima Oauth2 token refresh
scope = [
    "read",
    "write",
]


@app.route('/')
def home():
    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if client_id == "" or client_secret == "":
        return render_template('auth.html')
    else:
        return json.dumps(session)


@app.route('/auth')
def auth():
    print(session)
    if client_id == "" or client_secret == "" or 'oauth_token' in session:
        return render_template('auth.html')
    else:
        return 'Connected to Viima API!  <a href=" /logout">Logout</a>'


def token_updater(token):
    print('Outer token updater')
    session['oauth_token'] = token


@app.route('/do_auth', methods=['POST'])
def do_auth():
    if request.form['client_id'] and request.form['client_secret'] and request.form['username'] and request.form['password']:
        log.debug('Entered Client Id %s', request.form['client_id'])
        try:
            viima_client = OAuth2Session(
                client=LegacyApplicationClient(client_id=request.form['client_id']))
            token = viima_client.fetch_token(
                token_url=token_url,
                username=request.form['username'],
                password=request.form['password'],
                client_id=request.form['client_id'],
                client_secret=request.form['client_secret'])
            session['client_id'] = request.form['client_id']
            session['client_secret'] = request.form['client_secret']
            session['oauth_token'] = token
            print(session)
        except Exception as e:
            log.error("Oauth2 error: %s ", e)
            return redirect(url_for('auth'))

    else:
        log.debug('We should not get here!')
    return items()


@app.route("/items")
def items():

    if 'oauth_token' in session:
        token = session['oauth_token']
    else:
        return auth()

    if 'client_id' in session or 'client_secret' in session or 'access_token' in token:
        extra = {
            'client_id': session['client_id'],
            'client_secret': session['client_secret'],
        }
        viima_client = OAuth2Session(client_id,
                                     token=token,
                                     auto_refresh_kwargs=extra,
                                     auto_refresh_url=refresh_url,
                                     token_updater=token_updater)

    # Not efficient doing these API calls for every call to /items
        items_dict = viima_client.get('https://app.viima.com/api/customers/3730/items/').json()
        statuses = viima_client.get('https://app.viima.com/api/customers/3730/statuses/').json()
        response_item = {}
        response_items = []

    # Loop through items response. Ideas are stored in "[results]"
        for local_item in items_dict['results']:
            # log.debug('Extracted idea item: %s', local_item)
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    break
            response_items.append(response_item)
            response_item = {}

    else:
        return auth()

    return Response(json.dumps(response_items), mimetype='application/json', content_type='text/json; charset=utf-8')


@app.route("/table")
def table():
    labels = []
    rows = []
    rowdata = []

    if 'oauth_token' in session:
        token = session['oauth_token']
    else:
        return auth()

    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if 'client_id' in session or 'client_secret' in session or 'access_token' in token:
        extra = {
            'client_id': session['client_id'],
            'client_secret': session['client_secret'],
        }
        viima_client = OAuth2Session(client_id,
                                     token=token,
                                     auto_refresh_kwargs=extra,
                                     auto_refresh_url=refresh_url,
                                     token_updater=token_updater)

        # Not efficient doing these API calls for every call to /table
        items_dict = viima_client.get('https://app.viima.com/api/customers/3730/items/').json()
        statuses = viima_client.get('https://app.viima.com/api/customers/3730/statuses/').json()
        response_item = {}
        response_items = []
        # Loop through items response. Ideas are stored in "[results]"

        #
        # Break out data extraction into separate function
        # Add Viima_score, hotness and other valuable data
        #
        for local_item in items_dict['results']:
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    break
            response_items.append(response_item)
            response_item = {}

        # Create Table column names in separate list
        for row in response_items:
            for col in row.keys():
                labels.append(col)
            break
        for row in response_items:
            for value in row.values():
                rowdata.append(value)
            rows.append(rowdata)
            rowdata = []
    else:
        return auth()

    return render_template('table.html', records=response_items, colnames=labels)


@app.route('/create_item')
def create_item():
    if 'oauth_token' in session:
        token = session['oauth_token']
    else:
        return auth()

    if 'client_id' in session or 'client_secret' in session or 'access_token' in token:
        return render_template('create_item.html')
    else:
        return render_template('auth.html')


@app.route('/do_create_item', methods=['POST'])
def do_create_item():
    pass


if __name__ == "__main__":
    app.secret_key = os.urandom(12)

app.run(debug=True, host='0.0.0.0', port=4000)