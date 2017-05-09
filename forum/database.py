'''
Created on 13.02.2013

Modified on 09.03.2017

Provides the database API to access the forum persistent data.

@authors: Toni Narhi & Ville Kemppainen 
'''

#from datetime import datetime
import time, sqlite3, os#, re
#Default paths for .db and .sql files to create and populate the database.
DEFAULT_DB_PATH = 'db/forum.db'
DEFAULT_SCHEMA = "db/forum_schema_dump.sql"
DEFAULT_DATA_DUMP = "db/forum_data_dump.sql"


class Engine(object):
    '''
    Abstraction of the database.

    It includes tools to create, configure,
    populate and connect to the sqlite file. You can access the Connection
    instance, and hence, to the database interface itself using the method
    :py:meth:`connection`.

    :Example:

    >>> engine = Engine()
    >>> con = engine.connect()

    :param db_path: The path of the database file (always with respect to the
        calling script. If not specified, the Engine will use the file located
        at *db/forum.db*

    '''
    def __init__(self, db_path=None):
        '''
        '''

        super(Engine, self).__init__()
        if db_path is not None:
            self.db_path = db_path
        else:
            self.db_path = DEFAULT_DB_PATH

    def connect(self):
        '''
        Creates a connection to the database.

        :return: A Connection instance
        :rtype: Connection

        '''
        return Connection(self.db_path)

    def remove_database(self):
        '''
        Removes the database file from the filesystem.

        '''
        if os.path.exists(self.db_path):
            #THIS REMOVES THE DATABASE STRUCTURE
            os.remove(self.db_path)

    def clear(self):
        '''
        Purge the database removing all records from the tables. However,
        it keeps the database schema (meaning the table structure)

        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        #THIS KEEPS THE SCHEMA AND REMOVE VALUES
        con = sqlite3.connect(self.db_path)
        #Activate foreing keys support
        cur = con.cursor()
        cur.execute(keys_on)
        with con:
            cur = con.cursor()
            cur.execute("DELETE FROM exercise")
            cur.execute("DELETE FROM users")
            #NOTE since we have ON DELETE CASCADE BOTH IN users_profile AND
            #friends, WE DO NOT HAVE TO WORRY TO CLEAR THOSE TABLES.

    #METHODS TO CREATE AND POPULATE A DATABASE USING DIFFERENT SCRIPTS
    def create_tables(self, schema=None):
        '''
        Create programmatically the tables from a schema file.

        :param schema: path to the .sql schema file. If this parmeter is
            None, then *db/forum_schema_dump.sql* is utilized.

        
        con = sqlite3.connect(self.db_path)
        if schema is None:
            schema = DEFAULT_SCHEMA
        try:
            with open(schema) as f:
                sql = f.read()
                cur = con.cursor()
                cur.executescript(sql)
        finally:
            con.close()
