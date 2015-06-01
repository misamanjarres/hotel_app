__author__ = 'root'

from twython import TwythonStreamer
from hotelapp.models import Tweet,TwitterUser,BoundingBox
import configparser
config = configparser.ConfigParser()
config.read('../../app.conf')
from mongoengine.connection import connect,disconnect
connection=connect(config["MONGODB"]["DB_NAME"])

####################################################################
consumer_key="Vs7V2k4vPWMMyTFqLzqPkM6wE"
consumer_secret="aWNRzh74LUT1fuW35y6VzRDtvuimQ4LjFGMnMMkEXI0Y9LSpkf"

access_token="258113369-63Y2Cqr9q0Bo02WU4AS8Bjiv3JnHP2Us7HimK26G"
access_token_secret="Z4Sf9EyLbOJ4jPI5WlZPZUyv3OwluuZXiKXn0pamk8Dly"
###################################################################


#twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret)

#auth = twitter.get_authentication_tokens(callback_url='http://127.0.0.1:8000/callback')

class MyStreamer(TwythonStreamer):
    def on_success(self, data):
        if 'text' in data:
            print(data['text'].encode('utf-8'))
            #print(data["place"]["bounding_box"]['coordinates'])
        #try:
            qs=TwitterUser.objects.filter(userID=data["user"]["id_str"])
            #tweetlist=[]
            u = TwitterUser()
            if len(qs[:])>0:
                u=qs[:1].get()
                #print(u.gettweetObjIDs())
                #tweetlist= u.gettweetObjIDs()
                print(u)
            u.userID = data["user"]['id_str']#Should be uniqueId!!! Set as a qunique index
            u.userName = data["user"]["name"]
            u.followersCount = data["user"]["followers_count"]
            u.friendsCount = data["user"]["friends_count"]
            u.retweetCount = data["retweet_count"]
            u.isGeoEnabled = data["user"]['geo_enabled']
            u.language = data["user"]['lang']
            u.save()
            t=Tweet()
            coord=data["place"]["bounding_box"]['coordinates'][0]
            #print([[coord[0],coord[1],coord[2],coord[3],coord[0]]])
            t.geometry=[[coord[0],coord[1],coord[2],coord[3],coord[0]]]
            if data["geo"]!=None:
                t.geopoint = data["geo"]["coordinates"]
            t.placeId = data["place"]["id"]
            t.placeFullName = data["place"]["full_name"]
            t.placeName = data["place"]["name"]
            t.countryCode = data["place"]["country_code"]
            t.placeType = data["place"]["place_type"]
            t.language = data["lang"]
            t.text = data['text']
            t.createdAt = data["created_at"]
            t.favoriteCount = data["favorite_count"]
            t.retweetCount = data["retweet_count"]
            t.trends = data["entities"]["trends"]
            t.hashtags = data["entities"]["hashtags"]
            t.symbols = data["entities"]["symbols"]
            t.urls = data["entities"]["urls"]
            t.twitteruser=u
            t.save()



            """tweetlist.append(t._object_key)
            u.tweetObjIDs=tweetlist"""

            return True
        #except BaseException:
        #    print('failed ondata')
        #    time.sleep(2)

    def on_error(self, status_code, data):
        print(status_code)
        disconnect()


stream = MyStreamer(consumer_key, consumer_secret,access_token,access_token_secret)

#Biscaya
#[[[-3.4492757,42.9818774],[-3.4492757,43.4568551],[-2.4128145,43.4568551],[-2.4128145,42.9818774],[-3.4492757,42.9818774]]]
#stream.statuses.filter(locations=[-3.4492757,42.9818774,-2.4128145,43.4568551])
#All spain
box=BoundingBox()
box.lat_min=float(config["GEOLOCATION"]["SPAIN_MIN_LAT"])
box.lat_max=float(config["GEOLOCATION"]["SPAIN_MAX_LAT"])
box.lon_min=float(config["GEOLOCATION"]["SPAIN_MIN_LON"])
box.lon_max=float(config["GEOLOCATION"]["SPAIN_MAX_LON"])
stream.statuses.filter(locations=[box.lon_min, box.lat_min, box.lon_max, box.lat_max])
stream.statuses.filter(replies=all)
#Enable Count in IBM server
#stream.statuses.filter(count=50000)


"""
Rest API
from twython import Twython
twitter = Twython()

api_url = 'https://api.twitter.com/1.1/search/tweets.json'
constructed_url = twitter.construct_api_url(api_url, q='python',
result_type='popular')
print constructed_url
https://api.twitter.com/1.1/search/tweets.json?q=python&result_type=popular
"""


#twitter = Twython(consumer_key, consumer_secret,access_token,access_token_secret, oauth_version=2)
#print(twitter.get_home_timeline())

