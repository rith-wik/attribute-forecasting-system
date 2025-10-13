# Data Upload Feature Documentation

## Overview

The Attribute Forecasting System now supports dynamic dataset uploads through a web interface, with Azure Blob Storage integration for scalable data management.

## Features

### 1. Web-Based Upload Interface
- Drag-and-drop file upload
- Support for CSV and XLSX formats
- Real-time upload progress
- Detailed upload statistics
- Visual feedback for success/errors

### 2. Automatic Dataset Detection
Files are automatically categorized based on filename:
- **Products**: Files containing "product"
- **Sales**: Files containing "sales"
- **Inventory**: Files containing "inventory" or "stock"

Alternatively, you can specify the dataset type explicitly via API.

### 3. Duplicate Detection & Merging
The system intelligently handles incremental data uploads:

**Primary Keys:**
- **Products**: `sku`
- **Sales**: `date` + `store_id` + `sku`
- **Inventory**: `date` + `store_id` + `sku`

**Merge Logic:**
- New records are added
- Existing records are updated with new values
- No duplicates are created
- Statistics show: rows added, updated, and skipped

### 4. Schema Validation
Before processing, files are validated against expected schemas:

**Products Schema:**
- Required: `sku`, `style_code`, `style_desc`, `color_name`, `size`, `category`, `price`
- Optional: `color_hex`, `image_path`

**Sales Schema:**
- Required: `date`, `store_id`, `channel`, `sku`, `units_sold`, `price`
- Optional: `promo_flag`

**Inventory Schema:**
- Required: `date`, `store_id`, `sku`, `on_hand`
- Optional: `on_order`, `lead_time_days`

### 5. Dual Storage Support
The system supports both local and Azure storage:

**Local Mode** (Development):
```bash
STORAGE_MODE=local
```
Files stored in `./data/seed` directory

**Azure Mode** (Production):
```bash
STORAGE_MODE=azure
AZURE_STORAGE_CONNECTION_STRING=your-connection-string
AZURE_STORAGE_CONTAINER_NAME=datasets
```
Files stored in Azure Blob Storage

### 6. Dataset Management
- List all uploaded datasets
- Preview datasets (first N rows)
- Delete datasets
- View metadata (size, last modified)

## API Endpoints

### Upload Dataset
```http
POST /api/v1/upload
Content-Type: multipart/form-data

Parameters:
- file: File (CSV or XLSX)
- dataset_type (optional): products, sales, or inventory

Response:
{
  "success": true,
  "message": "Successfully processed products dataset",
  "dataset_type": "products",
  "original_filename": "products_2024.csv",
  "file_size_mb": 2.5,
  "statistics": {
    "total_new_rows": 100,
    "rows_added": 80,
    "rows_updated": 20,
    "rows_skipped": 0
  },
  "total_rows": 500,
  "columns": ["sku", "style_code", ...]
}
```

### List Datasets
```http
GET /api/v1/datasets

Response:
{
  "success": true,
  "datasets": [
    {
      "dataset_type": "products",
      "filename": "products.csv",
      "size": 2621440,
      "size_mb": 2.5,
      "last_modified": "2024-01-15T10:30:00",
      "metadata": {}
    }
  ],
  "count": 1
}
```

### Preview Dataset
```http
GET /api/v1/datasets/{dataset_type}/preview?limit=10

Response:
{
  "success": true,
  "dataset_type": "products",
  "total_rows": 500,
  "preview_rows": 10,
  "columns": ["sku", "style_code", ...],
  "data": [
    {"sku": "A001", "price": 19.99, ...},
    ...
  ]
}
```

### Delete Dataset
```http
DELETE /api/v1/datasets/{dataset_type}

Response:
{
  "success": true,
  "message": "Dataset products deleted successfully"
}
```

## Frontend Usage

### Accessing Data Management
Navigate to the **Data Management** page from the navigation menu.

### Uploading a File
1. Click the upload area or drag a file
2. Select a CSV or XLSX file
3. Wait for processing (shows spinner)
4. Review upload statistics

### Managing Datasets
- **Preview**: Click "Preview" to see first 10 rows
- **Delete**: Click "Delete" to remove a dataset
- **Refresh**: Click "Refresh" to update the list

## Configuration

### Backend Configuration
Edit `backend/app/config.py` or set environment variables:

