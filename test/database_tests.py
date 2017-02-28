'''
Created on 13.02.2014
Modified on 01.02.2016
Database interface testing for all users related methods.
The user has a data model represented by the following User dictionary:
    {'public_profile': {'registrationdate': ,'nickname': ''
                       'signature': '','avatar': ''},
    'restricted_profile': {'firstname': '','lastname': '','email': '',
                          'website': '','mobile': '','skype': '',
                          'birthday': '','residence': '','gender': '',
                          'picture': ''}
    }
    where:
     - registrationdate: UNIX timestamp when the user registered in
                         the system
     - nickname: nickname of the user
     - signature: text chosen by the user for signature
     - avatar: name of the image file used as avatar
     - firstanme: given name of the user
     - lastname: of the user
     - email: current email of the user.
     - website: url with the user's personal page
     - mobile: string showing the user's phone number
     - skype: user's nickname in skype
     - residence: complete user's home address.
     - picture: file which contains an image of the user.
     - gender: User's gender ('male' or 'female').
     - birthday: int with the birthday of the user.


List of users has the following data model:
[{'nickname':'', 'registrationdate':''}, {'nickname':'', 'registrationdate':''}]


@author: ivan
'''
import unittest, sqlite3
from forum import database

#Path to the database file, different from the deployment db
DB_PATH = 'db/forum.db'
ENGINE = database.Engine(DB_PATH)

#CONSTANTS DEFINING DIFFERENT USERS AND USER PROPERTIES
USER1_NICKNAME = 'Mystery'
USER1_ID = 1
USER1 = {'username': USER1_NICKNAME,
                            'password' : 'passwd',
                            'avatar': 101,
                            'description': 'Olen uusi user',
                            'visibility': 1}
         
MODIFIED_USER1 =  {'username': USER1_NICKNAME,
                            'password' : 'salasana',
                            'avatar': 999,
                            'description': 'Olen vanha user',
                            'visibility': 0}
USER2_NICKNAME = 'M'
USER2_ID = 2
USER2 = {'username': USER2_NICKNAME,
         'password' : 'pwd1',
                            'avatar': 101,
                            'description': 'uusi user',
                             'visibility': 0}
NEW_USER_NICKNAME = 'sully'
NEW_USER = {'username': NEW_USER_NICKNAME,
         'password' : 'pwd1',
                            'avatar': 101,
                            'description': 'uusi user',
                             'visibility': 0}
USER_WRONG_NICKNAME = 'Batty'
INITIAL_SIZE = 4

#Exercise constants
USER1_NICKNAME = 'Mystery'
USER1_ID = 1
EXERCISE1_ID=4
EXERCISE1 = { 'exercise_id': 4,
              'user_id': 1,
    'username': USER1_NICKNAME,
                            'type' : 'jump',
                            'value': 1,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 0,
                            'timeunit': 'h'
}
         
MODIFIED_EXERCISE1 =  {
'exercise_id' : 4,
'user_id': 1,
    'username': USER1_NICKNAME,
                            'type' : 'jump2',
                            'value': 11111,
                            'valueunit': 'sm',
                            'date': '12.12.2012',
                            'time': 21312,
                            'timeunit': 'kh'
}
USER2_NICKNAME = 'M'
USER2_ID = 2
EXERCISE2 = {
'exercise_id': 1, 
'user_id': 2,
    'username': USER2_NICKNAME,
                            'type' : 'run',
                            'value': 101,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 1,
                            'timeunit': 'h'
}

EXERCISE3 = {
'exercise_id': 2, 
'user_id': 2,
    'username': USER2_NICKNAME,
                            'type' : 'jog',
                            'value': 1010000,
                            'valueunit': 'm',
                            'date': '12.12.2012',
                            'time': 1,
                            'timeunit': 'h'
}

#NEW_USER_NICKNAME = 'sully'
NEW_EXERCISE = {
 
'user_id': 1,
    'username': USER1_NICKNAME,
                            'type' : 'run',
                            'value': 100,
                            'valueunit': 'km',
                            'date': '12.12.2012',
                            'time': 500,
                            'timeunit': 'h'
}
EXERCISE_WRONG_ID = 999
EXERCISE_SIZE = 4




