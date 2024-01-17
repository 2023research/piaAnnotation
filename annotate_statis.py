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
from sklearn import metrics

import requests
import json
url = "http://54.253.228.31:8000/piatextclassfier"

def connect_db():
    conn = psycopg2.connect("dbname=pia host=piadb.c4j0rw3vec6q.ap-southeast-2.rds.amazonaws.com user=postgres password=UTS-DSI2020")
    return conn

cur = connect_db().cursor()
cur.execute('select * from email.labels') 
df = pd.DataFrame(cur.fetchall())
df.columns = [ x.name for x in cur.description ]
df = df[df['timeuse'].notnull()]
print ('user names:',df['username'].unique())
df['timeuse'] = df['timeuse'].astype(int)

opts_location = df.groupby('username').agg({'timeuse':['mean','count']})
print ('total annotated emails:',df.shape[0])
print ('Number of annotated emails (time use > 100s):',sum(df['timeuse']>100))
print ('Number of annotated emails (time use <= 100s):',sum(df['timeuse']<=100))
statis = df.groupby('username').agg({'timeuse':['mean','count']})
statis.columns=['mean time use (s)', 'number of annotated']
print (statis)
df100 = df[df['timeuse']<=100]
statis = df100.groupby('username').agg({'timeuse':['mean','count']})
statis.columns=['mean time use (s)', 'number of annotated']
print (statis)

for name in ['andy', 'jeffrey', 'kevin', 'ray','tony', 'leon']:
    dfall = pd.read_csv('./data/'+name+'.csv', sep=',')
    print (name,dfall.shape[0])

for name in ['andy', 'jeffrey', 'kevin', 'ray','tony', 'leon']:
    if name =='andy':
        dfall = pd.read_csv('./data/'+name+'.csv', sep=',')
    else:
        dfother = pd.read_csv('./data/'+name+'.csv', sep=',')
        dfall = pd.concat((dfall,dfother))
    print (name,dfall.shape[0])

df_tony = df[df['username']=='tony']
email_list = []
for row in df_tony.iterrows():
    row=row[1]
    label, idemail = row['lable'],row['idemail']
    email_body = dfall[dfall['ID']==idemail]['Body'].values[0]
    email_list.append(email_body[:min(len(email_body),5000)])
    # print (row)
df_tony['Body']=email_list
df_tony['maintenance']=df_tony['lable'].apply(lambda x: x.split('|')[0])
# df_tony.to_csv('./data/tony_158_temp.csv')
label_pred=[]
for id in df['idemail'].values:
    email = dfall[dfall['ID']==id]['Body'].values[0]
    label = df[df['idemail']==id]['lable'].values[0]
    maintenance = 'maintenance' if label.split('|')[0]=='maintenance' else 'non-maintenance'
    # print (label, email)
    params = {"piatext": email}
    response = requests.post(url, params=params)
    res = json.loads(response.text)
    label_pred.append([maintenance,res['is_maintenance']])
    print('$$$$$$$$',maintenance, res['is_maintenance'])
label_pred = pd.DataFrame(label_pred,columns = ['label','pred'])
ground_true = label_pred[label_pred['label']=='maintenance']
ground_false = label_pred[label_pred['label']=='non-maintenance']
print (ground_true.shape[0],ground_false.shape[0])
print(sum(ground_true['pred']=='maintenance'),sum(ground_true['pred']=='non-maintenance'),sum(ground_false['pred']=='maintenance'),sum(ground_false['pred']=='non-maintenance'))

label_pred['label0'] = label_pred['label'].apply(lambda x:0 if x == 'non-maintenance' else 1)
label_pred['pred0'] = label_pred['pred'].apply(lambda x:0 if x == 'non-maintenance' else 1)
print ('auc:',metrics.roc_auc_score(label_pred['label0'],label_pred['pred0']),
       'accuracy_score:',metrics.accuracy_score(label_pred['label0'],label_pred['pred0']),
        'f1:',metrics.f1_score(label_pred['label0'],label_pred['pred0']),
    'recall_score:',metrics.recall_score(label_pred['label0'],label_pred['pred0']),
    'precision_score:',metrics.precision_score(label_pred['label0'],label_pred['pred0'])
       )

label_pred=[]
for id in df['idemail'].values:
    email = dfall[dfall['ID']==id]['Body'].values[0]
    label = df[df['idemail']==id]['lable'].values[0]
    maintenance = 'maintenance' if label.split('|')[0]=='maintenance' else label
    # print (label, email)
    params = {"piatext": email}
    response = requests.post(url, params=params)
    res = json.loads(response.text)
    label_pred.append([maintenance,res['is_maintenance'],id,email])
    print('$$$$$$$$',maintenance, res['is_maintenance'])
label_pred = pd.DataFrame(label_pred,columns = ['label','pred','id','email'])
ground_true = label_pred[label_pred['label']=='maintenance']
ground_false = label_pred[label_pred['label']!='maintenance']
print (ground_true.shape[0],ground_false.shape[0])
print(sum(ground_true['pred']=='maintenance'),sum(ground_true['pred']=='non-maintenance'),sum(ground_false['pred']=='maintenance'),sum(ground_false['pred']=='non-maintenance'))
print ('####',ground_false[ground_false['pred']=='maintenance'])

negative_predTrue = ground_false[ground_false['pred']=='maintenance']
negative_predTrue.to_csv('./data/negative_predTrue.csv')


label_pred['label0'] = label_pred['label'].apply(lambda x:0 if x != 'maintenance' else 1)
label_pred['pred0'] = label_pred['pred'].apply(lambda x:0 if x == 'non-maintenance' else 1)
print ('auc:',metrics.roc_auc_score(label_pred['label0'],label_pred['pred0']),
       'accuracy_score:',metrics.accuracy_score(label_pred['label0'],label_pred['pred0']),
        'f1:',metrics.f1_score(label_pred['label0'],label_pred['pred0']),
    'recall_score:',metrics.recall_score(label_pred['label0'],label_pred['pred0']),
    'precision_score:',metrics.precision_score(label_pred['label0'],label_pred['pred0'])
       )
print (df)
