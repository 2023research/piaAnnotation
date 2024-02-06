# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
###@@@@@@@@@@@@@@@@@
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# http://13.211.130.199:8501/ 
# python -m streamlit run Home.py
from urllib.error import URLError
import os, psycopg2, time,datetime
import pandas as pd
import numpy as np
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
from streamlit_modal import Modal
from streamlit.logger import get_logger

from sqlalchemy import create_engine
from sqlalchemy.sql import text

# from utils import *
# from maintenance import *
# import pybase64
import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout="wide")
from streamlit.elements.utils import _shown_default_value_warning
_shown_default_value_warning = True
##########################################################################################################
######################################## Functions #######################################################
##########################################################################################################

###############################################################################################   
##### load email #####################################################################################
def pull_idemail_labeled():
    cur = connect_db().cursor()
    cur.execute('select idemail from email.labels')    
    ids = [x[0] for x in cur.fetchall()]
    if len(ids)==0:
        ids=['temp']
    return ids
def pull_labeled_number():
    tstr = "25 Jan 2024 1:50:28"
    tstr = time.strptime(tstr, "%d %b %Y %H:%M:%S")

    cur = connect_db().cursor()
    cur.execute('select timesubmit from email.labels')  
    timesubmit = np.array([x[0] for x in cur.fetchall()], dtype=float)
    timesubmit = timesubmit[timesubmit>time.mktime(tstr)]

    # df = pd.DataFrame(cur.fetchall())
    # df.columns = [ x.name for x in cur.description ]
    # df = df[df['timeuse'].notnull()]

   
    # df['datesubmit'] = df['timesubmit'].astype('float')
    # df_period = df[df['datesubmit']>time.mktime(tstr)]  
    print ('1111111111111111111111111111111',timesubmit.shape[0])
    return timesubmit.shape[0]
def push_idemail_open(id_email=None,username=None):
    cur = connect_db().cursor()
    sql = f"""INSERT INTO email.openedids (timeopened, idemail, username) VALUES ('{str(time.time())}','{id_email}', '{username}')"""       
    print (sql)         
    cur = connect_db().cursor()
    cur.execute(sql)            
    cur.execute('commit')
def pull_idemail_open():
    cur = connect_db().cursor()
    cur.execute('select * from email.openedids') 
    df = pd.DataFrame(cur.fetchall()) 
    # print ('lllllllllllllllllllll',df.shape)       
    if df.shape[1]>0:
        df.columns = [ x.name for x in cur.description ]
        df['timeopened'] = time.time() - df['timeopened'].astype(float)
        ids = df['idemail'][df['timeopened']<1000].to_list()     
        # print (df)
    else:
        ids = ['temp']   
    return ids

def read_email(sample=False,username='other'):
    
    @st.cache_data
    def get_email_data():
        df = pd.read_csv('./data/test_pos_wlTFLR_key_20ksamples4annotation.csv',sep=',')
        idsallset = set(df["ID"].unique())
        return df, idsallset
    ####
    st.session_state.number_labeled = pull_labeled_number()
    print ('st.session_state.number_labeled',st.session_state.number_labeled)

    start_time = time.time()
    idslabeled = pull_idemail_labeled()
    # print ('idslabeled',idslabeled)
    idsopened = pull_idemail_open()
    # print('idsopened',idsopened)
    ids_used = set(idslabeled+idsopened)  
    # print ('ids_used',ids_used)
    print("--- %s pd seconds ---" % (time.time() - start_time))

    
    # if username=='ray':
    #     df, idsallset = get_email_data_ray()
    # elif username=='tony':
    #     df, idsallset = get_email_data_tony()
    # elif username=='leon':   
    #     df, idsallset = get_email_data_leon()
    # elif username=='kevin':
    #     df, idsallset = get_email_data_kevin()
    # elif username=='andy':
    #     df, idsallset = get_email_data_andy()
    # elif username=='jeffrey':
    #     df, idsallset = get_email_data_jeffrey()
    # elif username=='other':
    df, idsallset = get_email_data()
    print ('@@@@@@@@@@@@@@@@@@@@@ total un-annotated emails:',df.shape,df.columns)
    # df = df[['Body','ID']]
    df['sort']=df.index
    idx_unlabled = idsallset.difference(ids_used)
    df_email = df.set_index('ID',drop=True)
    df_out = df_email.loc[list(idx_unlabled)]
    # df_out.sort_values(by='sort',inplace=True)
    df_onerow = df_out.sample(1)
    # df_onerow = df_out.iloc[[0]]
    # print ('####',df_onerow)
    # print ('####',df_out.iloc[[0]])
    # idx_unlabled = list(idx_unlabled)
    # idx_unlabled.sort()
    # print ('@@@@@@@@@@@@@@@@@@@@@',df_onerow.columns)
    # df_bool = df['ID'].apply(lambda x: x not in files)
    ## check special case
    # df_onerow = df_email[df_email.index=='a1_26109']
    # return df_onerow['Body'].values[0],df_onerow.index[0]            
    text_email = f" * **From:** {df_onerow['From name'].values[0]} ({df_onerow['From address'].values[0]})\n* **To:** {df_onerow['To name'].values[0]} ({df_onerow['To address'].values[0]}) \n* **Subject:** {df_onerow['Subject'].values[0]}\n* **Content:** \n\n{df_onerow['Body'].values[0]}"
    # print ('@@@@@@@@@@@@@@@@@@@@@',text_email) 
    return text_email,df_onerow.index[0]            
    