class UserDBAPITestCase(unittest.TestCase):
    '''
    Test cases for the Users related methods.
    '''
    #INITIATION AND TEARDOWN METHODS
    @classmethod
    def setUpClass(cls):
        ''' Creates the database structure. Removes first any preexisting
            database file
        '''
        print "Testing ", cls.__name__
        ENGINE.remove_database()
        ENGINE.create_tables()

    @classmethod
    def tearDownClass(cls):
        '''Remove the testing database'''
        print "Testing ENDED for ", cls.__name__
        ENGINE.remove_database()

    def setUp(self):
        '''
        Populates the database
        '''
        #This method load the initial values from forum_data_dump.sql
        #ENGINE.populate_tables()
        
        con = sqlite3.connect('db/forum.db')

        cur = con.cursor()
        keys_on = 'PRAGMA foreign_keys = ON'
        cur.execute(keys_on)
        #Populate database from dump

        dump = "db/forum_data_dump.sql"
        with open (dump) as f:
            sql = f.read()
            cur = con.cursor()
            cur.executescript(sql)
        #Creates a Connection instance to use the API
        self.connection = ENGINE.connect()

    def tearDown(self):
        '''
        Close underlying connection and remove all records from database
        '''
        self.connection.close()
        ENGINE.clear()



    def test_get_user(self):
        '''
        Test get_user with id Mystery and HockeyFan
        '''
        print '('+self.test_get_user.__name__+')', \
              self.test_get_user.__doc__

        #Test with an existing user
        user = self.connection.get_user(USER1_NICKNAME)
        self.assertDictContainsSubset(user, USER1)

    

    def test_get_users(self):
        '''
        Test that get_users work correctly and extract required user info
        '''
        print '('+self.test_get_users.__name__+')', \
              self.test_get_users.__doc__
        users = self.connection.get_users()
        #Check that the size is correct
        self.assertEquals(len(users), INITIAL_SIZE)
        #Iterate throug users and check if the users with USER1_ID and
        #USER2_ID are correct:
        for user in users:
            if user['username'] == USER1_NICKNAME:
                self.assertDictContainsSubset(user, USER1)
            elif user['username'] == USER2_NICKNAME:
                self.assertDictContainsSubset(user, USER2)

    def test_delete_user(self):
        '''
        Test that the user Mystery is deleted
        '''
        print '('+self.test_delete_user.__name__+')', \
              self.test_delete_user.__doc__
        resp = self.connection.delete_user(USER1_NICKNAME)
        self.assertTrue(resp)
        #Check that the users has been really deleted throug a get
        resp2 = self.connection.get_user(USER1_NICKNAME)
        self.assertIsNone(resp2)

