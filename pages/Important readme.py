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
# from maintenance import *
# import pybase64
import yaml
from yaml.loader import SafeLoader

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

    st.header('Important:')
    st.markdown("""
                - For the part of email tagging:                 
                    - After selecting the options, **DO NOT Forget** to click the “add matter” button to add your selection into the list of matters.
                    - If the list of matters is empty, when you click the “Final submit” button, the popup will let you go back to re-analysis it.
                    - If this email is not related to any category, please select ‘other’ in the first question. In this case, you still need to click the “add matter” button for the final submit.
                    - If you need to add a new keyword, please select the last option in the drop list to activate the add new key word module. IMPORTANT: please carefully add a new key word because 1. all people will also see it in the following annotations. 2. If the keyword is chaos or complicated, it will confuse everyone.
                 """,unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.1,0.8,0.1])

    with col1:
        st.write(' ')

    with col2:
        st.image('readme1.png',caption='Please remember to add your selection into the list of matters')

    with col3:
        st.write(' ')
    st.header('Special case 1:')

    st.markdown("""
                - For the email that does not have any meaning content (as show in the figure below): 
                    - You do not need to do anything in the address and selection box BUT,
                    - You must click 'Add matter' to add an 'other' issue to the list and clik 'final submit',
                    - otherwise, this email will be re-load in your next annoation until you final submit it.
                 """,unsafe_allow_html=True)
    col1, col2, col3 = st.columns([0.1,0.8,0.1])

    with col1:
        st.write(' ')

    with col2:
        st.image('readme2.png',caption='Please remember to add your selection into the list of matters')

    with col3:
        st.write(' ')
    
###############################################################################################   
    
######## important readme #############################################################################
    # def displayPDF(file):
        # Opening file from file path
    # with open('readme.pdf', "rb") as f:
    #     base64_pdf = pybase64.b64encode(f.read()).decode('utf-8')

    # # Embedding PDF in HTML
    # pdf_display = F'<embed src="data:application/pdf;base64,{base64_pdf}" width="900" height="1000" type="application/pdf">'

    # # Displaying File
    # st.markdown(pdf_display, unsafe_allow_html=True)
    # st.sidebar.button("IMPORTANT readme", on_click=displayPDF, args=('readme.pdf',),disabled=False, key='key_readme')  
    # displayPDF('readme.pdf')
######## property address #############################################################################
   