#### slectbox options #####################################
def pull_options():
    cur = connect_db().cursor()
    cur.execute('select * from email.issues')
    opts_df = pd.DataFrame(cur.fetchall())
    if opts_df.shape[0]>0:
        opts_df.columns = [ x.name for x in cur.description ]
    else:
        opts_df = pd.DataFrame([['other','other','other','other','other','other']])
        # print (opts_df)
        opts_df.columns = ['area','location','issue','maintype','subtype','issuestr']
    st.session_state.opts_df = opts_df
def maintenance_options():    
    #### pull latest options from database ####
    # start_time = time.time()
    if st.session_state.opts_df is None:
        pull_options()    
    if time.time() - st.session_state.time_lastopt >5:
        st.session_state.time_lastopt = time.time()
        pull_options()
        print ('########---------------------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$-')
    ####################################################################
    
    opts_df = st.session_state.opts_df
    #### related #####################################################
    opts_related = opts_df['subsubsubtype']
    opts_related =opts_related.unique().tolist()
    if 'other' not in opts_related:
        opts_related.append('other')

    ##################################################################
    #### maintenance options #########################################
    opts_df = opts_df[opts_df['subsubsubtype']=='maintenance']
    # print (opts_df['subsubsubtype'])
    #### area ###########################################################
    opts_area = opts_df['area']
    opts_area =opts_area.unique().tolist()
    if 'other' not in opts_area:
        opts_area.append('other')
    #### location #######################################################
    opts_location = opts_df.groupby('area')['location'].agg(['unique'])
    opts_location['unique'] = opts_location['unique'].apply(lambda x: x.tolist())
    opts_location = opts_location['unique'].to_dict()
    def merge_room_parts(opts_location,location_general =  ['ensuite','bathroom']):
        location_list = []        
        for room in location_general:
            if room in opts_location.keys():
                location_list+=opts_location[room]
        for room in location_general:        
            opts_location[room] = list(set(location_list))
        if 'bedroom' in location_general:
            for key in opts_location.keys():
                if key not in location_general and key!='other':
                    opts_location[key] = list(set(opts_location[key]+list(set(location_list))))
        return opts_location
    location_general = ['entry/hall','living room','bedroom','study room','dining room']
    opts_location = merge_room_parts(opts_location,location_general)
    opts_location = merge_room_parts(opts_location,['ensuite','bathroom'])
    opts_location = merge_room_parts(opts_location,['storage room','balcony','courtyard','garage'])
    
    if 'other' not in opts_location:
        opts_location['other']=['other']
    #### issue ##############################################################
    opts_issue = opts_df.groupby('location')['issue'].agg(['unique'])
    opts_issue['unique'] = opts_issue['unique'].apply(lambda x: x.tolist())
    opts_issue = opts_issue['unique'].to_dict()
    if 'other' not in opts_issue:
        opts_issue['other']=['other']
    #### maintype ###########################################################
    opts_maintype = opts_df['maintype']
    opts_maintype =opts_maintype.unique().tolist()
    if 'other' not in opts_maintype:
        opts_maintype.append('other')

    #### subtype ############################################################
    opts_subtype = opts_df.groupby('maintype')['subtype'].agg(['unique'])
    opts_subtype['unique'] = opts_subtype['unique'].apply(lambda x: x.tolist())
    opts_subtype = opts_subtype['unique'].to_dict()
    if 'other' not in opts_subtype:
        opts_subtype['other']=['other']

    ####################################################################
    #### non-maintenance options ###################################
    opts_df = st.session_state.opts_df
    opts_df = opts_df[opts_df['subsubsubtype']!='maintenance']
    # print (opts_df['subsubsubtype'])
    opts_nonmain, opts_nonmain_sub,opts_nonmain_subsub={},{},{}
    if len(opts_df)==0:
        opts_nonmain['other']='other'
        opts_nonmain_sub['other']='other'
        opts_nonmain_subsub['other']='other'
    else:
        ####
        
        opts_nonmain = opts_df.groupby('subsubsubtype')['area'].agg(['unique'])
        opts_nonmain['unique'] = opts_nonmain['unique'].apply(lambda x: x.tolist())
        opts_nonmain = opts_nonmain['unique'].to_dict()
        # print ('=============:',opts_nonmain)
        if 'other' not in opts_nonmain:
            opts_nonmain['other']=['other']
        ####
        opts_nonmain_sub = opts_df.groupby('subsubsubtype')['location'].agg(['unique'])
        opts_nonmain_sub['unique'] = opts_nonmain_sub['unique'].apply(lambda x: x.tolist())
        opts_nonmain_sub = opts_nonmain_sub['unique'].to_dict()
        if 'other' not in opts_nonmain_sub:
            opts_nonmain_sub['other']=['other']

        for key in opts_nonmain_sub.keys():
             temp_list = opts_nonmain_sub[key]
             opts_nonmain_sub[key] = [value for value in temp_list if value != None]
             print ([value for value in temp_list if value != "None"])

        ####
        opts_nonmain_subsub = opts_df.groupby('subsubsubtype')['issue'].agg(['unique'])
        opts_nonmain_subsub['unique'] = opts_nonmain_subsub['unique'].apply(lambda x: x.tolist())
        opts_nonmain_subsub = opts_nonmain_subsub['unique'].to_dict()
        if 'other' not in opts_nonmain_subsub:
            opts_nonmain_subsub['other']=['other']

        for key in opts_nonmain_subsub.keys():
             temp_list = opts_nonmain_subsub[key]
             opts_nonmain_subsub[key] = [value for value in temp_list if value != None]
        ####
    return opts_related,opts_area, opts_location,opts_issue,opts_maintype,opts_subtype,opts_nonmain, opts_nonmain_sub,opts_nonmain_subsub


