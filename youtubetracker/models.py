import sys
import psycopg2
import sqlalchemy
import untangle
from datetime import date, timedelta
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy import Sequence
from sqlalchemy import ForeignKey
import gdata.youtube
import gdata.youtube.service

Base = declarative_base()

#models
class Video(Base):
    """
    Represents a unique YouTube video
    """
    __tablename__ = 'videos'
    
    id = Column(Integer, Sequence('video_id_seq'), primary_key = 'true')
    youtube_id = Column(String)
    search_term = Column(String)

    def find_or_create(self, session):
        """
        Returns a new, persisted Video record if the video has not yet been entered
        into the database; otherwise, returns the record of the video in the database
        """
        existing_video = session.query(Video).filter_by(youtube_id = self.youtube_id).first()
        if existing_video is not None:
            return existing_video
        else:
            session.add(self)
            session.flush()
            return self

class VideoDate(Base):
    """
    Represents a snapchat of a YouTube video's attributes (such as view count) on a
    specific date
    """
    __tablename__ = 'video_dates'
    
    id = Column(Integer, Sequence('video_date_id_seq'), primary_key = 'true')
    date = Column(Date)
    video_id = Column(Integer, ForeignKey('videos.id'))
    view_count = Column(Integer)

    def previous_video_date(self, session):
        """
        Returns the previous date's VideoDate record
        """
        previous_date = self.date - timedelta(days = 1)
        return session.query(VideoDate).filter_by(video_id = self.video_id, date = previous_date).first()

    def change_in_last_day(self, session):
        """
        Returns the difference between today's and yesterday's view counts for the same video
        """
        previous_video_date = self.previous_video_date(session)
        if previous_video_date is not None:
            return self.view_count - previous_video_date.view_count

class VideoFetcher(object):
    """
    Provides methods related to fetching new videos and new view counts for existing videos
    via the YouTube API
    """

    def __init__(self, search_term, max_results):
        """
        Initializes YouTube API service and client
        """
        self.client = gdata.youtube.service.YouTubeService()
        self.yt_service = gdata.youtube.service.YouTubeService()

        self.search_term = search_term
        self.date = date.today()
        self.max_results = max_results

    def get_new_videos(self, session):
        """
        Uses the YouTube API to get a video feeds containing up to 50 videos uploaded
        today
        """
        feed = self.client.GetYouTubeVideoFeed(self.youtube_api_request_url())
        for entry in feed.entry:
            id = entry.GetSwfUrl()[26:37]
            video = Video(youtube_id = id, search_term = self.search_term).find_or_create(session)
            video_date = VideoDate(video_id = video.id, date = self.date, view_count = entry.statistics.view_count)
            session.add(video_date)

    def get_new_views_for_existing_videos(self, session):
        """
        Creates a new video_date record for videos that are already in the database
        """
        for existing_video in session.query(Video).filter_by(search_term = self.search_term):
            entry = self.yt_service.GetYouTubeVideoEntry(video_id=existing_video.youtube_id)
            video_date = VideoDate(video_id = existing_video.id, date = self.date, view_count = entry.statistics.view_count)
            session.add(video_date)

    def youtube_api_request_url(self):
        """
        Returns the url string for the YouTube API request
        """
        url_string = ("http://gdata.youtube.com/feeds/api/videos?v=2&q="
        + self.search_term + "&start-index=1&max-results=" + str(self.max_results) + "&time=today&strict=true")
        return url_string
