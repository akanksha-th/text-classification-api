def get_videoId(video_url: str) -> str:
    try :
        validId = video_url.split("/")[-1].strip()
        validId = validId.removeprefix("watch?v=").split("?")[0].split('&')[0]
        
        # assert validId.isalnum() == True      # Video IDs aren't always alphanumeric. YouTube IDs can have - and _ characters 
        assert len(validId) == 11
        return validId
    
    except Exception as e:
        return None
