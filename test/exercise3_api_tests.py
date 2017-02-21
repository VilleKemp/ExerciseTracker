"""
Created on 26.01.2013
Modified on 05.02.2017
@author: ivan sanchez
@author: mika oja
"""
import unittest, copy
import json

import flask

import forum.resources as resources
import forum.database as database

DB_PATH = "db/forum_test.db"
ENGINE = database.Engine(DB_PATH)

MASONJSON = "application/vnd.mason+json"
JSON = "application/json"
HAL = "application/hal+json"
FORUM_USER_PROFILE ="/profiles/user-profile/"
FORUM_MESSAGE_PROFILE = "/profiles/message-profile/"
ATOM_THREAD_PROFILE = "https://tools.ietf.org/html/rfc4685"

#Tell Flask that I am running it in testing mode.
resources.app.config["TESTING"] = True
#Necessary for correct translation in url_for
resources.app.config["SERVER_NAME"] = "localhost:5000"

#Database Engine utilized in our testing
resources.app.config.update({"Engine": ENGINE})

#Other database parameters.
initial_messages = 20
initial_users = 5


class ResourcesAPITestCase(unittest.TestCase):
    #INITIATION AND TEARDOWN METHODS
    @classmethod
    def setUpClass(cls):
        """ Creates the database structure. Removes first any preexisting
            database file
        """
        print "Testing ", cls.__name__
        ENGINE.remove_database()
        ENGINE.create_tables()

    @classmethod
    def tearDownClass(cls):
        """Remove the testing database"""
        print "Testing ENDED for ", cls.__name__
        ENGINE.remove_database()

    def setUp(self):
        """
        Populates the database
        """
        #This method load the initial values from forum_data_dump.sql
        ENGINE.populate_tables()
        #Activate app_context for using url_for
        self.app_context = resources.app.app_context()
        self.app_context.push()
        #Create a test client
        self.client = resources.app.test_client()

    def tearDown(self):
        """
        Remove all records from database
        """
        ENGINE.clear()
        self.app_context.pop()

