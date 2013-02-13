import sys
import gdata.youtube
import gdata.youtube.service
import csv
import datetime
import urllib
import json
import time
import socket
import urllib2
import pymongo
import re
import time
import HTMLParser
import httplib
from bs4 import BeautifulSoup


#Define globals used for keeping track of daily view counts
today = str(datetime.date.today())
oneday = datetime.timedelta(days=1)
yesterday = str(datetime.date.today() - oneday)

#More globals
client = gdata.youtube.service.YouTubeService()
yt_service = gdata.youtube.service.YouTubeService()

#Connect to mongo database
conn = pymongo.Connection()
db = conn.youtubedata

def main():
    """
    Manage all database operations and call youtube API operations.
    Input: the keyword to be tracked
    """
    socket.setdefaulttimeout(10)

    """
    f = open("fields.txt", "a")
    f.write(today + "\n")
    f.close()
    """
    print("Update Views")
    errors = updateViews()
    print errors
    print("Handle Errors")
    handleErrors(errors)
    """
    print("Get New Videos")
    getNewVideos()
    print("Add Top Videos")
    addTopVideos()
    updateHighlights()
    """

def updateHighlights():
    """
    
    """
    db = conn.obamadata
    for entry in db.obamahighlights.find():
        id = entry["_id"]
        dbEntry = db.obamadata.find({"_id":id})
        for attr in dbEntry:
            for key in attr:
                a = attr[key]
                db.obamahighlights.update(entry, {'$set':{key:a}})


def addTopVideosObama():
    db = conn.obamadata
    for entry in db.obamadata.find():
        # flag1 is 0 if there's viewcount data for the first date
        flag1 = 0
        flag2 = 0
        difference = 0
        try:
            views1 = int(entry[yesterday])
        except (KeyError, ValueError, TypeError):
            flag1 = 1
        try: 
            views2 = int(entry[today])
        except (KeyError, ValueError, TypeError):
            flag2 = 1

        if ((flag1 == 0) and (flag2 == 0)):
            difference = views2 - views1
            db.obamadata.update(entry, {'$set':{str(today + 'daily'):difference}})

    list = db.obamadata.find().sort(str(today + 'daily'), -1).limit(100)
    for item in list:
        
        video = YouTubeVideo(item['_id'])
        video.get_data()

        try:
            db.obamahighlights.insert({"_id":video.metadata['_id'],"uploaded":video.metadata['uploaded'],
                "description":video.metadata['description'],"title":video.metadata["title"],
                "duration":video.metadata['duration'],"uploader":video.metadata['uploader'], 
                "category":video.metadata["category"]})
            for attr in item:
                a = item[attr]
                db.obamahighlights.update({"_id":video.metadata['_id']},
                    {'$set' : {attr:a}})
        except (pymongo.errors.DuplicateKeyError, ValueError, AttributeError,
            KeyError):
            # YouTube video data is already in MongoDB, or no more entries in
            # feed.
            pass


            
def getNewVideos():
    """
    Uses the YouTube API to get video feeds containing up 1000 videos uploaded
    today and 1000 videos listed as "relevant" to the search term.
    """

    #Add videos that were added today to the database
    for search in ("time=today","orderby=relevance"):
        x = 1
        while x <= 951:
            processFeed(client.GetYouTubeVideoFeed(
                "http://gdata.youtube.com/feeds/api/videos?v=2&q="
                + keyword + "&start-index="
                + str(x) + "&max-results=50&"+search+"&strict=true"))

            x = x + 50


def processFeed(feed):
    """
    Finds the video identified by each id in the feed and adds it to the 
    backend database.
    """

    for entry in feed.entry:
        url = str(entry.GetSwfUrl())
        id = url[26:37]

        try:

            video = yt_service.GetYouTubeVideoEntry(video_id=id)

            backend.insert({'_id':id, today:video.statistics.view_count})
            print "Video id: " + id + " added to database."

        except gdata.service.RequestError:
            continue
        except (pymongo.errors.DuplicateKeyError, ValueError, AttributeError,
            KeyError):
            # YouTube video data is already in MongoDB, or no more entries in
            # feed.
            pass
        time.sleep(1)
        

