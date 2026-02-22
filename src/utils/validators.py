from urllib.parse import urlparse, parse_qs
import re

VALID_YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "youtu.be", "m.youtube.com"}
VIDEO_ID_RE = re.compile(r'^[a-zA-Z0-9_-]{11}$')

def get_videoId(video_url: str) -> str:
    if not video_url or not isinstance(video_url, str):
        return None
    
    try:
        parsed = urlparse(video_url)
    except Exception:
        return None
    
    if parsed.scheme not in ("http", "https"):
        return None
    if parsed.netloc not in VALID_YOUTUBE_HOSTS:
        return None
    
    video_id = None
    if parsed.netloc == "youtu.be":
        video_id = parsed.path.strip("/").split("/")[0]
    elif parsed.path.startswith("/shorts/"):
        video_id = parsed.path.split("/shorts/")[-1].split("/")[0]
    elif parsed.path == "/watch":
        params = parse_qs(parsed.query)
        ids = params.get("v", [])
        video_id = ids[0] if ids else None

    if video_id and VIDEO_ID_RE.match(video_id):
        return video_id

# naive --for prototype testing
def old_get_videoId(video_url: str) -> str:
    try :
        validId = video_url.split("/")[-1].strip()
        validId = validId.removeprefix("watch?v=").split("?")[0].split('&')[0]
        
        # assert validId.isalnum() == True      # Video IDs aren't always alphanumeric. YouTube IDs can have - and _ characters 
        assert len(validId) == 11
        return validId
    
    except Exception as e:
        return None
