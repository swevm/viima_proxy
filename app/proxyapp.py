from flask import Flask, flash, request, Blueprint, url_for, redirect, render_template, request, session, abort, Response
from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import json
import logging
import sys


# Move configuration parameters to factory - Add a config.py and import from app.config.from_mapping()???
client_id = ""
client_secret = ""
redirect_uri = 'https://your.registered/callback' # Not used by Viima afaik

# Setup logging capabilities
log = logging.getLogger('Viima Proxy')
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

translate_map = {
    'name': 'Name of idea',
    'fullname': 'Creator',
    'hotness': 'hotness',
    'vote_count': 'vote count',
    'viima_score': 'AU Points',
    'au_status': 'In AU process stage',
}

proxyapp = Blueprint('proxyapp', __name__)


@proxyapp.route('/')
def home():
    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if client_id == "" or client_secret == "":
        return render_template('auth.html')
    else:
        return json.dumps(session)


@proxyapp.route('/auth')
def auth():
    log.debug('/auth() - Existing session: %s', session)
    if client_id == "" or client_secret == "" or 'oauth_token' in session:
        return render_template('auth.html')
    else:
        return 'Connected to Viima API!  <a href=" /logout">Logout</a>'


def token_updater(token):
    log.debug('Access token updated. Old = %s  New = %s', session['oauth_token']['access_token'], token['access_token'])
    session['oauth_token'] = token


@proxyapp.route('/do_auth', methods=['POST'])
def do_auth():
    if request.form['client_id'] and request.form['client_secret'] and request.form['username'] and request.form['password']:
        log.debug('/do_auth - Entered Client Id %s', request.form['client_id'])
        log.debug('/do_auth - Entered Client Secret %s', request.form['client_secret'])
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
            log.debug('/do_auth - New session: %s', session)
        except Exception as e:
            log.error("Oauth2 error: %s ", e)
            return redirect(url_for('auth'))

    else:
        log.debug('We should not get here!')
    return redirect(url_for('proxyapp.items'))


@proxyapp.route("/items")
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


@proxyapp.route("/table")
def table():
    labels = []
    rows = []
    rowdata = []
    friendlylabels = []

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

        # Create list with raw(API JSON) column names from response
        for row in response_items: # Only loop into first level
            for col in row.keys():
                labels.append(col)
            break

        # Create friendly Table column names in separate list to be used in Table representation of ideas
        for row in response_items: # Only loop into first level
            for col in row.keys():
                for friendlydescr in translate_map.keys():
                    if col == friendlydescr:
                        friendlylabels.append(translate_map[friendlydescr])
            break # Break - So that we only extract column names once. There must be better ways to do this?
    else:
        return auth()

    return render_template('table.html', records=response_items, colnames=labels, friendlycols=friendlylabels)


@proxyapp.route('/create_item')
def create_item():
    if 'oauth_token' in session:
        token = session['oauth_token']
    else:
        return auth()

    if 'client_id' in session or 'client_secret' in session or 'access_token' in token:
        return render_template('create_item.html')
    else:
        return render_template('auth.html')


@proxyapp.route('/do_create_item', methods=['POST'])
def do_create_item():
    if 'oauth_token' in session:
        token = session['oauth_token']
    else:
        return auth()

    if request.form['name'] and request.form['emailaddress'] and request.form['itemname'] and request.form['itemdescr']:
        log.debug('Creator: %s  Email: %s  Item name: %s  Item Description: %s',
                  request.form['name'],
                  request.form['emailaddress'],
                  request.form['itemname'],
                  request.form['itemdescr'])
        try:
            extra = {
                'client_id': session['client_id'],
                'client_secret': session['client_secret'],
            }
            post_item_data = {
                'name': request.form['itemname'],
                'description': 'Idea creator: ' + request.form['name'] + '\n' + 'Creator email: ' + request.form['emailaddress'] + '\n\n' + request.form['itemdescr']
            }
            viima_client = OAuth2Session(client_id,
                                         token=token,
                                         auto_refresh_kwargs=extra,
                                         auto_refresh_url=refresh_url,
                                         token_updater=token_updater)
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
            response = viima_client.post('https://app.viima.com/api/customers/3730/items/', data=json.dumps(post_item_data), headers=headers)
            log.debug('do_item_create() - POST response statuscode: %s', response.status_code)
            log.debug('do_item_create() - POST response: %s', response.content)
        except Exception as e:
            log.error("Oauth2 error: %s ", e)
            return redirect(url_for('auth'))

    else:
        log.debug('We should not get here!')
    return redirect(url_for('proxyapp.table'))
