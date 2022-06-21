'''
Jessica Dutton
DVDs (non-user protected entity)
'''


from google.cloud import datastore
from flask import Blueprint, Flask, request, make_response
import json
import constants
from google.oauth2 import id_token
from google.auth.transport import requests

client = datastore.Client()
bp = Blueprint('dvd', __name__, url_prefix='/dvds')

def valid_jwt(token):
    try:
        # Specify the CLIENT_ID of the app that accesses the backend:
        idinfo =  id_token.verify_oauth2_token(token, requests.Request(), 
       "81078508106-b0l94hn4php7ll5dlnucm5ln0t75pl3b.apps.googleusercontent.com")

        # ID token is valid. Get the user's Google Account ID from the decoded token.
        userid = idinfo['sub']
        return userid
    except ValueError:
        # Invalid token
        return False

@bp.route('', methods=['PUT', 'DELETE'])
def dvds_invalid():
    if  request.method == 'PUT':
        response = {"Error": "Cannot apply PUT to all DVDs"}
        res = make_response(response)
        res.status_code = 405
        return res
    elif  request.method == 'DELETE':
        response = {"Error": "Cannot apply DELETE to all DVDs"}
        res = make_response(response)
        res.status_code = 405
        return res

    else:
        return 'Method not recognized'


@bp.route('', methods=['POST'])
def dvds_post():
    if request.method == 'POST':
        content = request.get_json()
        new_dvd = datastore.entity.Entity(key=client.key(constants.dvds))
        # set response type

        if 'application/json' in request.accept_mimetypes:
            if "name" not in content or "genre" not in content or "length" not in content:
                # required attribute missing
               response = {"Error": "The request object is missing at least one of the required attributes"}
               return (response, 400)

            elif 'authorization' not in request.headers:
                response = {"Error": "The JWT is missing"}
                return (response, 401)

            else: 
                auth = request.headers['authorization']
                jwt = auth[7:]
                if valid_jwt(jwt) is False:
                    response = {"Error": "The JWT is not valid"}
                    return (response, 401)

                else:
                    store_manager = valid_jwt(jwt) # user
                    new_dvd.update({"name": content["name"], "genre": content["genre"],
                    "length": content["length"], "renter": None, 
                    "store_manager": store_manager})
                    client.put(new_dvd)
                    response = {"id" : str(new_dvd.id), 
                    "name" : new_dvd["name"], 
                    "length" : new_dvd["length"], 
                    "genre" : new_dvd["genre"],  
                    "renter": new_dvd["renter"],
                    "store_manager": new_dvd["store_manager"],
                    "self" : request.url_root + "dvds/" + str(new_dvd.id) } 
                    res = make_response(response)
                    res.mimetype = 'application/json'
                    res.headers['location'] = request.url_root + "dvds/" + str(new_dvd.id)
                    res.status_code = 201
                    return res          
        else:
 
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
            
    else:
        return 'Method not recognized'

@bp.route('', methods=['GET'])              
def dvds_get():
    if request.method == 'GET':
        dvd_arr = []
        jwt = ''
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        if 'authorization' in request.headers:
            auth = request.headers['authorization']
            jwt = auth[7:]
            if valid_jwt(jwt) is not False:
                 # JWT is valid
                store_manager = valid_jwt(jwt)   
                query = client.query(kind=constants.dvds)
                q_limit = int(request.args.get('limit', '5'))
                q_offset = int(request.args.get('offset', '0'))
                l_iterator = query.fetch(limit= q_limit, offset=q_offset)
                pages = l_iterator.pages
                results = list(next(pages))
                if l_iterator.next_page_token:
                    next_offset = q_offset + q_limit
                    next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)
                else:
                    next_url = None
                
                for val in results:
                    if val['store_manager'] == store_manager:
                        val["id"] = val.key.id
                        dvd_arr.append(val)
                output = {"dvds": dvd_arr}
                if next_url:
                    output["next"] = next_url
                return json.dumps(output)
            else:
                response = "You must be a valid store manager to view DVDs"
                return (response, 401)
        else: 
            response = "You must be a valid store manager to view DVDs"
            return (response, 401)

    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['GET'])
def dvd_get(id):
    if request.method == 'GET':
        dvd_key = client.key(constants.dvds, int(id))
        dvd = client.get(key=dvd_key)
        if json.dumps(dvd) == 'null':
            response = {"Error": "No DVD with this dvd_id exists"}
            res = make_response(response)
            res.status_code = 404
            return res
      
        if 'application/json' in request.accept_mimetypes:
            auth = request.headers['authorization']
            jwt = auth[7:]
            if valid_jwt(jwt) is not False:
                 # JWT is valid
                 if valid_jwt(jwt) == dvd["store_manager"]:
                    response = {"id" : str(dvd.id), 
                        "name" : dvd["name"], 
                        "length" : dvd["length"], 
                        "genre" : dvd["genre"], 
                        "renter" : dvd["renter"],
                        "store_manager": dvd["store_manager"],
                        "self" : request.url_root + "dvds/" + str(dvd.id)}
                    res = make_response(response)
                    res.status_code = 200
                    return res
                 else:
                    response = '"Error":  "You must be a valid store manager to view this DVD.'
                    res = make_response(response)
                    res.status_code = 401
                    return res
            else:
                response = '"Error":  "You must be a valid store manager to view this DVD.'
                res = make_response(response)
                res.status_code = 401
                return res
     
        else:
            response = {"Error": "Accept header type must be application/json"}
            res = make_response(response)
            res.status_code = 406
            return res
    
    else:
        return 'Method not recognized'


