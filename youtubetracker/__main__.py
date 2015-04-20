from models import VideoFetcher
from models import session

def main():
    video_fetcher = VideoFetcher('a', 10)
    video_fetcher.get_new_views_for_existing_videos()
    video_fetcher.get_new_videos()
    session.commit()

if __name__=="__main__":
    main()
