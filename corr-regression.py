import statsmodels.formula.api as smf
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from fiona.crs import from_string
from pyproj import CRS
import geopandas as gpd


# 단지형 아파트 csv를 가지고 다중 회귀분석

price=pd.read_csv(r'D:\부동산 빅데이터 분석 스터디\아파트 찾기 프로젝트 수정\전체 평형 1㎡당 평균 실거래가 포함.csv', encoding='cp949')
del price['Unnamed: 0']

price['geometry'] = price.apply(lambda row: Point(row.좌표X, row.좌표Y), axis=1)

price_geo=gpd.GeoDataFrame(price, geometry='geometry', crs='epsg:4326')

price_geo=price_geo.to_crs(epsg5181_qgis)

#%%
# 지하철 거리 구하기
subway=gpd.GeoDataFrame.from_file(r'D:\부동산 빅데이터 분석 스터디\아파트 찾기 프로젝트 수정\subway.shp', encoding='cp949')
subway2=subway.to_crs(epsg5181_qgis)

for i in tqdm(price_geo.index) :
    for j in range(10, 5000, 10) :
        buf=price_geo.loc[i, 'geometry'].buffer(j)
        try :
            a=pd.DataFrame(subway2.geometry.intersects(buf))
            a=a.astype(str)
            a.columns=['a']
            a=a[a['a']=='True']
            
            if len(a) > 0 :
                break 
            
            price_geo.loc[i, '지하철거리']=j
        
        except :
            break
            price_geo.loc[i, '지하철거리']=np.nan
            
#%%
# Dummy 변수 만들기
for i in price_geo.index :
    # print(price_geo['k-복도유형'].unique())
    
    if price_geo.loc[i, 'k-복도유형'] == '기타' :
        price_geo.loc[i, '복도유형'] = np.nan
        
    elif price_geo.loc[i, 'k-복도유형'] == '복도식' :
        price_geo.loc[i, '복도유형'] = 1
    
    elif price_geo.loc[i, 'k-복도유형'] == '혼합식' :
        price_geo.loc[i, '복도유형'] = 2
    
    elif price_geo.loc[i, 'k-복도유형'] == '타워형' :
        price_geo.loc[i, '복도유형'] = 3
        
    elif price_geo.loc[i, 'k-복도유형'] == '계단식' :
        price_geo.loc[i, '복도유형'] = 3

    # print(price_geo['k-난방방식'].unique())
    
    if price_geo.loc[i, 'k-난방방식'] == '기타' :
        price_geo.loc[i, '난방방식'] = np.nan
    
    if price_geo.loc[i, 'k-난방방식'] == '중앙난방' :
        price_geo.loc[i, '난방방식'] = 1
        
    if price_geo.loc[i, 'k-난방방식'] == '지역난방' :
        price_geo.loc[i, '난방방식'] = 2
        
    if price_geo.loc[i, 'k-난방방식'] == '개별난방' :
        price_geo.loc[i, '난방방식'] = 2
        
#%%
x_data=price_geo.dropna(subset=['경과연수', '세대수', '지하철거리', '종합병원거리', '초등학교거리', '중학교거리', '고등학교거리', '주요 공원 거리', '좌표X', '좌표Y', '복도유형', '난방방식'], how='any')

# 상관 관계 분석

x_data=x_data[['초등학교거리','중학교거리', '고등학교거리', '종합병원거리', '지하철거리', '주요 공원 거리',  '경과연수', '세대수', '복도유형', '난방방식', '좌표X', '좌표Y','전체 평형 1㎡당 평균 실거래가']]
corr=x_data.corr(method='pearson')

import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
font_path = 'C:\\Users\\user\\AppData\\Local\\Microsoft\\Windows\\Fonts\\NanumBarunpenR.ttf'
font = font_manager.FontProperties(fname=font_path).get_name()
rc('font', family=font)

cols_view= list(corr.columns)

sns.heatmap(corr.values,
               cbar = True,
               annot = True,
               square = True,
               fmt = '.2f' ,
               annot_kws = {'size' : 15},
               yticklabels = cols_view,
               xticklabels = cols_view)
plt.tight_layout()
plt.show()

x_data2=x_data[['초등학교거리','중학교거리', '고등학교거리', '종합병원거리', '지하철거리', '주요 공원 거리', '경과연수', '세대수', '좌표X', '좌표Y', '복도유형', '난방방식']]

target=x_data[['전체 평형 1㎡당 평균 실거래가']]

# 상수항 만들어주기
x_data3=sm.add_constant(x_data2)

# 다중회귀분석 모델 만들고 피팅
model = sm.OLS(target, x_data3)
fit_model=model.fit()

# 요약 출력 
# 다른건 다 이해 가는데 하나 신기한거는 예측 값에서는 초등학교가 가까우면 실거래가가 높게 찍혀야할텐데 초등학교 거리가 줄어들 수록 실거래가가 낮아진다는 점이다

fit_model.summary()

# 계수 값 출력
fit_model.params

# 다중회귀분석을 통한 예측값 만들기

pred1= pd.DataFrame(fit_model.predict(x_data3))

# 잔차 값 계산
fit_model.resid.plot(label='full')
plt.legend()

# plot 띄워보기

plt.plot(target[:1000], marker='o', color='blue', label='real')
plt.plot(pred1[:1000], marker='^', color='red', label='pred')
plt.title('R-Squared = 0.438')
plt.ylabel('price/m2')
plt.legend(loc='best')

# p-value가 높은 변수는 제외

x_data2=x_data[['중학교거리', '고등학교거리', '종합병원거리', '지하철거리', '주요 공원 거리', '경과연수', '세대수', '좌표X', '좌표Y', '복도유형']]

target=x_data[['전체 평형 1㎡당 평균 실거래가']]