#TODO testataan cascade
 #Check that the user does not have associated any message
 #       resp3 = self.connection.get_exercise(username=USER1_NICKNAME)
  #      self.assertEquals(len(resp3), 0)

    def test_delete_user_noexistingusername(self):
        '''
        Test delete_user with  Batty (no-existing)
        '''
        print '('+self.test_delete_user_noexistingusername.__name__+')', \
              self.test_delete_user_noexistingusername.__doc__
        #Test with an existing user
        resp = self.connection.delete_user(USER_WRONG_NICKNAME)
        self.assertFalse(resp)


    def test_modify_user(self):
        '''
        Test that the user Mystery is modifed
        '''
        print '('+self.test_modify_user.__name__+')', \
              self.test_modify_user.__doc__
        #Get the modified user
        resp = self.connection.modify_user(USER1_NICKNAME, MODIFIED_USER1)
        self.assertEquals(resp, USER1_NICKNAME)
        #Check that the users has been really modified through a get
        resp2 = self.connection.get_user(USER1_NICKNAME)
        #resp_p = resp2['public_profile']
        #resp_r_profile = resp2['restricted_profile']
        #Check the expected values
        #p_profile = MODIFIED_USER1['public_profile']
        #r_profile = MODIFIED_USER1['restricted_profile']
        #self.assertEquals(p_profile['signature'],
         #                 resp_p_profile['signature'])
        self.assertEquals(MODIFIED_USER1['avatar'], resp2['avatar'])
        self.assertEquals(MODIFIED_USER1['description'], resp2['description'])
        self.assertEquals(MODIFIED_USER1['password'], resp2['password'])
        self.assertEquals(MODIFIED_USER1['visibility'], resp2['visibility'])
        self.assertDictContainsSubset(resp2, MODIFIED_USER1)

    def test_modify_user_noexistingnickname(self):
        '''
        Test modify_user with  user Batty (no-existing)
        '''
        print '('+self.test_modify_user_noexistingnickname.__name__+')', \
              self.test_modify_user_noexistingnickname.__doc__
        #Test with an existing user
        resp = self.connection.modify_user(USER_WRONG_NICKNAME, USER1)
        self.assertIsNone(resp)

    def test_append_user(self):
        '''
        Test that I can add new users
        '''
        print '('+self.test_append_user.__name__+')', \
              self.test_append_user.__doc__
        username = self.connection.append_user(NEW_USER_NICKNAME, NEW_USER)
        self.assertIsNotNone(username)
        self.assertEquals(username, NEW_USER_NICKNAME)
        #Check that the messages has been really modified through a get
        resp2 = self.connection.get_user(username)
        self.assertDictContainsSubset(NEW_USER,
                                      resp2)


    def test_append_existing_user(self):
        '''
        Test that I cannot add two users with the same name
        '''
        print '('+self.test_append_existing_user.__name__+')', \
              self.test_append_existing_user.__doc__
        username = self.connection.append_user(USER1_NICKNAME, NEW_USER)
        self.assertIsNone(username)

    def test_get_user_id(self):
        '''
        Test that get_user_id returns the right value given a nickname
        '''
        print '('+self.test_get_user_id.__name__+')', \
              self.test_get_user_id.__doc__
        id = self.connection.get_user_id(USER1_NICKNAME)
        self.assertEquals(USER1_ID, id)
        id = self.connection.get_user_id(USER2_NICKNAME)
        self.assertEquals(USER2_ID, id)

    def test_get_user_id_unknown_user(self):
        '''
        Test that get_user_id returns None when the nickname does not exist
        '''
        print '('+self.test_get_user_id.__name__+')', \
              self.test_get_user_id.__doc__
        id = self.connection.get_user_id(USER_WRONG_NICKNAME)
        self.assertIsNone(id)

    def test_not_contains_user(self):
        '''
        Check if the database does not contain users with id Batty
        '''
        print '('+self.test_contains_user.__name__+')', \
              self.test_contains_user.__doc__
        self.assertFalse(self.connection.contains_user(USER_WRONG_NICKNAME))

    def test_contains_user(self):
        '''
        Check if the database contains users with nickname Mystery and HockeyFan
        '''
        print '('+self.test_contains_user.__name__+')', \
              self.test_contains_user.__doc__
        self.assertTrue(self.connection.contains_user(USER1_NICKNAME))
        self.assertTrue(self.connection.contains_user(USER2_NICKNAME))