class MessagesTestCase (ResourcesAPITestCase):

    #Anonymous user
    message_1_request = {       
        "headline": "Hypermedia course",
        "articleBody": "Do you know any good online hypermedia course?"
    }    

    #Existing user
    message_2_request = {
        "headline": "Hypermedia course",
        "articleBody": "Do you know any good online hypermedia course?",
        "author": "Axel"    
    }

    #Non exsiting user
    message_3_request = {
        "headline": "Hypermedia course",
        "articleBody": "Do you know any good online hypermedia course?",
        "author": "Onethatwashere"
    }

    #Missing the headline
    message_4_wrong = {
        "articleBody": "Do you know any good online hypermedia course?",
        "author": "Onethatwashere"
    }

    #Missing the articleBody
    message_5_wrong = {
        "articleBody": "Do you know any good online hypermedia course?",
        "author": "Onethatwashere"
    }

    url = "/forum/api/messages/"

    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        print "("+self.test_url.__name__+")", self.test_url.__doc__,
        with resources.app.test_request_context(self.url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Messages)

    def test_get_messages(self):
        """
        Checks that GET Messages return correct status code and data format
        """
        print "("+self.test_get_messages.__name__+")", self.test_get_messages.__doc__

        #Check that I receive status code 200
        resp = self.client.get(flask.url_for("messages"))
        self.assertEquals(resp.status_code, 200)

        # Check that I receive a collection and adequate href
        data = json.loads(resp.data)
        
        #Check controls
        controls = data["@controls"]
        self.assertIn("self", controls)
        self.assertIn("forum:add-message", controls)
        self.assertIn("forum:users-all", controls)

        self.assertIn("href", controls["self"])
        self.assertEquals(controls["self"]["href"], self.url)

        # Check that users-all control is correct
        users_ctrl = controls["forum:users-all"]
        self.assertIn("title", users_ctrl)
        self.assertIn("href", users_ctrl)
        self.assertEquals(users_ctrl["href"], "/forum/api/users/")

        #Check that add-message control is correct
        msg_ctrl = controls["forum:add-message"]
        self.assertIn("title", msg_ctrl)
        self.assertIn("href", msg_ctrl)
        self.assertEquals(msg_ctrl["href"], "/forum/api/messages/")
        self.assertIn("encoding", msg_ctrl)
        self.assertEquals(msg_ctrl["encoding"], "json")        
        self.assertIn("method", msg_ctrl)
        self.assertEquals(msg_ctrl["method"], "POST")
        self.assertIn("schema", msg_ctrl)
        
        schema_data = msg_ctrl["schema"]
        self.assertIn("type", schema_data)
        self.assertIn("properties", schema_data)
        self.assertIn("required", schema_data)
        
        props = schema_data["properties"]
        self.assertIn("headline", props)
        self.assertIn("articleBody", props)
        self.assertIn("author", props)
        
        req = schema_data["required"]
        self.assertIn("headline", req)
        self.assertIn("articleBody", req)
        
        for key, value in props.items():
            self.assertIn("description", value)
            self.assertIn("title", value)
            self.assertIn("type", value)
            self.assertEquals("string", value["type"])

        #Check that items are correct.
        items = data["items"]
        self.assertEquals(len(items), initial_messages)
        for item in items:
            self.assertIn("id", item)
            self.assertIn("headline", item)
            self.assertIn("@controls", item)
            self.assertIn("self", item["@controls"])
            self.assertIn("href", item["@controls"]["self"])
            self.assertEquals(item["@controls"]["self"]["href"], resources.api.url_for(resources.Message, messageid=item["id"], _external=False))
            self.assertIn("profile", item["@controls"])
            self.assertEquals(item["@controls"]["profile"]["href"], FORUM_MESSAGE_PROFILE)

    def test_get_messages_mimetype(self):
        """
        Checks that GET Messages return correct status code and data format
        """
        print "("+self.test_get_messages_mimetype.__name__+")", self.test_get_messages_mimetype.__doc__

        #Check that I receive status code 200
        resp = self.client.get(flask.url_for("messages"))
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers.get("Content-Type",None),
                          "{};{}".format(MASONJSON, FORUM_MESSAGE_PROFILE))

    def test_add_message(self):
        """
        Test adding messages to the database.
        """
        print "("+self.test_add_message.__name__+")", self.test_add_message.__doc__

        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.message_1_request)
                               )
        self.assertTrue(resp.status_code == 201)
        url = resp.headers.get("Location")
        self.assertIsNotNone(url)
        resp = self.client.get(url)
        self.assertTrue(resp.status_code == 200)

        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.message_2_request)
                               )
        self.assertTrue(resp.status_code == 201)
        url = resp.headers.get("Location")
        self.assertIsNotNone(url)
        resp = self.client.get(url)
        self.assertTrue(resp.status_code == 200)

        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.message_3_request)
                               )
        self.assertTrue(resp.status_code == 201)
        url = resp.headers.get("Location")
        self.assertIsNotNone(url)
        resp = self.client.get(url)
        self.assertTrue(resp.status_code == 200)

    def test_add_message_wrong_media(self):
        """
        Test adding messages with a media different than json
        """
        print "("+self.test_add_message_wrong_media.__name__+")", self.test_add_message_wrong_media.__doc__
        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": "text"},
                                data=self.message_1_request.__str__()
                               )
        self.assertTrue(resp.status_code == 415)

    def test_add_message_incorrect_format(self):
        """
        Test that add message response correctly when sending erroneous message
        format.
        """
        print "("+self.test_add_message_incorrect_format.__name__+")", self.test_add_message_incorrect_format.__doc__
        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.message_4_wrong)
                               )
        self.assertTrue(resp.status_code == 400)

        resp = self.client.post(resources.api.url_for(resources.Messages),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.message_5_wrong)
                               )
        self.assertTrue(resp.status_code == 400)

