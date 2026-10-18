from fastapi import APIRouter, HTTPException

from app.core.config import settings
from app.db.supabase import supabase_client

router = APIRouter()


@router.get("/")
async def health_check():
    """
    Liveness probe. Used by the compose healthcheck, the production smoke test
    (.github/workflows/production-smoke.yml) and the deploy scripts.

    `version` is the git SHA baked into the image at build time (Dockerfile
    ARG GIT_SHA → APP_VERSION). The smoke test compares it with `main` to warn
    when a merge has not been pulled onto the VPS yet.
    """
    return {
        "status": "ok",
        "message": "API is running",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }


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
