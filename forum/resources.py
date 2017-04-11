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
FORUM_EXERCISE_PROFILE = "/profiles/exercise-profile/"
ERROR_PROFILE = "/profiles/error-profile"

ATOM_THREAD_PROFILE = "https://tools.ietf.org/html/rfc4685"

# Fill these in
APIARY_PROFILES_URL = "STUDENT_APIARY_PROJECT/reference/profiles/"
APIARY_RELS_URL = "STUDENT_APIARY_PROJECT/reference/link-relations/"

USER_SCHEMA_URL = "/forum/schema/user/"
EXERCISE_SCHEMA_URL = "/forum/schema/exercise/"
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

#TODO TONI
        #Näillä luodaan controlsseja vastaukseen. Kato users get malliksi miten käytetään. add_control_list_exercises luulisi toimivan suoraa
        #muista exercisen add_controlseista en tiedä. users ja user liittyviin add_controlseihin ei tarvii koskea vaikka ne ei toimis. korjaan ne asap
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
            "href": api.url_for(Exercise),
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
    def add_control_messages_all(self):
        """
        Adds the message-all link to an object. Intended for the document object.
        """

        self["@controls"]["forum:messages-all"] = {
            "href": api.url_for(Messages),
            "title": "All messages"
        }

    def add_control_users_all(self):
        """
        This adds the users-all link to an object. Intended for the document object.  
        """

        self["@controls"]["forum:users-all"] = {
            "href": api.url_for(Users),
            "title": "List users"
        }

    def add_control_add_exercise(self):
        """
        Adds "add exercise" control to an object
        """

        self["@controls"]["add exercise"] = {
            "title": "add exercise",
            "href": api.url_for(Exercises),
            "encoding": "json",
            "method": "POST",
            "schemaUrl":EXERCISE_SCHEMA_URL
            
        }

    def add_control_delete_exercise(self, exercise_id):
        """
        Own method
        Adds the delete control to an object. This is intended for any 
        object that represents a exercise.

        : param str msgid: exercise id in the msg-N form
        """
        self["@controls"]["forum:delete"] = {
            "href": api.url_for(Exercise, exercise_id=exercise_id),  
            "title": "Delete this exercise",
            "method": "DELETE"
        }

    def add_control_edit_exercise(self, exerid):
        """
        Own method
        Adds the edit control to a exercise object. For the schema we need
        the one that's intended for editing (it has editor instead of author).

        : param str msgid: message id in the msg-N form
        """
        self["@controls"]["edit"] = {
            "href": api.url_for(Exercise, exercise_id=exerid),
            "title": "Edit this exercise",
            "encoding": "json",
            "method": "PUT",
            "schemaUrl":EXERCISE_SCHEMA_URL
            #"schema": self._exer_schema(edit=True)
        }
    
    def add_control_edit_public_profile(self, nickname):
        """
        Adds the edit control to a public profile object. Editing a public
        profile uses a limited version of the full user schema.
        
        : param str nickname: nickname of the user whose profile is edited        
        """
        
        self["@controls"]["edit"] = {
            "href": api.url_for(User_public, nickname=nickname),
            "title": "Edit this public profile",
            "encoding": "json",
            "method": "PUT",
            "schema": self._public_profile_schema()
        }
        
    def add_control_reply_to(self, msgid):
        """
        Adds a reply-to control to a message.

        : param str msgid: message id in the msg-N form
        """

        self["@controls"]["forum:reply"] = {
            "href": api.url_for(Message, messageid=msgid),
            "title": "Reply to this message",
            "encoding": "json",
            "method": "POST",
            "schema": self._msg_schema()
        }
    """#TODO 4 Implement necessary methods here to implement User and History"""

    def _msg_schema(self, edit=False):
        """
        Creates a schema dictionary for messages. If we're editing a message
        the editor field should be set. If the message is new, the author field
        should be set instead. This is controlled by the edit flag.

        This schema can also be accessed from the urls /forum/schema/edit-msg/ and 
        /forum/schema/add-msg/.

        : param bool edit: is this schema for an edit form
        : rtype:: dict
        """

        if edit:
            user_field = "editor"
        else:
            user_field = "author"

        schema = {
            "type": "object",
            "properties": {},
            "required": ["headline", "articleBody"]
        }

        props = schema["properties"]
        props["headline"] = {
            "title": "Headline",
            "description": "Message headline",
            "type": "string"
        }
        props["articleBody"] = {
            "title": "Contents",
            "description": "Message contents",
            "type": "string"
        }
        props[user_field] = {
            "title": user_field.capitalize(),
            "description": "Nickname of the message {}".format(user_field),
            "type": "string"
        }
        return schema

    def _history_schema(self):
        """
        Creates a schema dicionary for the messages history query parameters.

        This schema can also be accessed from /forum/schema/history-query/

        :rtype:: dict
        """

        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }

        props = schema["properties"]
        props["length"] = {
            "description": "Maximum number of messages returned",
            "type": "integer"
        }        
        props["before"] = {
            "description": "Find messages before (timestamp as seconds)",
            "type": "integer"
        }
        props["after"] = {
            "description": "Find messages after (timestamp as seconds)",
            "type": "integer"
        }

        return schema
    
    def _public_profile_schema(self):
        """
        Creates a schema dictionary for editing public profiles of users. 
        
        :rtype:: dict
        """
        
        schema = {
            "type": "object",
            "properties": {},
            "required": ["signature", "avatar"]
        }
        
        props = schema["properties"]
        props["signature"] = {
            "description": "User's signature",
            "title": "Signature",
            "type": "string"
        }
        
        props["avatar"] = {
            "description": "Avatar image file location",
            "title": "Avatar",
            "type": "string"
        }
        
        return schema
        

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

