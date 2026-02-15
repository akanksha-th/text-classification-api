from src.utils.validators import get_videoId

def test_youtube_watch_url():
    """Test standard youtube url format"""
    assert get_videoId("https://youtu.be/1yeLyV43o2o") == "1yeLyV43o2o"
    assert get_videoId("https://www.youtube.com/watch?v=52c7Kxp_14E&t=1023s") == "52c7Kxp_14E"
    assert get_videoId("https://youtu.be/1yeLyV43o2o?t=2") == "1yeLyV43o2o"
    assert get_videoId("https://www.youtube.com/watch?v=1yeLyV43o2o") == "1yeLyV43o2o"

def test_invalid_urls():
    """Test invalid/empty/None input"""
    assert get_videoId("youtube.com/watch?video=dQw4w9WgXcQ") == None
    assert get_videoId("www.youtube.com/watch?v=dQw4w9WgXcQ") == None
    assert get_videoId("https://www.youtube.com/@analyticswithadam") == None