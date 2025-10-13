from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from typing import List, Optional
import logging
from io import BytesIO

from app.storage.storage_service import get_storage_service
from app.services.data_processor import get_data_processor
from app.config import settings

router = APIRouter(tags=["uploads"])
logger = logging.getLogger(__name__)


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    dataset_type: Optional[str] = Query(None, description="Dataset type: products, sales, or inventory")
):
    """
    Upload a dataset file (CSV or XLSX) with duplicate detection and merging

    The file will be validated, merged with existing data, and stored.
    Duplicates are detected based on primary keys and updated accordingly.
    """
    try:
        # Validate file extension
        file_ext = file.filename.lower().split('.')[-1]
        if f".{file_ext}" not in settings.allowed_file_extensions:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid file type. Allowed types: {', '.join(settings.allowed_file_extensions)}"
            )

        # Read file content
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)

        # Validate file size
        if file_size_mb > settings.max_upload_size_mb:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.max_upload_size_mb}MB"
            )

        # Initialize services
        storage = get_storage_service()
        processor = get_data_processor()

        # Auto-detect dataset type if not provided
        detected_type = dataset_type or processor.detect_file_type(file.filename)
        if not detected_type:
            raise HTTPException(
                status_code=400,
                detail="Cannot determine dataset type. Please specify or include 'product', 'sales', or 'inventory' in filename"
            )

        # Check if existing data exists
        existing_data = None
        storage_filename = f"{detected_type}.csv"

        if storage.file_exists(storage_filename):
            try:
                existing_bytes = storage.download_file(storage_filename)
                existing_data = processor.dataframe_from_csv_bytes(existing_bytes)
                logger.info(f"Loaded existing {detected_type} data with {len(existing_data)} rows")
            except Exception as e:
                logger.warning(f"Could not load existing data: {e}")

        # Process the upload
        file_stream = BytesIO(content)
        result = processor.process_upload(
            file_data=file_stream,
            filename=file.filename,
            dataset_type=detected_type,
            existing_data=existing_data
        )

        # Convert processed DataFrame back to CSV and store
        processed_csv = processor.dataframe_to_csv_bytes(result["processed_df"])
        csv_stream = BytesIO(processed_csv)

        # Upload to storage
        upload_info = storage.upload_file(
            file_data=csv_stream,
            filename=storage_filename,
            metadata={
                "original_filename": file.filename,
                "upload_time": str(result.get("upload_time", "")),
                "total_rows": str(result["total_rows"])
            }
        )

        logger.info(f"Successfully uploaded {detected_type} dataset")

        return {
            "success": True,
            "message": f"Successfully processed {detected_type} dataset",
            "dataset_type": detected_type,
            "original_filename": file.filename,
            "stored_filename": storage_filename,
            "file_size_mb": round(file_size_mb, 2),
            "statistics": result["statistics"],
            "total_rows": result["total_rows"],
            "columns": result["columns"],
            "storage_info": {
                "size": upload_info["size"],
                "last_modified": str(upload_info["last_modified"])
            }
        }

    except ValueError as e:
        logger.error(f"Validation error during upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during file upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/datasets")
async def list_datasets():
    """
    List all uploaded datasets
    """
    try:
        storage = get_storage_service()
        files = storage.list_files()

        datasets = []
        for file_info in files:
            # Only include CSV files (our processed datasets)
            if file_info["name"].endswith(".csv"):
                dataset_type = file_info["name"].replace(".csv", "")
                datasets.append({
                    "dataset_type": dataset_type,
                    "filename": file_info["name"],
                    "size": file_info["size"],
                    "size_mb": round(file_info["size"] / (1024 * 1024), 2),
                    "last_modified": str(file_info["last_modified"]),
                    "metadata": file_info.get("metadata", {})
                })

        return {
            "success": True,
            "datasets": datasets,
            "count": len(datasets)
        }

    except Exception as e:
        logger.error(f"Error listing datasets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/datasets/{dataset_type}/preview")
async def preview_dataset(
    dataset_type: str,
    limit: int = Query(10, ge=1, le=100, description="Number of rows to preview")
):
    """
    Preview a dataset (first N rows)
    """
    try:
        storage = get_storage_service()
        processor = get_data_processor()

        filename = f"{dataset_type}.csv"

        if not storage.file_exists(filename):
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_type}")

        # Download and parse
        content = storage.download_file(filename)
        df = processor.dataframe_from_csv_bytes(content)

        # Get preview
        preview_df = df.head(limit)

        return {
            "success": True,
            "dataset_type": dataset_type,
            "total_rows": len(df),
            "preview_rows": len(preview_df),
            "columns": list(df.columns),
            "data": preview_df.to_dict(orient="records")
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/datasets/{dataset_type}")
async def delete_dataset(dataset_type: str):
    """
    Delete a dataset
    """
    try:
        storage = get_storage_service()
        filename = f"{dataset_type}.csv"

        if not storage.file_exists(filename):
            raise HTTPException(status_code=404, detail=f"Dataset not found: {dataset_type}")

        success = storage.delete_file(filename)

        if success:
            return {
                "success": True,
                "message": f"Dataset {dataset_type} deleted successfully"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete dataset")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))
