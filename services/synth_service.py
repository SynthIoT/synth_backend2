# services/synth_service.py
import os, io, math, pickle, threading
from typing import Iterator, Optional
import pandas as pd
from utils.firebase import db
from dotenv import load_dotenv

load_dotenv()

CTGAN_MODEL_PATH = os.getenv("CTGAN_MODEL_PATH") 

_MODEL = None
_MODEL_LOCK = threading.Lock()

def get_model_path() -> str:
    return os.getenv("CTGAN_MODEL_PATH") or ""

def _load_model() -> None:
    global _MODEL
    if _MODEL is not None:
        return
    path = get_model_path()
    if not path or not os.path.exists(path):
        raise FileNotFoundError("CTGAN model not found. Set CTGAN_MODEL_PATH.")
    with open(path, "rb") as f:
        from services.pickle_compat import load_old_pickle
        _MODEL = load_old_pickle(CTGAN_MODEL_PATH)  

def ensure_model_loaded() -> None:
    # Call this from routers to fail fast (before streaming)
    with _MODEL_LOCK:
        _load_model()

def _project_belongs_to_user(project_id: str, user_id: str) -> bool:
    proj = db.collection("projects").document(project_id).get()
    return bool(proj.exists and proj.to_dict().get("user_id") == user_id)

def _df_to_csv_chunk(df: pd.DataFrame, header: bool) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False, header=header)
    return buf.getvalue().encode("utf-8")

def stream_synthetic_csv(project_id: str, user_id: str, rows: int, batch_size: int = 2000) -> Iterator[bytes]:
    if rows <= 0:
        raise ValueError("rows must be > 0")
    if not _project_belongs_to_user(project_id, user_id):
        raise PermissionError("Unauthorized")

    # At this point we assume ensure_model_loaded() already succeeded.
    model = _MODEL  # safe to read without lock after ensure

    batches = math.ceil(rows / batch_size)
    wrote_header = False
    for i in range(batches):
        n = batch_size if (i < batches - 1) else (rows - batch_size * (batches - 1))
        df = model.sample(n)
        yield _df_to_csv_chunk(df, header=(not wrote_header))
        wrote_header = True
