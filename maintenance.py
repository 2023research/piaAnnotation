from Home import *

###############################################################################################   
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
    # print ('lllllllllllllllllllll',df.shape)       
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
    # print ('idslabeled',idslabeled)
    idsopened = pull_idemail_open()
    # print('idsopened',idsopened)
    ids_used = set(idslabeled+idsopened)  
    # print ('ids_used',ids_used)
    print("--- %s pd seconds ---" % (time.time() - start_time))

    df, idsallset = get_email_data()
    df = df[['Body','ID']]
    idx_unlabled = idsallset.difference(ids_used)
    df_email = df.set_index('ID',drop=True)
    df_out = df_email.loc[list(idx_unlabled)]
    df_onerow = df_out.sample(1)
    # df_bool = df['ID'].apply(lambda x: x not in files)
    ## check special case
    df_onerow = df_email[df_email.index=='a1_26109']
    return df_onerow['Body'].values[0],df_onerow.index[0]            
    

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