@bp.route('/<id>', methods=['PUT'])
def dvds_put(id):
    if request.method == 'PUT':
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
       
        else:
            auth = request.headers['authorization']
            jwt = auth[7:]
            content = request.get_json()
            dvd_key = client.key(constants.dvds, int(id))
            dvd = client.get(key=dvd_key)
            if json.dumps(dvd) == 'null':
                response = {"Error": "No DVD with this dvd_id exists"}
                return (response, 404)
            elif valid_jwt(jwt) is False or valid_jwt(jwt) != dvd["store_manager"]:
                response = '"Error":  "You must be a valid store manager to update this DVD.'
                res = make_response(response)
                res.status_code = 401
                return res
                 
            elif "name" not in content or "genre" not in content or "length" not in content or "renter" not in content:
                    # required attribute missing
                response = {"Error": "The request object is missing at least one of the required attributes"}
                return (response, 400)
            else:
                dvd.update({"name": content["name"], "genre": content["genre"],
                "length": content["length"], "renter": content["renter"],
                "store_manager": valid_jwt(jwt)})
                client.put(dvd)
                response = {"id" : str(dvd.id), 
                    "name" : dvd["name"], 
                    "length" : dvd["length"],
                    "genre" : dvd["genre"], 
                    "renter": dvd["renter"],
                    "store_manager": dvd["store_manager"],
                    "self" : request.url_root + "dvds/" + str(dvd.id)}
                res = make_response(response)
                res.mimetype = 'application/json'
                res.headers['location'] = request.url_root + "dvds/" + str(dvd.id)
                res.status_code = 201
                return res           
    else:
        return 'Method not recognized'


@bp.route('/<id>', methods=['PATCH'])
def dvds_patch(id):
    #booleans for updates
    update_name = False
    update_genre = False
    update_length = False
    update_renter = False

    if request.method == 'PATCH':
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        else: 
            auth = request.headers['authorization']
            jwt = auth[7:]
            content = request.get_json()
            dvd_key = client.key(constants.dvds, int(id))
            dvd = client.get(key=dvd_key)
            if json.dumps(dvd) == 'null':
                response = {"Error": "No DVD with this dvd_id exists"}
                return (response, 404)
            elif valid_jwt(jwt) is False or valid_jwt(jwt) != dvd["store_manager"]:
                response = {"Error":  "You must be a valid store manager to update this DVD."}
                res = make_response(response)
                res.status_code = 401
                return res
            elif "name" not in content and "genre" not in content and "length" not in content and \
             "renter" not in content:
                # required attribute missing
                response = {"Error": "The request object is missing at least one attribute to PATCH"}
                return (response, 400)
      
            if "name" in content:
                update_name = True

            if "genre" in content:
                update_genre = True

            if "length" in content:
                update_length = True

            if "renter" in content:
                update_renter = True                  
       
            # make updates 
            if update_name: 
                dvd.update({"name" : content["name"]})

            if update_genre: 
                dvd.update({"genre" : content["genre"]})

            if update_length: 
                dvd.update({"length" : content["length"]})

            if update_renter: 
                dvd.update({"renter" : content["renter"]})
     
            client.put(dvd)
            response = response = {"id" : str(dvd.id), 
                                "name" : dvd["name"], 
                                "length" : dvd["length"],
                                "genre" : dvd["genre"], 
                                "renter": dvd["renter"],
                                "store_manager": dvd["store_manager"],
                                "self" : request.url_root + "dvds/" + str(dvd.id)}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.headers['location'] = request.url_root + "dvds/" + str(dvd.id)
            res.status_code = 200
            return res

    else:
        return 'Method not recognized'



@bp.route('/<id>', methods=['DELETE'])
def dvds_delete(id):
    if request.method == 'DELETE':
        auth = request.headers['authorization']
        jwt = auth[7:]
        dvd_key = client.key(constants.dvds, int(id))
        dvd = client.get(key=dvd_key)
        if json.dumps(dvd) == 'null':
            response = {"Error": "No DVD with this dvd_id exists"}
            return (response, 404)
        elif valid_jwt(jwt) is False or valid_jwt(jwt) != dvd["store_manager"]:
            response = '"Error":  "You must be a valid store manager to update this DVD.'
            res = make_response(response)
            res.status_code = 401
            return res
        else:
            if dvd["renter"] != None:
                # DVD must be returned in order to delete
                cid = int(dvd["renter"].id)
                customer_key = client.key(constants.customers, int(cid))
                customer= client.get(key=customer_key)
                customer_bp.return_dvd(dvd["renter"].id, int(id))

            client.delete(dvd_key)
            return ('',204)
    else:
        return 'Method not recognized'

