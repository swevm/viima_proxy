from oauthlib.oauth2 import LegacyApplicationClient
from requests_oauthlib import OAuth2Session
import json
import logging


class Viimawrapper: # I wonder if this inheritance will work??
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

        # Create Oauth2Session - perhaps have these utility functions in a separate method instead of __init__
        # I wondr if this really work defining the session here. What is the difference between client=LegacyApplicationClient and just passing in client_id as done in get, post etc????
        self.viimaAppClient = None

        self.api_connection_state = False  # True if class har working connection to Viima API
        self.logger = logging.getLogger('Viima Proxy')  # Get degined logging facility

    def connect(self, username, password):
        pass

    def isconnected(self):
        """
                Returns
                -------
                Boolean - True for connected to Viima API otherwise false
        """
        return self.api_connection_state

    def token_updater(self, token):
        self.logger.debug('Access token updated. Old = %s ', self.token['access_token'])
        self.token = token
        self.logger.debug('Access token updated. New = %s ', self.token['access_token'])

    def refresh(self): # Method refreshes cached data, such as Categories, Statuses, Items(think about if its worth caching this data????)
        pass

    def get_token(self):
        if self.isconnected():
            return self.token
        else:
            return False

    def login(self, username, password, client_id, client_secret, **kwargs):  # BUG: **kwargs seem not to work here as expected. Why?
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
            print("Login token:  %s", self.token)
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
            self.logger.error('getitems() error: %s', e)
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
            self.logger.error('getitems_flattened() error: %s', e)
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
            self.logger.error('getitem() error: %s', e)
            self.api_connection_state = False
            return -1
        return item

    def createitem(self):
        pass

    def createstatus(self):
        pass

    def createcategory(self):
        pass

    def getcustomfields(self):
        pass
        # return a list of name tied to a unique id used in createitem to populate  custom_fields

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
            self.logger.error('getstatuses() error: %s', e)
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
            self.logger.error('getcategories() error: %s', e)
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
            leaderboards = self.client.get('https://app.viima.com/api/customers/' + self.customer_id + '/leaderboards/?sort_key=' + local_sort_key).json()
        except Exception as e:
            print(e)
            self.logger.error('leaderboards() error: %s', e)
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
            self.logger.error('get() error: %s', e)
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
            self.logger.error('post() error: %s', e)
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
            self.logger.error('delete() error: %s', e)
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
            self.logger.error('put() error: %s', e)
            self.api_connection_state = False
            return -1
        return response
