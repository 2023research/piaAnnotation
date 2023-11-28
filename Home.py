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

import yaml
from yaml.loader import SafeLoader

print ('-------------------------------------------new run-------------------------------------------------')
#######basic setting######################################################################################
# LOGGER = get_logger(__name__)
path_results = './results'
st.set_page_config(layout="wide")
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
    st.session_state.is_maintenance = 'no'
    st.session_state.key_area = 'unclear'
    st.session_state.key_location = 'unclear'
    st.session_state.key_issue = 'unclear'
    st.session_state.key_maintype = 'unclear'
    st.session_state.key_subtype = None   
    st.session_state.key_area_new=None
    st.session_state.key_location_new=None
    st.session_state.key_issue_new=None
    st.session_state.key_maintype_new=None
    st.session_state.key_subtype_new=None
####### database ############
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
# usernames = ['john','james','oliver','david','emma','alex']
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
    def reset_no():
        if st.session_state.is_maintenance == 'no':
            st.session_state.key_area = 'unclear'
            st.session_state.key_location = 'unclear'
            st.session_state.key_issue = 'unclear'
            st.session_state.key_maintype = 'unclear'
            st.session_state.key_subtype = None   
            st.session_state.key_area_new=None
            st.session_state.key_location_new=None
            st.session_state.key_issue_new=None
            st.session_state.key_maintype_new=None
            st.session_state.key_subtype_new=None
    
    reset_no()
    ####
    def reset():
        st.session_state.is_maintenance = 'no'
        reset_no()
        st.session_state.issue_list = []
        st.session_state.deletes = []
    if st.session_state.bool_final_submit_confirm==2:
        st.session_state.bool_final_submit_confirm=0
        print('^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^')
        st.session_state.bool_read_email = True
        reset()
        if st.session_state.bool_final_submit_sccuss == 1:
            st.sidebar.warning("Your final submition is successfully")
        elif st.session_state.bool_final_submit_sccuss == 0:
            st.sidebar.error("Your final submition is not saved! please report this to shuming.liang@uts.edu.au")
##### load email #####################################################################################
    def pull_idemail_labeled():
        cur = connect_db().cursor()
        cur.execute('select idemail from email.labels')    
        ids = [x[0] for x in cur.fetchall()]
        if len(ids)==0:
            ids=['temp']
        return ids
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
        print ('lllllllllllllllllllll',df.shape)       
        if df.shape[1]>0:
            df.columns = [ x.name for x in cur.description ]
            df['timeopened'] = time.time() - df['timeopened'].astype(float)
            ids = df['idemail'][df['timeopened']<1000].to_list()     
            # print (df)
        else:
            ids = ['temp']   
        return ids
    
    def read_email(sample=False):
        @st.cache_data
        def get_email_data():
            df = pd.read_csv('./data/test_pos_wlTFLR_key_6k.csv',sep=',')
            idsallset = set(df["ID"].unique())
            print('######################')
            return df, idsallset
        ####
        start_time = time.time()
        idslabeled = pull_idemail_labeled()
        print ('idslabeled',idslabeled)
        idsopened = pull_idemail_open()
        print('idsopened',idsopened)
        ids_used = set(idslabeled+idsopened)  
        print ('ids_used',ids_used)
        print("--- %s pd seconds ---" % (time.time() - start_time))

        df, idsallset = get_email_data()
        df = df[['Body','ID']]
        idx_unlabled = idsallset.difference(ids_used)
        df_email = df.set_index('ID',drop=True)
        df_out = df_email.loc[list(idx_unlabled)]
        df_onerow = df_out.sample(1)
        # df_bool = df['ID'].apply(lambda x: x not in files)
        return df_onerow['Body'].values[0],df_onerow.index[0]            
        
    if st.session_state.bool_read_email == True:
         st.session_state.bool_read_email = False
         st.session_state.text_email, st.session_state.id_email = read_email()
         push_idemail_open(id_email=st.session_state.id_email,username=username)

    text_email,id_email = st.session_state.text_email, st.session_state.id_email
    print (id_email)    
    st.header(f'Text to analyze. The email id is: {id_email}', divider='red')
    st.markdown(text_email)
    st.header(body='',divider='red' )
    st.header('End')
