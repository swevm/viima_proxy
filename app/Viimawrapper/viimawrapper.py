from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import json
import logging
import base64


mySession = {}
class Viimawrapper:
    """
        Viimawrapper class is a CRUD wrapper for public Viima REST API that wrap the basic api features in Python methods

        ...

        Attributes
        ----------
        something : str
            information about this attribute

        Methods
        -------
        login(username, password)
            Login to Viima API - Requires __init__() parameters to exist to work
        """

    def __init__(self, customer_id, base_authorization_url="", base_api_url="", **kwargs):
        """
                Parameters
                ----------
                client_id : str
                    Unique ID that one get by creating an app as an admin form within Viima interface
                client_secret : str
                    Unique secret code that one get by creating an app as an admin form within Viima interface
                base_authorization_url : str
                    Base URL for Oauth2 endpoint (usually https://app.viima.com/oauth2/token/)
                base_api_url : str
                    Base Viima API endpoint (usually app.viima.com/api/customers/)
                **customer_id : int
                    Unique number that correspond to the the Board connected too.
                **scope : list
                    Contains a list of strings can be either 'read' 'write' or both in a list
                HOW TO DOCUMENT KWARGS???
        """
        self.client_id = ''  # Default to empty
        self.client_secret = ''  # Default to empty
        self.base_authorization_url = base_authorization_url
        self.base_api_url = base_api_url  # Set base URL for API endpoint
        self.customer_id = str(customer_id)  # For board ID - This is unique per Viima board and is not really a customer per definition
        self.scope = ['read']  # Default to readonly API access unless scope set during login()
        self.authorization_url = base_authorization_url  # Set Oauth2 authentication URL
        self.token = {}  # Default to empty token dict
        self.client = None  # Holds teh actual client object used to access backend API (with token refresh capability)
        self.extras = {'client_id': self.client_id, 'client_secret': self.client_secret}  # Used for Oauth2 token session handling
        self.sess = {}
        self.read = None
        # Create Oauth2Session - perhaps have these utility functions in a separate method instead of __init__
        # I wondr if this really work defining the session here. What is the difference between client=LegacyApplicationClient and just passing in client_id as done in get, post etc????
        self.viimaAppClient = None

        self.api_connection_state = False  # True if class har working connection to Viima API
        self.logger = logging.getLogger('Viima Proxy')  # Get degined logging facility

    def connect(self, username, password):
        pass
        
    def writeSession(self, sess):
        encoded_session = base64.b64encode(bytes(json.dumps(self.sess) ,'utf-8'))
        txt = open("binary.sn","wb")
        txt.write(encoded_session)
        txt.close()

    def readSession(self):
        try: 
            data = open("binary.sn", "r").read()
            decoded = base64.b64decode(data)
            decoded = decoded.decode()
            session = json.loads(decoded)
        except:
            session = {}    
            #print(session)
        return session

    def isconnected(self):
        """
                Returns
                -------
                Boolean - True for connected to Viima API otherwise false
        """
        return self.api_connection_state

    def token_updater(self, token):
        self.logger.debug('Access token updated. Old = {} '.format(self.token['access_token']))
        self.token = token
        self.logger.debug('Access token updated. New = {} '.format(self.token['access_token']))



    def refresh(self): # Method refreshes cached data, such as Categories, Statuses, Items(think about if its worth caching this data????)
        pass

    def get_token(self):
        if self.isconnected():
            return self.token
        else:
            return False

    def login(self, username="", password="", client_id="", client_secret="", manual=True, **kwargs):  # BUG: **kwargs seem not to work here as expected. Why?
        if not (manual):
            #This happens after first login
            mySession = self.readSession()
            self.client_id = mySession['client_id']
            self.client_secret = mySession['client_secret']
            self.token = mySession['ouath_token']
            self.api_connection_state = True

            if self.token != mySession['ouath_token']:
                mySession['ouath_token'] = self.token
                self.writeSession(mySession)   
        else:
            self.client_id = client_id
            self.client_secret = client_secret
            for key, value in kwargs.items():
                if key == 'scope':
                    self.scope = value
            try:
                self.viimaAppClient = OAuth2Session(
                    client=LegacyApplicationClient(client_id=self.client_id), scope=self.scope)

                self.token = self.viimaAppClient.fetch_token(
                    token_url=self.authorization_url,
                    username=username,
                    password=password,
                    client_id=self.client_id,
                    client_secret=self.client_secret,
                    scope=self.scope)
               
                #print("Login token:  %s", self.token)
                #print(self.client_id, client_secret)
                self.sess['client_id'] = client_id
                self.sess['client_secret'] = client_secret
                self.sess['ouath_token'] = self.token
                self.writeSession(self.sess)

            except Exception as e:
                print("Exception in login: %s", e)
                self.logger.error('Login() error: %s', e)
                self.api_connection_state = False
                return -1
        # Validate that token contain, access_token, refresh_token
        #for k, v in self.token:

        self.api_connection_state = True
        return 1  # Add exception control and return login status with error message if present

    def getitems(self): # Result is a combination of items, item status and item category in a json list
        """
                Returns
                -------
                JSON
                data returned is directly fetched from Viima /items endpoint without filtering
        """
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        #auto_refresh_url=self.authorization_url,
                                        token_updater=self.token_updater)

            #print(self.client)
            items = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/items/').json()
        except Exception as e:
            print(e)
            self.logger.error('getitems() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return items

    def getitems_flattened(self): # Result is a combination of items, item status and item category in a json list
        """
                Returns
                -------
                JSON
                data returned is directly fetched from Viima /items endpoint enriched with status per item fetched
                from Viima /status endpoint
        """
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

        # Not efficient doing these API calls for every call to /items
            items_dict = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/items/').json()
            statuses = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/statuses/').json()
        except Exception as e:
            print(e)
            self.logger.error('getitems_flattened() error: {}'.format(e))
            self.api_connection_state = False
            return -1

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

        return response_items

    def getitem(self, item_id):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Get JSON of specific Viima Idea
            item = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/items/' + str(item_id)).json()
        except Exception as e:
            print(e)
            self.logger.error('getitem() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return item

    def createitem(self, name, emailaddress, itemname, itemdescr, **kwargs):
        self.logger.debug('Creator: %s  Email: %s  Item name: %s  Item Description: %s  kwargs %s',
                          name,
                          emailaddress,
                          itemname,
                          itemdescr,
                          kwargs)
        try:
            item_data = {
                'name': itemname,
                'status': str(16911),  # This need to configurable asd it relate fo board 3730´s specific status config
                'description': 'Idea creator: ' + name + '\n' + 'Creator email: ' + emailaddress + '\n\n' + itemdescr}
            headers = {'Content-type': 'application/json', 'Accept': 'application/json'}

            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            response = self.client.post('https://app.viima.com/api/customers/' + self.customer_id + '/items/',
                                        data=json.dumps(item_data),
                                        headers=headers)

            self.logger.debug('do_item_create(add idea) - POST response status code: {}'.format(response.status_code))
            self.logger.debug('do_item_create(add idea) - POST response: {}'.format(response.json()))
            response_content_json = response.json()

            # ADD CUSTOM FIELD DATA FROM FORMs to Viima:
            for key, value in kwargs.items():
                if key == 'itemsolves':
                    # POST custom fields data from form - "What is the problem this idea solves?"
                    item_customfields_data = {'custom_field': "102", 'value': value}
                    item_id_customfield = response_content_json['id']
                    self.logger.debug(
                        'ITEMSOLVES: https://app.viima.com/api/customers/' + self.customer_id + '/items/' + str(item_id_customfield) + '/custom_field_values/')
                    self.logger.debug('Custom field data: {}  Id={}'.format(item_customfields_data, item_id_customfield))
                    response = self.client.post('https://app.viima.com/api/customers/' + self.customer_id + '/items/' +
                                                str(item_id_customfield) + '/custom_field_values/',
                                                data=json.dumps(item_customfields_data),
                                                headers=headers)
                    self.logger.debug('do_item_create(add custom) - POST response status code: {}'.format(response.status_code))
                    self.logger.debug('do_item_create(add custom) - POST response: %s', response.json())
                    # Handle this response
                    #response_content_json = response.json()
                if key == 'itemresults':
                    # POST custom fields data from form - "What result will it bring?"
                    item_customfields_data = {'custom_field': "103", 'value': value}
                    self.logger.debug(
                        'ITEMRESULTS: https://app.viima.com/api/customers/' + self.customer_id + '/items/' + str(
                            item_id_customfield) + '/custom_field_values/')
                    item_id_customfield = response_content_json['id']
                    self.logger.debug('Custom field data: {}  Id={}'.format(item_customfields_data, item_id_customfield))
                    response = self.client.post('https://app.viima.com/api/customers/' + self.customer_id + '/items/' +
                                                str(item_id_customfield) + '/custom_field_values/',
                                                data=json.dumps(item_customfields_data),
                                                headers=headers)
                    self.logger.debug(item_customfields_data)
                    self.logger.debug('do_item_create(add custom) - POST response status code: {}'.format(response.status_code))
                    self.logger.debug('do_item_create(add custom) - POST response: {}'.format(response.json()))
                    # Handle this response
                    #response_content_json = response.json()
        except Exception as e:
            self.logger.error("Oauth2 error:  {}".format(e))
            # raise
            return -1
        return 1

    def createstatus(self):
        pass

    def createcategory(self):
        pass

    def getcustomfields(self):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Get JSON of Viima statuses
            custom_fields = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/custom_fields/').json()
        except Exception as e:
            print(e)
            self.logger.error('getcustomfields() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return custom_fields

    def getstatuses(self):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Get JSON of Viima statuses
            statuses = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/statuses/').json()
        except Exception as e:
            print(e)
            self.logger.error('getstatuses() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return statuses

    def getcategories(self):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Get JSON of Viima categories
            categories = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/categories/').json()
        except Exception as e:
            print(e)
            self.logger.error('getcategories() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return categories

    def leaderboards(self, sort_key="points"):
        if sort_key == "points" or sort_key == "upvotes":
            local_sort_key = sort_key
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Get JSON of Viima leaderboards
            leaderboards = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/public_user_profiles/?sort_key=' + local_sort_key).json()
        except Exception as e:
            print(e)
            self.logger.error('leaderboards() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return leaderboards

    # Base utility functions for for doing custom or non non-existing wrapper methods
    def get(self, url, **kwargs):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)
            # Do a HTTP GET using Oauth2 access_token with same flexibility as requests_oauthlib GET emthod
            response = self.client.get(url, **kwargs)
        except Exception as e:
            print(e)
            self.logger.error('get() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return response

    def post(self, url, data, json, **kwargs):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Do a HTTP GET using Oauth2 access_token with same flexibility as requests_oauthlib GET emthod
            response = self.client.post(url, data, json, **kwargs)
        except Exception as e:
            print(e)
            self.logger.error('post() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return response

    def delete(self, url, **kwargs):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Do a HTTP GET using Oauth2 access_token with same flexibility as requests_oauthlib GET emthod
            response = self.client.delete(url, **kwargs)
        except Exception as e:
            print(e)
            self.logger.error('delete() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return response

    def put(self, url, data, **kwargs):
        try:
            self.client = OAuth2Session(self.client_id,
                                        token=self.token,
                                        auto_refresh_kwargs=self.extras,
                                        token_updater=self.token_updater)

            # Do a HTTP GET using Oauth2 access_token with same flexibility as requests_oauthlib GET emthod
            response = self.client.put(url, data, **kwargs)
        except Exception as e:
            print(e)
            self.logger.error('put() error: {}'.format(e))
            self.api_connection_state = False
            return -1
        return response
