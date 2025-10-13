from fastapi import APIRouter, UploadFile, File
from typing import List

router = APIRouter(tags=["uploads"])

@router.post("/upload")
async def upload_files(
    files: List[UploadFile] = File(...)
):
    # TODO: Implement file upload and processing
    return {
        "status": "ok",
        "files_received": [f.filename for f in files]
    }
