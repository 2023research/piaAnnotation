# Copyright (c) Streamlit Inc. (2018-2022) Snowflake Inc. (2022)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
from urllib.error import URLError
import os, psycopg2, time
import pandas as pd
import streamlit as st
import streamlit_authenticator as stauth
import streamlit.components.v1 as components
from streamlit_modal import Modal
from streamlit.logger import get_logger

from sqlalchemy import create_engine
from sqlalchemy.sql import text

# from utils import *
from maintenance import *

import yaml
from yaml.loader import SafeLoader

st.set_page_config(layout="wide")
print ('-------------------------------------------new run-------------------------------------------------')
#######basic setting######################################################################################
# path_results = './results'
####### initialize global session state
if "issue_list" not in st.session_state:
    st.session_state.id_email = None
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
####### database ############ nonmain,nonmain_sub,nonmain_subsub
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
else: 
    st.markdown(f"<h2 style='text-align: center; color: red;'>Welcome {username}!</h2>", unsafe_allow_html=True)
    authenticator.logout('Logout')
###############################################################################################   
    def reset_maintenance_no():
        # if st.session_state.is_maintenance == 'no':
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

    if st.session_state.bool_read_email == True:
         st.session_state.load_email_time = time.time()
         st.session_state.bool_read_email = False
         st.session_state.text_email, st.session_state.id_email = read_email()
         push_idemail_open(id_email=st.session_state.id_email,username=username)

    text_email,id_email = st.session_state.text_email, st.session_state.id_email
    print (id_email)    
    st.header(f'Text to analyze. The email id is: {id_email}', divider='red')
    st.markdown(text_email)
    st.header(body='',divider='red' )
    st.header('End')
######## property address #############################################################################
    st.sidebar.subheader('Peoperty Address')
    with st.sidebar:
        adstreet = st.text_input(label='street',value ='other')
        if adstreet=='': adstreet="other"
        c1, c2, c3 = st.columns([0.4,0.4,0.2], gap='small') 
        with c1:
            adsuburb = st.text_input(label='suburb')
            if adsuburb=='': adsuburb="other"
        with c2:
            adstate = st.text_input(label='state')
            if adstate=='': adstate="other"
        with c3:
            adpostcode = st.text_input(label='postcode')
            
            if adpostcode is '': 
                adpostcode="other"                
                print ('ddddddddddddddddd',adpostcode)
    st.sidebar.subheader('',divider='red')
    ads_list = [adstreet,adsuburb,adstate,adpostcode]
    address =""
    for i, ele in enumerate(ads_list):  
        if i<len(ads_list)-1:
            address=address+ele+'|' #if ele !=None else address+'None|'
        elif ele !='':
            address=address+ele # if ele !=None else issue_str+'None'
    print ('########',address)
#### slectbox options ##########################################################################################
    opts_related,opts_area, opts_location,opts_issue,opts_maintype,opts_subtype,opts_nonmain, opts_nonmain_sub,opts_nonmain_subsub = maintenance_options()    

###### maintenance selection box ################################################################################ 

    def select_issues(label='0',opt=['0','1'], phld="", disable=False,key=['0','1']):
        def change_key():
            pass
        opt = [value for value in opt if value != "other"]        
        opt.sort()
        opt.append('other')  
        opt.append('add a new option') 
        idx = opt.index('other')
        c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
        with c1:
            item = st.selectbox(label=label, options=opt, placeholder=phld, on_change = change_key, disabled=disable, key=key[0])  #index=idx,   
            if st.session_state[key[0]] != "add a new option":
                st.session_state[key[1]] = None         
        with c2:                
            disable_newopt = (item!="add a new option") or (disable)
            new_option = st.text_input(label="Input your new keyword",label_visibility='visible', placeholder='Input your new keyword',
                                        disabled = disable_newopt,key=key[1])              
            if item=="add a new option":
                if new_option!='':
                    item = new_option.lower()  
                    if new_option in opt or new_option[:-1] in opt:
                        # st.session_state[key[0]] = new_option
                        # item = st.selectbox(label=label, options=opt, index=idx, placeholder=phld, disabled=disable, key=key[0]) 
                        st.warning(f"Your new option '{new_option}' has been existed in the left selectbox.")
                    else:                        
                        st.session_state.newopts[label]=item
                else:
                    item = 'other'                    
        
        return item
    #### related is_maintenance ###############################################################
    print (st.session_state.key_area)
    is_maintenance = select_issues("what is the email related to?",opts_related,key=['is_maintenance','is_maintenance_new'])  
    disable = False
    if is_maintenance=='maintenance':
        ###################################################################
        #### area ####
        print (st.session_state.key_area)
        area = select_issues("which area has issue?",opts_area,disable=disable,key=['key_area','key_area_new'])  
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
    else:
        ###################################################################
        #### nonmain ####
        if is_maintenance not in opts_nonmain.keys():
            opts_nonmain[is_maintenance] = ['other']
        if 'other' not in  opts_nonmain[is_maintenance]:
            opts_nonmain[is_maintenance].append('other')
        nonmain = select_issues("main type of the matter",opts_nonmain[is_maintenance], key=['key_nonmain','key_nonmain_new'])

        ###################################################################
        #### nonmain_sub ####
        if is_maintenance not in opts_nonmain_sub.keys():
            opts_nonmain_sub[is_maintenance] = ['other']
        if 'other' not in  opts_nonmain_sub[is_maintenance]:
            opts_nonmain_sub[is_maintenance].append('other')
        nonmain_sub = select_issues("subtype",opts_nonmain_sub[is_maintenance], key=['key_nonmain_sub','key_nonmain_sub_new'])

        ###################################################################
        #### nonmain_subsub ####
        if is_maintenance not in opts_nonmain_subsub.keys():
            opts_nonmain_subsub[is_maintenance] = ['other']
        if 'other' not in  opts_nonmain_subsub[is_maintenance]:
            opts_nonmain_subsub[is_maintenance].append('other')
        nonmain_subsub = select_issues("sub-subtype",opts_nonmain_subsub[is_maintenance], key=['key_nonmain_subsub','key_nonmain_subsub_new'])
        ###################################################################
        issue_str_list = [is_maintenance,nonmain,nonmain_sub,nonmain_subsub]
    
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

