import forum.database as database
import sqlite3
DEFAULT_DATA_DUMP = "db/forum_data_dump.sql"
engine= database.Engine()
engine.create_users_table()
engine.create_exercise_table()
engine.create_friends_table()

con = sqlite3.connect('db/forum.db')

cur = con.cursor()
keys_on = 'PRAGMA foreign_keys = ON'
cur.execute(keys_on)
        #Populate database from dump

dump = DEFAULT_DATA_DUMP
with open (dump) as f:
    sql = f.read()
    cur = con.cursor()
    cur.executescript(sql)
    