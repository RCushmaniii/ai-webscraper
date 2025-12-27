from fastapi import APIRouter, HTTPException

from app.db.supabase import supabase_client

router = APIRouter()


@router.get("/")
async def health_check():
    return {"status": "ok", "message": "API is running"}


@router.get("/supabase")
async def supabase_health_check():
    try:
        response = supabase_client.table("users").select("id").limit(1).execute()

        if hasattr(response, "error") and response.error is not None:
            error_text = str(response.error)
            if "does not exist" in error_text or "relation" in error_text:
                return {"status": "ok", "supabase": "reachable", "schema": "missing_or_uninitialized"}
            raise HTTPException(status_code=500, detail="Supabase query failed")

        return {"status": "ok", "supabase": "reachable"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail="Supabase connectivity check failed")
