import warnings
warnings.simplefilter(action='ignore', category=FutureWarning)

from urllib.error import URLError
import os, psycopg2, datetime,re
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

df['datesubmit'] = df['timesubmit'].apply(lambda x: datetime.datetime.fromtimestamp(float(x)).strftime('%Y-%m-%d %H:%M:%S'))
df['datesubmit'] = pd.to_datetime(df['datesubmit'])
df = df[df['datesubmit']>datetime.datetime(2024, 1, 17)]
df = df[df['datesubmit']<=datetime.datetime(2024, 1, 18)]
df['first_category'] = df['lable'].apply(lambda x: x.split('|')[0])
df['second_category'] = df['lable'].apply(lambda x: x.split('|')[1] if len(x.split('|'))>=2 else None)
timeoutlier = 300

print ('total annotated emails:',df.shape[0])
print (f'Number of annotated emails (time use > {timeoutlier}s):',sum(df['timeuse']>timeoutlier))
print (f'Number of annotated emails (time use <= {timeoutlier}s):',sum(df['timeuse']<=timeoutlier))
# statis = df.groupby('username').agg({'timeuse':['mean','count']})
# statis.columns=['mean time use (s)', 'number of annotated']
# print (statis)
# df100 = df[df['timeuse']<=timeoutlier]
# statis = df100.groupby('username').agg({'timeuse':['mean','count']})
# statis.iloc[:,0] = statis.iloc[:,0].apply(lambda x: round(x))
# col_all1,col_all2 = 'mean timeuse(s)', 'num of annotated emails'
# statis.columns=[col_all1,col_all2]
# # statis['mean time use (s)'] = statis['mean time use (s)'].apply(lambda x: round(x))
# statis_all = statis.copy()
# print (statis_all)
#
# # maintenance speed########
# df_mainte = df[df['timeuse']<=timeoutlier]
# df_mainte = df_mainte[df_mainte['first_category']=='maintenance']
# statis = df_mainte.groupby('username').agg({'timeuse':['mean','count']})
# statis.iloc[:,0] = statis.iloc[:,0].apply(lambda x: round(x))
# col1,col2 = 'mean timeuse(s) on maintenance email', 'num of annotated emails (maintenance)'
# statis.columns=[col1,col2]
# statis_mainte = statis[[col2,col1]]
# print (statis_mainte)
# statis=statis_all.merge(statis_mainte,how='left',left_index=True,right_index=True)
# print (statis)
# statis['maintenance percentage'] = statis[col2]/statis[col_all2]
#
# # tenancy related ###
# # maintenance speed########
# df_tenancy= df[df['timeuse']<=timeoutlier]
# df_tenancy = df_tenancy[df_tenancy['first_category']=='tenancy related']
# statis_tenancy = df_tenancy['second_category'].value_counts()
# # statis_tenancy = df_tenancy.groupby('second_category').agg({'timeuse':['count']})
# print (statis_tenancy)
#
# df_first_cate = df100['first_category'].value_counts().to_frame()
# # df_first_cate.to_csv('./results/firstcate.csv')
# print (df_first_cate.index)
# print (df_first_cate.count)
#
# top_category = 4
#
# top = []
# for name in statis.index:
#     df_person = df100[df100['username']==name]
#     counts = df_person['first_category'].value_counts()
#     counts = counts.iloc[:top_category].to_dict()
#     top.append(counts)
#     print (name,df_person['first_category'].value_counts())
# statis[f'counts of top {top_category} categories'] = top
# # statis.to_csv('./results/statis.csv')

# for name in ['andy', 'jeffrey', 'kevin', 'ray','tony', 'leon']:
#     dfall = pd.read_csv('./data/'+name+'.csv', sep=',')
#     print (name,dfall.shape[0])

for name in ['andy', 'jeffrey', 'kevin', 'ray','tony', 'leon']:
    if name =='andy':
        dfall = pd.read_csv('../../data/'+name+'.csv', sep=',')
    else:
        dfother = pd.read_csv('../../data/'+name+'.csv', sep=',')
        dfall = pd.concat((dfall,dfother))
    print (name,dfall.shape[0])

df_tony = df[df['timeuse']<=timeoutlier]
# df_tony = df[df['username']=='tony']
email_list = []
for row in df_tony.iterrows():
    row=row[1]
    label, idemail = row['lable'],row['idemail']
    email_body = dfall[dfall['ID']==idemail]['Body'].values[0]
    email_list.append(email_body[:min(len(email_body),5000)])
    # print (row)
df_tony['Body']=email_list


def clean_text(text):
    # words = set(nltk.corpus.words.words())
    # text = text.lower()
    # text = re.sub("[^a-zA-Z]"," ",text)
    # text = " ".join(w for w in nltk.wordpunct_tokenize(text) if w.lower() in words or not w.isalpha())
    text = re.sub(
        "[Â,Ã,,ÃÂ, Ã,¢, ,  ,¤, , ¥,¹,´,¦, ,  ,   ,  , º,¨ , ¤, , ¸, , , , ,©, , , ¯, ¼, , »,¿,]",
        " ", text)
    # text = text.encode('latin-1').decode("utf-8")
    # text = re.sub(r'\n\s*\n', '\n\n', text)
    # text = '\n'.join(text.split())
    return text

df_tony['Body'] = df_tony['Body'].apply(lambda x: clean_text(x))
df_tony['Body'] = df_tony['Body'].apply(lambda x: re.sub(r'\n\s*\n', '\n\n', x))

df_tony = df_tony[['lable', 'first_category', 'second_category', 'Body', 'idemail', 'username', 'timeuse',
       'address', 'datesubmit']]
df_tony.columns = ['label', 'first_category', 'second_category', 'email', 'email id', 'username', 'timeusage',
       'property address', 'datesubmit']
df_save = df_tony.groupby('label').sample(n=2, replace=True,random_state=1)
df_save.drop_duplicates(inplace=True)
df_save.to_csv('./results/annotation_samples_by_PMs.csv',index=False)
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
