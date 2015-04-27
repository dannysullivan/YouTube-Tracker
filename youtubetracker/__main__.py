from models import VideoFetcher
from models import Base
from database import engine, Session

def main():
    Base.metadata.create_all(engine)
    session = Session()
    video_fetcher = VideoFetcher('a', 10)
    video_fetcher.get_new_views_for_existing_videos(session)
    video_fetcher.get_new_videos(session)
    session.commit()

if __name__=="__main__":
    main()
