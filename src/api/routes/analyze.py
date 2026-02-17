from fastapi import APIRouter, HTTPException
from src.schemas.requests import AnalyzeRequest
from src.schemas.responses import AnalysisResponse
from src.services.youtube import YouTubeService
from src.services.analyzer import AnalyzerService
from src.utils.validators import get_videoId

router = APIRouter()

youtube_service = YouTubeService()
analyzer_service = AnalyzerService()

@router.post("/analyze")
def analyze_url(request: AnalyzeRequest):
    """
    Analyze Sentiment of YouTube video comments
    """
    # Step 1: Extract video ID
    video_id = get_videoId(request.video_url)
    if not video_id:
        raise HTTPException(
            status_code=400, 
            detail="Invalid YouTube URL"
        )
    
    # Step 2: Fetch Comments
    try:
        comments_data = youtube_service.get_comments(
            video_id, 
            request.max_comments
        )
    except ValueError as e:
        # Handle validation errors (video not found, etc.)
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        print(f"YouTube API Error: {e}")
        raise HTTPException(status_code=503, detail=f"YouTube API error: {str(e)}")
    
    # Step 3: Analyze Comments
    try:
        result = analyzer_service.analyze_comments(
            video_id=video_id,
            comments=comments_data["comments"]
        )
    except Exception as e:
        print(f"Analysis Error: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

    # Step 4: Return Response
    try:
        return AnalysisResponse(**result)
    except Exception as e:
        print(f"Schema Validation Error: {e}")
        print(f"Result was: {result}")
        raise HTTPException(status_code=500, detail=f"Response error: {str(e)}")