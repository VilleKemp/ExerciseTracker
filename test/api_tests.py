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
FORUM_EXERCISE_PROFILE = "/profiles/exercise-profile/"
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
    incomplete_request = {
        "username": "kalle",
        "password": "hunter2",
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
        

        #check header
        resp = self.client.post(resources.api.url_for(resources.Users),
                                data=json.dumps(self.user_1_request)
                               )
        self.assertEquals(resp.status_code, 415)

        #incomplete request. missing avatar field
        resp = self.client.post(resources.api.url_for(resources.Users),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.incomplete_request)
                               )
        self.assertEquals(resp.status_code, 400)

        
        

class UserTestCase (ResourcesAPITestCase):
    user_1_request = {
        "username": "Mystery",
        "password": "hunter2",
        "avatar": 123,
        "description": "minu juuri",
        "visibility": 1
        
    }
    wrong_request = {
        "username": "Nobody",
        "password": "hunter2",
        "avatar": 123,
        "description": "minu juuri",
        "visibility": 1
        
    }

    incomplete_request = {
        "username": "Mystery",
        "password": "hunter2",
        "avatar": 123,
        "description": "minu juuri",
        
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

        #with wrong name. expect 404
        resp = self.client.get(flask.url_for("user",username="nobody"))
        self.assertEquals(resp.status_code, 404)        

    def test_modify_user(self):
        """
        Test modify user

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

        #header check
        resp = self.client.put(flask.url_for("user",username="Mystery"),
                                data=json.dumps(self.user_1_request)
                               )
    
        self.assertEquals(resp.status_code, 415)

        #with incomplete request
        resp = self.client.put(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.incomplete_request)
                               )        
        self.assertEquals(resp.status_code, 400)

        #with wrong name
        resp = self.client.put(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.wrong_request)
                               )        
        self.assertEquals(resp.status_code, 500)
    
        
    def test_delete_user(self):
        """
        Test delete user method
        """
        print "("+self.test_delete_user.__name__+")", self.test_delete_user.__doc__

        resp = self.client.delete(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON})
        
        self.assertEquals(resp.status_code, 204)
        #Run the same request twice. second should fail because the user is already deleted
        resp = self.client.delete(flask.url_for("user",username="Mystery"),
                                headers={"Content-Type": JSON})       
        self.assertEquals(resp.status_code, 404)
        #header check
        resp = self.client.delete(flask.url_for("user",username="Dakka"),
                                headers={"Content-Type": "not right"})       
        self.assertEquals(resp.status_code, 415)
        

class FriendsTestCase (ResourcesAPITestCase):
    aa = {
    "username": "Dakka",
    "friendname": "Sekoitus"
    }

    remove = {"username": "Mystery",
              "friendname" : "M"}
    incomplete = {"username": "Mystery"}
    

    

    def setUp(self):
        super(FriendsTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Friends,username="Mystery",
                                         
                                         _external=False)

    def test_get_friends(self):
        
        print "("+self.test_get_friends.__name__+")", self.test_get_friends.__doc__

        resp = self.client.get(flask.url_for("friends",username="Mystery"),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 200)
        #
        resp = self.client.get(flask.url_for("friends",username="Mysterya"),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 404)

        

    
    def test_add_friend(self):
        print "("+self.test_add_friend.__name__+")", self.test_add_friend.__doc__
        #Header check
        resp = self.client.post(flask.url_for("friends",username="Dakka"),
                                headers={"Content-Type": "not json"},
                                data = json.dumps(self.aa))
        self.assertEquals(resp.status_code, 415)

        #proper format. should be success
        resp = self.client.post(flask.url_for("friends",username="Dakka"),
                                headers={"Content-Type": JSON},
                                data = json.dumps(self.aa))
        self.assertEquals(resp.status_code, 204)
        #incomplete
        resp = self.client.post(flask.url_for("friends",username="Dakka"),
                                headers={"Content-Type": JSON},
                                data = json.dumps(self.incomplete))
        self.assertEquals(resp.status_code, 400)


        
          
    
    
    def test_delete_friend(self):
        print "("+self.test_delete_friend.__name__+")", self.test_delete_friend.__doc__

        #Proper format
        resp = self.client.delete(flask.url_for("friends",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data = json.dumps(self.remove))
        self.assertEquals(resp.status_code, 204)
        #header
        resp = self.client.delete(flask.url_for("friends",username="Mystery"),
                                headers={"Content-Type": "SON"},
                                data = json.dumps(self.remove))
        self.assertEquals(resp.status_code, 415)

        #resend proper request. should yield 404
        resp = self.client.delete(flask.url_for("friends",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data = json.dumps(self.remove))
        self.assertEquals(resp.status_code, 404)
    
        #send wrong request
        resp = self.client.delete(flask.url_for("friends",username="Mystery"),
                                headers={"Content-Type": JSON},
                                data = json.dumps(self.incomplete))
        self.assertEquals(resp.status_code, 400)
    
        
#TODO TONI
#tee exercise testit. user testit on kesken. lisään ne myöhemmin
class ExercisesTestCase (ResourcesAPITestCase):

    #USER1_NICKNAME = 'Mystery'
    #USER1_ID = 1
    #EXERCISE1_ID=4
    exercise1_request = { 'exercise_id': 4,
                            'user_id': 1,
                            'username': 'Mystery',
                            'type' : 'jump',
                            'value': 1,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 0,
                            'timeunit': 'h'
    }

    exercise_mod_req_1 = { 'exercise_id': 4,
                            'user_id': 1,
                            'username': 'Mystery',
                            'type' : 'jump',
                            'value': 1,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 0,
                            'timeunit': 'h'
    }
    def setUp(self):
        super(ExercisesTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Exercises,
                                         _external=False)

    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() shuould work.
        _url = "/exercisetracker/api/exercises/"
        print "("+self.test_url.__name__+")", self.test_url.__doc__,
        with resources.app.test_request_context(_url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Exercises)

    def test_get_exercises(self):
        """
        Checks that GET exercises return correct status code and data format
        """
        print "("+self.test_get_exercises.__name__+")", self.test_get_exercises.__doc__
        #Check that I receive status code 200
        resp = self.client.get(flask.url_for("exercises"))
        print flask.url_for("exercises")
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
            self.assertIn("type", item)
            self.assertIn("value", item)
            self.assertIn("valueunit", item)
            self.assertIn("date", item)
            self.assertIn("time", item)
            self.assertIn("timeunit", item)
            self.assertIn("@controls", item)
            self.assertIn("self", item["@controls"])
            self.assertIn("href", item["@controls"]["self"])
            self.assertEquals(item["@controls"]["self"]["href"], resources.api.url_for(resources.Exercises, exercise_id=item["exercise_id"], _external=False))

    def test_add_exercise(self):
        """
        Checks that the exercise is added correctly

        """
        print "("+self.test_add_exercise.__name__+")", self.test_add_exercise.__doc__

        # With a complete request
        resp = self.client.post(resources.api.url_for(resources.Exercises),
                                headers={"Content-Type": JSON},
                                data=json.dumps(self.exercise1_request)
                               )
        
        self.assertEquals(resp.status_code, 201)
        data = json.loads(resp.data)
        
        controls = data["@controls"]
        #self.assertIn("self", controls)

class ExerciseTestCase (ResourcesAPITestCase):

    
    #USER1_NICKNAME = 'Mystery'
    #USER1_ID = 1
    #EXERCISE1_ID=4

    def setUp(self):
        super(ExerciseTestCase, self).setUp()
        self.url = resources.api.url_for(resources.Exercise,
                                         exercise_id="0",
                                         _external=False)
        self.url_wrong = resources.api.url_for(resources.Exercise,
                                        exercise_id="200",
                                        _external=False)

    def test_url(self):
        """
        Checks that the URL points to the right resource
        """
        #NOTE: self.shortDescription() should work.
        _url = "/exercisetracker/api/exercises/<exercise_id>/"
        print "("+self.test_url.__name__+")", self.test_url.__doc__,
        with resources.app.test_request_context(_url):
            rule = flask.request.url_rule
            view_point = resources.app.view_functions[rule.endpoint].view_class
            self.assertEquals(view_point, resources.Exercise)

    def test_wrong_url(self):
        """
        Checks that GET Exercise return correct status code if given a
        wrong message
        """
        resp = self.client.get(self.url_wrong, "0")
        self.assertEquals(resp.status_code, 404)

    exercise1_request = { 'exercise_id': 4,
                            'user_id': 1,
                            'username': 'Mystery',
                            'type' : 'jump',
                            'value': 1,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 0,
                            'timeunit': 'h'
    }

    exercise_mod_req_1 = { 'exercise_id': 4,
                            'user_id': 1,
                            'username': 'Mystery',
                            'type' : 'jump',
                            'value': 1,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 0,
                            'timeunit': 'h'
    }

    exercise_wrong_req_1 = { 'exercise_id': -9
    }
    exercise_wrong_req_2 = { 'time': -9
    }
    def test_get_exercise(self):
        """
        Checks that GET Exercise return correct status code and data format
        """
        print "("+self.test_get_exercise.__name__+")", self.test_get_exercise.__doc__
        #with resources.app.test_client() as client:
        resp = self.client.get(flask.url_for("exercise",exercise_id=1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 200)
        data = json.loads(resp.data)

        #Check controls
        controls = data["@controls"]
        self.assertIn("self", controls)
        self.assertIn("forum:add-exercise", controls)
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
        self.assertEquals(msg_ctrl["href"], "/forum/api/exercises/")
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
            self.assertEquals(item["@controls"]["self"]["href"], resources.api.url_for(resources.Exercise, exercise_id=item["id"], _external=False))
            self.assertIn("profile", item["@controls"])
            self.assertEquals(item["@controls"]["profile"]["href"], FORUM_EXERCISE_PROFILE)

    def test_get_exercise_mimetype(self):
        """
        Checks that GET Exerrcises return correct status code and data format
        """
        print "("+self.test_get_exercise_mimetype.__name__+")", self.test_get_exercise_mimetype.__doc__

        #Check that I receive status code 200
        resp = self.client.get(flask.url_for("exercise",exercise_id=1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 200)
        self.assertEquals(resp.headers.get("Content-Type",None),
                          "{};{}".format(MASONJSON, FORUM_EXERCISE_PROFILE))

    def test_modify_exercise (self):
        """
        Modify an exsiting exercise and check that the exercise has been modified correctly in the server
        """
        print "("+self.test_modify_exercise.__name__+")", self.test_modify_exercise.__doc__
        resp = self.client.put(flask.url_for("exercise",exercise_id=1),
                               data=json.dumps(self.exercise_mod_req_1),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 204)
        #Check that the message has been modified
        resp2 = self.client.get(flask.url_for("exercise",exercise_id=1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp2.status_code, 200)
        data = json.loads(resp2.data)
        #Check that the title and the body of the message has been modified with the new data
        self.assertEquals(data["type"], self.exercise_mod_req_1["type"])
        self.assertEquals(data["date"], self.exercise_mod_req_1["date"])

    def test_modify_unexisting_exercise(self):
        """
        Try to modify a exercise that does not exist
        """
        print "("+self.test_modify_unexisting_exercise.__name__+")", self.test_modify_unexisting_exercise.__doc__
        resp = self.client.put(flask.url_for("exercise",exercise_id=200),
                                data=json.dumps(self.exercise_mod_req_1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 404)


    def test_modify_wrong_exercise(self):
        """
        Try to modify a exercise sending wrong data
        """
        print "("+self.test_modify_wrong_exercise.__name__+")", self.test_modify_wrong_exercise.__doc__
        resp = self.client.put(flask.url_for("exercise",exercise_id=1),
                               data=json.dumps(self.exercise_wrong_req_1),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)        
        resp = self.client.put(flask.url_for("exercise",exercise_id=1),
                               data=json.dumps(self.exercise_wrong_req_2),
                               headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 400)


    def test_delete_exercise(self):
        """
        Checks that Delete Exercise return correct status code if corrected delete
        """
        print "("+self.test_delete_exercise.__name__+")", self.test_delete_exercise.__doc__
        resp = self.client.delete(flask.url_for("exercise",exercise_id=1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 204)
        resp2 = self.client.get(flask.url_for("exercise",exercise_id=1),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp2.status_code, 404)

    def test_delete_unexisting_exercise(self):
        """
        Checks that Delete Exercise return correct status code if given a wrong address
        """
        print "("+self.test_delete_unexisting_exercise.__name__+")", self.test_delete_unexisting_exercise.__doc__
        resp = self.client.delete(flask.url_for("exercise",exercise_id=200),
                                headers={"Content-Type": JSON})
        self.assertEquals(resp.status_code, 404)
        
if __name__ == "__main__":
    print "Start running tests"
    unittest.main()                       
                              
