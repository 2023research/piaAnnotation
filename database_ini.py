from urllib.error import URLError
import os, psycopg2
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
from streamlit_modal import Modal
from streamlit.logger import get_logger

from sqlalchemy import create_engine
from sqlalchemy.sql import text


import yaml
from yaml.loader import SafeLoader

# database
@st.cache_resource
def sqlalchemy_engine():
    engine = create_engine('postgresql://postgres:UTS-DSI2020@piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com/pia')
    return engine
@st.cache_resource
def connect_db():
    conn = psycopg2.connect("dbname=pia host=piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com user=postgres password=UTS-DSI2020")
    return conn
# create schema####
def create_grant_schema(schema):
    cur = connect_db().cursor()
    print (cur)
    cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema} AUTHORIZATION postgres ")
    cur.execute(f"GRANT CREATE, USAGE ON SCHEMA {schema} TO postgres")
    cur.execute(f"GRANT SELECT ON ALL TABLES IN SCHEMA {schema} TO postgres")
    cur.execute(f"GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA {schema} TO postgres")
    cur.execute("COMMIT")
# create_grant_schema('email')
## create table###############
def create_table_issue():
    sql = """CREATE TABLE IF NOT EXISTS email.issues (
        area varchar(150),
        location varchar(150),
        issue varchar(150),
        maintype varchar(150),
        subtype varchar(150),
        subsubtype varchar(150),
        subsubsubtype varchar(150),
        issuestr varchar(1500),
        idemail varchar(150),
        username varchar(150),
        note varchar(1500)
        )"""
    cur = connect_db().cursor()
    cur.execute(sql)
    cur.execute("COMMIT")
create_table_issue()

#  # st method#################################
# start_time = time.time()
# conn = st.connection("postgresql", type="sql")
# # Perform query.
# conn.session.execute(text(sql))
# conn.session.execute('commit')
# print("---1 %s cur seconds ---" % (time.time() - start_time))
# start_time = time.time()

# # pandas method #################################
# start_time = time.time()
# print (pd.read_sql('select issuestr from email.issues', con=sqlalchemy_engine()))
# print("--- %s pd seconds ---" % (time.time() - start_time))

# #psycopg2 method #################################
# #db data to datafram####
# start_time = time.time()
# cur = connect_db().cursor()
# cur.execute('select issuestr from email.issues')
# df = pd.DataFrame(cur.fetchall())
# df.columns = [ x.name for x in cur.description ]
# print(df)