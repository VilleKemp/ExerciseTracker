"""
Created on 26.01.2013
Modified on 05.02.2017
@author: ivan sanchez
@author: mika oja
"""

import json

from flask import Flask, request, Response, g, _request_ctx_stack, redirect, send_from_directory
from flask.ext.restful import Resource, Api, abort
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

    def add_control_add_message(self):
        """
        This adds the add-message control to an object. Intended for the  
        document object. Here you can see that adding the control is a bunch of 
        lines where all we're basically doing is nested dictionaries to 
        achieve the correctly formed JSON document representation. 
        """

        self["@controls"]["forum:add-message"] = {
            "href": api.url_for(Messages),
            "title": "Create message",
            "encoding": "json",
            "method": "POST",
            "schema": self._msg_schema()
        }

    def add_control_add_user(self):
        """
        This adds the add-user control to an object. Intended ffor the 
        document object. Instead of adding a schema dictionary we are pointing
        to a schema url instead for two reasons: 1) to demonstrate both options;
        2) the user schema is relatively large.
        """

        self["@controls"]["forum:add-user"] = {
            "href": api.url_for(Users),
            "title": "Create user",
            "encoding": "json",
            "method": "POST",
            "schemaUrl": USER_SCHEMA_URL
        }

    def add_control_delete_message(self, msgid):
        """
        Adds the delete control to an object. This is intended for any 
        object that represents a message.

        : param str msgid: message id in the msg-N form
        """

        self["@controls"]["forum:delete"] = {
            "href": api.url_for(Message, messageid=msgid),  
            "title": "Delete this message",
            "method": "DELETE"
        }

    def add_control_delete_user(self, nickname):
        """
        Adds the delete control to an object. This is intended for any 
        object that represents a user.

        : param str nickname: The nickname of the user to remove
        """

        self["@controls"]["forum:delete"] = {
            "href": api.url_for(User, nickname=nickname),  
            "title": "Delete this user",
            "method": "DELETE"
        }

    def add_control_edit_message(self, msgid):
        """
        Adds the edit control to a message object. For the schema we need
        the one that's intended for editing (it has editor instead of author).

        : param str msgid: message id in the msg-N form
        """

        self["@controls"]["edit"] = {
            "href": api.url_for(Message, messageid=msgid),
            "title": "Edit this message",
            "encoding": "json",
            "method": "PUT",
            "schema": self._msg_schema(edit=True)
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
        
    def add_control_edit_private_profile(self, nickname):
        """
        Adds the edit control to a private profile object. Editing a private
        profile uses large subset of the user schema, so we're just going to
        use a URL this time. 
        
        : param str nickname: nickname of the user whose profile is edited        
        """
        
        self["@controls"]["edit"] = {
            "href": api.url_for(User_restricted, nickname=nickname),
            "title": "Edit this private profile",
            "encoding": "json",
            "method": "PUT",
            "schemaUrl": PRIVATE_PROFILE_SCHEMA_URL
        }    

    def add_control_messages_history(self, user):
        """
        This adds the messages history control to a user which defines a href 
        template for making queries. In Mason query parameters are defined with 
        a schema just like forms.

        : param str user: nickname of the user
        """

        self["@controls"]["forum:messages-history"] = {
            "href": api.url_for(History, nickname=user).rstrip("/") + u"{?length,before,after}",
            "title": "Message history",
            "isHrefTemplate": True,
            "schema": self._history_schema()
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
class Messages(Resource):
    """
    Resource Messages implementation
    """

    def get(self):
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

        #Extract messages from database
        messages_db = g.con.get_messages()

        envelope = ForumObject()
        envelope.add_namespace("forum", LINK_RELATIONS_URL)

        envelope.add_control("self", href=api.url_for(Messages))
        envelope.add_control_users_all()
        envelope.add_control_add_message()

        items = envelope["items"] = []

        for msg in messages_db:             
            item = ForumObject(id=msg["messageid"], headline=msg["title"])
            item.add_control("self", href=api.url_for(Message, messageid=msg["messageid"]))
            item.add_control("profile", href=FORUM_MESSAGE_PROFILE)
            items.append(item)

        #RENDER
        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_MESSAGE_PROFILE)

    def post(self):
        """
        Adds a a new message.

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
            title = request_body["headline"]            
            body = request_body["articleBody"]
            sender = request_body.get("author", "Anonymous")
            ipaddress = request.remote_addr

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include message title and body")
        #Create the new message and build the response code"
        newmessageid = g.con.create_message(title, body, sender, ipaddress)
        if not newmessageid:
            return create_error_response(500, "Problem with the database",
                                         "Cannot access the database")

        #Create the Location header with the id of the message created
        url = api.url_for(Message, messageid=newmessageid)

        #RENDER
        #Return the response
        return Response(status=201, headers={"Location": url})

class Message(Resource):
    """
    Resource that represents a single message in the API.
    """

    def get(self, messageid):
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

        #PEFORM OPERATIONS INITIAL CHECKS
        #Get the message from db
        message_db = g.con.get_message(messageid)
        if not message_db:
            abort(404, message="There is no a message with id %s" % messageid,
                       resource_type="Message",
                       resource_url=request.path,
                       resource_id=messageid)

        sender = message_db.get("sender", "Anonymous")
        parent = message_db.get("replyto", None)

        #FILTER AND GENERATE RESPONSE
        #Create the envelope:
        envelope = ForumObject(
            headline=message_db["title"],
            articleBody=message_db["body"],
            author=sender,
            editor=message_db["editor"]            
        )

        envelope.add_namespace("forum", LINK_RELATIONS_URL)
        envelope.add_namespace("atom-thread", ATOM_THREAD_PROFILE)

        envelope.add_control_delete_message(messageid)
        envelope.add_control_edit_message(messageid)
        envelope.add_control_reply_to(messageid)
        envelope.add_control("profile", href=FORUM_MESSAGE_PROFILE)        
        envelope.add_control("collection", href=api.url_for(Messages))
        envelope.add_control("self", href=api.url_for(Message, messageid=messageid))                
        envelope.add_control("author", href=api.url_for(User, nickname=sender))

        if parent:
            envelope.add_control("atom-thread:in-reply-to", href=api.url_for(Message, messageid=parent))
        else:
            envelope.add_control("atom-thread:in-reply-to", href=None)

        #RENDER
        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_MESSAGE_PROFILE)

    def delete(self, messageid):
        """
        Deletes a message from the Forum API.

        INPUT PARAMETERS:
       : param str messageid: The id of the message to be deleted

        RESPONSE STATUS CODE
         * Returns 204 if the message was deleted
         * Returns 404 if the messageid is not associated to any message.
        """

        #PERFORM DELETE OPERATIONS
        if g.con.delete_message(messageid):
            return "", 204
        else:
            #Send error message
            return create_error_response(404, "Unknown message",
                                         "There is no a message with id %s" % messageid
                                        )

    def put(self, messageid):
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
        if not g.con.contains_message(messageid):
            return create_error_response(404, "Message not found",
                                         "There is no a message with id %s" % messageid
                                        )

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:            
            title = request_body["headline"]            
            body = request_body["articleBody"]
            editor = request_body.get("editor", "Anonymous")
            ipaddress = request.remote_addr

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include message title and body")                                          
        else:
            #Modify the message in the database
            if not g.con.modify_message(messageid, title, body, editor):
                return create_error_response(500, "Internal error",
                                         "Message information for %s cannot be updated" % messageid
                                        )
            return "", 204

    def post(self, messageid):
        """
        Adds a response to a message with id <messageid>.

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
        if not g.con.contains_message(messageid):
            return create_error_response(404, "Message not found",
                                         "There is no a message with id %s" % messageid
                                        )

        if JSON != request.headers.get("Content-Type",""):
            return create_error_response(415, "UnsupportedMediaType",
                                         "Use a JSON compatible format")
        request_body = request.get_json(force=True)
         #It throws a BadRequest exception, and hence a 400 code if the JSON is
        #not wellformed
        try:            
            title = request_body["headline"]            
            body = request_body["articleBody"]
            sender = request_body.get("author", "Anonymous")
            ipaddress = request.remote_addr

        except KeyError:
            #This is launched if either title or body does not exist or if
            # the template.data array does not exist.
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include message title and body")

        #Create the new message and build the response code"
        newmessageid = g.con.append_answer(messageid, title, body,
                                           sender, ipaddress)
        if not newmessageid:
            abort(500)

        #Create the Location header with the id of the message created
        url = api.url_for(Message, messageid=newmessageid)

        #RENDER
        #Return the response
        return Response(status=201, headers={"Location": url})

class Users(Resource):

    def get(self):
        """
        Gets a list of all the users in the database.

        It returns always status code 200.

        RESPONSE ENTITITY BODY:

         OUTPUT:
            * Media type: Collection+JSON:
             http://amundsen.com/media-types/collection/
             - Extensions: template validation and value-types
               https://github.com/collection-json/extensions
            * Profile: Forum_User
                /profiles/user-profile

        Link relations used in items: messages

        Semantic descriptions used in items: nickname, registrationdate

        Link relations used in links: messages-all

        Semantic descriptors used in template: address, avatar, birthday,
        email,familyname,gender,givenName,image, nickname, signature, skype, telephone,
        website

        NOTE:
         * The attribute signature is obtained from the column users_profile.signature
         * The attribute givenName is obtained from the column users_profile.firstname
         * The attribute familyName is obtained from the column users_profile.lastname
         * The attribute address is obtained from the column users_profile.residence
            The address from users_profile.residence has the format:
                addressLocality, addressCountry
         * The attribute image is obtained from the column users_profile.picture
         * The rest of attributes match one-to-one with column names in the
           database.
        """
        #PERFORM OPERATIONS
        #Create the messages list
        users_db = g.con.get_users()

        #FILTER AND GENERATE THE RESPONSE
       #Create the envelope
        envelope = ForumObject()

        envelope.add_namespace("forum", LINK_RELATIONS_URL)

        envelope.add_control_add_user()
        envelope.add_control_messages_all()
        envelope.add_control("self", href=api.url_for(Users))

        items = envelope["items"] = []

        for user in users_db:
            item = ForumObject(
                nickname=user["nickname"],
                registrationdate=user["registrationdate"]
            )
            item.add_control_messages_history(user["nickname"])
            item.add_control("self", href=api.url_for(User, nickname=user["nickname"]))
            item.add_control("profile", href=FORUM_USER_PROFILE)
            items.append(item)

        #RENDER
        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_USER_PROFILE)

    def post(self):
        """
        Adds a new user in the database.

        REQUEST ENTITY BODY:
         * Media type: JSON:
         * Profile: Forum_User
           http://atlassian.virtues.fi: 8090/display/PWP
           /Exercise+4#Exercise4-Forum_User

        Semantic descriptors used in template: address(optional),
        avatar(mandatory), birthday(mandatory),email(mandatory),
        familyName(mandatory), gender(mandatory), givenName(mandatory),
        image(optional), signature(mandatory), skype(optional),
        telephone(optional), website(optional).

        RESPONSE STATUS CODE:
         * Returns 201 + the url of the new resource in the Location header
         * Return 409 Conflict if there is another user with the same nickname
         * Return 400 if the body is not well formed
         * Return 415 if it receives a media type != application/json

        NOTE:
         * The attribute signature is obtained from the column users_profile.signature
         * The attribute givenName is obtained from the column users_profile.firstname
         * The attribute familyName is obtained from the column users_profile.lastname
         * The attribute address is obtained from the column users_profile.residence
            The address from users_profile.residence has the format:
                addressLocality, addressCountry
         * The attribute image is obtained from the column users_profile.picture
         * The rest of attributes match one-to-one with column names in the
           database.

        NOTE:
        The: py: method:`Connection.append_user()` receives as a parameter a
        dictionary with the following format.
        {"public_profile":{"nickname":""
                           "signature":"","avatar":""},
         "restricted_profile":{"firstname":"","lastname":"","email":"",
                                  "website":"","mobile":"","skype":"",
                                  "birthday":"","residence":"","gender":"",
                                  "picture":""}
            }

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
            nickname = request_body["nickname"]
        except KeyError:
            return create_error_response(400, "Wrong request format", "User nickname was missing from the request")

        #Conflict if user already exist
        if g.con.contains_user(nickname):
            return create_error_response(409, "Wrong nickname",
                                         "There is already a user with same"
                                         "nickname:%s." % nickname)

        # pick up rest of the mandatory fields
        try:
            avatar = request_body["avatar"]
            birthdate = request_body["birthDate"]
            email = request_body["email"]
            familyname = request_body["familyName"]
            gender = request_body["gender"]
            givenname = request_body["givenName"]
            signature = request_body["signature"]
        except KeyError:
            return create_error_response(400, "Wrong request format", "Be sure to include all mandatory properties")

        # check address if given

        address = request_body.get("address", None)
        if address:
            try:                
                residence = "{addressLocality}, {addressCountry}".format(**address)
            except (KeyError, TypeError):
                return create_error_response(400, "Wrong request format", "Incorrect format of address field")
        else:
            residence = None

        # pick up rest of the optional fields

        image = request_body.get("image", "")
        mobile = request_body.get("telephone", "")
        skype = request_body.get("skype", "")
        website = request_body.get("website", "")

        user = {"public_profile": {"nickname": nickname,
                                   "signature": signature, "avatar": avatar},
                "restricted_profile": {"firstname": givenname,
                                       "lastname": familyname,
                                       "email": email,
                                       "website": website,
                                       "mobile": mobile,
                                       "skype": skype,
                                       "birthday": birthdate,
                                       "residence": residence,
                                       "gender": gender,
                                       "picture": image}
        }

        try:
            nickname = g.con.append_user(nickname, user)
        except ValueError:
            return create_error_response(400, "Wrong request format",
                                         "Be sure you include all"
                                         " mandatory properties"
                                        )

        #CREATE RESPONSE AND RENDER
        return Response(status=201,
            headers={"Location": api.url_for(User, nickname=nickname)})

class User(Resource):
    """
    User Resource. Public and private profile are separate resources.
    """

    def get(self, nickname):
        """
        Get basic information of a user:

        INPUT PARAMETER:
       : param str nickname: Nickname of the required user.

        OUTPUT:
         * Return 200 if the nickname exists.
         * Return 404 if the nickname is not stored in the system.

        RESPONSE ENTITY BODY:

        * Media type recommended: application/vnd.mason+json
        * Profile recommended: application/vnd.mason+json

        Link relations used: self, collection, public-data, private-data,
        messages.

        Semantic descriptors used: nickname and registrationdate

        NOTE:
        The: py: method:`Connection.get_user()` returns a dictionary with the
        the following format.

        {"public_profile":{"registrationdate":,"nickname":""
                               "signature":"","avatar":""},
        "restricted_profile":{"firstname":"","lastname":"","email":"",
                              "website":"","mobile":"","skype":"",
                              "birthday":"","residence":"","gender":"",
                              "picture":""}
            }
        """

        #PERFORM OPERATIONS
        user_db = g.con.get_user(nickname)
        if not user_db:
            return create_error_response(404, "Unknown user",
                                         "There is no a user with nickname %s"
                                         % nickname)
        #FILTER AND GENERATE RESPONSE
        #Create the envelope:
        envelope = ForumObject(
            nickname=nickname,
            registrationdate= user_db["public_profile"]["registrationdate"]        
        )

        envelope.add_namespace("forum", LINK_RELATIONS_URL)
        envelope.add_control("self", href=api.url_for(User, nickname=nickname))
        envelope.add_control("profile", href=FORUM_USER_PROFILE)
        envelope.add_control("forum:private-data", href=api.url_for(User_restricted, nickname=nickname))
        envelope.add_control("forum:public-data", href=api.url_for(User_public, nickname=nickname))
        envelope.add_control_messages_history(nickname)
        envelope.add_control_messages_all()
        envelope.add_control("collection", href=api.url_for(Users))
        envelope.add_control_delete_user(nickname)

        return Response(json.dumps(envelope), 200, mimetype=MASON+";" + FORUM_USER_PROFILE)
  

    def delete(self, nickname):
        """
        Delete a user in the system.

       : param str nickname: Nickname of the required user.

        RESPONSE STATUS CODE:
         * If the user is deleted returns 204.
         * If the nickname does not exist return 404
        """

        #PEROFRM OPERATIONS
        #Try to delete the user. If it could not be deleted, the database
        #returns None.
        if g.con.delete_user(nickname):
            #RENDER RESPONSE
            return '', 204
        else:
            #GENERATE ERROR RESPONSE
            return create_error_response(404, "Unknown user",
                                         "There is no a user with nickname %s"
                                         % nickname)

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
api.add_resource(Messages, "/forum/api/messages/",
                 endpoint="messages")
api.add_resource(Message, "/forum/api/messages/<regex('msg-\d+'):messageid>/",
                 endpoint="message")
api.add_resource(User_public, "/forum/api/users/<nickname>/public_profile/",
                 endpoint="public_profile")
api.add_resource(User_restricted, "/forum/api/users/<nickname>/restricted_profile/",
                 endpoint="restricted_profile")
api.add_resource(Users, "/forum/api/users/",
                 endpoint="users")
api.add_resource(User, "/forum/api/users/<nickname>/",
                 endpoint="user")
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