class MessageTestCase (ResourcesAPITestCase):

    #ATTENTION: json.loads return unicode
    message_req_1 = {
        "headline": "Do not use IE",
        "articleBody": "Do not try to fix what others broke",
        "author": "HockeyFan"
    }

    message_mod_req_1 = {
        "headline": "CSS: Margin problems with IE 6.0",
        "articleBody": "I am using a float layout on my website but I've run into some problems with Internet Explorer. I have set the left margin of a float to 100 pixels, but IE 6.0 uses a margin of 200px instead. Why is that? Is this one of the many bugs in IE 6.0? It does not happen with IE 7.0",
        "author": "AxelW",
        "editor": "AxelW"
    }

    message_wrong_req_1 = {
        "headline": "CSS: Margin problems with IE 6.0"
    }

    message_wrong_req_2 = {
        "articleBody": "Do not try to fix what others broke",
    }

    def setUp(self):
        super(MessageTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Message,
                                         messageid="msg-1",
                                         _external=False)
        self.url_wrong = resources.api.url_for(resources.Message,
                                               messageid="msg-290",
                                               _external=False)

    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        _url = "/forum/api/messages/msg-1/"
        print "("+self.test_url.__name__+")", self.test_url.__doc__
        with resources.app.test_request_context(_url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Message)

    def test_wrong_url(self):
        """
        Checks that GET Message return correct status code if given a
        wrong message
        """
        resp = self.client.get(self.url_wrong)
        self.assertEquals(resp.status_code, 404)

    def test_get_message(self):
        """
        Checks that GET Message return correct status code and data format
        """
        print "("+self.test_get_message.__name__+")", self.test_get_message.__doc__
        with resources.app.test_client() as client:
            resp = client.get(self.url)
            self.assertEquals(resp.status_code, 200)
            data = json.loads(resp.data)


            controls = data["@controls"]
            self.assertIn("self", controls)
            self.assertIn("profile", controls)
            self.assertIn("author", controls)
            self.assertIn("collection", controls)
            self.assertIn("edit", controls)
            self.assertIn("forum:delete", controls)
            self.assertIn("forum:reply", controls)
            self.assertIn("atom-thread:in-reply-to", controls)
            
            edit_ctrl = controls["edit"]
            self.assertIn("title", edit_ctrl)
            self.assertIn("href", edit_ctrl)
            self.assertEquals(edit_ctrl["href"], self.url)
            self.assertIn("encoding", edit_ctrl)
            self.assertEquals(edit_ctrl["encoding"], "json")        
            self.assertIn("method", edit_ctrl)
            self.assertEquals(edit_ctrl["method"], "PUT")
            self.assertIn("schema", edit_ctrl)
            
            reply_ctrl = controls["forum:reply"]
            self.assertIn("title", reply_ctrl)
            self.assertIn("href", reply_ctrl)
            self.assertEquals(reply_ctrl["href"], self.url)
            self.assertIn("encoding", reply_ctrl)
            self.assertEquals(reply_ctrl["encoding"], "json")        
            self.assertIn("method", reply_ctrl)
            self.assertEquals(reply_ctrl["method"], "POST")
            self.assertIn("schema", reply_ctrl)
            
            # Test edit schema
            schema_data = edit_ctrl["schema"]
            self.assertIn("type", schema_data)
            self.assertIn("properties", schema_data)
            self.assertIn("required", schema_data)
            
            props = schema_data["properties"]
            self.assertIn("headline", props)
            self.assertIn("articleBody", props)
            self.assertIn("editor", props)
            
            req = schema_data["required"]
            self.assertIn("headline", req)
            self.assertIn("articleBody", req)

            # Test reply schema
            schema_data = reply_ctrl["schema"]
            self.assertIn("type", schema_data)
            self.assertIn("properties", schema_data)
            self.assertIn("required", schema_data)
            
            props = schema_data["properties"]
            self.assertIn("headline", props)
            self.assertIn("articleBody", props)
            self.assertIn("author", props)
            
            req = schema_data["required"]
            self.assertIn("headline", req)
            self.assertIn("articleBody", req)
            
            self.assertIn("href", controls["self"])
            self.assertEquals(controls["self"]["href"], self.url)
            
            self.assertIn("href", controls["profile"])
            self.assertEquals(controls["profile"]["href"], FORUM_MESSAGE_PROFILE)

            self.assertIn("href", controls["author"])
            self.assertEquals(controls["author"]["href"], resources.api.url_for(
                resources.User, nickname="AxelW", _external=False
            ))
            
            self.assertIn("href", controls["collection"])
            self.assertEquals(controls["collection"]["href"], resources.api.url_for(
                resources.Messages, _external=False
            ))
            
            self.assertIn("href", controls["atom-thread:in-reply-to"])
            self.assertEquals(controls["atom-thread:in-reply-to"]["href"], None)
            
            del_ctrl = controls["forum:delete"]
            self.assertIn("href", del_ctrl)
            self.assertEquals(del_ctrl["href"], self.url)
            self.assertIn("method", del_ctrl)
            self.assertEquals(del_ctrl["method"], "DELETE")
                        
            #Check rest attributes
            self.assertIn("articleBody", data)
            self.assertIn("author", data)
            self.assertIn("headline", data)
            self.assertIn("editor", data)

    def test_get_message_mimetype(self):
        """
        Checks that GET Messages return correct status code and data format
        """
        print "("+self.test_get_message_mimetype.__name__+")", self.test_get_message_mimetype.__doc__

        #Check that I receive status code 200
        resp = self.client.get(self.url)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers.get("Content-Type",None),
                          "{};{}".format(MASONJSON, FORUM_MESSAGE_PROFILE))

    def test_add_reply_unexisting_message(self):
        """
        Try to add a reply to an unexisting message
        """
        print "("+self.test_add_reply_unexisting_message.__name__+")", self.test_add_reply_unexisting_message.__doc__
        resp = self.client.post(self.url_wrong,
                                data=json.dumps(self.message_req_1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 404)

    def test_add_reply_wrong_message(self):
        """
        Try to add a reply to a message sending wrong data
        """
        print "("+self.test_add_reply_wrong_message.__name__+")", self.test_add_reply_wrong_message.__doc__
        resp = self.client.post(self.url,
                                data=json.dumps(self.message_wrong_req_1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)
        resp = self.client.post(self.url,
                                data=json.dumps(self.message_wrong_req_2),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)

    def test_add_reply_wrong_type(self):
        """
        Checks that returns the correct status code if the Content-Type is wrong
        """
        print "("+self.test_add_reply_wrong_type.__name__+")", self.test_add_reply_wrong_type.__doc__
        resp = self.client.post(self.url,
                                data=json.dumps(self.message_req_1),
                                headers={"Content-Type": "text/html"})
        self.assertEquals(resp.status_code, 415)

    def test_add_reply(self):
        """
        Add a new message and check that I receive the same data
        """
        print "("+self.test_add_reply.__name__+")", self.test_add_reply.__doc__
        resp = self.client.post(self.url,
                                data=json.dumps(self.message_req_1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 201)
        self.assertIn("Location", resp.headers)
        message_url = resp.headers["Location"]
        #Check that the message is stored
        resp2 = self.client.get(message_url)
        self.assertEquals(resp2.status_code, 200)
        #data = json.loads(resp2.data)
        #self.assertEquals(data, self.message_resp_1)

    def test_modify_message(self):
        """
        Modify an exsiting message and check that the message has been modified correctly in the server
        """
        print "("+self.test_modify_message.__name__+")", self.test_modify_message.__doc__
        resp = self.client.put(self.url,
                               data=json.dumps(self.message_mod_req_1),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 204)
        #Check that the message has been modified
        resp2 = self.client.get(self.url)
        self.assertEquals(resp2.status_code, 200)
        data = json.loads(resp2.data)
        #Check that the title and the body of the message has been modified with the new data
        self.assertEquals(data["headline"], self.message_mod_req_1["headline"])
        self.assertEquals(data["articleBody"], self.message_mod_req_1["articleBody"])

    def test_modify_unexisting_message(self):
        """
        Try to modify a message that does not exist
        """
        print "("+self.test_modify_unexisting_message.__name__+")", self.test_modify_unexisting_message.__doc__
        resp = self.client.put(self.url_wrong,
                                data=json.dumps(self.message_mod_req_1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 404)

    def test_modify_wrong_message(self):
        """
        Try to modify a message sending wrong data
        """
        print "("+self.test_modify_wrong_message.__name__+")", self.test_modify_wrong_message.__doc__
        resp = self.client.put(self.url,
                               data=json.dumps(self.message_wrong_req_1),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)
        resp = self.client.put(self.url,
                               data=json.dumps(self.message_wrong_req_2),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)

    def test_delete_message(self):
        """
        Checks that Delete Message return correct status code if corrected delete
        """
        print "("+self.test_delete_message.__name__+")", self.test_delete_message.__doc__
        resp = self.client.delete(self.url)
        self.assertEquals(resp.status_code, 204)
        resp2 = self.client.get(self.url)
        self.assertEquals(resp2.status_code, 404)

    def test_delete_unexisting_message(self):
        """
        Checks that Delete Message return correct status code if given a wrong address
        """
        print "("+self.test_delete_unexisting_message.__name__+")", self.test_delete_unexisting_message.__doc__
        resp = self.client.delete(self.url_wrong)
        self.assertEquals(resp.status_code, 404)

class UsersTestCase (ResourcesAPITestCase):

    user_1_request = {
        "nickname": "Rigors",
        "address": {"addressLocality": "Manchester", "addressCountry":"UK"},
        "avatar": "image3.jpg",
        "birthDate": "2009-09-09",
        "email": "rigors@gmail.com",
        "familyName": "Rigors",
        "gender": "Male",
        "givenName": "Reagan",
        "image": "image2.jpg",
        "signature": "I am like Ronald McDonald",
        "skype": "rigors",
        "telephone": "0445555666",
        "website": "http://rigors.com"
    }

    user_2_request = {
        "nickname": "Rango",
        "avatar": "image3.jpg",
        "birthDate": "2009-09-09",
        "email": "rango@gmail.com",
        "familyName": "Rango",
        "gender": "Male",
        "givenName": "Rangero",
        "signature": "I am like Ronald McDonald"
    }

    #Existing nickname
    user_wrong_1_request = {
        "nickname": "AxelW",
        "avatar": "image3.jpg",
        "birthDate": "2009-09-09",
        "email": "rango@gmail.com",
        "familyName": "Rango",
        "gender": "Male",
        "givenName": "Rangero",
        "signature": "I am like Ronald McDonald"
    }

    #Mssing nickname
    user_wrong_2_request = {
        "avatar": "image3.jpg",
        "birthDate": "2009-09-09",
        "email": "rango@gmail.com",
        "familyName": "Rango",
        "gender": "Male",
        "givenName": "Rangero",
        "signature": "I am like Ronald McDonald",
    }

    #Missing mandatory
    user_wrong_3_request = {
        "nickname": "Rango",
        "email": "rango@gmail.com",
        "familyName": "Rango",
        "gender": "Male",
        "givenName": "Rangero",
        "signature": "I am like Ronald McDonald",
    }

    #Wrong address
    user_wrong_4_request = {
        "nickname": "Rango",
        "avatar": "image3.jpg",
        "address": "Indonesia, Spain",
        "birthDate": "2009-09-09",
        "email": "rango@gmail.com",
        "familyName": "Rango",
        "gender": "Male",
        "givenName": "Rangero",
        "signature": "I am like Ronald McDonald"
    }

    def setUp(self):
        super(UsersTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Users,
                                         _external=False)

    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        _url = "/forum/api/users/"
        print "("+self.test_url.__name__+")", self.test_url.__doc__,
        with resources.app.test_request_context(_url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Users)

    def test_get_users(self):
        """
        Checks that GET users return correct status code and data format
        """
        print "("+self.test_get_users.__name__+")", self.test_get_users.__doc__
        #Check that I receive status code 200
        resp = self.client.get(flask.url_for("users"))
        self.assertEquals(resp.status_code, 200)

        # Check that I receive a collection and adequate href
        data = json.loads(resp.data)

        controls = data["@controls"]
        self.assertIn("self", controls)
        self.assertIn("forum:add-user", controls)
        self.assertIn("forum:messages-all", controls)
        
        self.assertIn("href", controls["self"])
        self.assertEquals(controls["self"]["href"], self.url)
        
        msgs_ctrl = controls["forum:messages-all"]
        self.assertIn("href", msgs_ctrl)
        self.assertEquals(msgs_ctrl["href"], "/forum/api/messages/")
        self.assertIn("title", msgs_ctrl)
        
        add_ctrl = controls["forum:add-user"]
        self.assertIn("href", add_ctrl)
        self.assertEquals(add_ctrl["href"], "/forum/api/users/")
        self.assertIn("encoding", add_ctrl)
        self.assertEquals(add_ctrl["encoding"], "json")
        self.assertIn("method", add_ctrl)
        self.assertEquals(add_ctrl["method"], "POST")
        self.assertIn("title", add_ctrl)
        self.assertIn("schemaUrl", add_ctrl)
        self.assertEquals(add_ctrl["schemaUrl"], "/forum/schema/user/")

        items = data["items"]
        self.assertEquals(len(items), initial_users)
        for item in items:
            self.assertIn("nickname", item)
            self.assertIn("registrationdate", item)
            self.assertIn("@controls", item)
            self.assertIn("self", item["@controls"])
            self.assertIn("href", item["@controls"]["self"])
            self.assertEquals(item["@controls"]["self"]["href"], resources.api.url_for(resources.User, nickname=item["nickname"], _external=False))
            self.assertIn("forum:messages-history", item["@controls"])
            hist_ctrl = item["@controls"]["forum:messages-history"]
            self.assertIn("href", hist_ctrl)
            self.assertEquals(hist_ctrl["href"], resources.api.url_for(resources.History, nickname=item["nickname"], _external=False).rstrip("/") + u"{?length,before,after}")
            self.assertIn("isHrefTemplate", hist_ctrl)
            self.assertEquals(hist_ctrl["isHrefTemplate"], True)
            self.assertIn("schema", hist_ctrl)
            schema_data = hist_ctrl["schema"]
            
            self.assertIn("type", schema_data)
            self.assertIn("properties", schema_data)
            self.assertIn("required", schema_data)
            
            props = schema_data["properties"]
            self.assertIn("length", props)
            self.assertIn("before", props)
            self.assertIn("after", props)
            
            req = schema_data["required"]
            self.assertEquals(len(req), 0)
            
            for key, value in props.items():
                self.assertIn("description", value)
                self.assertIn("type", value)
                self.assertEquals("integer", value["type"])
                
            self.assertIn("profile", item["@controls"])
            self.assertEquals(item["@controls"]["profile"]["href"], FORUM_USER_PROFILE)                
                              

    def test_get_users_mimetype(self):
        """
        Checks that GET Messages return correct status code and data format
        """
        print "("+self.test_get_users_mimetype.__name__+")", self.test_get_users_mimetype.__doc__

        #Check that I receive status code 200
        resp = self.client.get(self.url)
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers.get("Content-Type",None),
                          "{};{}".format(MASONJSON, FORUM_USER_PROFILE))

    def test_add_user(self):
        """
        Checks that the user is added correctly

        """
        print "("+self.test_add_user.__name__+")", self.test_add_user.__doc__

        # With a complete request
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_1_request)
                               )
        self.assertEquals(resp.status_code, 201)
        self.assertIn("Location", resp.headers)
        url = resp.headers["Location"]
        resp2 = self.client.get(url)
        self.assertEquals(resp2.status_code, 200)

        #With just mandaaory parameters
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_2_request)
                               )
        self.assertEquals(resp.status_code, 201)
        self.assertIn("Location", resp.headers)
        url = resp.headers["Location"]
        resp2 = self.client.get(url)
        self.assertEquals(resp2.status_code, 200)

    def test_add_user_missing_mandatory(self):
        """
        Test that it returns error when is missing a mandatory data
        """
        print "("+self.test_add_user_missing_mandatory.__name__+")", self.test_add_user_missing_mandatory.__doc__

        # Removing nickname
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_wrong_2_request)
                               )
        self.assertEquals(resp.status_code, 400)

        #Removing avatar
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_wrong_3_request)
                               )
        self.assertEquals(resp.status_code, 400)

    def test_add_existing_user(self):
        """
        Testign that trying to add an existing user will fail

        """
        print "("+self.test_add_existing_user.__name__+")", self.test_add_existing_user.__doc__
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_wrong_1_request)
                               )
        self.assertEquals(resp.status_code, 409)

    def test_add_bad_formmatted(self):
        """
        Test that it returns error when address is bad formatted
        """
        print "("+self.test_add_bad_formmatted.__name__+")", self.test_add_bad_formmatted.__doc__

        # Removing nickname
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_wrong_4_request)
                               )
        self.assertEquals(resp.status_code, 400)

    def test_wrong_type(self):
        """
        Test that return adequate error if sent incorrect mime type
        """
        print "("+self.test_wrong_type.__name__+")", self.test_wrong_type.__doc__
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": "text/html"},
                                data=json.dumps(self.user_1_request)
                               )
        self.assertEquals(resp.status_code, 415)