#Define the resources

#TODO TONI tänne classi exercise ja exercises. Katso apiarysta minka mallisia palautusten pitää olla. Jos apiaryssa on jotain vikaa niin sano. Sita voi muuttaa. Tama on suoraan ex4 filu. ainoat asiat mita olen muuttanu on #OWN STUFF merkilla
        #merkitty osa add_controlseissa ja users get.
class Exercises(Resource):
    """
    Resource Messages implementation
    """

    def get(self):#, exerciseid):
        """
        Get all messages.

        INPUT parameters:
          None

        RESPONSE ENTITY BODY:
        * Media type: Mason
          https://github.com/JornWildt/Mason
         * Profile: Forum_Message
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_Message

        NOTE:
         * The attribute articleBody is obtained from the column messages.body
         * The attribute headline is obtained from the column messages.title
         * The attribute author is obtained from the column messages.sender
        """
        #PERFORM OPERATIONS
        #Create the users list
        exercises_db = g.con.get_exercises()
        if not exercises_db:
            return create_error_response(404, "No exercises")

        #FILTER AND GENERATE THE RESPONSE
        #Create the envelope
        envelope = ForumObject()
        #add controls to response
        envelope.add_control("self", href=api.url_for(Exercises))
 
        envelope.add_control_add_user()
        envelope.add_control_list_exercises()
        #not yet implemented
        #envelope.add_control_list_exercises()
        #SHOULD NOT BE IN HERE
        #envelope.add_control_get_user_information()
                
        items = envelope["items"] = []

        for exercise in exercises_db:
            item = ForumObject(
                exercise_id=exercise["exercise_id"],
                username=exercise["username"],
                type=exercise["type"],
                value=exercise["value"],
                valueunit=exercise["valueunit"],
                date=exercise["date"],   
                time=exercise["time"],   
                timeunit=exercise["timeunit"]   
            )
            #add controls to each object in the list
            item.add_control("self", href=api.url_for(Exercises, exercise_id=exercise["exercise_id"]))

            
            items.append(item)


        return Response(json.dumps(envelope), 200, mimetype=MASON+";")



        #Extract messages from database
      

    def post(self):
        """
        Adds a a new exercise.

        REQUEST ENTITY BODY:
         * Media type: JSON:
         * Profile: Forum_Message
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_Message

        NOTE:
         * The attribute articleBody is obtained from the column messages.body
         * The attribute headline is obtained from the column messages.title
         * The attribute author is obtained from the column messages.sender

        The body should be a JSON document that matches the schema for new messages
        If author is not there consider it  "Anonymous".

        RESPONSE STATUS CODE:
         * Returns 201 if the message has been added correctly.
           The Location header contains the path of the new message
         * Returns 400 if the message is not well formed or the entity body is
           empty.
         * Returns 415 if the format of the response is not json
         * Returns 500 if the message could not be added to database.

        """

        #Extract the request body. In general would be request.data
        #Since the request is JSON I use request.get_json
        #get_json returns a python dictionary after serializing the request body
        #get_json returns None if the body of the request is not formatted
        # using JSON. We use force=True since the input media type is not
        # application/json.

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:
            user_id=request_body["user_id"]
            username=request_body["username"]
            type=request_body["type"]
            value=request_body["value"]
            valueunit=request_body["valueunit"]
            date=request_body["date"]   
            time=request_body["time"]   
            timeunit=request_body["timeunit"]               

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include message title and body")
        #Create the new message and build the response code"
        exercise = {"username": username, "type": type,
                "value": value, "valueunit": valueunit, "date": date, "time": time, "timeunit": timeunit}

        #Create the new message and build the response code"
        newexercise_id = g.con.create_exercise(exercise)
        #newexerciseid = g.con.create_exercise(username, type, value, valueunit, date, time, timeunit)
        if not newexercise_id:
            return create_error_response(500, "Problem with the database",
                                         "Cannot access the database")

        #Create the Location header with the id of the message created
        url = api.url_for(Exercise, exercise_id=newexercise_id)

        #RENDER
        #Return the response
        #return Response((json.dumps(envelope),status=201)
        #return Response(status=201, headers={"Location": url})

        exerciseinfo=g.con.get_exercise(newexercise_id)
        envelope = ForumObject(
            username=exerciseinfo["username"],
            type=exerciseinfo["type"],
            value=exerciseinfo["value"],
            valueunit=exerciseinfo["valueunit"],
            date=exerciseinfo["date"],   
            time=exerciseinfo["time"],   
            timeunit=exerciseinfo["timeunit"]   
            )

        return Response(json.dumps(envelope),status=201)
        #CREATE RESPONSE AND RENDER
        #return Response(json.dumps(envelope),status=200)

