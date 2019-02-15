from flask import Flask, flash, request, Blueprint, url_for, redirect, render_template, request, session, abort, Response
import json
import logging
import sys
from app.Viimawrapper.viimawrapper import Viimawrapper
import requests
import time
# Move configuration parameters to factory - Add a config.py and import from app.config.from_mapping()???
client_id = ""
client_secret = ""
session = {}
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


def send_data_to_portal(dataBody):

    URL = '***************'
    header = {
                'Accept': 'application/json',
                'Content-Type': 'application/json',
            }
    
    body = dataBody
 
    r = requests.post(URL, headers=header, data=json.dumps(body))
    time.sleep(0.5)
    print(r)


proxyapp = Blueprint('proxyapp', __name__)


@proxyapp.route('/')
def home():
    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if appclient.isconnected():
        return redirect(url_for('proxyapp.items'))
    else:
        return redirect(url_for('proxyapp.auth'))


@proxyapp.route('/status')
def status():
    # Show connection status for backend API
    if appclient.isconnected():
        return render_template('status.html', is_connected=appclient.isconnected()) #redirect(url_for('proxyapp.items'))  # Add dynamic data to status to show that connecvtion is live or down.
    else:
        return render_template('status.html', is_connected=appclient.isconnected())

@proxyapp.route('/thanks')
def thanks():
    # Show connection status for backend API
    if appclient.isconnected():
        return render_template('thanks.html', is_connected=appclient.isconnected()) #redirect(url_for('proxyapp.items'))  # Add dynamic data to status to show that connecvtion is live or down.
    else:
        return render_template('status.html', is_connected=appclient.isconnected())


@proxyapp.route('/auth')
def auth():
    #appclient.login(manual=False)
    if appclient.isconnected():
        return 'Connected to Viima API!  <a href=" /logout">Logout</a>'
    else:
        if len(appclient.readSession()) > 0:
            return table()
        else:
            return render_template('auth.html')


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
    try:
        appclient.login(manual=False)
        if appclient.isconnected():
            items = appclient.getitems()
            statuses = appclient.getstatuses()
            response_item = {}
            response_items = []

            # Loop through items response. Ideas are stored in "[results]"
            for local_item in items['results']:
                if not (local_item['viima_score']):
                    response_item['viima_score'] = 0
                else:
                    response_item['viima_score'] = local_item['viima_score']
                # log.debug('Extracted idea item: %s', local_item)
                response_item['name'] = local_item['name']
                response_item['fullname'] = local_item['fullname']
                response_item['hotness'] = local_item['hotness']
                response_item['vote_count'] = local_item['vote_count']
                
                for status in statuses:
                    if local_item['status'] == status['id']:
                        response_item['au_status'] = status['name']
                        break
                response_items.append(response_item)
                #send data to portal function..
                #send_data_to_portal(response_item)
                response_item = {}
                
            return Response(json.dumps(response_items),  mimetype='application/json', content_type='text/json; charset=utf-8')
        else:
            return redirect(url_for('proxyapp.status'))
    except Exception as e:
        print(e)
        return render_template('status.html')

@proxyapp.route("/table")
def table():
    try:
        appclient.login(manual=False)
        if appclient.isconnected():
            labels = []
            friendlylabels = []
            items = appclient.getitems()
            statuses = appclient.getstatuses()
            response_item = {}
            response_items = []
            #appclient.login(manual=False)
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
                log.debug('Response item(local): {}'.format(response_item))
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
            return redirect(url_for('proxyapp.status'))
    except Exception as e:
        print(e)
        return render_template('auth.html')


@proxyapp.route('/create_item')
def create_item():
    try:
        appclient.login(manual=False)
        if appclient.isconnected():
            return render_template('create_item.html')
        else:
            return redirect(url_for('proxyapp.status'))
    except Exception as e:
        return render_template('auth.html')

@proxyapp.route('/do_create_item', methods=['POST'])
def do_create_item():
    appclient.login(manual=False)
    if appclient.isconnected():
        appclient.createitem(request.form['itemname'],
                             request.form['emailaddress'],
                             request.form['itemname'],
                             request.form['itemdescr'],
                             itemsolves=request.form['itemsolves'],
                             itemresults=request.form['itemresults'])
        #appclient.login(manual=False)
    else:
        return redirect(url_for('proxyapp.status'))
    return redirect(url_for('proxyapp.thanks'))
