from flask import Flask, flash, request, Blueprint, url_for, redirect, render_template, request, session, abort, Response
import json
import logging
import sys
from app.Viimawrapper.viimawrapper import Viimawrapper
import requests
import time

import c3pyo as c3
from collections import Counter

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
    'name': 'Namn på idé',
    'fullname': 'Skapad',
    'hotness': 'Aktivitsnivå',
    'vote_count': 'Röster',
    'viima_score': 'AU poäng',
    'au_status': 'Status',
    'description': 'Beskrivning',
}


def send_data_to_portal(dataBody):
    URL = '*********'
    header = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
    }

    body = dataBody

    r = requests.post(URL, headers=header, data=json.dumps(body))
    time.sleep(0.5)
    print(r)


status_counter_cache = []  # Holds a list of idea statuses - used to create a dynamic chart
proxyapp = Blueprint('proxyapp', __name__)


@proxyapp.route('/')
def home():
    # Show connection status. Should do a basic API call to make sure we´re connected. If not redirect to /auth
    if appclient.isconnected():
        return redirect(url_for('proxyapp.items'))
    else:
        return redirect(url_for('proxyapp.auth'))


def get_bar_chart_au_status_json():
    labels = Counter(status_counter_cache).keys()
    values = Counter(status_counter_cache).values()
    au_state_count = values

    chart = c3.BarChart()
    chart.plot(au_state_count, label='AU process stage')
    chart.set_xticklabels(labels)
    chart.ylabel('Amount')
    chart.bind_to('bar_chart_div')
    return chart.json()


@proxyapp.route("/au_process_stage_chart", methods=['GET', 'POST'])
def au_process_stage_chart():
    chart_json = get_bar_chart_au_status_json()
    return render_template("barchart.html", chart_json=chart_json)

@proxyapp.route('/auth')
def auth():
    if appclient.isconnected():
        return 'Connected to Viima API!  <a href=" /logout">Logout</a>'
    else:
        return render_template('auth.html')

@proxyapp.route('/piechart')
def pie_chart_test():
    if appclient.isconnected():

        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        status_counter=[]
        # Loop through items response. Ideas are stored in "[results]"
        for local_item in items['results']:
            # log.debug('Extracted idea item: %s', local_item)
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            response_item['description'] = local_item['description']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    status_counter_cache.append(status['name'])  # Create list of AU Status as base for barchart
                    break
            response_items.append(response_item)
     
            response_item = {}

        i = status_counter
        d = {x:i.count(x) for x in i}
            
        status_names = list(d.keys())
        status_count = list(d.values())

        return render_template('pie_chart_test.html', labels=status_names,data=status_count)
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.items'))
@proxyapp.route('/linechart')
def line_chart_test():
    if appclient.isconnected():

        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        status_counter=[]
        # Loop through items response. Ideas are stored in "[results]"
        for local_item in items['results']:
            # log.debug('Extracted idea item: %s', local_item)
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            response_item['description'] = local_item['description']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    status_counter.append(status['name']) # Create list of AU Status as base for barchart
                    break
            response_items.append(response_item)
     
            response_item = {}

        i = status_counter
        d = {x:i.count(x) for x in i}
            
        status_names = list(d.keys())
        status_count = list(d.values())

        return render_template('line_chart_test.html', labels=status_names,data=status_count)
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.status'))

@proxyapp.route('/barchart')
def bar_chart_test():
     #cashetools
    if appclient.isconnected():

        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        status_counter=[]
        # Loop through items response. Ideas are stored in "[results]"
        for local_item in items['results']:
            # log.debug('Extracted idea item: %s', local_item)
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            response_item['description'] = local_item['description']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    status_counter.append(status['name']) # Create list of AU Status as base for barchart
                    break
            response_items.append(response_item)
          
            response_item = {}
            #Create a dict for counting values for every key.
        i = status_counter
        d = {x:i.count(x) for x in i}
            
        status_names = list(d.keys())
        status_count = list(d.values())

        return render_template('bar_chart_test.html', labels=status_names,data=status_count)
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.status'))

@proxyapp.route('/do_auth', methods=['POST'])
def do_auth():
    print(len(appclient.readSession()))
    if len(appclient.readSession()) <= 0:

        appclient.login(request.form['username'],
                        request.form['password'],
                        request.form['client_id'],
                        request.form['client_secret'],
                        scope=scope)

        return redirect(url_for('proxyapp.table'))
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.table'))


@proxyapp.route("/items")
def items():
    #cashetools
    if appclient.isconnected():

        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        status_counter=[]
        # Loop through items response. Ideas are stored in "[results]"
        for local_item in items['results']:
            # log.debug('Extracted idea item: %s', local_item)
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = local_item['hotness']
            response_item['vote_count'] = local_item['vote_count']
            response_item['viima_score'] = local_item['viima_score']
            response_item['description'] = local_item['description']
            for status in statuses:
                if local_item['status'] == status['id']:
                    response_item['au_status'] = status['name']
                    status_counter.append(status['name']) # Create list of AU Status as base for barchart
                    status_counter_cache.append(status['name'])  # Create list of AU Status as base for barchart
                    break
            response_items.append(response_item)
            #send_data_to_portal(response_item)
            response_item = {}
            #Create a dict for counting values for every key.
        i = status_counter
        d = {x:i.count(x) for x in i}
            
        status_names = list(d.keys())
        status_count = list(d.values())

        return Response(json.dumps(response_items), mimetype='application/json', content_type='text/json; charset=utf-8')
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.status'))


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


@proxyapp.route("/table")
def table():
    if appclient.isconnected():
        labels = []
        friendlylabels = []
        items = appclient.getitems()
        statuses = appclient.getstatuses()
        response_item = {}
        response_items = []
        description = {}
        descriptions = []
        # Loop through items response. Ideas are stored in "[results]"

        #
        # Break out data extraction into separate function
        # Add Viima_score, hotness and other valuable data
        #
        for local_item in items['results']:
            response_item['name'] = local_item['name']
            response_item['fullname'] = local_item['fullname']
            response_item['hotness'] = round(float(local_item['hotness']), 1)
            if local_item['vote_count'] is None:
                response_item['vote_count'] = 0
            else:
                response_item['vote_count'] = local_item['vote_count']
            if local_item['viima_score'] is None:
                response_item['viima_score'] = 0
            else:
                response_item['viima_score'] = round(float(local_item['viima_score']), 1)
            #response_item['viima_score'] = local_item['viima_score']
            #description['description'] = local_item['description']
            #description['name'] = local_item['name']

            for status in statuses:
                if status['id'] == local_item['status']:
                    response_item['au_status'] = status['name']
                    break
            response_items.append(response_item)
            #descriptions.append(description)
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
        if appclient.login(manual=False) == 1:
            return redirect(url_for('proxyapp.table'))
        else:
            return redirect(url_for('proxyapp.status'))


@proxyapp.route('/create_item')
def create_item():
    if appclient.isconnected():
        return render_template('create_item.html')
    else:
        return redirect(url_for('proxyapp.status'))


@proxyapp.route('/do_create_item', methods=['POST'])
def do_create_item():
    if appclient.isconnected():
        appclient.createitem(request.form['name'],
                             request.form['emailaddress'],
                             request.form['itemname'],
                             request.form['itemdescr'],
                             itemsolves=request.form['itemsolves'],
                             itemresults=request.form['itemresults'])
    else:
        appclient.login(manual=False)
        return redirect(url_for('proxyapp.status'))
    return redirect(url_for('proxyapp.thanks'))