##########################################################################################################
##########################################################################################################
##########################################################################################################


print ('-------------------------------------------new run-------------------------------------------------')
#######basic setting######################################################################################
# path_results = './results'
####### initialize global session state
if "issue_list" not in st.session_state or 'id_email' not in st.session_state or 'is_maintenance' not in st.session_state:
    st.session_state.number_labeled = 0
    st.session_state.id_email = ''
    st.session_state.text_email = None
    st.session_state.issue_list = []
    st.session_state.deletes = []
    st.session_state.newopts = {}
    st.session_state.bool_read_email = True
    st.session_state.bool_save_newopt_confirm=0
    st.session_state.bool_add_newopt_button = False
    st.session_state.bool_final_submit = False
    st.session_state.bool_final_submit_confirm = 0
    ##
    st.session_state.time_lastopt = time.time()
    st.session_state.opts_df = None
    ##
    st.session_state.is_maintenance = 'other'
    st.session_state.key_area = 'other'
    st.session_state.key_location = 'other'
    st.session_state.key_issue = 'other'
    st.session_state.key_maintype = 'other'
    st.session_state.key_subtype = 'other'
    st.session_state.key_nonmain = 'other'
    st.session_state.key_nonmain_sub = 'other'
    st.session_state.key_nonmain_subsub = 'other' 
    st.session_state.is_maintenance_new=None  
    st.session_state.key_area_new=None
    st.session_state.key_location_new=None
    st.session_state.key_issue_new=None
    st.session_state.key_maintype_new=None
    st.session_state.key_subtype_new=None
    st.session_state.key_nonmain_new=None
    st.session_state.key_nonmain_sub_new=None
    st.session_state.key_nonmain_subsub_new=None
    #
    st.session_state.key_street=''
    st.session_state.key_suburb=''
    st.session_state.key_state=''
    st.session_state.key_post=''
####### database ############ nonmain,nonmain_sub,nonmain_subsub
# print ('======================',st.session_state.is_maintenance)
@st.cache_resource
def sqlalchemy_engine():
    engine = create_engine('postgresql://postgres:UTS-DSI2020@piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com/pia')
    return engine
