# -*- coding: utf-8 -*-
"""
Created on Thu May 13 00:33:51 2021

@author: user
"""

import pandas as pd
from tqdm import tqdm
import requests
import numpy as np

sil_2020=pd.read_csv(r'D:\부동산 빅데이터 분석 스터디\아파트 찾기 프로젝트 수정\아파트(매매)__실거래가_20210513021116.csv', encoding='cp949', header=15)
sil_2020['구 이름']=[a.split(' ')[1] for a in sil_2020['시군구']]
sil_2020['동 이름']=[a.split(' ')[2] for a in sil_2020['시군구']]

for_pnu=pd.read_csv(r'D:\부동산 빅데이터 분석 스터디\상권 프로젝트 수정\상권 프로젝트\상권 프로젝트\소상공인시장진흥공단_상가(상권)정보_서울.csv', engine='python', encoding='utf-8', sep='|')
for_pnu=for_pnu.drop_duplicates(subset='법정동코드')

bjdcode_list=[]

for i in tqdm(sil_2020.index) :
    for j in for_pnu.index :
        if (sil_2020.loc[i, '구 이름'] == for_pnu.loc[j, '시군구명']) & (sil_2020.loc[i, '동 이름'] == for_pnu.loc[j, '법정동명']) :
            bjdcode_list.append(str(for_pnu.loc[j, '법정동코드']))
bjd_df=pd.DataFrame(bjdcode_list)
sil_2020.insert(loc=2, column='법정동코드', value=bjd_df)

sil_2020[['본번', '부번']]=sil_2020[['본번', '부번']].astype(str)
sil_2020['본번']=sil_2020['본번'].str[:-2]
sil_2020['부번']=sil_2020['부번'].str[:-2]

sil_2020['본번']=sil_2020['본번'].str.zfill(4)
sil_2020['부번']=sil_2020['부번'].str.zfill(4)

sil_2020['PNU']=sil_2020['법정동코드'] + '1'+ sil_2020['본번'] + sil_2020['부번']
sil_2020.rename(columns={'거래금액(만원)' : '거래금액'}, inplace=True)

sil_2020['거래금액']=[int(a.replace(',', ''))*10000 for a in sil_2020['거래금액']]

sil_2020['1㎡당 실거래가']=sil_2020['거래금액'] / sil_2020['전용면적(㎡)']

sil_2020['평균 1㎡당 실거래가']=sil_2020.groupby(['PNU'])['1㎡당 실거래가'].transform('mean')
sil_2020=sil_2020.drop_duplicates(subset=['PNU'])

sil_2020_copy=sil_2020.copy()

#%%

danji_apt=pd.read_csv(r'D:\부동산 빅데이터 분석 스터디\아파트 찾기 프로젝트 수정\서울 아파트.csv', encoding='cp949', sep=',')
del danji_apt['Unnamed: 0']
del danji_apt['geometry']

danji_apt.rename(columns={'사용연수' : '경과연수', 'k-전체세대수' : '세대수', 'k-아파트명' : '건물 이름'}, inplace=True)

for i in danji_apt.index :
    sep=danji_apt.loc[i, '건물 이름'].split('(')[0]
    danji_apt.loc[i, '건물 이름']=sep

def find_doro(searching) :
    url= "https://dapi.kakao.com/v2/local/search/keyword.json?query={}".format(searching)
    headers={"Authorization": "KakaoAK 1f26ccd78d132c1a8df33f46e92cabce"}
    places=requests.get(url,headers=headers).json()['documents']
    
    try :
        place=places[0]        
        road_address_name=place['road_address_name'].replace('서울', '서울특별시')
        
    except :
        road_address_name=np.nan
        
    return road_address_name

for i in danji_apt.index :
    doro_bool=danji_apt.loc[[i], ['kapt도로명주소']].isnull()
    if doro_bool.loc[i, 'kapt도로명주소']==True :
        danji_apt.loc[i, 'kapt도로명주소']=find_doro(danji_apt.loc[i, '건물 이름'])

danji_apt=danji_apt.dropna(subset=['kapt도로명주소'])
danji_apt=danji_apt[danji_apt['kapt도로명주소']!='']
danji_apt_copy=danji_apt.copy()

#%%

# sil_2020=sil_2020_copy.copy()

for i in sil_2020.index :
    sep=sil_2020.loc[i, '단지명'].split('(')[0]
    sil_2020.loc[i, '단지명']=sep

def find_doro2(searching) :
    url= "https://dapi.kakao.com/v2/local/search/keyword.json?query={}".format(searching)
    headers={"Authorization": "KakaoAK 1f26ccd78d132c1a8df33f46e92cabce"}
    places=requests.get(url,headers=headers).json()['documents']
    
    try :
        place=places[0]        
        road_address_name=place['road_address_name'].split(' ')[2] + ' '+place['road_address_name'].split(' ')[3]
        
    except :
        road_address_name=np.nan
        
    return road_address_name

for i in sil_2020.index :
    if sil_2020.loc[i, '도로명']==' ' :
        sil_2020.loc[i, '도로명']=find_doro2(sil_2020.loc[i, '단지명'])

sil_2020['도로명주소']='서울특별시 ' + sil_2020['구 이름'] + ' ' + sil_2020['도로명']

#%%

match=pd.merge(danji_apt, sil_2020[['도로명주소', '평균 1㎡당 실거래가']], how='inner', left_on='kapt도로명주소', right_on='도로명주소')

match.rename(columns={'평균 1㎡당 실거래가' : '전체 평형 1㎡당 평균 실거래가'}, inplace=True)

match.to_csv(r'D:\부동산 빅데이터 분석 스터디\아파트 찾기 프로젝트 수정\전체 평형 1㎡당 평균 실거래가 포함.csv', encoding='cp949')
