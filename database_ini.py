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
if False:
    create_grant_schema('email')
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
        timesubmit varchar(1500),
        note varchar(1500)
        )"""
    cur = connect_db().cursor()
    cur.execute(sql)
    cur.execute("COMMIT")
if False:
    create_table_issue()

def create_table_labels():
    sql = """CREATE TABLE IF NOT EXISTS email.labels (
        lable varchar(1500),
        timesubmit varchar(1500),
        idemail varchar(150),
        username varchar(150),
        note varchar(1500),
        timeuse varchar(1500)
        )"""
    cur = connect_db().cursor()
    cur.execute(sql)
    cur.execute("COMMIT")
if False:
    create_table_labels()

def create_table_openedids():
    sql = """CREATE TABLE IF NOT EXISTS email.openedids (
        timeopened varchar(1500),
        idemail varchar(150),
        username varchar(150),
        note varchar(1500)
        )"""
    cur = connect_db().cursor()
    cur.execute(sql)
    cur.execute("COMMIT")
if False:
    create_table_openedids()
###################################################
# login ini #########
if False:
    import yaml
    import random
    import streamlit_authenticator as stauth
    f_name = "login.yaml"
    with open(f_name) as f:
        list_doc = yaml.safe_load(f)
    # print (list_doc['credentials']['usernames'])
    for num in range(1,20):
        name = 'PM'+str(num)
        random.seed(num)
        pw = random.randint(1000, 9999)
        hashed_passwords = stauth.Hasher([str(pw)]).generate()[0]
        print (pw,hashed_passwords)
        # print (list_doc['credentials']['usernames'])
        list_doc['credentials']['usernames'][name]={'email':'sample','name':name,'realpassword':pw,'password':hashed_passwords}
    

    with open(f_name, "w") as f:
        yaml.dump(list_doc, f)
# print usernames and passwords ###
if False:
    import yaml
    import random
    import streamlit_authenticator as stauth
    f_name = "login.yaml"
    with open(f_name) as f:
        list_doc = yaml.safe_load(f)
    users = list_doc['credentials']['usernames'].keys()
    print (users)
    dict_tmp = {}
    for user in users:
        pw = list_doc['credentials']['usernames'][user]['realpassword']
        dict_tmp[user] = pw
        print (pw)
    print (dict_tmp)  
# 'PM1': 3201, 'PM10': 1533, 'PM11': 8411, 'PM12': 8775, 'PM13': 5243, 'PM14': 2750, 'PM15': 4423, 'PM16': 6923, 'PM17': 9552, 'PM18': 3969, 'PM19': 1708, 'PM2': 1926, 'PM3': 4898, 'PM4': 4867, 'PM5': 5185, 'PM6': 2320, 'PM7': 6305, 'PM8': 4714, 'PM9': 8585, 'andy': 2836, 'jeffrey': 6323, 'kevin': 8963, 'leon': 4936, 'michael': 3232, 'ray': 3232, 'shuming': 8768, 'tony': 8768, 'xiaohan': 6323
# login ini PM name#########
if True:
    import yaml
    import random
    import streamlit_authenticator as stauth
    f_name = "login.yaml"
    with open(f_name) as f:
        list_doc = yaml.safe_load(f)
    # print (list_doc['credentials']['usernames'])
    pms = ['winkie','massimo','reina','alexchiu','kel','michaellee','henry','yolanda','brian','jason','isabella','martin','rain','stephen','jesse','jay','melvin','zenith','lyric','mark','sophie']
    random.seed(1)
    for name in pms:
        # name = 'PM'+str(num)
        pw = random.randint(1000, 9999)
        hashed_passwords = stauth.Hasher([str(pw)]).generate()[0]
        print (name,pw,hashed_passwords)
        # print (list_doc['credentials']['usernames'])
        list_doc['credentials']['usernames'][name]={'email':'sample','name':name,'realpassword':pw,'password':hashed_passwords}   

    with open(f_name, "w") as f:
        yaml.dump(list_doc, f)
    # print for zelin
    pms_print = ['kevin','winkie','tony','massimo','reina','alexchiu','andy','kel','michaellee','henry','jeffrey','yolanda','brian','jason','leon','isabella','martin','rain','ray','stephen','jesse','jay','melvin','zenith','lyric','mark','sophie']
    with open(f_name) as f:
        list_doc = yaml.safe_load(f)
    users = list_doc['credentials']['usernames'].keys()
    print (users)
    dict_tmp = {}
    for user in users:
        if user in pms_print:
            pw = list_doc['credentials']['usernames'][user]['realpassword']
            dict_tmp[user] = pw
            # print (user,':',pw)
    for user in pms_print:
        print (user,':',dict_tmp[user])
    print (dict_tmp) 
# kevin : 8963
# winkie : 3201
# tony : 8768
# massimo : 2033
# reina : 5179
# alexchiu : 2931
# andy : 2836
# kel : 9117
# michaellee : 8364
# henry : 8737
# jeffrey : 6323
# yolanda : 7219
# brian : 4439
# jason : 2537
# leon : 4936
# isabella : 8993
# martin : 1464
# rain : 7386
# ray : 3232
# stephen : 8090
# jesse : 1034
# jay : 8297
# melvin : 5363
# zenith : 4748
# lyric : 2674
# mark : 6200
# sophie : 1501
###########################################
