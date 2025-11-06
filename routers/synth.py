# routers/synth.py
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from services.synth_service import stream_synthetic_csv, ensure_model_loaded

router = APIRouter(prefix="/synth", tags=["Synthesis"])

@router.get("/generate")
def generate_csv(
    project_id: str,
    user_id: str,
    chat_id: str,  # include chat_id so filename uses it
    rows: int = Query(..., ge=1, le=1_000_000),
    batch_size: int = Query(2000, ge=100, le=100_000),
):
    try:
        # FAIL FAST here (no 200 until we know the model is loaded)
        ensure_model_loaded()

        generator = stream_synthetic_csv(project_id, user_id, rows, batch_size)
        filename = f"{chat_id}.csv"
        headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
        return StreamingResponse(generator, media_type="text/csv", headers=headers)

    except PermissionError:
        raise HTTPException(status_code=403, detail="Unauthorized")
    except FileNotFoundError as e:
        # clean 500 before streaming
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate CSV: {e}")