class Exercise(Resource):
    """
    Resource that represents a single message in the API.
    """

    def get(self, exercise_id):
        """
        Get the body, the title and the id of a specific message.

        Returns status code 404 if the messageid does not exist in the database.

        INPUT PARAMETER
       : param str messageid: The id of the message to be retrieved from the
            system

        RESPONSE ENTITY BODY:
        * Media type: Mason
          https://github.com/JornWildt/Mason
         * Profile: Forum_Message
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_Message

            Link relations used: self, collection, author, replies and
            in-reply-to

            Semantic descriptors used: articleBody, headline, editor and author
            NOTE: editor should not be included in the output if the database
            return None.

        RESPONSE STATUS CODE
         * Return status code 200 if everything OK.
         * Return status code 404 if the message was not found in the database.

        NOTE:
         * The attribute articleBody is obtained from the column messages.body
         * The attribute headline is obtained from the column messages.title
         * The attribute author is obtained from the column messages.sender
        """
        exercise_db = g.con.get_exercise(exercise_id)
        if not exercise_db:
            return create_error_response(404, "There is no a exercise with id %s" % exercise_id)#,

                       #resource_type="Exercise",
                      # resource_url=request.path,
                       #resource_id=exercise_id)

        #envelope = ForumObject()
        #envelope.add_namespace("forum", LINK_RELATIONS_URL)

        #envelope.add_control_users_exercise()
        #envelope.add_control_add_exercise()

        #items = envelope["items"] = []

        #for  exercise in exercises_db:
        envelope = ForumObject(
                    username=exercise_db["username"],
                    type=exercise_db["type"],
                    value=exercise_db["value"],
                    valueunit=exercise_db["valueunit"],
                    date=exercise_db["date"],   
                    time=exercise_db["time"],   
                    timeunit=exercise_db["timeunit"]      
        )

        envelope.add_control("self", href=api.url_for(Exercises))
        envelope.add_control_delete_exercise(exercise_id)
        envelope.add_control_edit_exercise(exercise_id)
        envelope.add_control("self", href=api.url_for(Exercises), exercise_id=exercise_db["exercise_id"])

        #RENDER
        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_EXERCISE_PROFILE)

        

    def delete(self, exercise_id):
        """
        Deletes a message from the Forum API.

        INPUT PARAMETERS:
       : param str messageid: The id of the message to be deleted

        RESPONSE STATUS CODE
         * Returns 204 if the message was deleted
         * Returns 404 if the messageid is not associated to any message.
        """

        #PERFORM DELETE OPERATIONS
        if g.con.delete_exercise(exercise_id):
            return "", 204
        else:
            #Send error message
            return create_error_response(404, "Unknown message",
                                         "There is no a message with id %s" % exercise_id
                                        )

    def put(self, exercise_id):
        """
        Modifies the title, body and editor properties of this message.

        INPUT PARAMETERS:
       : param str messageid: The id of the message to be deleted

        RESPONSE ENTITY BODY:
        * Media type: Mason
          https://github.com/JornWildt/Mason
        * Profile: Forum_Message
          /profiles/message-profile

        The body should be a JSON document that matches the schema for editing messages
        If author is not there consider it  "Anonymous".

        OUTPUT:
         * Returns 204 if the message is modified correctly
         * Returns 400 if the body of the request is not well formed or it is
           empty.
         * Returns 404 if there is no message with messageid
         * Returns 415 if the input is not JSON.
         * Returns 500 if the database cannot be modified

        NOTE:
         * The attribute articleBody is obtained from the column messages.body
         * The attribute headline is obtained from the column messages.title
         * The attribute author is obtained from the column messages.sender

        """

        #CHECK THAT MESSAGE EXISTS
        if not g.con.get_exercise(exercise_id):#g.con.contains_exercise(exercise_id):
            return create_error_response(404, "Exercise not found",
                                         "There is no a exercise with id %s" % exercise_id
                                        )

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:         
            _username=request_body["username"]
            _type=request_body["type"]
            _value=request_body["value"]
            _valueunit=request_body["valueunit"]
            _date=request_body["date"]
            _time=request_body["time"] 
            _timeunit=request_body["timeunit"]   
            #ipaddress = request.remote_addr
        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include exercise title and body")                                          
        else:
            exercise = {"username": _username, "type": _type,
            "value": _value, "valueunit": _valueunit, "date": _date, "time": _time, "timeunit": _timeunit}
            #Modify the message in the database
            if not g.con.modify_exercise(exercise_id, exercise):
                return create_error_response(500, "Internal error",
                                         "Message information for %s cannot be updated" % exercise_id
                                        )
            return "", 204


    def post(self, exercise_id):
        """
        Adds a response to a message with id <exerciseid>.

        INPUT PARAMETERS:
       : param str messageid: The id of the message to be deleted

        REQUEST ENTITY BODY:
        * Media type: JSON:
         * Profile: Forum_Message
          /profiles/message-profile

        The body should be a JSON document that matches the schema for new messages
        If author is not there consider it  "Anonymous".

        RESPONSE HEADERS:
         * Location: Contains the URL of the new message

        RESPONSE STATUS CODE:
         * Returns 201 if the message has been added correctly.
           The Location header contains the path of the new message
         * Returns 400 if the message is not well formed or the entity body is
           empty.
         * Returns 404 if there is no message with messageid
         * Returns 415 if the format of the response is not json
         * Returns 500 if the message could not be added to database.

         NOTE:
         * The attribute articleBody is obtained from the column messages.body
         * The attribute headline is obtained from the column messages.title
         * The attribute author is obtained from the column messages.sender
        """

        #CHECK THAT MESSAGE EXISTS
        #If the message with messageid does not exist return status code 404
        if not g.con.contains_exercise(exercise_id):
            return create_error_response(404, "Exercise not found",
                                         "There is no a exercise with id %s" % exercise_id
                                        )

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:            
            #exerciseid=request_body["exerciseid"],           
            username=request_body["username"],
            type=request_body["type"],
            value=request_body["value"],
            valueunit=request_body["valueunit"],
            date=request_body["date"],   
            time=request_body["time"],   
            timeunit=request_body["timeunit"]   
            #ipaddress = request.remote_addr

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include exercise title and body")

        exercise = {"username": username, "type": type,
                "value": value, "valueunit": valueunit, "date": date, "time": time, "timeunit": timeunit}

        #Create the new message and build the response code"
        newexercise_id = g.con.append_exercise(username, exercise)
        if not newexercise_id:
            abort(500)

        #Create the Location header with the id of the message created
        url = api.url_for(Exercise, exercise_id=newexercise_id)

        #RENDER
        #Return the response
        return Response(status=200, headers={"Location": url})

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
class User_public(Resource):

    def get(self, nickname):
        """
        
        Get the public profile (avatar and signature) of a single user.
        
        RESPONSE ENTITY BODY:
        * Media type: Mason
          https://github.com/JornWildt/Mason
         * Profile: Forum_User_Profile
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_User_Profile
        """
        
        user_db = g.con.get_user(nickname)
        if not user_db:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with nickname %s"
                                         % nickname)
        
        pub_profile = user_db["public_profile"]
        
        # We could also by lazy and do the next step with:
        # envelope = ForumObject(nickname=nickname)
        # envelope.update(pub_profile)
        
        envelope = ForumObject(
            nickname=nickname,
            registrationdate=pub_profile["registrationdate"],
            signature=pub_profile["signature"],
            avatar=pub_profile["avatar"],
        )
        
        envelope.add_namespace("forum", LINK_RELATIONS_URL)
        envelope.add_control("self", href=api.url_for(User_public, nickname=nickname))
        envelope.add_control("up", href=api.url_for(User, nickname=nickname))
        envelope.add_control("forum:private-data", href=api.url_for(User_restricted, nickname=nickname))
        envelope.add_control_messages_history(nickname)
        envelope.add_control_edit_public_profile(nickname)
        
        return Response(json.dumps(envelope), 200, mimetype=MASON + ";" + FORUM_USER_PROFILE)

    def put(self, nickname):
        """
        Modify the public profile of a user. 
        
        REQUEST ENTITY BODY:
        * Media type: JSON
        
        """
        
        if not g.con.contains_user(nickname):
            return create_error_response(404, "Unknown user", "There is no user with nickname {}".format(nickname))
            
        request_body = request.get_json()
        if not request_body:
            return create_error_response(415, "Unsupported Media Type", "Use a JSON compatible format")            
        
        try:
            avatar = request_body["avatar"]
            signature = request_body["signature"]
        except KeyError:
            return create_error_response(400, "Wrong request format", "Be sure to include all mandatory properties")
        
        user = {
            "public_profile":
            {
                "signature": signature,
                "avatar": avatar
            }
        }
            
        if not g.con.modify_user(nickname, user):
            return create_error_response(404, "Unknown user", "There is no user with nickname {}".format(nickname))
        
        return "", 204

