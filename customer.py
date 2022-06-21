'''
Jessica Dutton
Customers (Non-user entity)
'''


from google.cloud import datastore
from flask import Blueprint, Flask, request, make_response
import json
import constants
from google.oauth2 import id_token
from google.auth.transport import requests
import dvd as dvd_bp

client = datastore.Client()
bp = Blueprint('customer', __name__, url_prefix='/customers')

@bp.route('', methods=['PUT', 'DELETE'])
def customers_invalid():
    if  request.method == 'PUT':
        response = {"Error": "Cannot apply PUT to all Customers"}
        res = make_response(response)
        res.status_code = 405
        return res
    elif  request.method == 'DELETE':
        response = {"Error": "Cannot apply DELETE to all Customers"}
        res = make_response(response)
        res.status_code = 405
        return res

    else:
        return 'Method not recognized'


@bp.route('', methods=['POST'])
def customers_post():
    if request.method == 'POST':
        content = request.get_json()
        new_customer = datastore.entity.Entity(key=client.key(constants.customers))
        # set response type
        if 'application/json' in request.accept_mimetypes:
            if "name" not in content or "member" not in content or "birth_month" not in content:
                # required attribute missing
               response = {"Error": "The request object is missing at least one of the required attributes"}
               return (response, 400)
            else:
                new_customer.update({"name": content["name"], "member": content["member"],
                "birth_month": content["birth_month"], "rentals": []})
                client.put(new_customer)
                response = {"id" : str(new_customer.id), 
                "name" : new_customer["name"], 
                "rentals" : new_customer["rentals"], 
                "member" : new_customer["member"], 
                "birth_month" : new_customer["birth_month"], 
                "self" : request.url_root + "customers/" + str(new_customer.id) } 
                res = make_response(response)
                res.mimetype = 'application/json'
                res.headers['location'] = request.url_root + "customers/" + str(new_customer.id)
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
def customers_get():
    if request.method == 'GET':
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        else:
            query = client.query(kind=constants.customers)
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
                val["id"] = val.key.id
            output = {"customers": results}
            if next_url:
                output["next"] = next_url
            return json.dumps(output)
    else:
        return 'Method not recognized'

@bp.route('/<id>', methods=['GET'])
def customer_get(id):
    if request.method == 'GET':
        customer_key = client.key(constants.customers, int(id))
        customer = client.get(key=customer_key)
        if json.dumps(customer) == 'null':
            response = {"Error": "No Customer with this customer_id exists"}
            res = make_response(response)
            res.status_code = 404
            return res
      
        if 'application/json' in request.accept_mimetypes:
            response = {"id" : str(customer.id), 
                "name" : customer["name"], 
                "rentals" : customer["rentals"], 
                "member" : customer["member"], 
                "birth_month" : customer["birth_month"],
                "self" : request.url_root + "customer/" + str(customer.id)}
            res = make_response(response)
            res.status_code = 200
            return res
            
        else:
            response = {"Error": "Accept header type must be application/json"}
            res = make_response(response)
            res.status_code = 406
            return res
    
    else:
        return 'Method not recognized'


@bp.route('/<id>', methods=['PUT'])
def customers_put(id):
    if request.method == 'PUT':
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
       
        else:
            content = request.get_json()
            customer_key = client.key(constants.customers, int(id))
            customer = client.get(key=customer_key)
            if json.dumps(customer) == 'null':
                response = {"Error": "No Customer with this customer_id exists"}
                return (response, 404)
                 
            elif "name" not in content or "member" not in content or "rentals" not in content or "birth_month" not in content:
                    # required attribute missing
                response = {"Error": "The request object is missing at least one of the required attributes"}
                return (response, 400)
            elif content["rentals"] != customer["rentals"]:
                response = {"Error": "Cannot rent or return DVDs at this URL."}
                return (response, 403)
            
            else:
                customer.update({"name": content["name"], "member": content["member"],
                "rentals": content["rentals"], "birth_month": content["birth_month"]})
                client.put(customer)
                response = {"id" : str(customer.id), 
                    "name" : customer["name"], 
                    "member" : customer["member"],
                    "rentals" : customer["rentals"], 
                    "birth_month" : customer["birth_month"],
                    "self" : request.url_root + "customers/" + str(customer.id)}
                res = make_response(response)
                res.mimetype = 'application/json'
                res.headers['location'] = request.url_root + "customers/" + str(customer.id)
                res.status_code = 201
                return res           
    else:
        return 'Method not recognized'