def updateViews():
    """
    Adds a new viewcount to each of the videos already in the backend database.
    Returns an array containing the video ids that caused errors.
    """

    #g = open("errorlogs/errorsdefinite.txt", "a")

    errors = []
    f = open('errorlogs/errors' + today + '.txt', 'a')
    n = 0
    try:
        print "here"
        #{'down':0, today:{'$exists':False}}
        for entry in backend.find():

            n = n+1
            print n

            try:
                id = entry['_id']
                video = yt_service.GetYouTubeVideoEntry(video_id=id)
                try:
                    newViews = video.statistics.view_count
                    print newViews

                except AttributeError as e:
                    url = 'http://www.youtube.com/watch?v=' + id
                    try:
                        h = urllib2.urlopen(url)
                        s = h.read()
                        s = s.rstrip('\n')
                        h.close()

                        soup = BeautifulSoup(s)
                        span = soup('span', {'class':'watch-view-count'})
                        views = int(span[0].strong.text.replace(',',''))

                        backend.update({'_id':id}, {'$set':
                            {str(datetime.date.today()):views}})    
                        print "o" + str(views)

                    except urllib2.HTTPError:
                        print "a"
                        continue

                    except (AttributeError, IndexError, 
                        HTMLParser.HTMLParseError,
                        IOError, httplib.BadStatusLine, 
                        pymongo.errors.OperationFailure) as e:

                        f.write(id)
                        f.write("\n")
                        errors.append(id)
                        print e
                        continue

                    continue

                backend.update(entry, { "$set" : {
                    today:newViews} })


            #If the YouTube API rejects the requests because there have been 
            #too many, use urllib2 to get view information.
            except gdata.service.RequestError as e:
                print e[0]
                if e[0]['body'] == ("<?xml version='1.0' encoding='UTF-8'?>" +
                "<errors><error><domain>yt:quota</domain><code>too_many_rec" +
                "ent_calls</code></error></errors>"):


                    url = 'http://www.youtube.com/watch?v=' + id
                    try:
                        h = urllib2.urlopen(url)
                        s = h.read()
                        s = s.rstrip('\n')
                        h.close()

                        soup = BeautifulSoup(s)
                        span = soup('span', {'class':'watch-view-count'})
                        views = int(span[0].strong.text.replace(',',''))

                        backend.update({'_id':id}, {'$set':
                            {today:views}})    
                        print str(views)

                    except urllib2.HTTPError:
                        continue

                    except (AttributeError, IndexError, 
                        HTMLParser.HTMLParseError,
                        IOError, httplib.BadStatusLine,  
                        pymongo.errors.OperationFailure) as e:
                        f.write(id)
                        f.write("\n")
                        print e
                        continue

            
                else:
                    db.obamadata.update(entry, { "$set" : {
                        "down":1} })

            except (KeyError, ValueError, pymongo.errors.OperationFailure) as e:
                print e
                continue

    finally:
        return errors


        



def handleErrors(errors):
    
    n = open('errorlogs/errors' + today + '.txt', 'w')

    for line in errors:
        url = 'http://www.youtube.com/watch?v=' + line
        try:
            h = urllib2.urlopen(url)
            s = h.read()
            s = s.rstrip('\n')
            h.close()

            soup = BeautifulSoup(s)
            span = soup('span', {'class':'watch-view-count'})
            views = int(span[0].strong.text.replace(',',''))

            backend.update({'_id':line}, {'$set':
                    {today:views}})    
            print "o" + str(views)

        except urllib2.HTTPError:
            print "a"
            continue

        except (AttributeError, IndexError, HTMLParser.HTMLParseError,
            IOError, httplib.BadStatusLine,  pymongo.errors.OperationFailure) as e:
            n.write(line + "\n")
            print e
            continue

    

if __name__ == "__main__":
    
    keyword = sys.argv[1]
    backend = pymongo.collection.Collection(db, keyword + "backend")
    highlights = pymongo.collection.Collection(db, keyword + "highlights")

    main()



