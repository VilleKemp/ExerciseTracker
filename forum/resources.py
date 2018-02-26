# -*- coding: cp1252 -*-
"""
Group17 
"""

import json

from flask import Flask, request, Response, g, _request_ctx_stack, redirect, send_from_directory
from flask_restful import Resource, Api, abort
from werkzeug.exceptions import HTTPException, NotFound


from utils import RegexConverter
import database

#Constants for hypermedia formats and profiles
MASON = "application/vnd.mason+json"
JSON = "application/json"

FORUM_USER_PROFILE = "/profiles/user-profile/"
FORUM_MESSAGE_PROFILE = "/profiles/message-profile/"
ERROR_PROFILE = "/profiles/error-profile"

ATOM_THREAD_PROFILE = "https://tools.ietf.org/html/rfc4685"

# Fill these in
APIARY_PROFILES_URL = "STUDENT_APIARY_PROJECT/reference/profiles/"
APIARY_RELS_URL = "STUDENT_APIARY_PROJECT/reference/link-relations/"

USER_SCHEMA_URL = "/forum/schema/user/"
PRIVATE_PROFILE_SCHEMA_URL = "/forum/schema/private-profile/"
LINK_RELATIONS_URL = "/forum/link-relations/"

#Define the application and the api
app = Flask(__name__, static_folder="static", static_url_path="/.")
app.debug = True
# Set the database Engine. In order to modify the database file (e.g. for
# testing) provide the database path   app.config to modify the
#database to be used (for instance for testing)
app.config.update({"Engine": database.Engine()})
#Start the RESTful API.
api = Api(app)

# These two classes below are how we make producing the resource representation
# JSON documents manageable and resilient to errors. As noted, our mediatype is
# Mason. Similar solutions can easily be implemented for other mediatypes.

