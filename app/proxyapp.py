from flask import Flask, flash, request, Blueprint, url_for, redirect, render_template, request, session, abort, Response
#from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import json
import logging
import sys
from app.Viimawrapper.viimawrapper import Viimawrapper


# Move configuration parameters to factory - Add a config.py and import from app.config.from_mapping()???
client_id = ""
client_secret = ""

# Setup logging capabilities
log = logging.getLogger('Viima Proxy')
log.addHandler(logging.StreamHandler(sys.stdout))
log.setLevel(logging.DEBUG)
logging.basicConfig(format='%(process)d-%(levelname)s-%(message)s')

# OAuth2 given in the Viima API documentation
authorization_base_url = "https://app.viima.com/oauth2/token/"
api_base_url = "app.viima.com/api/customers/3730/"  # 3730 correspond to specific Viima Board ID
customer_id = 3730
token_url = "https://app.viima.com/oauth2/token/"  # Not really used by Viima but act as base API URL
refresh_url = "https://app.viima.com/oauth2/token/"  # This one is used for Viima Oauth2 token refresh
scope = [
    "read",
    "write",
]

# Required variables for Viima wrapper
appclient = Viimawrapper(customer_id, authorization_base_url, api_base_url)

translate_map = {
    'name': 'Name of idea',
    'fullname': 'Creator',
    'hotness': 'hotness',
    'vote_count': 'vote count',
    'viima_score': 'AU Points',
    'au_status': 'Process stage',
}

proxyapp = Blueprint('proxyapp', __name__)


@proxyapp.route('/')
def home():
    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if appclient.isconnected():
        return redirect(url_for('proxyapp.items'))
    else:
        return redirect(url_for('proxyapp.auth'))


@proxyapp.route('/auth')
def auth():
    if appclient.isconnected():
        return 'Connected to Viima API!  <a href=" /logout">Logout</a>'
    else:
        return render_template('auth.html')

#def token_updater(token):
#    log.debug('Access token updated. Old = %s  New = %s', session['oauth_token']['access_token'], token['access_token'])
#    session['oauth_token'] = token


@proxyapp.route('/do_auth', methods=['POST'])
def do_auth():
    appclient.login(request.form['username'],
                    request.form['password'],
                    request.form['client_id'],
                    request.form['client_secret'],
                    scope=scope)
    return redirect(url_for('proxyapp.items'))


@proxyapp.route("/items")
def items():
    if appclient.isconnected():
        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []

        # Loop through items response. Ideas are stored in "[results]"
        for local_item in items['results']:
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
        return Response(json.dumps(response_items), mimetype='application/json', content_type='text/json; charset=utf-8')
    else:
        return redirect(url_for('proxyapp.auth'))

@proxyapp.route("/table")
def table():
    if appclient.isconnected():
        labels = []
        rows = []
        rowdata = []
        friendlylabels = []

        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        # Loop through items response. Ideas are stored in "[results]"

        #
        # Break out data extraction into separate function
        # Add Viima_score, hotness and other valuable data
        #
        for local_item in items['results']:
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = round(float(local_item['hotness']), 1)
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            for status in statuses:
                if status['id'] == local_item['status']:
                    response_item['au_status'] = status['name']
                    break
            response_items.append(response_item)
            log.debug('Response item(local): %s', response_item)
            response_item = {}

        # Create list with raw(API JSON) column names from response
        for row in response_items:  # Only loop into first level
            log.debug('Row: %s', row)
            for col in row.keys():
                labels.append(col)
                log.debug('Key: %s', col)
            break

        # Create friendly Table column names in separate list to be used in Table representation of ideas
        for row in response_items:  # Only loop into first level
            for col in row.keys():
                for friendlydescr in translate_map.keys():
                    if col == friendlydescr:
                        friendlylabels.append(translate_map[friendlydescr])
            break  # Break - So that we only extract column names once. There must be better ways to do this?

        return render_template('table.html', records=response_items, colnames=labels, friendlycols=friendlylabels)
    else:
        return redirect(url_for('proxyapp.auth'))


@proxyapp.route('/create_item')
def create_item():
    if appclient.isconnected():
        return render_template('create_item.html')
    else:
        return redirect(url_for('proxyapp.auth'))


@proxyapp.route('/do_create_item', methods=['POST'])
def do_create_item():
    if appclient.isconnected():
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
                                             #auto_refresh_url=refresh_url,
                                             token_updater=token_updater)
                headers = {'Content-type': 'application/json', 'Accept': 'application/json'}
                response = viima_client.post('https://app.viima.com/api/customers/3730/items/',
                                             data=json.dumps(post_item_data),
                                             headers=headers)
                log.debug('do_item_create(add idea) - POST response statuscode: %s', response.status_code)
                log.debug('do_item_create(add idea) - POST response: %s', response.json())
                response_content_json = response.json()

                # ADD CUSTOM FIELD DATA FROM FORMs to Viima:
                # POST custom fields data from form - "What is the problem this idea solves?"
                post_item_customfields_data = {
                    'custom_field': "102",
                    'value': request.form['item_solves']}
                item_id_customfield = response_content_json['id']
                log.debug('https://app.viima.com/api/customers/3730/items/' + str(item_id_customfield) + '/custom_field_values/')
                log.debug(post_item_customfields_data)
                response = viima_client.post('https://app.viima.com/api/customers/3730/items/'
                                             + str(item_id_customfield) + '/custom_field_values/',
                                             data=json.dumps(post_item_customfields_data),
                                             headers=headers)
                log.debug('do_item_create(add custom) - POST response statuscode: %s', response.status_code)
                log.debug('do_item_create(add custom) - POST response: %s', response.json())
                # Handle this response
                response_content_json = response.json()


                # POST custom fields data from form - "What result will it bring?"
                post_item_customfields_data = {
                    'custom_field': "103",
                    'value': request.form['item_results']}
                #item_id_customfield = response_content_json['id']
                response = viima_client.post('https://app.viima.com/api/customers/3730/items/'
                                             + str(item_id_customfield) + '/custom_field_values/',
                                             data=json.dumps(post_item_customfields_data),
                                             headers=headers)
                log.debug(post_item_customfields_data)
                log.debug('do_item_create(add custom) - POST response statuscode: %s', response.status_code)
                log.debug('do_item_create(add custom) - POST response: %s', response.json())
                # Handle this response
                response_content_json = response.json()

            except Exception as e:
                log.error("Oauth2 error: %s ", e)
                #raise
                return redirect(url_for('proxyapp.auth'))

        else:
            log.debug('We should not get here!')
            # We should redirect to a thank you page and then back to create_item_form
            # - May just a simple popup and then back to form
    else:
        return redirect(url_for('proxyapp.auth'))
    return redirect(url_for('proxyapp.table'))
