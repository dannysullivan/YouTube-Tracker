import sys
import psycopg2
import sqlalchemy
import untangle
from datetime import date, timedelta
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Sequence
from sqlalchemy import ForeignKey
import gdata.youtube
import gdata.youtube.service

engine = create_engine('sqlite:///:memory:', echo=True)
Base = declarative_base()
Session = sessionmaker(bind=engine)
session = Session()

# def main():
    # connect_to_database()
  
# def connect_to_database():
    # #Define our connection string
    # conn_string = "host='localhost' dbname='my_database'"

    # # print the connection string we will use to connect
    # print "Connecting to database\n	->%s" % (conn_string)

    # # get a connection, if a connect cannot be made an exception will be raised here
    # conn = psycopg2.connect(conn_string)

    # # conn.cursor will return a cursor object, you can use this cursor to perform queries
    # cursor = conn.cursor()
    # print "Connected!\n"

#models
class Video(Base):
    __tablename__ = 'videos'
    
    id = Column(Integer, Sequence('video_id_seq'), primary_key = 'true')
    title = Column(String)
    url = Column(String)
    search_term = Column(String)

    def find_or_create(self, session):
        existing_video = session.query(Video).filter_by(url = self.url).first()
        if existing_video is not None:
            return existing_video
        else:
            session.add(self)
            return self

class VideoDate(Base):
    __tablename__ = 'video_dates'
    
    id = Column(Integer, Sequence('video_date_id_seq'), primary_key = 'true')
    date = Column(Date)
    video_id = Column(Integer, ForeignKey('videos.id'))
    view_count = Column(Integer)

    def previous_video_date(self, session):
        previous_date = self.date - timedelta(days = 1)
        return session.query(VideoDate).filter_by(video_id = self.video_id, date = previous_date).first()

    def change_in_last_day(self, session):
        """
        Returns the difference between today's and yesterday's view counts for the same video
        """
        return self.view_count - self.previous_video_date(session).view_count

class VideoFetcher(object):
    def __init__(self, search_term):
        self.client = gdata.youtube.service.YouTubeService()
        self.yt_service = gdata.youtube.service.YouTubeService()

        self.search_term = search_term
        self.date = date.today

    def get_new_videos(self):
        """
        Uses the YouTube API to get a video feeds containing up to 50 videos uploaded
        today
        """
        feed = self.client.GetYouTubeVideoFeed(self.youtube_api_request_url())
        for entry in feed.entry:
            video = Video(title = entry.media.title.text, url = entry.GetSwfUrl()).find_or_create(session)
            # video_date = VideoDate(video_id = video.id, date = self.date, view_count = entry.statistics.view_count)
            # session.add(video_date)

    def youtube_api_request_url(self):
        url_string = ("http://gdata.youtube.com/feeds/api/videos?v=2&q="
        + self.search_term + "&start-index=1&max-results=50&time=today&strict=true")
        return url_string
            

# Set up schema
Base.metadata.create_all(engine) 

def main():
    video_fetcher = VideoFetcher('someSearch')
    video_fetcher.get_new_videos()

if __name__=="__main__":
    main()
