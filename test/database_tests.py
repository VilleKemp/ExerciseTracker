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
                            'description': 'Olen uusi user' }
         
MODIFIED_USER1 = {'public_profile': {'registrationdate': 1362015937,
                                     'nickname': USER1_NICKNAME,
                                     'signature': 'New signature',
                                     'avatar': 'new_avatar.jpg'},
                  'restricted_profile': {'firstname': 'Mystery',
                                         'lastname': 'Williams',
                                         'email': 'new_email@myname',
                                         'birthday': '1940-01-22',
                                         'residence': 'Bank of Zurich, Spain',
                                         'gender': 'Female',
                                         'picture': 'new_picture.jpg',
                                         'website': 'http: //www.mynewsite.com',
                                         'mobile': "8002020",
                                         'skype': 'mystery'}
                  }
USER2_NICKNAME = 'M'
USER2_ID = 2
USER2 = {'username': USER2_NICKNAME,
         'password' : 'pwd1',
                            'avatar': 101,
                            'description': 'uusi user' }
NEW_USER_NICKNAME = 'sully'
NEW_USER = {'public_profile': {'signature': 'I am blue',
                               'avatar': 'na_vi.jpg'},
            'restricted_profile': {'firstname': 'Jake', 'lastname': 'Sully',
                                   'email': 'sully@rda.com',
                                   'birthday': '2011-12-10',
                                   'website': 'http: //www.pandora.com/',
                                   'residence': 'USA', 'gender': 'Male',
                                   'picture': 'na_vi2.png',
                                   'mobile': "83232323",
                                   'skype': 'jakesully'},
            }
USER_WRONG_NICKNAME = 'Batty'
INITIAL_SIZE = 4


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
        print '('+self.test_delete_user_noexistingnickname.__name__+')', \
              self.test_delete_user_noexistingusername.__doc__
        #Test with an existing user
        resp = self.connection.delete_user(USER_WRONG_NICKNAME)
        self.assertFalse(resp)

 
if __name__ == '__main__':
    print 'Start running user tests'
    unittest.main()