@bp.route('/<id>', methods=['PATCH'])
def customer_patch(id):
    #booleans for updates
    update_name = False
    update_member = False
    update_birth_month = False

    if request.method == 'PATCH':
        if 'application/json' not in request.accept_mimetypes:
            response = {"Error": "Response type must be JSON"}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.status_code = 406
            return res
        else: 
            content = request.get_json()
            customer_key = client.key(constants.customers, int(id))
            customer = client.get(key=customer_key)
            if json.dumps(customer) == 'null':
                response = {"Error": "No Customer with this customer_id exists"}
                return (response, 404)
            elif "name" not in content and "member" not in content and "rentals" not in content and \
            "birth_month" not in content:
                # required attribute missing
                response = {"Error": "The request object is missing at least one attribute to PATCH"}
                return (response, 400)

            elif "rentals" in content and content["rentals"] != customer["rentals"]:
                response = {"Error": "Cannot rent or return DVDs at this URL."}
                return (response, 403)
      
            if "name" in content:
                update_name = True

            if "member" in content:
                update_member = True

            if "birth_month" in content:
                update_birth_month = True                  
       
            # make updates 
            if update_name: 
                customer.update({"name" : content["name"]})

            if update_member: 
                customer.update({"member" : content["member"]})

            if update_birth_month: 
                customer.update({"birth_month" : content["birth_month"]})
     
            client.put(customer)

            response = response = {"id" : str(customer.id), 
                                "name" : customer["name"], 
                                "rentals" : customer["rentals"],
                                "member" : customer["member"], 
                                "birth_month" : customer["birth_month"],
                                "self" : request.url_root + "customers/" + str(customer.id)}
            res = make_response(response)
            res.mimetype = 'application/json'
            res.headers['location'] = request.url_root + "customers/" + str(customer.id)
            res.status_code = 200
            return res

    else:
        return 'Method not recognized'



@bp.route('/<id>', methods=['DELETE'])
def customers_delete(id):
    if request.method == 'DELETE':
        customer_key = client.key(constants.customers, int(id))
        customer = client.get(key=customer_key)
        if json.dumps(customer) == 'null':
            response = {"Error": "No Customer with this customer_id exists"}
            return (response, 404)
        else:
            if "rentals" in customer and customer["rentals"] != []:
                # return all dvds customer has rented
                for rental in customer["rentals"]:
                    return_dvd(id, rental)
            client.delete(customer_key)
            return ('',204)
    else:
        return 'Method not recognized'

@bp.route('/<cid>/dvds/<did>', methods=['PUT'])
def rent_dvd(cid,did):
    if request.method == 'PUT':
        customer_key = client.key(constants.customers, int(cid))
        customer = client.get(key=customer_key)
        dvd_key = client.key(constants.dvds, int(did))
        dvd = client.get(key=dvd_key)
        if dvd != 'null' and 'authorization' in request.headers:
            auth = request.headers['authorization']
            jwt = auth[7:]
            if json.dumps(customer) == 'null' or json.dumps(dvd) == 'null':
                    response = {"Error": "This DVD and/or this customer does not exist"}
                    return (response, 404)

            elif dvd_bp.valid_jwt(jwt) is not False and dvd['store_manager'] == dvd_bp.valid_jwt(jwt):
                 # JWT is valid and store manager

                # check whether DVD is available to rent
                if 'renter' in dvd.keys() and dvd["renter"] != None:
                   #DVD rented, error
                   response = {"Error": "The DVD is not available to rent"}
                   return (response, 403)
       
                # update customer
                curr_rentals = customer['rentals']
                curr_rentals.append(dvd.id)
                customer['rentals'] = curr_rentals
  
                # update dvd
                dvd['renter'] = customer
     
                client.put(customer)
                client.put(dvd)
                return('',204)
            else:
                response = "You must be a valid store manager to rent DVDs"
                return (response, 401)
        else: 
            response = "You must be a valid store manager to rent DVDs"
            return (response, 401)
    else:
        return 'Method not recognized'

@bp.route('/<cid>/dvds/<did>', methods=['DELETE'])
def return_dvd(cid, did):
    if request.method == 'DELETE':
        customer_key = client.key(constants.customers, int(cid))
        customer = client.get(key=customer_key)
        dvd_key = client.key(constants.dvds, int(did))
        dvd = client.get(key=dvd_key)
        if 'authorization' in request.headers:
            auth = request.headers['authorization']
            jwt = auth[7:]
            if dvd_bp.valid_jwt(jwt) is not False and dvd['store_manager'] == dvd_bp.valid_jwt(jwt):
                 # JWT is valid and store manager

                # confirm dvd and customer are not null
                if json.dumps(customer) == 'null' or json.dumps(dvd) == 'null':
                    response = {"Error": "This DVD and/or this customer does not exist"}
                    return (response, 404)
                # check whether DVD is rented to customer
      
                if 'renter' in dvd and dvd["renter"].id == int(cid):
                   #dvd rented to customer, remove
                   customer["rentals"].remove(int(did))
                    # update DVD
                   dvd["renter"] = None
                   client.put(customer)
                   client.put(dvd)
                   return('',204)
                else:
                    response = {"Error": "No DVD with this dvd_id is rented to a customer with this customer id"}
                    return (response, 404)
            else:
                response = "You must be a valid store manager to return DVDs"
                return (response, 401)
        else: 
            response = "You must be a valid store manager to rent DVDs"
            return (response, 401)
    else:
        return 'Method not recognized'
