# Jessica Dutton
# Movies (DVD Store)


import google.oauth2.credentials
import google_auth_oauthlib.flow
from google.cloud import datastore
from flask import Flask, request, make_response, render_template, redirect, jsonify
from urllib.parse import urlparse, unquote
import random
import requests 
import json
import dvd
import customer
import store_manager

app = Flask(__name__)
app.register_blueprint(dvd.bp)
app.register_blueprint(customer.bp)
app.register_blueprint(store_manager.bp)


# Use the client_secret.json file to identify the application requesting
# authorization. The client ID (from that file) and access scopes are required.
flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
    'client_secret.json',
    scopes=['https://www.googleapis.com/auth/userinfo.profile'])


#flow.redirect_uri = 'http://localhost:8080/'
flow.redirect_uri = 'https://fluent-radar-352505.uw.r.appspot.com/'

# Generate URL for request to Google's OAuth 2.0 server.
# Use kwargs to set optional request parameters.
authorization_url, state = flow.authorization_url(
    # Enable offline access so that you can refresh an access token without
    # re-prompting the user for permission. Recommended for web server apps.
    access_type='offline',
    # Enable incremental authorization. Recommended as a best practice.
    include_granted_scopes='true')


@app.route('/')
def index():
    authorization_response = request.url
    if authorization_response == 'http://localhost:8080/' or authorization_response == 'https://fluent-radar-352505.uw.r.appspot.com/':
        return render_template('index.html')
    else: 
        # directed from oath
        data = oath(authorization_response)
        return render_template('info.html', data = data)


@app.route('/oath/', methods=['GET'])
def get_auth():
    if  request.method == 'GET':
        return redirect(authorization_url)

    else:
        return 'Method not recognized' 

def oath(authorization_response):
        # verify state matches the state that was sent
        parsed =urlparse(authorization_response)
        # parse response for code
        i = 0
        code = ""
        while i < (len(parsed.query) - 1) and parsed.query[i] != '&':
            i += 1
        i += 6

        while i < (len(parsed.query) - 1) and parsed.query[i] != '&':
            code = code + parsed.query[i]
            i+=1

        decoded = unquote(code)
 
        data = {'code': decoded,
        'client_id':'omitted',
        'client_secret': 'omitted' ,
        'redirect_uri': 'https://fluent-radar-352505.uw.r.appspot.com/',  
        #'redirect_uri': 'http://localhost:8080/',
        'grant_type' : 'authorization_code'
        }
     
        # use access code to make post request
        
        access_token = requests.post('https://oauth2.googleapis.com/token', data=data)
        if access_token:
            jsoncontent = json.loads(access_token.content)

            token = jsoncontent['access_token']
            jwt = jsoncontent['id_token']
            
            auth = "Bearer "+ token
            headers = {'Authorization': auth}

            # use access token to get user info 
            r = requests.get('https://people.googleapis.com/v1/people/me?personFields=names', headers = headers)
 
            jsoncontent = r.json()
            
            firstName = jsoncontent['names'][0]['givenName']
            lastName = jsoncontent['names'][0]['familyName']
           
            data = [firstName, lastName, jwt]
        
            return data
        else:
            return


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8080, debug=True)