class UserTestCase (ResourcesAPITestCase):

    def setUp(self):
        super(UserTestCase, self).setUp()
        user1_nickname = "AxelW"
        user2_nickname = "Jacobino"
        self.url1 = resources.api.url_for(resources.User,
                                          nickname=user1_nickname,
                                          _external=False)
        self.url_wrong = resources.api.url_for(resources.User,
                                               nickname=user2_nickname,
                                               _external=False)
    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        print "("+self.test_url.__name__+")", self.test_url.__doc__
        url = "/forum/api/users/AxelW/"
        with resources.app.test_request_context(url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.User)

    """#TODO 4 Implement methods for this class"""

class HistoryTestCase (ResourcesAPITestCase):


    def setUp(self):
        super(HistoryTestCase, self).setUp()
        self.url1= resources.api.url_for(resources.History, nickname="AxelW",
                                         _external=False)
        self.messages1_number = 2
        self.url2= resources.api.url_for(resources.History, nickname="Mystery",
                                         _external=False)
        self.messages2_number = 2
        self.url3 = self.url1+"?length=1"
        self.messages3_number = 1
        self.url4 = self.url1+"?after=1362317481"
        self.messages4_number = 1
        self.url5 = self.url1+"?before=1362317481"
        self.messages5_number = 1
        self.url6 = self.url1+"?before=1362317481&after=1362217481"
        self.url_wrong= resources.api.url_for(resources.History, nickname="WRONG",
                                         _external=False)


    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        print "("+self.test_url.__name__+")", self.test_url.__doc__,
        url = "/forum/api/users/AxelW/history/"
        with resources.app.test_request_context(url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.History)

    """#TODO 4 Implement methods for this class"""

if __name__ == "__main__":
    print "Start running tests"
    unittest.main()
