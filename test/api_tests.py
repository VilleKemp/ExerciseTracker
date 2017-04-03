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
initial_users = 4


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


class UsersTestCase (ResourcesAPITestCase):
    user_1_request = {
        "username": "kalle",
        "password": "hunter2",
        "avatar": 123,
        "description": "minu juuri",
        "visibility": 1
        
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
        _url = "/exercisetracker/api/users/"
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
        
        self.assertIn("href", controls["self"])
        self.assertEquals(controls["self"]["href"], self.url)
        
        items = data["items"]
        self.assertEquals(len(items), initial_users)
        
        for item in items:
            self.assertIn("username", item)
            self.assertIn("avatar", item)
            self.assertIn("description", item)
            self.assertIn("visibility", item)
            self.assertIn("@controls", item)
            self.assertIn("self", item["@controls"])
            self.assertIn("href", item["@controls"]["self"])
            self.assertEquals(item["@controls"]["self"]["href"], resources.api.url_for(resources.Users, username=item["username"], _external=False))

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
        
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        
        controls = data["@controls"]
        self.assertIn("self", controls)

class UserTestCase (ResourcesAPITestCase):
    user_1_request = {
        "username": "Mystery",
        "password": "hunter2",
        "avatar": 123,
        "description": "minu juuri",
        "visibility": 1
        
    }    

    def setUp(self):
        super(UserTestCase, self).setUp()
        user1_nickname = "Mystery"
        user2_nickname = "M"
        self.url1 = resources.api.url_for(resources.User,
                                          username=user1_nickname,
                                          _external=False)
        self.url_wrong = resources.api.url_for(resources.User,
                                               username=user2_nickname,
                                            _external=False)
        """
    def test_url(self):
        """
       # Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        print "("+self.test_url.__name__+")", self.test_url.__doc__
        url = "/forum/api/users/AxelW/"
        with resources.app.test_request_context(url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.User)
        """
    def test_get_user(self):
        
        """
        Test get user method
        """
        print "("+self.test_get_user.__name__+")", self.test_get_user.__doc__
        #Check that I receive status code 200
  
        resp = self.client.get(flask.url_for("user",username="Mystery"))

        
        self.assertEquals(resp.status_code, 200)

        # Check that I receive a collection and adequate href
        data = json.loads(resp.data)

        controls = data["@controls"]
        self.assertIn("self", controls)
        
        self.assertIn("href", controls["self"])

    def test_modify_user(self):
        """
        incomplete

        """
        print "("+self.test_modify_user.__name__+")", self.test_modify_user.__doc__

        # With a complete request
        resp = self.client.put(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.user_1_request)
                               )
        
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)
        
        controls = data["@controls"]
        self.assertIn("self", controls)

    def test_delete_user(self):
        """

        """
        print "("+self.test_delete_user.__name__+")", self.test_delete_user.__doc__

        resp = self.client.delete(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON})
        
        self.assertEquals(resp.status_code, 204)
        #Run the same request twice. second should fail because the user is already deleted
        resp = self.client.delete(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON})       
        self.assertEquals(resp.status_code, 404)

        
#TODO TONI
#tee exercise testit. user testit on kesken. lisään ne myöhemmin 
if __name__ == "__main__":
    print "Start running tests"
    unittest.main()                       
                              