class MasonObject(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.
    """

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.

        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.

        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.

        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.

        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md

        : param str ctrl_name: name of the control (including namespace if any)        
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs

class ForumObject(MasonObject):    
    """
    A convenience subclass of MasonObject that defines a bunch of shorthand 
    methods for inserting application specific objects into the document. This
    class is particularly useful for adding control objects that are largely
    context independent, and defining them in the resource methods would add a 
    lot of noise to our code - not to mention making inconsistencies much more
    likely!

    In the forum code this object should always be used for root document as 
    well as any items in a collection type resource. 
    """

    def __init__(self, **kwargs):
        """
        Calls dictionary init method with any received keyword arguments. Adds
        the controls key afterwards because hypermedia without controls is not 
        hypermedia. 
        """

        super(ForumObject, self).__init__(**kwargs)
        self["@controls"] = {}



    ###OWN STUFF
##user controls ###################################################
    def add_control_get_user_information(self,username):
        """
        Adds "get user information" control to an object
        """

        self["@controls"]["get user information"] = {
            "title": "get user information",
            "href": api.url_for(User, username=username),
            "encoding": "json",
            "method": "GET",           
        }
        
    def add_control_delete_user(self,username):
        """
        Adds "delete user information" control to an object
        """

        self["@controls"]["delete user information"] = {
            "title": "delete user",
            "href": api.url_for(User,username=username),
            "encoding": "json",
            "method": "DELETE",
        }          
        


    def add_control_modify_user(self,username):
        """
        Adds "modify" control to an object
        """

        self["@controls"]["modify user"] = {
            "title": "modify user",
            "href": api.url_for(User, username=username),
            "encoding": "json",
            "method": "PUT",
            "schemaUrl":"exercisetracker/schema/user/"
            
        }

#exercises controls  #cant use until exercise endpoints are done
    def add_control_list_exercises(self):
        """
        Adds "list exercises" control to an object
        """

        self["@controls"]["list exercises"] = {
            "title": "list exercises",
            "href": api.url_for(Exercises),
            "encoding": "json",
            "method": "GET"
            
        }
#exercise controls #cant use until exercise endpoints are done
    def add_control_get_exercise(self):
        """
        Adds "get exercise" control to an object
        """

        self["@controls"]["get exercise"] = {
            "title": "get exercise",
            "href": api.url_for(Exercise),
            "encoding": "json",
            "method": "GET"
            
        }
    def add_control_remove_exercise(self):
        """
        Adds "remove exercise" control to an object
        """

        self["@controls"]["remove exercise"] = {
            "title": "remove exercise",
            "href": api.url_for(Exercise),
            "encoding": "json",
            "method": "DELETE"
            
        }
    def add_control_modify_exercise(self):
        """
        Adds "modify exercise" control to an object
        """

        self["@controls"]["modify exercise"] = {
            "title": "modify exercise information",
            "href": "/exercisetracker/api/exercises/<exerciseid>",
            "encoding": "json",
            "method": "PUT",
            "schemaUrl": "/exercisetracker/schema/exercise/" 
        }


#users controls
    def add_control_list_users(self):
        """
        Adds "list users" control to an object
        """

        self["@controls"]["list users"] = {
            "title": "list users",
            "href": api.url_for(Users),
            "encoding": "json",
            "method": "GET"
            
        }

    def add_control_add_user(self):
        """
        Adds "add user" control to an object
        """

        self["@controls"]["add user"] = {
            "title": "add user",
            "href": api.url_for(Users),
            "encoding": "json",
            "method": "POST",
            "schemaUrl":USER_SCHEMA_URL
            
        }
        
        

    ###END OF OWN STUFF#############################################################################
       

#ERROR HANDLERS

def create_error_response(status_code, title, message=None):
    """ 
    Creates a: py: class:`flask.Response` instance when sending back an
    HTTP error response

    : param integer status_code: The HTTP status code of the response
    : param str title: A short description of the problem
    : param message: A long description of the problem
    : rtype:: py: class:`flask.Response`
    """

    resource_url = None
    #We need to access the context in order to access the request.path
    ctx = _request_ctx_stack.top
    if ctx is not None:
        resource_url = request.path
    envelope = MasonObject(resource_url=resource_url)
    envelope.add_error(title, message)

    return Response(json.dumps(envelope), status_code, mimetype=MASON+";"+ERROR_PROFILE)

@app.errorhandler(404)
def resource_not_found(error):
    return create_error_response(404, "Resource not found",
                                 "This resource url does not exit")

@app.errorhandler(400)
def resource_not_found(error):
    return create_error_response(400, "Malformed input format",
                                 "The format of the input is incorrect")

@app.errorhandler(500)
def unknown_error(error):
    return create_error_response(500, "Error",
                    "The system has failed. Please, contact the administrator")

@app.before_request
def connect_db():
    """
    Creates a database connection before the request is proccessed.

    The connection is stored in the application context variable flask.g .
    Hence it is accessible from the request object.
    """

    g.con = app.config["Engine"].connect()

#HOOKS
@app.teardown_request
def close_connection(exc):
    """ 
    Closes the database connection
    Check if the connection is created. It migth be exception appear before
    the connection is created.
    """

    if hasattr(g, "con"):
        g.con.close()



####################################################################
class Users(Resource):
    """
    Users resource
    """

    def get(self):
        """
        Gets a list of all the users in the database.

        Returns 404 if users don't exist. Otherwise returns 200


        """
        #PERFORM OPERATIONS
        #Create the users list
        users_db = g.con.get_users()
        if not users_db:
            return create_error_response(404, "No users")

        #FILTER AND GENERATE THE RESPONSE
       #Create the envelope
        envelope = ForumObject()
        #add controls to response
        envelope.add_control("self", href=api.url_for(Users))
 
        envelope.add_control_add_user()
        #not yet implemented
        #envelope.add_control_list_exercises()

        

        
        items = envelope["items"] = []

        for user in users_db:
            item = ForumObject(
                username=user["username"],
                description = user["description"],
                avatar=user["avatar"],
                visibility=user["visibility"]
            )
            #add controls to each object in the list
            item.add_control("self", href=api.url_for(Users, username=user["username"]))
            #WIP
            #envelope.add_control_get_user_information(username)
            
  
            items.append(item)


        return Response(json.dumps(envelope), 200, mimetype=MASON+";")

    def post(self):
        """
        Adds a new user in the database.

        Returns 415 if request isn't JSON
        Returns 400 if data is missing
        Returns 200 and user information if succesful 

        """
        
        if JSON != request.headers.get("Content-Type", ""):
            abort(415)
        #PARSE THE REQUEST:
        request_body = request.get_json(force=True)

 

        if not request_body:
            return create_error_response(415, "Unsupported Media Type",
                                         "Use a JSON compatible format",
                                         )
        
        #Get the request body and serialize it to object
        #We should check that the format of the request body is correct. Check
        #That mandatory attributes are there.

        # pick up nickname so we can check for conflicts
        try:
            username = request_body["username"]

        except KeyError:
            return create_error_response(400, "Wrong request format", "Username was missing from the request")
        """
        #Conflict if user already exist
        if g.con.contains_user(username):
            return create_error_response(409, "Wrong username",
                                         "There is already a user with same"
                                         "username:%s." % username)
        """
        # pick up rest of the mandatory fields
        try:
            password = request_body["password"]
            avatar = request_body["avatar"]
            description = request_body["description"]
            visibility = request_body["visibility"]
        except KeyError:
            return create_error_response(402, "Wrong request format", "Be sure to include all mandatory properties")


        user = {"username": username, "password": password,
                "avatar": avatar, "description": description, "visibility": visibility}

        

        
        response = g.con.append_user(username, user)
        if (response == None):
            return create_error_response(415, "Data restriction failed, user already exists"
                                        )
        #Get user info
        userinfo=g.con.get_user(username)
        envelope = ForumObject(
                username=userinfo["username"],
                description = userinfo["description"],
                avatar=userinfo["avatar"],
                visibility=userinfo["visibility"]
            )
        #Controls
        envelope.add_control("self", href=api.url_for(User,username=username))       
        envelope.add_control_get_user_information(username)
                #not yet implemented
        #envelope.add_control_list_exercises()
                    #WIP
        #envelope.add_control_get_user_information(username)

        
        #CREATE RESPONSE AND RENDER
        return Response(json.dumps(envelope),status=200)

class User(Resource):
    """
    User Resource.
    """

    def get(self, username):
        """
        Possible bug. controls menee toiseksi argumentiksi vastaus viestis?
        """

        #PERFORM OPERATIONS

        user_db = g.con.get_user(username)
        if not user_db:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with name %s"
                                         % username)
        #FILTER AND GENERATE RESPONSE
        #Create the envelope:

        envelope = ForumObject(
                username=user_db["username"],
                description = user_db["description"],
                avatar=user_db["avatar"],
                visibility=user_db["visibility"]
            )

        #Controls
        envelope.add_control("self", href=api.url_for(User,username=username)) 
        envelope.add_control_modify_user(username)
        envelope.add_control_list_users()
        envelope.add_control_delete_user(username)
     
        #mahdollisesti turhia?
        #envelope.add_control_modify_exercise
        #envelope.add_control_remove_exercise
        #envelope.add_control_get_exercise

        return Response(json.dumps(envelope), 200, mimetype=MASON+";")
  

    def delete(self, username):
        """
        en toteuttanut linkkeja palatuksiin. Ne ovat KAI turhia eli ne on poistettava apiarysta
        """

        #PEROFRM OPERATIONS
        #Try to delete the user. If it could not be deleted, the database
        #returns None.
        if g.con.delete_user(username):
            #RENDER RESPONSE
            
            return '', 204
        else:
            #GENERATE ERROR RESPONSE
            return create_error_response(404, "Unknown user",
                                         "There is no a user with username %s"
                                         % username)
    def put(self,username):
        #check if exists?

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:
            username = request_body["username"]
            password = request_body["password"]
            avatar = request_body["avatar"]
            description = request_body["description"]
            visibility = request_body["visibility"]

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format")                                          
        else:
  
            if not g.con.modify_user(username,request_body ):
                return create_error_response(500, "Internal error",
                                         "User information for %s cannot be updated" % messageid
                                        )
        user_db = g.con.get_user(username)
        if not user_db:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with name %s"
                                         % username)
        #FILTER AND GENERATE RESPONSE
        #Create the envelope:

        envelope = ForumObject(
                username=user_db["username"],
                description = user_db["description"],
                avatar=user_db["avatar"],
                visibility=user_db["visibility"]
            )
        envelope.add_control("self", href=api.url_for(User,username=username)) 
        envelope.add_control_modify_user(username)
        envelope.add_control_list_users()
        envelope.add_control_delete_user(username)
        #exercise jutut

        return Response(json.dumps(envelope), 200, mimetype=MASON+";")       
         


class Friends(Resource):

    def get(self,username):
        """
        Get all of the users friends
        """
        friends = g.con.get_friends(username)
        
        if not friends:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with name %s"
                                         % username)
        #FILTER AND GENERATE RESPONSE
        #Create the envelope:
#Create the envelope
        envelope = ForumObject()
        #add controls to response
        envelope.add_control("self", href=api.url_for(Friends,username=username))
        envelope.add_control_list_users() 
        
        items = envelope["items"] = []

        for user in friends:
            username=g.con.get_username(user["friend_id"])
            item = ForumObject(
                username=username
                

            )
            item.add_control_get_user_information(username)
            #add controls to each object in the list
            item.add_control("self", href=api.url_for(Users, username=username))
            #WIP
            #envelope.add_control_get_user_information(username)
            
  
            items.append(item)
        

        return Response(json.dumps(envelope), 200, mimetype=MASON+";")


    def post(self,username):
        """
        """
        
        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        
        username = request_body["username"]
        friendname= request_body["friendname"]
        
      
        if g.con.add_friend(username,friendname) is not True:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with name %s"
                                         % username)
        

        return '',204

    def delete(self,username):
        """
        """
        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        
        username = request_body["username"]
        friendname= request_body["friendname"]

       
        if g.con.delete_friend(username,friendname) is not True:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with name %s"
                                         % username)
        

        return '',204
    

#######################################################################################


#Add the Regex Converter so we can use regex expressions when we define the
#routes
app.url_map.converters["regex"] = RegexConverter

####OWN
api.add_resource(Users, "/exercisetracker/api/users/",
                 endpoint="users")
api.add_resource(User, "/exercisetracker/api/users/<username>/",
                 endpoint="user")

api.add_resource(Friends,"/exercisetracker/api/users/<username>/friends",
                 endpoint="friends")
###
#TODO TONI
# sama ku ylempänä on tehty userille. Exercise add_controls funktiot ei toimi ennen tätä

api.add_resource(History, "/forum/api/users/<nickname>/history/",
                 endpoint="history")

#Redirect profile
@app.route("/profiles/<profile_name>")
def redirect_to_profile(profile_name):
    return redirect(APIARY_PROFILES_URL + profile_name)

@app.route("/forum/link-relations/<rel_name>/")
def redirect_to_rels(rel_name):
    return redirect(APIARY_RELS_URL + rel_name)

#Send our schema file(s)
@app.route("/forum/schema/<schema_name>/")
def send_json_schema(schema_name):
    return send_from_directory(app.static_folder, "schema/{}.json".format(schema_name))

#Start the application
#DATABASE SHOULD HAVE BEEN POPULATED PREVIOUSLY
if __name__ == "__main__":
    #Debug true activates automatic code reloading and improved error messages
    app.run(debug=True)
