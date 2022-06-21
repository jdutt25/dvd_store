'''
Jessica Dutton
Store Manager (user entity)
'''


from google.cloud import datastore
from flask import Blueprint, Flask, request, make_response
import json
import constants
from google.oauth2 import id_token
from google.auth.transport import requests

client = datastore.Client()
bp = Blueprint('store_manager', __name__, url_prefix='/store_managers')

@bp.route('', methods=['GET'])
def store_managers_get():
    if  request.method == 'GET':
        store_managers = []
        if 'application/json' not in request.accept_mimetypes:
                response = {"Error": "Response type must be JSON"}
                res = make_response(response)
                res.mimetype = 'application/json'
                res.status_code = 406
                return res

        # get the dvds
        query = client.query(kind=constants.dvds)
        results = list(query.fetch())
        for dvd in results:
            if dvd['store_manager'] not in store_managers:
                store_managers.append(dvd['store_manager'])
        if len(store_managers) != 0:
            response = {"List of store manager IDs": store_managers}
        else:
            response = {"Results" : "No store managers currently registered in app"}
        return (response, 200)
 
    else:
        return 'Method not recognized'