#### slectbox options #####################################
    def pull_options():
        cur = connect_db().cursor()
        cur.execute('select * from email.issues')
        opts_df = pd.DataFrame(cur.fetchall())
        if opts_df.shape[0]>0:
            opts_df.columns = [ x.name for x in cur.description ]
        else:
            opts_df = pd.DataFrame(['unclear','unclear','unclear','unclear','unclear','unclear'])
            opts_df.columns = ['area','location','issue','maintype','subtype','issuestr']
        st.session_state.opts_df = opts_df
    #### pull latest options from database ####
    # start_time = time.time()
    if st.session_state.opts_df is None:
        pull_options()    
    if time.time() - st.session_state.time_lastopt >5:
        st.session_state.time_lastopt = time.time()
        pull_options()
        print ('########---------------------$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$-')
    opts_df = st.session_state.opts_df
    #### area ####
    opts_area = opts_df['area']
    opts_area =opts_area.unique().tolist()
    if 'unclear' not in opts_area:
        opts_area.append('unclear')
    #### location ####
    opts_location = opts_df.groupby('area')['location'].agg(['unique'])
    opts_location['unique'] = opts_location['unique'].apply(lambda x: x.tolist())
    opts_location = opts_location['unique'].to_dict()
    opts_location['unclear']=['unclear']
    #### issue ####
    opts_issue = opts_df.groupby('location')['issue'].agg(['unique'])
    opts_issue['unique'] = opts_issue['unique'].apply(lambda x: x.tolist())
    opts_issue = opts_issue['unique'].to_dict()
    opts_issue['unclear']=['unclear']
    #### maintype ####
    opts_maintype = opts_df.groupby('issue')['maintype'].agg(['unique'])
    opts_maintype['unique'] = opts_maintype['unique'].apply(lambda x: x.tolist())
    opts_maintype = opts_maintype['unique'].to_dict()
    opts_maintype['unclear']=['unclear']
    #### subtype ####
    opts_subtype = opts_df.groupby('maintype')['subtype'].agg(['unique'])
    opts_subtype['unique'] = opts_subtype['unique'].apply(lambda x: x.tolist())
    opts_subtype = opts_subtype['unique'].to_dict()
    opts_subtype['unclear']=['unclear']

    # print("---1 %s cur seconds ---" % (time.time() - start_time))

###### add issue ################################################################################  
    
    is_maintenance = st.sidebar.selectbox( "Is it related to the property maintenance?", ("no","yes"), 
                                            placeholder="Select yes or no...", key='is_maintenance')   
    disable = False if is_maintenance=='yes'else True

    def select_issues(label='0',opt=['0','1'], phld="", idx=0, disable=disable,key=['0','1']):
        def change_key():
            pass
        opt.sort()
        opt.append('add a new option')        
        
        c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
        with c1:
            item = st.selectbox(label=label, options=opt, index=idx, placeholder=phld, on_change = change_key, disabled=disable, key=key[0])   
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
                    item = 'unclear'                    
        
        return item
    ################################
    area = select_issues("which room or area has issue?",opts_area,disable=disable,key=['key_area','key_area_new'])  
    ########## 
    if area not in opts_location.keys():
        opts_location[area] = ['unclear']  
    location = select_issues(f"In {area}, which part has issue?",opts_location[area],disable=disable,key=['key_location','key_location_new'])
    # check if new location has been existed in area like bedroom
    if location in opts_area and location != "add a new option" and location != "unclear" and location != "general":        
        st.sidebar.error(f"""Your new keyword '{location}' has been existed in the selectbox of "which room or area has issue?".""")
    ##########
    if location not in opts_issue.keys():
        opts_issue[location] = ['unclear']
    issue = select_issues(f"What's the problem with {location}?",opts_issue[location],disable=disable,key=['key_issue','key_issue_new'])
    ##########
    if issue not in opts_maintype.keys():
        opts_maintype[issue] = ['unclear']
    maintype = select_issues("what maintenance requied?",opts_maintype[issue],disable=disable,key=['key_maintype','key_maintype_new'])
    ##########
    if maintype not in opts_subtype.keys():
        opts_subtype[maintype] = ['unclear']
    subtype = select_issues("more maintenance requied?",opts_subtype[maintype],idx=None,disable=disable,key=['key_subtype','key_subtype_new'])
    # print ('st.session_state.key_area',st.session_state.key_area)    
    
   
######## add issue description ################################################################################
    issue_str_list = [is_maintenance,area,location,issue,maintype,subtype]
    opt_long_checklist=[]
    issue_str=""
    for i, ele in enumerate(issue_str_list):  
        if ele !=None:
            if len(ele)>22:
                opt_long_checklist.append(ele)
        if i<len(issue_str_list)-1:
            issue_str=issue_str+ele+'/'# if ele !=None else issue_str+'None/'
        elif ele !=None:
            issue_str=issue_str+ele # if ele !=None else issue_str+'None'
    print (issue_str)

    ### add issue button ##########
    def add_issue(issue_str=None):
        if issue_str !=None and issue_str not in st.session_state.issue_list:
            st.session_state.issue_list.append(issue_str)

    def delete_field(index):
        del st.session_state.issue_list[index]
        del st.session_state.deletes[index]

    def add_newopt_button():
        st.session_state.bool_add_newopt_button = True
    
    bool_addissue = disable
    if  "add a new option" in [st.session_state.key_area, st.session_state.key_location, st.session_state.key_issue,
                               st.session_state.key_maintype, st.session_state.key_subtype]:
        bool_addissue = True
    bool_addopt = (not bool_addissue) or (is_maintenance=='no') 
    c1, c2 = st.sidebar.columns([0.6,0.4], gap='small') 
    with c1:
        add_issue_res = st.button("➕ Add issue", on_click=add_issue, args=(issue_str,),disabled=bool_addissue, key='add_issue')  
    with c2:
        st.button("➕ Add new keywrod", on_click=add_newopt_button, disabled=bool_addopt, key='add_new_options')
   
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
        sql = f"""INSERT INTO email.issues (area, location, issue, maintype, subtype, issuestr, idemail, username) VALUES ('{area}','{location}','{issue}','{maintype}','{subtype}', '{issue_str}', '{id_email}', '{username}')"""       
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
        
