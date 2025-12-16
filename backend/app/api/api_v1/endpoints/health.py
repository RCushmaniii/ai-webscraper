from fastapi import APIRouter

router = APIRouter()

@router.get("/")
async def health_check():
    """
    Health check endpoint to verify API is running
    """
    return {"status": "ok", "message": "API is running"}