class User_restricted(Resource):

    def get (self, nickname):
        """
        Get the private profile of a user
        
        RESPONSE ENTITY BODY:
        * Media type: Mason
          https://github.com/JornWildt/Mason
         * Profile: Forum_User_Profile
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_User_Profile
        """
        
        user_db = g.con.get_user(nickname)
        if not user_db:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with nickname %s"
                                         % nickname)
        
        priv_profile = user_db["restricted_profile"]
        
        # Here we can't just update the envelope
        # with private profile because some of the keys
        # differ... So, lesson, if you want to be lazy
        # make sure to use the same key names everywhere =p
        
        try:
            country, locality = priv_profile["residence"].split(":")
            address = {"addressCountry": country, "addressLocality": locality}
        except (AttributeError, ValueError):
            address = {"addressCountry": "", "addressLocality": ""}
        
        envelope = ForumObject(
            nickname=nickname,
            address=address,
            birthDate=priv_profile["birthday"],
            email=priv_profile["email"],
            familyName=priv_profile["lastname"],
            gender=priv_profile["gender"],
            givenName=priv_profile["firstname"],
            website=priv_profile["website"],
            telephone=priv_profile["mobile"],
            skype=priv_profile["skype"],
            image=priv_profile["picture"]
        )
        
        envelope.add_namespace("forum", LINK_RELATIONS_URL)
        envelope.add_control("self", href=api.url_for(User_restricted, nickname=nickname))
        envelope.add_control("up", href=api.url_for(User, nickname=nickname))
        envelope.add_control("forum:public-data", href=api.url_for(User_public, nickname=nickname))
        envelope.add_control_messages_history(nickname)
        envelope.add_control_edit_private_profile(nickname)
        
        return Response(json.dumps(envelope), 200, mimetype=MASON + ";" + FORUM_USER_PROFILE)

    def put(self, nickname):
        """
        Edit the private profile of a user
        
        REQUEST ENTITY BODY:
        * Media type: JSON
        """
        
        if not g.con.contains_user(nickname):
            return create_error_response(404, "Unknown user", "There is no user with nickname {}".format(nickname))
            
        request_body = request.get_json()
        if not request_body:
            return create_error_response(415, "Unsupported Media Type", "Use  JSON format")            
        
        # Note: this is basically the reverse of what
        # we did in get(). Those identical keys would
        # have been nice again, no?
        
        try:
            priv_profile = dict(
                residence="{addressCountry}:{addressLocality}".format(**request_body["address"]),
                birthday=request_body["birthDate"],
                email=request_body["email"],
                lastname=request_body["familyName"],
                gender=request_body["gender"],
                firstname=request_body["givenName"],
                website=request_body.get("website", ""),
                mobile=request_body.get("telephone", ""),
                skype=request_body.get("skype", ""),
                image=request_body.get("picture", "")
            )
        except KeyError:
            return create_error_response(400, "Wrong request format", "Be sure to include all mandatory properties")
        
        user = {"restricted_profile": priv_profile}
            
        if not g.con.modify_user(nickname, user):
            return NotFound()
        
        return "", 204