######## showing issues###############################################
    # st.sidebar.divider()
    st.sidebar.subheader('list of issue description',divider='orange')
    for i in range(len(st.session_state.issue_list)):
        c1, c2 = st.sidebar.columns([0.2,0.8], gap='small')    
        if is_maintenance=='yes':                    
            with c1:
                st.session_state.deletes.append(st.button("❌", key=f"delete{i}", on_click=delete_field, args=(i,)))
            with c2:
                st.write(st.session_state.issue_list[i])       
            
    # st.write(issue_list)
    print ('st.session_state.issue_list',st.session_state.issue_list)
    if is_maintenance == 'no':
        c1, c2 = st.sidebar.columns([0.4,0.5], gap='small')    
        with c2:
            st.write('no')
    st.sidebar.subheader('',divider='orange')

###### submit final results to email.labels##################################################################      
    def bool_final_submit():
        st.session_state.bool_final_submit=True
    def bool_final_submit_confirm():
        st.session_state.bool_final_submit_confirm=1

    st.sidebar.button(label="Final submit", on_click=bool_final_submit, key='key_final_submit')    

    res_final = ';'.join(st.session_state.issue_list) if len(st.session_state.issue_list)>0 else 'no'
    with st.sidebar:   
        if st.session_state.bool_final_submit:             
            my_modal = Modal(title='', key='key_final_submit_modal',padding=0,max_width=800)      
            st.session_state.bool_final_submit=False

            if st.session_state.is_maintenance == 'yes' and res_final=='no':
                with my_modal.container(): 
                    st.markdown(f"<p style='text-align: center; '>Your have selected 'yes' in the first question, but the list of issue descriptions is empty! </p>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; '>Please go back re-edit it. Add issue if the first question is 'yes'. If no any issues, the first question must be 'no'.</p>", unsafe_allow_html=True)
                    # st.markdown(f"<p style='text-align: center; '>Please go back re-edit it. Click the 'Add issue' button after selecting the options in the slectbox if the first question is 'yes'.</p>", unsafe_allow_html=True)                    
                    st.button('Back to re-edit it', key='key_final_submit_revise')
            else:
                with my_modal.container(): 
                    st.markdown(f"<p style='text-align: center; '>Your final categorization result is:</p>", unsafe_allow_html=True)
                    st.markdown(f"<h3 style='text-align: center; color: red;'>{res_final}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<p style='text-align: center; '>Please confirm to submit or re-edit it. Note that once submit it, you cannot change the result for this text!</p>", unsafe_allow_html=True)
                    
                    st.button('Back to re-edit it', key='key_final_submit_revise')
                    st.button('Confirm to submit it',on_click=bool_final_submit_confirm, key='key_final_submit_confirm')
    if st.session_state.bool_final_submit_confirm==1:
        st.session_state.bool_final_submit_confirm=2
        sql = f"""INSERT INTO email.labels (lable, timesubmit, idemail, username) VALUES ('{res_final}','{str(time.time())}','{id_email}', '{username}')"""       
        print (sql)         
        cur = connect_db().cursor()
        # cur.execute(sql)            
        # cur.execute('commit')
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
    
            
    # if st.session_state.bool_final_submit_confirm==2:
        # st.session_state.bool_final_submit_confirm=0
        # st.session_state.bool_read_email = True
        # reset()
        # if st.session_state.bool_final_submit_sccuss == 1:
        #     st.sidebar.warning("Your final submition is successfully")
        # elif st.session_state.bool_final_submit_sccuss == 0:
        #     st.sidebar.error("Your final submition is not saved! please report this to shuming.liang@uts.edu.au")
    

    # if not submit and is_maintenance is not None:
    # st.sidebar.write("Please do not forget to submit your results before annotating next one")
##########################################################################################################################################################
##########################################################################################################################################################

# if __name__ == "__main__":
#     run()

