from pathlib import Path
from uuid import UUID

from fastapi import APIRouter
from fastapi.responses import FileResponse

router = APIRouter()

OUTPUT_DIR = Path("outputs")


@router.get("/{visualization_id}")
async def get_visualization(visualization_id: str):

    try:
        UUID(visualization_id)
    except ValueError:
        return {
            "status_code": 400,
            "message": "Invalid visualization ID",
            "data": None,
        }

    file_path = OUTPUT_DIR / f"{visualization_id}.png"

    if not file_path.exists():
        return {
            "status_code": 404,
            "message": "Visualization not found",
            "data": None,
        }

    return FileResponse(
        path=file_path,
        media_type="image/png",
    )