class History(Resource):
    def get (self, nickname):
        """
            This method returns a list of messages that has been sent by an user
            and meet certain restrictions (result of an algorithm).
            The restrictions are given in the URL as query parameters.

            INPUT:
            The query parameters are:
             * length: the number of messages to return
             * after: the messages returned must have been modified after
                      the time provided in this parameter.
                      Time is UNIX timestamp
             * before: the messages returned must have been modified before the
                       time provided in this parameter. Time is UNIX timestamp

            RESPONSE STATUS CODE:
             * Returns 200 if the list can be generated and it is not empty
             * Returns 404 if no message meets the requirement

            RESPONSE ENTITY BODY:
            * Media type recommended: application/vnd.mason+json
            * Profile recommended: Forum_Message
                /profiles/message-profile

            Link relations used in items: None

            Semantic descriptions used in items: headline

            Link relations used in links: messages-all, author

            Semantic descriptors used in queries: after, before, lenght
        """

        #INTIAL CHECKING
        #Extract query parameters
        parameters = request.args
        length = int(parameters.get('length', -1))
        before = int(parameters.get('before', -1))
        after = int(parameters.get('after', -1))
        #PERFORM OPERATIONS
        #Get the messages. This method return None if there is
        #not user with nickname = nickname
        messages_db = g.con.get_messages(nickname, length, before, after)
        if messages_db is None or not messages_db:
            return create_error_response(404, "Empty list",
                                         "Cannot find any message with the"
                                         " provided restrictions")
        envelope = ForumObject()
        envelope.add_namespace("forum", LINK_RELATIONS_URL)
        envelope.add_control("self", href=api.url_for(History, nickname=nickname))
        envelope.add_control("author", href=api.url_for(User,nickname=nickname))
        envelope.add_control_messages_all()
        envelope.add_control_users_all()

        items = envelope["items"] = []

        for msg in messages_db:
            item = ForumObject(id=msg["messageid"], headline=msg["title"])
            item.add_control("self", href=api.url_for(Message, messageid=msg["messageid"]))
            item.add_control("profile", href=FORUM_MESSAGE_PROFILE)
            items.append(item)

        #RENDER
        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_MESSAGE_PROFILE)

        return None

#Add the Regex Converter so we can use regex expressions when we define the
#routes
app.url_map.converters["regex"] = RegexConverter

#Define the routes
####OWN

api.add_resource(Users, "/exercisetracker/api/users/",
                 endpoint="users")
api.add_resource(User, "/exercisetracker/api/users/<username>/",
                 endpoint="user")
api.add_resource(Exercises, "/exercisetracker/api/exercises/",
                 endpoint="exercises")
api.add_resource(Exercise, "/exercisetracker/api/exercises/<exercise_id>/",
                 endpoint="exercise")
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
