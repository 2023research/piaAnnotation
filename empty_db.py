from urllib.error import URLError
import os, psycopg2
# database
def connect_db():
    conn = psycopg2.connect("dbname=pia host=piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com user=postgres password=UTS-DSI2020")
    return conn
# create schema####
cur = connect_db().cursor()
sql = 'TRUNCATE TABLE email.openedids'
cur.execute(sql)
cur.execute('commit')