@st.cache_resource
def connect_db():
    conn = psycopg2.connect("dbname=pia host=piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com user=postgres password=UTS-DSI2020")
    return conn
###### style setting ##########
st.markdown( """<style>section[data-testid="stSidebar"] {
            width: 800px !important; # Set the width to your desired value}</style> """, unsafe_allow_html=True, )
st.markdown("""<style>div.stButton {text-align:center; color: blue;}</style>""", unsafe_allow_html=True)
########################################################################################################

##### login #######################################################################################
# login authorization ###########
# usernames = ['john','james','oliver','david','emma','alex']shuming 8768, xiaohan:6323,michael:3232
#Kevin:8963, Andy:2836, Leon:4936, Ray:3232, Jeffrey:6323, Tony:8768
# passwords = ['8963','2836', '4936','3232','6323','8768']
# 'PM1': 3201, 'PM10': 1533, 'PM11': 8411, 'PM12': 8775, 'PM13': 5243, 'PM14': 2750, 'PM15': 4423, 'PM16': 6923, 'PM17': 9552, 'PM18': 3969, 'PM19': 1708, 'PM2': 1926, 'PM3': 4898, 'PM4': 4867, 'PM5': 5185, 'PM6': 2320, 'PM7': 6305, 'PM8': 4714, 'PM9': 8585, 'andy': 2836, 'jeffrey': 6323, 'kevin': 8963, 'leon': 4936, 'michael': 3232, 'ray': 3232, 'shuming': 8768, 'tony': 8768, 'xiaohan': 6323

# hashed_passwords = stauth.Hasher(['8963','2836', '4936','3232','6323','8768']).generate()
# print (hashed_passwords)