'''
       
        self.create_users_table()
        self.create_exercise_table()
        self.create_friends_table()   
    def populate_tables(self, dump=None):
        '''
        Populate programmatically the tables from a dump file.

        :param dump:  path to the .sql dump file. If this parmeter is
            None, then *db/forum_data_dump.sql* is utilized.

        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        con = sqlite3.connect(self.db_path)
        #Activate foreing keys support
        cur = con.cursor()
        cur.execute(keys_on)
        #Populate database from dump
        if dump is None:
            dump = DEFAULT_DATA_DUMP
        with open (dump) as f:
            sql = f.read()
            cur = con.cursor()
            cur.executescript(sql)

    #METHODS TO CREATE THE TABLES PROGRAMMATICALLY WITHOUT USING SQL SCRIPT
    def create_exercise_table(self):
        '''
        (Own implementation)

        Create the table ``exercise`` programmatically, without using .sql file.

        Print an error message in the console if it could not be created.

        :return: ``True`` if the table was successfully created or ``False``
            otherwise.

        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        stmnt = 'CREATE TABLE exercise(exercise_id INTEGER PRIMARY KEY AUTOINCREMENT, \
                    user_id INTEGER, username TEXT, \
                    type TEXT, value INTEGER, valueunit TEXT, \
                    date TEXT, time INTEGER, \
                    timeunit TEXT, \
                    FOREIGN KEY(user_id,username) \
                    REFERENCES users(user_id, username) ON DELETE SET NULL)'
        con = sqlite3.connect(self.db_path)
        with con:
            #Get the cursor object.
            #It allows to execute SQL code and traverse the result set
            cur = con.cursor()
            try:
                cur.execute(keys_on)
                #execute the statement
                cur.execute(stmnt)
            except sqlite3.Error, excp:
                print "Error %s:" % excp.args[0]
                return False
        return True

    def create_users_table(self):
        '''
        (Own implementation)
        Create the table ``users`` programmatically, without using .sql file.

        Print an error message in the console if it could not be created.

        :return: ``True`` if the table was successfully created or ``False``
            otherwise.

        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        stmnt = 'CREATE TABLE users(user_id INTEGER PRIMARY KEY AUTOINCREMENT,\
                                    username TEXT UNIQUE, password TEXT, \
                                    avatar BLOB, description TEXT, \
                                    visibility INTEGER, \
                                    UNIQUE(user_id, username))'
        #Connects to the database. Gets a connection object
        con = sqlite3.connect(self.db_path)
        with con:
            #Get the cursor object.
            #It allows to execute SQL code and traverse the result set
            cur = con.cursor()
            try:
                cur.execute(keys_on)
                #execute the statement
                cur.execute(stmnt)
            except sqlite3.Error, excp:
                print "Error %s:" % excp.args[0]
                return False
        return True



    def create_friends_table(self):
        '''
        Create the table ``friends`` programmatically, without using .sql file.

        Print an error message in the console if it could not be created.

        :return: ``True`` if the table was successfully created or ``False``
            otherwise.
        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        stmnt = 'CREATE TABLE friends (user_id INTEGER, friend_id INTEGER, \
                     PRIMARY KEY(user_id, friend_id), \
                     FOREIGN KEY(user_id) REFERENCES users(user_id) \
                     ON DELETE CASCADE, \
                     FOREIGN KEY(friend_id) REFERENCES users(user_id) \
                     ON DELETE CASCADE)'
        #Connects to the database. Gets a connection object
        con = sqlite3.connect(self.db_path)
        with con:
            #Get the cursor object.
            #It allows to execute SQL code and traverse the result set
            cur = con.cursor()
            try:
                cur.execute(keys_on)
                #execute the statement
                cur.execute(stmnt)
            except sqlite3.Error, excp:
                print "Error %s:" % excp.args[0]
        return None


class Connection(object):
    '''
    API to access the Forum database.

    The sqlite3 connection instance is accessible to all the methods of this
    class through the :py:attr:`self.con` attribute.

    An instance of this class should not be instantiated directly using the
    constructor. Instead use the :py:meth:`Engine.connect`.

    Use the method :py:meth:`close` in order to close a connection.
    A :py:class:`Connection` **MUST** always be closed once when it is not going to be
    utilized anymore in order to release internal locks.

    :param db_path: Location of the database file.
    :type dbpath: str

    '''
    def __init__(self, db_path):
        super(Connection, self).__init__()
        self.con = sqlite3.connect(db_path)

    def close(self):
        '''
        Closes the database connection, commiting all changes.

        '''
        if self.con:
            self.con.commit()
            self.con.close()

    #FOREIGN KEY STATUS
    def check_foreign_keys_status(self):
        '''
        Check if the foreign keys has been activated.

        :return: ``True`` if  foreign_keys is activated and ``False`` otherwise.
        :raises sqlite3.Error: when a sqlite3 error happen. In this case the
            connection is closed.

        '''
        try:
            #Create a cursor to receive the database values
            cur = self.con.cursor()
            #Execute the pragma command
            cur.execute('PRAGMA foreign_keys')
            #We know we retrieve just one record: use fetchone()
            data = cur.fetchone()
            is_activated = data == (1,)
            print "Foreign Keys status: %s" % 'ON' if is_activated else 'OFF'
        except sqlite3.Error, excp:
            print "Error %s:" % excp.args[0]
            self.close()
            raise excp
        return is_activated

    def set_foreign_keys_support(self):
        '''
        Activate the support for foreign keys.

        :return: ``True`` if operation succeed and ``False`` otherwise.

        '''
        keys_on = 'PRAGMA foreign_keys = ON'
        try:
            #Get the cursor object.
            #It allows to execute SQL code and traverse the result set
            cur = self.con.cursor()
            #execute the pragma command, ON
            cur.execute(keys_on)
            return True
        except sqlite3.Error, excp:
            print "Error %s:" % excp.args[0]
            return False

    def unset_foreign_keys_support(self):
        '''
        Deactivate the support for foreign keys.

        :return: ``True`` if operation succeed and ``False`` otherwise.

        '''
        keys_on = 'PRAGMA foreign_keys = OFF'
        try:
            #Get the cursor object.
            #It allows to execute SQL code and traverse the result set
            cur = self.con.cursor()
            #execute the pragma command, OFF
            cur.execute(keys_on)
            return True
        except sqlite3.Error, excp:
            print "Error %s:" % excp.args[0]
            return False

    #HELPERS
    #Here the helpers that transform database rows into dictionary. They work
    #similarly to ORM
    #EVERYTHING below this is our own implementation
    #Helpers for exercises
    def _create_exercise_object(self, row):

        '''
        It takes a :py:class:`sqlite3.Row` and transform it into a dictionary.

        :param row: The row obtained from the database.
        :type row: sqlite3.Row
        :return: a dictionary containing the following keys:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)
        '''
        return {'exercise_id': row['exercise_id'],
                    'user_id' : row['user_id'], 
                    'username': row['username'],
                    'type' : row['type'],
                    'value' : row['value'],
                    'valueunit' : row['valueunit'],
                    'date' : row['date'],
                    'time' : row['time'],
                    'timeunit' : row['timeunit']}

    def _create_exercise_list_object(self, row):

        '''
        Same as :py:meth:`_create_exercise_object`. However, the resulting
        dictionary is targeted to build messages in a list.

        :param row: The row obtained from the database.
        :type row: sqlite3.Row
        :return: a dictionary containing the following keys:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)
        '''
        return {'exercise_id': row['exercise_id'],
                    'user_id' : row['user_id'], 
                    'username': row['username'],
                    'type' : row['type'],
                    'value' : row['value'],
                    'valueunit' : row['valueunit'],
                    'date' : row['date'],
                    'time' : row['time'],
                    'timeunit' : row['timeunit']}




   

    #Helpers for users
    def _create_user_object(self, row):
        '''
        It takes a :py:class:`sqlite3.Row` and transform it into a dictionary.

        :param row: The row obtained from the database.
        :type row: sqlite3.Row
        :return: a dictionary containing the following keys:

            * ``username``: Name of the user (string)
            * ``password``: Password of the user(string)
            * ``avatar``: Users avatar (blob)
            * ``description``: Users description (string)
            * ``visibility``: Users visibility value (int)

        '''

        return {'username': row['username'],
                            'password':row['password'],
                            'avatar': row['avatar'],
                            'description': row ['description'],
                            'visibility': row ['visibility'] }

                

    def _create_user_list_object(self, row):
        '''
        Same as :py:meth:`_create_user_object`. However, the resulting
        dictionary is targeted to build users in a list.

        :param row: The row obtained from the database.
        :type row: sqlite3.Row
        :return: a dictionary containing the following keys:

            * ``username``: Name of the user (string)
            * ``password``: Password of the user(string)
            * ``avatar``: Users avatar (blob)
            * ``description``: Users description (string)
            * ``visibility``: Users visibility value (int)
        '''
        return {'username': row['username'],
                            'password':row['password'],
                            'avatar': row['avatar'],
                            'description': row ['description'],
                            'visibility': row ['visibility'] }

    def _create_friends_list_object(self,row):
  
        '''
        :param row: The row obtained from the database.
        :type row: sqlite3.Row
        :return: a dictionary containing the following keys:

            * ``friend_id``: Friends id.  (int)

        '''
        return {'friend_id': row['friend_id']}

    #API ITSELF
   

    #USER
    def get_users(self):
        '''
        Extracts all users in the database.

        :return: list of Users of the database. Each user is a dictionary
            that contains same keys as user_list_object

        '''
        #Create the SQL Statements
          #SQL Statement for retrieving the users
        query = 'SELECT users.* FROM users'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Create the cursor
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute main SQL Statement
        cur.execute(query)
        #Process the results
        rows = cur.fetchall()
        if rows is None:
            return None
        #Process the response.
        users = []
        for row in rows:
            users.append(self._create_user_list_object(row))
        return users

    def get_user(self, username):
        '''
        Extracts all the information of a user.

        :param str username: The nickname of the user to search for.
        :return: dictionary with the format provided in the method:
            :py:meth:`_create_user_object`

        '''
        #Create the SQL Statements
          #SQL Statement for retrieving the user given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement for retrieving the user information

        query2 = 'SELECT users.* FROM users\
                  WHERE users.user_id = ?'
          #Variable to be used in the second query.
        user_id = None
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute SQL Statement to retrieve the id given a nickname
        pvalue = (username,)
        cur.execute(query1, pvalue)
        #Extract the user id
        row = cur.fetchone()
        if row is None:
            return None
        user_id = row["user_id"]
        # Execute the SQL Statement to retrieve the user invformation.
        # Create first the valuse
        pvalue = (user_id, )
        #execute the statement
        cur.execute(query2, pvalue)
        #Process the response. Only one posible row is expected.
        row = cur.fetchone()
        return self._create_user_object(row)

    def get_username(self,user_id):
        """
        """
        query1 = 'SELECT username from users WHERE user_id = ?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute SQL Statement to retrieve the id given a nickname
        pvalue = (user_id,)
        cur.execute(query1, pvalue)
        #Extract the user id
        row = cur.fetchone()
        if row is None:
            return None
        username = row["username"]
 
        return username

    def delete_user(self, username):
        '''
        Remove all user information of the user with the nickname passed in as
        argument.

        :param str username: The nickname of the user to remove.

        :return: True if the user is deleted, False otherwise.

        '''
        #Create the SQL Statements
          #SQL Statement for deleting the user information
        query = 'DELETE FROM users WHERE username = ?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to delete
        pvalue = (username,)
        cur.execute(query, pvalue)
        self.con.commit()
        #Check that it has been deleted
        if cur.rowcount < 1:
            return False
        return True

    def modify_user(self, username, user):
        '''
        Modify the information of a user.

        :param str username: The nickname of the user to modify
        :param dict user: a dictionary with the information to be modified. The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'username:'',password:'','avatar':'', 'description:'','visibility:''}

                where:

            * ``username``: Name of the user (string)
            * ``password``: Password of the user(string)
            * ``avatar``: Users avatar (blob)
            * ``description``: Users description (string)
            * ``visibility``: Users visibility value (int)


        :return: the username of the modified user or None if the
            `username`` passed as parameter is not  in the database.
        '''
                #Create the SQL Statements
           #SQL Statement for extracting the userid given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement to update the user_profile table
        #START UPDATE statement
        query2_start = 'UPDATE users SET '
        query2_public = 'password = ?,avatar = ?, description = ?, visibility = ?'
        query2_end = ' WHERE user_id = ?'
          #SQL Statement to update the user_profile table
        query2 = query2_start
        #temporal variables
        user_id = None
        pvalue_array = []
       # p_profile = user.get('public_profile', None)
       # r_profile = user.get('restricted_profile', None)
        #if p_profile:
        _password = user.get('password', None)
        _avatar = user.get('avatar', None)
        _description = user.get('description', None)
        _visibility = user.get('visibility', None)        
        query2 += query2_public
        pvalue_array.extend([_password,_avatar,_description,_visibility])
 
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (username,)
        cur.execute(query1, pvalue)
        #Only one value expected
        row = cur.fetchone()
        #if does not exist, return
        if row is None:
            return None
        else:
            user_id = row["user_id"]
            #pvalue_array.append(user_id)
            #execute the main statement
            pvalue = tuple(pvalue_array)
            print query2
            print pvalue
            cur.execute(query2, pvalue)
            self.con.commit()
            #Check that I have modified the user
            if cur.rowcount < 1:
                return None
            return username

    def append_user(self, username, user):
        '''
        Create a new user in the database.

        :param str username: The nickname of the user to modify
        :param dict user: a dictionary with the information to be modified. The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'username:'',password:'','avatar':'', 'description:'','visibility:''}

                where:

            * ``username``: Name of the user (string)
            * ``password``: Password of the user(string)
            * ``avatar``: Users avatar (blob)
            * ``description``: Users description (string)
            * ``visibility``: Users visibility value (int)

        :return: the username of the modified user or None if the
            `username`` passed as parameter is not  in the database.


        '''
        #Create the SQL Statements
          #SQL Statement for extracting the userid given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement to create the row in  users table
        query2 = 'INSERT INTO users(username,password,avatar,description,visibility)\
                  VALUES(?,?,?,?,?)'
          #SQL Statement to create the row in user_profile table

        #temporal variables for user table
        #timestamp will be used for lastlogin and regDate.
       # timestamp = time.mktime(datetime.now().timetuple())
        #timesviewed = 0
        #temporal variables for user profiles
        _password = user.get('password', None)
        _avatar = user.get('avatar', None)
        _description = user.get('description', None)
        _visibility = user.get('visibility', None)
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (username,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        row = cur.fetchone()
        #If there is no user add rows in user and user profile
        if row is None:
            #Add the row in users table
            # Execute the statement
            pvalue = (username, _password, _avatar, _description, _visibility)
            cur.execute(query2, pvalue)
            #Extrat the rowid => user-id

            self.con.commit()
            #We do not do any comprobation and return the nickname
            return username
        else:
            return None

#exercise

    def create_exercise(self, exercise):
        '''
        Create new exercise

        :param dict exercise:a dictionary with the information to be modified. The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'username':'', 'type:'','value:'','valueunit:''
                    ,'time:'','timeunit:''}

                where:

            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)

        :return exercise_id if succesfull. None otherwise    
        '''

 #Create the SQL Statements
          #SQL Statement for extracting the userid given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement to create the row in  users table
        query2 = 'INSERT INTO exercise(user_id,username,type,value,valueunit,date,time,timeunit)\
                  VALUES(?,?,?,?,?,?,?,?)'

        _user_id = exercise.get('user_id', None)
        _username = exercise.get('username', None)
        _type = exercise.get('type', None)
        _value = exercise.get('value', None)
        _valueunit = exercise.get('valueunit', None)
        _date = exercise.get('date', None)
        _time = exercise.get('time', None)
        _timeunit = exercise.get('timeunit', None)

        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (_username,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        row = cur.fetchone()
        #If there is no user add rows in user and user profile
        if row is not None:
            #Add the row in users table
            # Execute the statement
            pvalue = (_user_id,_username,_type,_value,_valueunit,_date,_time,_timeunit)
            cur.execute(query2, pvalue)
            #Extrat the rowid => user-id
            
            lid = cur.lastrowid

            self.con.commit()
            #We do not do any comprobation and return the nickname
            return lid
        else:
            return None

    def get_exercise(self, exercise_id):
        '''
        Get all information of an exercise

        :param int exercise_id 
        :return dict exercise:a dictionary with the exercise information. The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'exercise_id:'','user_id':'','username':'', 'type:'','value:'','valueunit:''
                    ,'time:'','timeunit:''}

                where:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)

        '''

        
        query1 = 'SELECT * from exercise WHERE exercise_id = ?'
          #SQL Statement for retrieving the user information

        #query2 = 'SELECT users.* FROM users\
         #         WHERE users.user_id = ?'
          #Variable to be used in the second query.
        user_id = None
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute SQL Statement to retrieve the id given a nickname
        pvalue = (exercise_id,)
        cur.execute(query1, pvalue)
        #Extract the user id
        row = cur.fetchone()
        if row is None:
            return None
 
        return self._create_exercise_object(row)

    def get_exercises(self):
        '''
        Extracts all exercises in the database.

        :return list exercise:a list of dictionarys with the exercise information. Otherwise return None The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'exercise_id:'','user_id':'','username':'', 'type:'','value:'','valueunit:''
                    ,'time:'','timeunit:''}

                where:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)

        '''
        #Create the SQL Statements
          #SQL Statement for retrieving the users
        query = 'SELECT exercise.* FROM exercise'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Create the cursor
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute main SQL Statement
        cur.execute(query)
        #Process the results
        rows = cur.fetchall()
        if rows is None:
            return None
        #Process the response.
        exercises = []
        for row in rows:
            exercises.append(self._create_exercise_list_object(row))
        return exercises

    def get_user_exercises(self,username):
        '''
        Get all of the users exercises

        :param str username: Name of the user whose exercise are to be fetch
        :return list exercise:a list containing dictionaries with the exercise information. The
        dictionary has the following structure:

                .. code-block:: javascript

                    {'exercise_id:'','user_id':'','username':'', 'type:'','value:'','valueunit:''
                    ,'time:'','timeunit:''}

                where:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)


  
        '''
        #Create the SQL Statements
          #SQL Statement for retrieving the users
        query = 'SELECT exercise.* FROM exercise WHERE username= ?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Create the cursor
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute main SQL Statement
        pvalue=(username,)
        cur.execute(query,pvalue)
        #Process the results
        rows = cur.fetchall()
        if rows is None:
            return None
        #Process the response.
        exercises = []
        for row in rows:
            exercises.append(self._create_exercise_list_object(row))
        return exercises

    def delete_exercise(self, exercise_id):
        '''
        Remove a specific exercise

        :param int exercise_id: Exercises id.

        :return: True if the exercise is deleted, False otherwise.

        '''
        #Create the SQL Statements
          #SQL Statement for deleting the user information
        query = 'DELETE FROM exercise WHERE exercise_id = ?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to delete
        pvalue = (exercise_id,)
        cur.execute(query, pvalue)
        self.con.commit()
        #Check that it has been deleted
        if cur.rowcount < 1:
            return False
        return True

    def modify_exercise(self, exercise_id, exercise):
        '''
        Modify the information of an exercise.

        :param int exercise_id: The id of the exercise to be modified
        :param dict exercise: a dictionary with the information to be modified. The
            dictionary has the following structure:

                .. code-block:: javascript

                    {'exercise_id:'','user_id':'','username':'', 'type:'','value:'','valueunit:''
                    ,'time:'','timeunit:''}

                where:

            * ``exercise_id``: Id of the exercise (int)
            * ``user_id``: Id of the user who submitted the exercise(int)
            * ``username``: Name of the user who submitted the exercise (string)
            * ``type``: Type of the exercise. For example "running" (string)
            * ``value``: Value of the exercise.(int)
            * ``valueunit``: Values unit. For example "km". (string)
            * ``time``: Time the exercise took.(int)
            * ``timeunit``: Times unit. For example 'h'(string)

 

        :return: True if successful, None otherwise

        '''
                #Create the SQL Statements
           #SQL Statement for extracting the userid given a nickname
        #query1 = 'SELECT u_id from users WHERE username = ?'
          #SQL Statement to update the user_profile table
        #START UPDATE statement
        query1 = 'SELECT * from exercise WHERE exercise_id = ?'
        query2_start = 'UPDATE exercise SET '
        query2_public = 'type = ?,value = ?, valueunit = ?, date = ?, time = ? , timeunit = ?'
        query2_end = ' WHERE exercise_id = ?'
          #SQL Statement to update the user_profile table
        query2 = query2_start
        #temporal variables
        #user_id = None
        pvalue_array = []
       # p_profile = user.get('public_profile', None)
       # r_profile = user.get('restricted_profile', None)
        #if p_profile:
        _type = exercise.get('type', None)
        _value = exercise.get('value', None)
        _valueunit = exercise.get('valueunit', None)
        _date = exercise.get('date', None)
        _time = exercise.get('time', None)
        _timeunit = exercise.get('timeunit', None)

        query2 += query2_public
        pvalue_array.extend([_type,_value,_valueunit,_date,_time,_timeunit,exercise_id])

        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (exercise_id,)
        cur.execute(query1, pvalue)
        #Only one value expected
        row = cur.fetchone()
        #if does not exist, return
        if row is None:
            return None
        else:

            query2+=query2_end
            pvalue = tuple(pvalue_array)
            print query2
            print pvalue
            
            cur.execute(query2, pvalue)
            self.con.commit()
            #Check that I have modified the user
            if cur.rowcount < 1:
                return None
            return True

    # UTILS
    def get_friends(self, username):
        '''
        Get a list with friends of a user.

        :param str username: username of the target user
        :return: a list of users ids or None if ``user_id`` is not in the
            database
        '''
        #Create the SQL Statements
        #SQL Statement for retrieving the users
        query = 'SELECT friends.* FROM friends WHERE user_id= ?'
        query2= 'SELECT user_id FROM users WHERE username=?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Create the cursor
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute main SQL Statement
        pvalue=(username,)
        cur.execute(query2,pvalue)
        #Process the results
        rows = cur.fetchone()

        if rows is None:
            return None
        #Process the response.
        user_id=rows['user_id']
        pvalue=(user_id,)
        cur.execute(query,pvalue)
        #Process the results
        rows = cur.fetchall()
        if rows is None:
            return None
        
        friends = []
        for row in rows:
            friends.append(self._create_friends_list_object(row))
        
        return friends
        

    def add_friend(self, username, friendname):
        '''
        Add a new friend to the user

        :param str username: Name of the user who will receive a friend
        :param str friendname: username of a user who will be added as a friend

        :return True if succesful, None otherwise
        '''
        #Create the SQL Statements
          #SQL Statement for extracting the userid given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement to create the row in  users table
        query2 = 'INSERT INTO friends(user_id,friend_id)\
                  VALUES(?,?)'
          #SQL Statement to create the row in user_profile table


        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (username,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        user = cur.fetchone()
        user_id=user['user_id']
        #Execute the statement to extract the id associated to a nickname
        pvalue = (friendname,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        friend = cur.fetchone()
        friend_id=friend['user_id']
        #If there is no user add rows in user and user profile
        
        if user_id is None or friend_id is None:
            return None
        pvalue = (user_id, friend_id)
        cur.execute(query2, pvalue)
        self.con.commit()
        
        return True


    def delete_friend(self, username,friendname):
        '''
        Remove friend from users friendlist

        :param str username: Name of the user whos friend will be removed
        :param str friendname: Username of a friend who will be removed from the friendlist
    

        :return: True if the user is deleted, False otherwise.

        '''
        #Create the SQL Statements
          #SQL Statement for deleting the user information
        query2 = 'DELETE FROM friends WHERE user_id = ? AND friend_id =?'
       #Create the SQL Statements
          #SQL Statement for extracting the userid given a nickname
        query1 = 'SELECT user_id from users WHERE username = ?'
          #SQL Statement to create the row in  users table

          #SQL Statement to create the row in user_profile table


        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the statement to extract the id associated to a nickname
        pvalue = (username,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        user = cur.fetchone()
        user_id=user['user_id']
        #Execute the statement to extract the id associated to a nickname
        pvalue = (friendname,)
        cur.execute(query1, pvalue)
        #No value expected (no other user with that nickname expected)
        friend = cur.fetchone()
        friend_id=friend['user_id']
        #If there is no user add rows in user and user profile
        
        if user_id is None or friend_id is None:
            return None
        pvalue = (user_id, friend_id)
        cur.execute(query2, pvalue)
        self.con.commit()

                #Check that it has been deleted
        if cur.rowcount < 1:
            return False
        return True


    def get_user_id(self, username):
        '''
        Get the key of the database row which contains the user with the given
        nickname.

        :param str nickname: The nickname of the user to search.
        :return: the database attribute user_id or None if ``nickname`` does
            not exit.
        :rtype: str

        '''

        '''
        TASK5 TODO :
        * Implement this method.
        HINTS:
          * Check the method get_message as an example.
          * The value to return is a string and not a dictionary
          * You can access the columns of a database row in the same way as
            in a python dictionary: row [attribute] (Check the exercises slides
            for more information)
          * There is only one possible user_id associated to a nickname
          * HOW TO TEST: Use the database_api_tests_user. The following tests
            must pass without failure or error:
                * test_get_user_id
                * test_get_user_id_unknown_user
        '''
        query = 'SELECT user_id from users WHERE username = ?'
        #Activate foreign key support
        self.set_foreign_keys_support()
        #Cursor and row initialization
        self.con.row_factory = sqlite3.Row
        cur = self.con.cursor()
        #Execute the  main statement
        pvalue = (username,)
        cur.execute(query, pvalue)
        #Extract the results. Just one row expected.
        row = cur.fetchone()
        if row is None:
            return None
        else:
            return row["user_id"]

    def contains_user(self, username):
        '''
        :return: True if the user is in the database. False otherwise
        '''
        return self.get_user_id(username) is not None
