import unittest
from datetime import date
from models import Video, VideoDate, VideoFetcher, Base
from sqlalchemy.engine import create_engine
from sqlalchemy.orm.session import Session

# Database Setup
def setup_module():
    global transaction, connection, engine
    engine = create_engine('sqlite:///:memory:', echo=True)
    connection = engine.connect()
    transaction = connection.begin()
    Base.metadata.create_all(connection)

def teardown_module():
    transaction.rollback()
    connection.close()
    engine.dispose()

class DatabaseTest(object):
    def setUp(self):
        self.session = Session(connection)

    def tearDown(self):
        self.session.close()

# Model Tests
class TestVideoMethods(DatabaseTest, unittest.TestCase):
    def setUp(self):
        super(TestVideoMethods, self).setUp()
        self.existing_video = Video(youtube_id = "testvideo")
        self.session.add(self.existing_video)
        self.session.commit()

    def test_find_or_create(self):
        duplicate_video = Video(youtube_id = "testvideo").find_or_create(self.session)
        new_video = Video(youtube_id = "othertestvideo").find_or_create(self.session)
        self.assertEqual(duplicate_video.id, self.existing_video.id)
        self.assertIsNotNone(new_video.id)
        self.assertNotEqual(new_video.id, self.existing_video.id)

class TestVideoDateMethods(DatabaseTest, unittest.TestCase):
    def setUp(self):
        super(TestVideoDateMethods, self).setUp()
        self.first_video_date = VideoDate(video_id = 1, view_count = 1, date = date(2015, 4, 18))
        self.second_video_date = VideoDate(video_id = 1, view_count = 3, date = date(2015, 4, 19))
        self.session.add_all([self.first_video_date, self.second_video_date])
        self.session.add(VideoDate(video_id = 2, view_count = 2, date = date(2015, 4, 18)))
        self.session.add(VideoDate(video_id = 1, view_count = 2, date = date(2015, 4, 17)))
        self.session.commit()

    def test_previous_video_date(self):
        previous_video_date = self.second_video_date.previous_video_date(self.session)
        self.assertEqual(previous_video_date.view_count, 1)
        self.assertEqual(previous_video_date.date, date(2015, 4, 18))

    def test_change_in_last_day(self):
        self.assertEqual(self.second_video_date.change_in_last_day(self.session), 2)

class TestVideoFetcherMethods(unittest.TestCase):
    def test_youtube_api_request_url(self):
        video_fetcher = VideoFetcher("someSearchTerm", 10)
        request_url = video_fetcher.youtube_api_request_url()
        self.assertIn("someSearchTerm", request_url)
        self.assertIn("max-results=10", request_url)

if __name__ == '__main__':
    setup_module()
    unittest.main()
    teardown_module()
