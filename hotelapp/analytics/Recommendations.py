__author__ = 'anil'

import configparser
config = configparser.ConfigParser()
config.read('../../app.conf')
from mongoengine.connection import connect,disconnect
connection=connect(config["MONGODB"]["DB_NAME"])
from hotelapp.models import Cluster, TAHotel
from pymongo import MongoClient
import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

client = MongoClient('localhost',27017)
db = client.hotelapp
reviews = db.review
attractions = db.attraction
users = db.t_a_user

dfAttractions = pd.DataFrame(list(attractions.find({"_id":{"$exists":"true"}})))
dfReviews = pd.DataFrame(list(reviews.find({"_id":{"$exists":"true"}})))
lUsers = np.unique(np.array(dfReviews['user'])).tolist()

row = []
for user in lUsers:
    locations = dfReviews[dfReviews['user'] == user]["reviewLocation"] #attraction IDs
    at = []
    typ = []
    for location in locations:
        at.append(dfAttractions[dfAttractions['_id'] == location]['properties'].values[0]['locationName']) #Append attraction name
        typ.append(','.join(dfAttractions[dfAttractions['_id'] == location]['properties'].values[0]['type'])) #Append attraction type
    row.append([user,";".join(at), ",".join(typ)])

dfUsers = pd.DataFrame(row, columns = ['users', 'attractions', 'types'])
f = lambda x: x.replace('\n','')
dfUsers['types']= dfUsers['types'].map(f)
dfUsers['attractions']= dfUsers['attractions'].map(f)
dfUsers['users'].astype(str)

class splitter1(object):
    def __call__(self, doc):
        return doc.split(';')

class splitter2(object):
    def __call__(self, doc):
        return doc.split(',')

vectorizer = CountVectorizer(tokenizer= splitter1())
x = vectorizer.fit_transform(dfUsers['attractions'].tolist())
Xattractions = pd.DataFrame(x.toarray(),columns=vectorizer.get_feature_names())

vectorizer = CountVectorizer(tokenizer= splitter2())
x = vectorizer.fit_transform(dfUsers['types'].tolist())
Xtypes = pd.DataFrame(x.toarray(),columns=vectorizer.get_feature_names())

userVect = Xattractions.join(Xtypes)
userVect.insert(0, 'Users', dfUsers['users'])
userVect = userVect.drop_duplicates(cols='Users', take_last=True)

users = db.t_a_user
dfUsers2 = pd.DataFrame(list(users.find({"_id":{"$exists":"true"}})))
dfUsers2['_id'].astype(str)

f = lambda x: str(x).replace('[','')
g = lambda x: x.replace(']','')
dfUsers2['visited']= dfUsers2['visited'].map(f)
dfUsers2['visited']= dfUsers2['visited'].map(g)

vectorizer = CountVectorizer(tokenizer= splitter2())
x = vectorizer.fit_transform(dfUsers2['visited'].tolist())
Xvisited = pd.DataFrame(x.toarray(),columns=vectorizer.get_feature_names())


dfUsers2['travelStyle']= dfUsers2['travelStyle'].map(f)
dfUsers2['travelStyle']= dfUsers2['travelStyle'].map(g)
z = lambda x: x.replace("'",'')
dfUsers2['travelStyle']= dfUsers2['travelStyle'].map(z)

vectorizer = CountVectorizer(tokenizer= splitter2())
x = vectorizer.fit_transform(dfUsers2['travelStyle'].tolist())
Xstyle = pd.DataFrame(x.toarray(),columns=vectorizer.get_feature_names())

loc =[]
for location in dfReviews['reviewLocation']:
    loc.append(dfAttractions[dfAttractions['_id'] == location]['properties'].values[0]['locationName'])
dfReviews['Loc_Names'] = loc
ratingsMtx = dfReviews.pivot_table(values='rating', rows='user', columns = 'Loc_Names').fillna(0)

from sklearn.cluster import KMeans
kmeans = KMeans()
clusters = kmeans.fit(ratingsMtx)
x = kmeans.predict(ratingsMtx)

clusters = pd.DataFrame(ratingsMtx.index.tolist(), columns= ["name"])
clusters['clusters'] = x.tolist()
clusCount = clusters.groupby(by='clusters').count().shape[0]

def model(clf, x, y):

    X_train = x
    y_train = y
    #print('_' * 80)
    clf.fit(X_train, y_train)

    #print("top 10 keywords per class:")
    features = []
    for i in range(clusCount):
        top10 = np.argsort(clf.coef_[i])[-5:]
        feature_names = x.columns
        features.append(feature_names[top10].values)
        #print(feature_names[top10])
        #print('-' *80)

    return features

Xtypes.insert(0,'name', dfUsers['users'])
dfClusters = clusters.merge(Xtypes, on='name') #Cluster type of attraction analysis. X= 2, y= 1

dfClusters2 = clusters.join(ratingsMtx, on='name', how='left') #Cluster attraction analysis X= 2:, y= 1

Xstyle.insert(0, '_id', dfUsers2['_id'])
dfClusters3 = clusters.join(Xstyle, on='name', how= 'left') #Cluster travel style analysis X= 2:, y= 1'''
dfClusters3 = dfClusters3.fillna(0)

from sklearn.linear_model import Perceptron
features = []
for cluster in [dfClusters, dfClusters2, dfClusters3]:
    features.append(model(Perceptron(n_iter=50), cluster.ix[:,2:], cluster.ix[:,1]))

clusterFeatures = pd.DataFrame(features, columns=['Cluster 1','Cluster 2','Cluster 3','Cluster 4','Cluster 5','Cluster 6','Cluster 7', 'Cluster 8'], index=['Types','Attractions', 'Styles'] )
clusterFeatures= clusterFeatures.T

hotelReviews = db.hotel_review
dfHReviews = pd.DataFrame(list(hotelReviews.find({"_id":{"$exists":"true"}})))
dfHReviews = pd.merge(dfHReviews, clusters, left_on='user', right_on='name', how='inner')
dfHRPivot = dfHReviews.pivot_table(rows='reviewLocation', columns='clusters', values='rating', aggfunc= lambda x: [len(x.unique()), round(np.mean(x),2)]).fillna(0)

c = Cluster()
indexes = clusterFeatures.index.values.tolist()
for i in range(clusterFeatures.shape[0]):
    c.cluster = indexes[i]
    c.types = clusterFeatures.ix[i,0].tolist()
    c.attractions = clusterFeatures.ix[i,1].tolist()
    c.save()

for i in range(dfHRPivot.shape[0]):
    h=TAHotel.objects.filter(_id=dfHRPivot.ix[i,0]).get()
    h.clusters = dfHRPivot.ix[i,:].tolist()
    h.save()

disconnect()