with open('./login.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

authenticator = stauth.Authenticate(
    config['credentials'],
    config['cookie']['name'],
    config['cookie']['key'],
    config['cookie']['expiry_days'],
    config['preauthorized']
)
showingname, authenticator_status, username = authenticator.login('Login','main')
if authenticator_status==False:
    st.error('username/password is incorrect')
elif authenticator_status==None:
    st.warning("please enter your username and password")
elif st.session_state.number_labeled>9888: #check how many labeled emails
    st.header(f'Congratulations! The annotation task has been completed.', divider='red')
else:
    st.markdown(f"<h2 style='text-align: center; color: red;'>Welcome {username}!</h2>", unsafe_allow_html=True)
    authenticator.logout('Logout')
###############################################################################################   
    def reset_maintenance_no():
        st.session_state.is_maintenance = 'other'
        st.session_state.key_area = 'other'
        st.session_state.key_location = 'other'
        st.session_state.key_issue = 'other'
        st.session_state.key_maintype = 'other'
        st.session_state.key_subtype = 'other'
        st.session_state.key_nonmain = 'other'
        st.session_state.key_nonmain_sub = 'other'
        st.session_state.key_nonmain_subsub = 'other' 
        st.session_state.is_maintenance_new=None  
        st.session_state.key_area_new=None
        st.session_state.key_location_new=None
        st.session_state.key_issue_new=None
        st.session_state.key_maintype_new=None
        st.session_state.key_subtype_new=None
        st.session_state.key_nonmain_new=None
        st.session_state.key_nonmain_sub_new=None
        st.session_state.key_nonmain_subsub_new=None
        #
        st.session_state.key_street=''
        st.session_state.key_suburb=''
        st.session_state.key_state=''
        st.session_state.key_post=''
        
    
    # reset_maintenance_no()   
    
####### load email #####################################################################################
#############
    def reset_maintenance():
        reset_maintenance_no()
        st.session_state.issue_list = []
        st.session_state.deletes = []

    if st.session_state.bool_final_submit_confirm==2:
        st.session_state.bool_final_submit_confirm=0
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        st.session_state.bool_read_email = True
        reset_maintenance()
        if st.session_state.bool_final_submit_sccuss == 1:
            st.sidebar.warning("Your final submition is successfully")
        elif st.session_state.bool_final_submit_sccuss == 0:
            st.sidebar.error("Your final submition is not saved! please report this to shuming.liang@uts.edu.au")

    if st.session_state.bool_read_email == True or st.session_state.id_email=='':
        st.session_state.load_email_time = time.time()
        st.session_state.bool_read_email = False
        # if username in ['ray','tony','leon','kevin','andy','jeffrey']:
        #     st.session_state.text_email, st.session_state.id_email = read_email(username=username)
        # else:
        st.session_state.text_email, st.session_state.id_email = read_email()    
        push_idemail_open(id_email=st.session_state.id_email,username=username)

    text_email,id_email = st.session_state.text_email, st.session_state.id_email
    print (id_email)    
    st.header(f'Text to analyze. The email id is: {id_email}', divider='red')
    st.markdown(text_email)
    st.header(body='',divider='red' )
    st.header('End')

######## property address #############################################################################
    # # st.sidebar.subheader('',divider='red')
    # st.sidebar.subheader('Peoperty Address')
    # with st.sidebar:
    #     adstreet = st.text_input(label='street',key='key_street')
    #     if adstreet=='': adstreet="other"
    #     c1, c2, c3 = st.columns([0.4,0.4,0.2], gap='small') 
    #     with c1:
    #         adsuburb = st.text_input(label='suburb',key='key_suburb')
    #         if adsuburb=='': adsuburb="other"
    #     with c2:
    #         adstate = st.text_input(label='state',key='key_state')
    #         if adstate=='': adstate="other"
    #     with c3:
    #         adpostcode = st.text_input(label='postcode',key='key_post')
            
    #         if adpostcode == '': 
    #             adpostcode="other"                
    #             print ('ddddddddddddddddd',adpostcode)
    # st.sidebar.subheader('',divider='red')
    # st.sidebar.subheader('Email Tagging')
    # ads_list = [adstreet,adsuburb,adstate,adpostcode]
    # address =""
    # for i, ele in enumerate(ads_list):  
    #     if i<len(ads_list)-1:
    #         address=address+ele+'|' #if ele !=None else address+'None|'
    #     elif ele !='':
    #         address=address+ele # if ele !=None else issue_str+'None'
    address ="other|APInotopen"
    print ('########',address)
#### slectbox options ##########################################################################################
    opts_related,opts_area, opts_location,opts_issue,opts_maintype,opts_subtype,opts_nonmain, opts_nonmain_sub,opts_nonmain_subsub = maintenance_options()    

###### maintenance selection box ################################################################################ 
    # def select_issues_1column(label='0',opt=['0','1'], phld="", disable=False,key=['0','1']):
    #     def change_key():
    #         pass
    #     opt = [value for value in opt if value != "other"] 
    #     opt = [value for value in opt if value != None]        
    #     opt.sort()
    #     opt.append('other')  

    #     # if key[0]=='is_maintenance':
    #     #     opt = [value for value in opt if value != "maintenance"]
    #     #     opt = ['maintenance']+opt
    #     print ('############:',opt)
    #     idx = opt.index('other')
    #     c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
    #     with c1:
    #         item = st.selectbox(label=label, options=opt, placeholder=phld, index=idx, on_change = change_key, disabled=disable, key=key[0])  #index=idx,   
    #         if st.session_state[key[0]] != "add a new option":
    #             st.session_state[key[1]] = None         
    #     with c2:                
    #         disable_newopt = (item!="add a new option") or (disable)
    #         new_option = ''# st.text_input(label="Input your new keyword",label_visibility='visible', placeholder='Input your new keyword', disabled = disable_newopt,key=key[1])              
    #         if item=="add a new option":
    #             if new_option!='':
    #                 item = new_option.lower()  
    #                 if new_option in opt or new_option[:-1] in opt:
    #                     # st.session_state[key[0]] = new_option
    #                     # item = st.selectbox(label=label, options=opt, index=idx, placeholder=phld, disabled=disable, key=key[0]) 
    #                     st.warning(f"Your new option '{new_option}' has been existed in the left selectbox.")
    #                 else:                        
    #                     st.session_state.newopts[label]=item
    #             else:
    #                 item = 'other'                    
        
    #     return item

    def select_issues(label='0',opt=['0','1'], phld="", disable=False,key=['0','1']):
        def change_key():
            pass
        opt = [value for value in opt if value != "other"] 
        opt = [value for value in opt if value != None]        
        opt.sort()
        opt.append('other')  
        if key[0]!='is_maintenance':
            opt.append('add a new option') 

        if key[0]=='is_maintenance':
            opt = [value for value in opt if value != "maintenance"]
            opt = ['maintenance']+opt
        # print ('############:',opt)
        idx = opt.index('other')
        c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
        with c1:
            item = st.selectbox(label=label, options=opt, placeholder=phld, index=idx, on_change = change_key, disabled=disable, key=key[0])  #index=idx,   
            if st.session_state[key[0]] != "add a new option":
                st.session_state[key[1]] = None         
        with c2:                
            disable_newopt = (item!="add a new option") or (disable)
            if key[0]=='is_maintenance':
                new_option = ''
            else:
                new_option = st.text_input(label="Input your new keyword",label_visibility='visible', placeholder='Input your new keyword', disabled = disable_newopt,key=key[1])              
            if item=="add a new option":
                if new_option!='':
                    item = new_option.lower()  
                    if new_option in opt or new_option[:-1] in opt:
                        # st.session_state[key[0]] = new_option
                        # item = st.selectbox(label=label, options=opt, index=idx, placeholder=phld, disabled=disable, key=key[0]) 
                        st.warning(f"Your new keyword '{new_option}' has been existed in the left selectbox.")
                    elif ';'in new_option or '|' in new_option:
                        st.warning(f"Your new keyword '{new_option}' has reserved character ';' or '|'. Please avoid using them")
                        item = ''.join(e for e in item if e != ';')
                        item = ''.join(e for e in item if e != '|')
                        print (item)
                    else:                        
                        st.session_state.newopts[label]=item
                else:
                    item = 'other'                    
        
        return item
    #### related is_maintenance ###############################################################
    print ('+++++++++++++',st.session_state.is_maintenance)
    
    opts_related = ['strata','maintenance','account','leasing','inspection','portfolio management','rent review','complaints','NCAT','property sales']
    is_maintenance = select_issues("what is the email related to?",opts_related,key=['is_maintenance','is_maintenance_new'])  
    disable = False
    if is_maintenance=='maintenance':
        ###################################################################
        #### area ####
        print (st.session_state.key_area)
        area = select_issues("which area has issue?",opts_area,disable=disable,key=['key_area','key_area_new']) 
        # print (opts_area) 
        ################################################################### 
        #### location ####
        if area not in opts_location.keys():
            opts_location[area] = ['other'] 
        if 'other' not in opts_location[area]:
            opts_location[area].append('other') 
        location = select_issues(f"which part?",opts_location[area],disable=disable,key=['key_location','key_location_new'])
        # check if new location has been existed in area like bedroom
        if location in opts_area and location != "add a new option" and location != "other" and location != "general":        
            st.sidebar.error(f"""Your new keyword '{location}' has been existed in the selectbox of "which area has issue?".""")
        ################################################################### 
        #### issue ####
        if location not in opts_issue.keys():
            opts_issue[location] = ['other']
        if 'other' not in opts_issue[location]:
            opts_issue[location].append('other')
        issue = select_issues(f"issue details",opts_issue[location],disable=disable,key=['key_issue','key_issue_new'])
        ###################################################################   
        #### maintype #### 
        maintype = select_issues("maintenance maintype",opts_maintype,disable=disable,key=['key_maintype','key_maintype_new'])
        ################################################################### 
        #### subtype ####
        if maintype not in opts_subtype.keys():
            opts_subtype[maintype] = ['other']
        if 'other' not in  opts_subtype[maintype]:
            opts_subtype[maintype].append('other')
        subtype = select_issues("maintenance subtype",opts_subtype[maintype], disable=disable,key=['key_subtype','key_subtype_new'])
        ###################################################################
        issue_str_list = [is_maintenance,area,location,issue,maintype,subtype]
    elif is_maintenance=='other':
        ###################################################################
        #### nonmain ####
        if is_maintenance not in opts_nonmain.keys():
            opts_nonmain[is_maintenance] = ['other']
        if 'other' not in  opts_nonmain[is_maintenance]:
            opts_nonmain[is_maintenance].append('other')
        nonmain = select_issues("main type of the matter",opts_nonmain[is_maintenance], key=['key_nonmain','key_nonmain_new'])

        # ###################################################################
        # #### nonmain_sub ####
        # if is_maintenance not in opts_nonmain_sub.keys():
        #     opts_nonmain_sub[is_maintenance] = ['other']
        # if 'other' not in  opts_nonmain_sub[is_maintenance]:
        #     opts_nonmain_sub[is_maintenance].append('other')
        # nonmain_sub = select_issues("subtype",opts_nonmain_sub[is_maintenance], key=['key_nonmain_sub','key_nonmain_sub_new'])
        nonmain_sub = 'not given'
        # ###################################################################
        # #### nonmain_subsub ####
        # if is_maintenance not in opts_nonmain_subsub.keys():
        #     opts_nonmain_subsub[is_maintenance] = ['other']
        # if 'other' not in  opts_nonmain_subsub[is_maintenance]:
        #     opts_nonmain_subsub[is_maintenance].append('other')
        # nonmain_subsub = select_issues("sub-subtype",opts_nonmain_subsub[is_maintenance], key=['key_nonmain_subsub','key_nonmain_subsub_new'])
        nonmain_subsub = 'not given'
        # ###################################################################
        # issue_str_list = [is_maintenance,nonmain,nonmain_sub,nonmain_subsub]
        issue_str_list = [is_maintenance,nonmain]
    else:
        issue_str_list = [is_maintenance]
    
######## add issue description ################################################################################
    opt_long_checklist=[]
    issue_str=""
    for i, ele in enumerate(issue_str_list):  
        if ele !='':
            if len(ele)>50:
                opt_long_checklist.append(ele)
        if i<len(issue_str_list)-1:
            issue_str=issue_str+ele+'|'# if ele !=None else issue_str+'None|'
        elif ele !='':
            issue_str=issue_str+ele # if ele !=None else issue_str+'None'
    print (issue_str)

    ### add issue button ##########
    def add_issue(issue_str=''):
        if issue_str !='' and issue_str not in st.session_state.issue_list:
            st.session_state.issue_list.append(issue_str)

    def delete_field(index):
        del st.session_state.issue_list[index]
        del st.session_state.deletes[index]

    def add_newopt_button():
        st.session_state.bool_add_newopt_button = True
    
    bool_addissue = disable
    if  "add a new option" in [st.session_state.key_area, st.session_state.key_location, st.session_state.key_issue,
                               st.session_state.key_maintype, st.session_state.key_subtype, st.session_state.is_maintenance,
                               st.session_state.key_nonmain, st.session_state.key_nonmain_sub, st.session_state.key_nonmain_subsub]:
        bool_addissue = True
    bool_addopt = (not bool_addissue)
    c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
    with c1:
        add_issue_res = st.button("➕ Add matter", on_click=add_issue, args=(issue_str,),disabled=bool_addissue, key='add_issue')  
    with c2:
        st.button("➕ Add new keywrod", on_click=add_newopt_button, disabled=bool_addopt, key='add_new_options')
    
    ######## showing issues###############################################
    # st.sidebar.divider()
    # st.sidebar.subheader('',divider='orange')
    st.sidebar.subheader('list of matters',divider='orange')
    for i in range(len(st.session_state.issue_list)):
        c1, c2 = st.sidebar.columns([0.2,0.8], gap='small')    
        with c1:
            st.session_state.deletes.append(st.button("❌", key=f"delete{i}", on_click=delete_field, args=(i,)))
        with c2:
            st.write(st.session_state.issue_list[i])       
            
    print ('st.session_state.issue_list',st.session_state.issue_list)
    st.sidebar.subheader('',divider='orange')
   
    ### add_newopt_button popup double confirm ###################################
    def modal_save_newopt_confirm():
        st.session_state.bool_save_newopt_confirm=1
    
    with st.sidebar:   
        if st.session_state.bool_add_newopt_button:             
            my_modal = Modal(title='', key='key_add_newopt_modal',padding=0,max_width=800)      
            st.session_state.bool_add_newopt_button=False
            if len(opt_long_checklist) > 0:
                with my_modal.container(): 
                    st.warning(f"Your new option as below is too long, please use a short key-words.")
                    st.markdown(f"<h3 style='text-align: center; color: red;'>{opt_long_checklist}</h3>", unsafe_allow_html=True)
                    st.button('Back to re-edit it', key='key_add_newopt_revise')
            else:
                if issue_str in st.session_state.opts_df['issuestr'].values:
                    # print ('--------new issue_str is',issue_str)
                    with my_modal.container(): 
                        st.warning(f"Your new issue description {issue_str} has been existed in the system.")
                        st.markdown(f"<h3 style='text-align: center; color: red;'>{issue_str}</h3>", unsafe_allow_html=True)
                        st.button('Back to re-edit it', key='key_add_newopt_revise')
                else:
                    with my_modal.container(): 
                        st.markdown(f"<p style='text-align: center; '>Your new keyword description is:</p>", unsafe_allow_html=True)
                        st.markdown(f"<h3 style='text-align: center; color: red;'>{issue_str}</h3>", unsafe_allow_html=True)
                        st.markdown(f"<p style='text-align: center; '>Please save or re-edit it. Note that the saving will update the options in the system!</p>", unsafe_allow_html=True)
                        
                        st.button('Back to re-edit it', key='key_add_newopt_revise')
                        st.button('Confirm to save it to system',on_click=modal_save_newopt_confirm, key='key_add_newopt_confirm')
    #### insert new options ########################################################
    print ('st.session_state.bool_save_newopt_confirm',st.session_state.bool_save_newopt_confirm)
    if st.session_state.bool_save_newopt_confirm==1:        
        st.session_state.bool_save_newopt_confirm=2
        if is_maintenance=='maintenance':
            sql = f"""INSERT INTO email.issues (area, location, issue, maintype, subtype, subsubsubtype, issuestr, idemail, username, timesubmit) VALUES ('{area}','{location}','{issue}','{maintype}','{subtype}', '{is_maintenance}', '{issue_str}', '{id_email}', '{username}','{str(time.time())}')""" 
        else:
            sql = f"""INSERT INTO email.issues (area, location, issue, subsubsubtype, issuestr, idemail, username, timesubmit) VALUES ('{nonmain}','{nonmain_sub}','{nonmain_subsub}', '{is_maintenance}', '{issue_str}', '{id_email}', '{username}','{str(time.time())}')"""      
        print (sql)         
        cur = connect_db().cursor()
        try:
            cur.execute(sql)            
            cur.execute('commit')            
            pull_options()
            # add_issue(issue_str)
            st.session_state.bool_save_newopt_sccuss = 1
        except:
            cur.execute("rollback") 
            st.session_state.bool_save_newopt_sccuss = 0
        print (';;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;')
        st.rerun()
    if st.session_state.bool_save_newopt_confirm==2:
        st.session_state.bool_save_newopt_confirm=0
        if st.session_state.bool_save_newopt_sccuss == 1:
            st.sidebar.warning("Your new keyword is saved successfully")
        elif st.session_state.bool_save_newopt_sccuss == 0:
            st.sidebar.error("Your new keyword is not saved! please report this to shuming.liang@uts.edu.au")
        

###### submit final results to email.labels##################################################################      
    def bool_final_submit():
        st.session_state.bool_final_submit=True
    def bool_final_submit_confirm():
        st.session_state.bool_final_submit_confirm=1

    st.sidebar.button(label="Final submit", on_click=bool_final_submit, key='key_final_submit')    

    res_final = ';'.join(st.session_state.issue_list) if len(st.session_state.issue_list)>0 else 'empty'
    with st.sidebar:   
        if st.session_state.bool_final_submit:             
            my_modal = Modal(title='', key='key_final_submit_modal',padding=0,max_width=800)      
            st.session_state.bool_final_submit=False

            if res_final=='empty':
                with my_modal.container(): 
                    st.markdown(f"<p style='text-align: center; color: red'>The list of matters between the orange lines is empty! </p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; color: red'>Please using Add issue button to add you slections or skip this email by refresh the webpage.</p>", unsafe_allow_html=True)
                    # st.markdown(f"<p style='text-align: center; '>Please go back re-edit it. Click the 'Add issue' button after selecting the options in the slectbox if the first question is 'yes'.</p>", unsafe_allow_html=True)                    
                    st.button('Back to re-edit it', key='key_final_submit_revise')
            else:
                with my_modal.container(): 
                    st.markdown(f"<p style='text-align: center; '>Your final email tags are:</p>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='text-align: center; color: red;'>{res_final}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; '>Please confirm to submit or re-edit it. Note that once submit it, you cannot change the result for this text!</p>", unsafe_allow_html=True)
                    
                    st.button('Back to re-edit it', key='key_final_submit_revise')
                    st.button('Confirm to submit it',on_click=bool_final_submit_confirm, key='key_final_submit_confirm')
    if st.session_state.bool_final_submit_confirm==1:
        st.session_state.bool_final_submit_confirm=2
        sql = f"""INSERT INTO email.labels (lable, timesubmit, idemail, username, timeuse, address) VALUES ('{res_final}','{str(time.time())}','{id_email}', '{username}','{str(int(time.time()-st.session_state.load_email_time))}','{address}')"""       
        print (sql)         
        cur = connect_db().cursor()
        try:
            cur.execute(sql)            
            cur.execute('commit')            
            st.session_state.bool_final_submit_sccuss = 1
            print ('***********this is end **************************',st.session_state.bool_final_submit_sccuss)
            st.rerun()    
        except Exception as e:
            cur.execute("rollback") 
            st.session_state.bool_final_submit_sccuss = 0
            print ('***********this is end **************************',e)
    
##########################################################################################################################################################

# if __name__ == "__main__":
#     run()

