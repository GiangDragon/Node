from fastapi import FastAPI, UploadFile, Form
from fastapi.responses import FileResponse
from fastapi import HTTPException
import os, time
from pathlib import Path

app = FastAPI()

STORAGE_DIR = Path("Storage/Data/Chunks")
os.makedirs(STORAGE_DIR, exist_ok=True)


def safe_filename(filename):
    name = Path(filename).name
    if not name or name in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename")
    return name


def parse_chunk_name(chunk_name):
    if "_chunk_" not in chunk_name:
        return None

    filename, chunk_index = chunk_name.rsplit("_chunk_", 1)
    try:
        chunk_index = int(chunk_index)
    except ValueError:
        return None

    if chunk_index < 1:
        return None

    try:
        filename = safe_filename(filename)
    except HTTPException:
        return None

    return {
        "filename": filename,
        "chunk_index": chunk_index,
        "chunk_name": chunk_name,
    }


@app.post("/store_chunk")
async def store_chunk(
        file : UploadFile, 
        filename: str = Form(...), 
        chunk_index: int = Form(...)) :
    filename = safe_filename(filename)
    if chunk_index < 1:
        raise HTTPException(status_code=400, detail="Invalid chunk index")

    path = os.path.join(STORAGE_DIR, f"{filename}_chunk_{chunk_index}")
    with open(path, "wb") as f:
        content = await file.read()
        f.write(content)
    return {"status": "stored", "chunk": file.filename}

@app.get("/get_chunk/{filename}/{chunk_index}")
def get_chunk(filename: str, chunk_index: int) :
    filename = safe_filename(filename)
    path = os.path.join(STORAGE_DIR, f"{filename}_chunk_{chunk_index}")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Chunk not found")
    return FileResponse(
        path, 
        media_type="application/octet-stream",
        filename=f"{filename}_chunk_{chunk_index}"
    )

@app.get("/chunks")
def list_chunks():
    chunks = []
    for path in STORAGE_DIR.iterdir():
        if not path.is_file():
            continue

        chunk = parse_chunk_name(path.name)
        if chunk is not None:
            chunks.append(chunk)

    return {"chunks": chunks}

@app.delete("/delete_chunk/{filename}/{chunk_index}")
def delete_chunk(filename : str, chunk_index : int) :
    filename = safe_filename(filename)
    path = os.path.join(STORAGE_DIR, f"{filename}_chunk_{chunk_index}")
    if os.path.exists(path):
        os.remove(path)
        return {"status": "ok"}
    raise HTTPException(status_code=404, detail="Chunk not found")


@app.get("/health")
def health():
    return {"status": "ok", "ts": time.time()}
