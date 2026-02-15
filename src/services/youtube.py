import googleapiclient.discovery as discovery
import googleapiclient.errors as errors
from src.utils.validators import get_videoId
import pandas as pd
from src.core.config import get_settings


class YouTubeService:
    def __init__(self):
        """Initialize YouTube API client"""
        settings = get_settings()
        self.youtube_client = discovery.build(
            settings.API_SERVICE_NAME,
            settings.API_VERSION,
            developerKey=settings.YOUTUBE_API_KEY
        )

    def get_comments(self, video_id: str, max_results: int) -> dict:
        try:
            request = self.youtube_client.commentThreads().list(
                part="snippet",
                videoId=video_id,
                maxResults=max_results
            )
            response = request.execute()

            comments = []
            for item in response["items"]:
                comment = item["snippet"]["topLevelComment"]["snippet"]
                comments.append([
                    comment["authorDisplayName"],
                    comment["publishedAt"],
                    comment["updatedAt"],
                    comment["likeCount"],
                    comment["textDisplay"]
                ])

            # return pd.DataFrame(
            #     comments, 
            #     columns=["author", "published_at", "updated_at", "like_count", "text"]
            # )
            return {
                "video_id": video_id,
                "comments": comments,
                "total": len(comments)
            }
        
        except errors.HttpError as e:
            if e.resp.status == 404:
                raise ValueError(f"Video not found: {video_id}")
            elif e.resp.status == 403:
                raise ValueError("API quota exceeded or comments disabled")
            else:
                raise Exception(f"YouTube API error: {str(e)}")