```python
STORAGE_MODE = "local"  # or "azure"
AZURE_STORAGE_CONNECTION_STRING = "..."
AZURE_STORAGE_CONTAINER_NAME = "datasets"
MAX_UPLOAD_SIZE_MB = 50
ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx"]
```

### Environment Variables
```bash
# Storage
STORAGE_MODE=azure
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
AZURE_STORAGE_CONTAINER_NAME=datasets

# Upload limits
MAX_UPLOAD_SIZE_MB=50
```

## Example Upload Scenarios

### Scenario 1: Initial Products Upload
```csv
sku,style_code,style_desc,color_name,size,category,price
A1001,ST-001,Slim Tee,Black,M,Tops,19.99
A1002,ST-001,Slim Tee,Black,L,Tops,19.99
```

**Result**: 2 rows added

### Scenario 2: Update Product Prices
```csv
sku,style_code,style_desc,color_name,size,category,price
A1001,ST-001,Slim Tee,Black,M,Tops,22.99
```

**Result**: 1 row updated (price changed from 19.99 to 22.99)

### Scenario 3: Add New Products
```csv
sku,style_code,style_desc,color_name,size,category,price
A1003,ST-002,Wide Tee,White,M,Tops,24.99
```

**Result**: 1 row added (existing products unchanged)

### Scenario 4: Incremental Sales Data
```csv
date,store_id,channel,sku,units_sold,price
2024-01-15,DXB01,store,A1001,5,19.99
2024-01-15,DXB02,store,A1001,3,19.99
```

**Result**: 2 rows added (no duplicates with previous dates)

## Error Handling

### Common Errors

**Invalid File Type**
```json
{
  "detail": "Invalid file type. Allowed types: .csv, .xlsx"
}
```

**File Too Large**
```json
{
  "detail": "File too large. Maximum size: 50MB"
}
```

**Schema Validation Failed**
```json
{
  "detail": "Schema validation failed: Missing required columns: sku, price"
}
```

**Ambiguous Filename**
```json
{
  "detail": "Cannot determine dataset type. Please specify or include 'product', 'sales', or 'inventory' in filename"
}
```

## Testing

Run the test suite:
```bash
cd backend
pytest tests/test_upload.py -v
```

Test coverage includes:
- File type detection
- CSV/XLSX parsing
- Schema validation
- Duplicate detection
- Merge logic
- API endpoints

## Performance Considerations

### File Size Limits
- Default maximum: 50MB
- Configurable via `MAX_UPLOAD_SIZE_MB`
- Larger files may require timeout adjustments

### Processing Time
- CSV files: ~100,000 rows per second
- XLSX files: ~50,000 rows per second
- Duplicate detection: O(n) complexity

### Storage Costs
Azure Blob Storage:
- Storage: ~$0.02/GB/month (LRS)
- Operations: Minimal for typical usage
- Estimated: <$5/month for most use cases

## Security

### File Validation
- Extension whitelist (`.csv`, `.xlsx` only)
- Size limits enforced
- Schema validation required
- No code execution from uploaded files

### Azure Storage Security
- Connection strings stored as secrets
- Managed Identity support (recommended)
- CORS configuration for browser access
- Firewall rules available

### Best Practices
1. Use Managed Identity in production
2. Rotate storage keys regularly
3. Enable soft delete for recovery
4. Monitor access logs
5. Set up alerts for unusual activity

## Troubleshooting

### Upload Fails Silently
- Check browser console for errors
- Verify API endpoint is accessible
- Check file size is within limits

### "Storage not configured" Error
- Verify environment variables are set
- Check connection string format
- Ensure container exists in Azure

### Duplicate Detection Not Working
- Verify primary key columns exist in data
- Check column names match exactly
- Review merge statistics in response

### Preview Shows Wrong Data
- Refresh the datasets list
- Check correct dataset type
- Verify file was uploaded successfully

## Future Enhancements

Potential improvements:
- Bulk upload (multiple files at once)
- Data transformation rules
- Scheduled uploads from external sources
- Data quality reports
- Version history for datasets
- Export functionality
- Real-time upload progress
- Background processing for large files

## Additional Resources

- [Azure Storage Setup Guide](AZURE_STORAGE_SETUP.md)
- [API Documentation](http://localhost:8000/docs)
- [Azure Blob Storage Docs](https://docs.microsoft.com/en-us/azure/storage/blobs/)