##Exercise tests

    def test_create_exercise(self):

        print '('+self.test_create_exercise.__name__+')', \
              self.test_create_exercise.__doc__
        exercise_id = self.connection.create_exercise(NEW_EXERCISE)
        self.assertIsNotNone(exercise_id)
        
        #self.assertEquals(username, NEW_USER_NICKNAME)
        #Check that the messages has been really modified through a get
        resp2 = self.connection.get_exercise(exercise_id)
        self.assertDictContainsSubset(NEW_EXERCISE,
                                      resp2)


    def test_get_exercise(self):
        '''
        Test get_user with id Mystery and HockeyFan
        '''
        print '('+self.test_get_exercise.__name__+')', \
              self.test_get_exercise.__doc__

        #Test with an existing user
        exercise = self.connection.get_exercise(EXERCISE1_ID)
        self.assertDictContainsSubset(exercise, EXERCISE1)

    

    def test_get_exercises(self):
        '''
        Test that get_users work correctly and extract required user info
        '''
        print '('+self.test_get_exercises.__name__+')', \
              self.test_get_exercises.__doc__
        exercises = self.connection.get_exercises()
        #Check that the size is correct
        self.assertEquals(len(exercises), EXERCISE_SIZE)
        #Iterate throug users and check if the users with USER1_ID and
        #USER2_ID are correct:
        for exercise in exercises:
            if exercise['type'] == 'jump':
                self.assertDictContainsSubset(exercise, EXERCISE1)
            elif exercise['type'] == 'run':
                self.assertDictContainsSubset(exercise, EXERCISE2)

    def test_get_user_exercises(self):
        '''
        Test that get_users work correctly and extract required user info
        '''
        print '('+self.test_get_user_exercises.__name__+')', \
              self.test_get_user_exercises.__doc__
        exercises = self.connection.get_user_exercises('M')
        #Check that the size is correct
        self.assertEquals(len(exercises), 2)
        #Iterate throug users and check if the users with USER1_ID and
        #USER2_ID are correct:
        for exercise in exercises:
            if exercise['type'] == 'jog':
                self.assertDictContainsSubset(exercise, EXERCISE3)
            elif exercise['type'] == 'run':
                self.assertDictContainsSubset(exercise, EXERCISE2)


    def test_delete_exercise(self):
        '''
        Test that the user Mystery is deleted
        '''
        print '('+self.test_delete_exercise.__name__+')', \
              self.test_delete_exercise.__doc__
        resp = self.connection.delete_exercise(EXERCISE1_ID)
        self.assertTrue(resp)
        #Check that the users has been really deleted throug a get
        resp2 = self.connection.get_exercise(EXERCISE1_ID)
        self.assertIsNone(resp2)

#TODO testataan cascade
 #Check that the user does not have associated any message
 #       resp3 = self.connection.get_exercise(username=USER1_NICKNAME)
  #      self.assertEquals(len(resp3), 0)

    def test_delete_exercise_noexistingusername(self):
        '''
        Test delete_user with  Batty (no-existing)
        '''
        print '('+self.test_delete_exercise_noexistingusername.__name__+')', \
              self.test_delete_exercise_noexistingusername.__doc__
        #Test with an existing user
        resp = self.connection.delete_exercise(EXERCISE_WRONG_ID)
        self.assertFalse(resp)


    def test_modify_exercise(self):
        '''
        Test that the user Mystery is modifed
        '''
        print '('+self.test_modify_exercise.__name__+')', \
              self.test_modify_exercise.__doc__
        #Get the modified user
        resp = self.connection.modify_exercise(EXERCISE1_ID, MODIFIED_EXERCISE1)
        self.assertTrue(resp)
        #Check that the users has been really modified through a get
        resp2 = self.connection.get_exercise(EXERCISE1_ID)
        #resp_p = resp2['public_profile']
        #resp_r_profile = resp2['restricted_profile']
        #Check the expected values
        #p_profile = MODIFIED_USER1['public_profile']
        #r_profile = MODIFIED_USER1['restricted_profile']
        #self.assertEquals(p_profile['signature'],
         #                 resp_p_profile['signature'])
        self.assertEquals(MODIFIED_EXERCISE1['type'], resp2['type'])
        self.assertEquals(MODIFIED_EXERCISE1['value'], resp2['value'])
        self.assertEquals(MODIFIED_EXERCISE1['valueunit'], resp2['valueunit'])
        self.assertEquals(MODIFIED_EXERCISE1['date'], resp2['date'])
        self.assertEquals(MODIFIED_EXERCISE1['time'], resp2['time'])
        self.assertEquals(MODIFIED_EXERCISE1['timeunit'], resp2['timeunit'])
        self.assertDictContainsSubset(resp2, MODIFIED_EXERCISE1)

    def test_modify_exercise_noexistingID(self):
        '''
        Test modify_user with  user Batty (no-existing)
        '''
        print '('+self.test_modify_exercise_noexistingID.__name__+')', \
              self.test_modify_exercise_noexistingID.__doc__
        #Test with an existing user
        resp = self.connection.modify_user(EXERCISE_WRONG_ID, EXERCISE1)
        self.assertIsNone(resp)
    

 
if __name__ == '__main__':
    print 'Start running user tests'
    unittest.main()
