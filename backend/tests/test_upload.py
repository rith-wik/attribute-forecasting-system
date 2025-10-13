"""Tests for data upload and processing functionality"""
import pytest
from io import BytesIO
import pandas as pd
from fastapi.testclient import TestClient

from app.main import app
from app.services.data_processor import DataProcessor, get_data_processor
from app.storage.storage_service import StorageService


class TestDataProcessor:
    """Test data processing functionality"""

    def setup_method(self):
        self.processor = get_data_processor()

    def test_detect_file_type_products(self):
        """Test file type detection for products"""
        assert self.processor.detect_file_type("products.csv") == "products"
        assert self.processor.detect_file_type("PRODUCTS_2024.xlsx") == "products"
        assert self.processor.detect_file_type("product_catalog.csv") == "products"

    def test_detect_file_type_sales(self):
        """Test file type detection for sales"""
        assert self.processor.detect_file_type("sales.csv") == "sales"
        assert self.processor.detect_file_type("SALES_DATA.xlsx") == "sales"
        assert self.processor.detect_file_type("daily_sales.csv") == "sales"

    def test_detect_file_type_inventory(self):
        """Test file type detection for inventory"""
        assert self.processor.detect_file_type("inventory.csv") == "inventory"
        assert self.processor.detect_file_type("STOCK_LEVELS.xlsx") == "inventory"
        assert self.processor.detect_file_type("warehouse_inventory.csv") == "inventory"

    def test_detect_file_type_unknown(self):
        """Test file type detection for unknown files"""
        assert self.processor.detect_file_type("unknown.csv") is None
        assert self.processor.detect_file_type("random_data.xlsx") is None

    def test_read_csv_file(self):
        """Test reading CSV file"""
        csv_data = "sku,price\nA001,19.99\nA002,29.99"
        file_data = BytesIO(csv_data.encode('utf-8'))

        df = self.processor.read_file(file_data, "test.csv")

        assert len(df) == 2
        assert list(df.columns) == ["sku", "price"]
        assert df.iloc[0]["sku"] == "A001"

    def test_validate_schema_products_valid(self):
        """Test schema validation for valid products data"""
        df = pd.DataFrame({
            "sku": ["A001"],
            "style_code": ["ST-001"],
            "style_desc": ["Slim Tee"],
            "color_name": ["Black"],
            "size": ["M"],
            "category": ["Tops"],
            "price": [19.99]
        })

        is_valid, errors = self.processor.validate_schema(df, "products")
        assert is_valid
        assert len(errors) == 0

    def test_validate_schema_products_missing_columns(self):
        """Test schema validation with missing columns"""
        df = pd.DataFrame({
            "sku": ["A001"],
            "price": [19.99]
        })

        is_valid, errors = self.processor.validate_schema(df, "products")
        assert not is_valid
        assert any("Missing required columns" in error for error in errors)

    def test_validate_schema_products_duplicate_skus(self):
        """Test schema validation with duplicate SKUs"""
        df = pd.DataFrame({
            "sku": ["A001", "A001"],
            "style_code": ["ST-001", "ST-001"],
            "style_desc": ["Slim Tee", "Slim Tee"],
            "color_name": ["Black", "Black"],
            "size": ["M", "L"],
            "category": ["Tops", "Tops"],
            "price": [19.99, 19.99]
        })

        is_valid, errors = self.processor.validate_schema(df, "products")
        assert not is_valid
        assert any("duplicates" in error for error in errors)

    def test_validate_schema_sales_valid(self):
        """Test schema validation for valid sales data"""
        df = pd.DataFrame({
            "date": ["2024-01-01"],
            "store_id": ["DXB01"],
            "channel": ["store"],
            "sku": ["A001"],
            "units_sold": [5],
            "price": [19.99]
        })

        is_valid, errors = self.processor.validate_schema(df, "sales")
        assert is_valid
        assert len(errors) == 0

    def test_merge_data_products_new_records(self):
        """Test merging new product records"""
        existing_df = pd.DataFrame({
            "sku": ["A001"],
            "style_code": ["ST-001"],
            "style_desc": ["Slim Tee"],
            "color_name": ["Black"],
            "size": ["M"],
            "category": ["Tops"],
            "price": [19.99]
        })

        new_df = pd.DataFrame({
            "sku": ["A002"],
            "style_code": ["ST-002"],
            "style_desc": ["Wide Tee"],
            "color_name": ["White"],
            "size": ["L"],
            "category": ["Tops"],
            "price": [24.99]
        })

        merged_df, stats = self.processor.merge_data(existing_df, new_df, "products")

        assert len(merged_df) == 2
        assert stats["rows_added"] == 1
        assert stats["rows_updated"] == 0

    def test_merge_data_products_update_records(self):
        """Test updating existing product records"""
        existing_df = pd.DataFrame({
            "sku": ["A001"],
            "style_code": ["ST-001"],
            "style_desc": ["Slim Tee"],
            "color_name": ["Black"],
            "size": ["M"],
            "category": ["Tops"],
            "price": [19.99]
        })

        new_df = pd.DataFrame({
            "sku": ["A001"],
            "style_code": ["ST-001"],
            "style_desc": ["Slim Tee Updated"],
            "color_name": ["Black"],
            "size": ["M"],
            "category": ["Tops"],
            "price": [22.99]
        })

        merged_df, stats = self.processor.merge_data(existing_df, new_df, "products")

        assert len(merged_df) == 1
        assert stats["rows_added"] == 0
        assert stats["rows_updated"] == 1
        assert merged_df.iloc[0]["price"] == 22.99
        assert merged_df.iloc[0]["style_desc"] == "Slim Tee Updated"

    def test_merge_data_sales_incremental(self):
        """Test incremental sales data merge"""
        existing_df = pd.DataFrame({
            "date": ["2024-01-01", "2024-01-02"],
            "store_id": ["DXB01", "DXB01"],
            "channel": ["store", "store"],
            "sku": ["A001", "A001"],
            "units_sold": [5, 3],
            "price": [19.99, 19.99]
        })

        new_df = pd.DataFrame({
            "date": ["2024-01-03"],
            "store_id": ["DXB01"],
            "channel": ["store"],
            "sku": ["A001"],
            "units_sold": [7],
            "price": [19.99]
        })

        merged_df, stats = self.processor.merge_data(existing_df, new_df, "sales")

        assert len(merged_df) == 3
        assert stats["rows_added"] == 1
        assert stats["rows_updated"] == 0

    def test_merge_data_empty_existing(self):
        """Test merge with empty existing data"""
        existing_df = pd.DataFrame()

        new_df = pd.DataFrame({
            "sku": ["A001"],
            "style_code": ["ST-001"],
            "style_desc": ["Slim Tee"],
            "color_name": ["Black"],
            "size": ["M"],
            "category": ["Tops"],
            "price": [19.99]
        })

        merged_df, stats = self.processor.merge_data(existing_df, new_df, "products")

        assert len(merged_df) == 1
        assert stats["rows_added"] == 1
        assert stats["rows_updated"] == 0

    def test_dataframe_to_csv_bytes(self):
        """Test DataFrame to CSV bytes conversion"""
        df = pd.DataFrame({
            "sku": ["A001", "A002"],
            "price": [19.99, 29.99]
        })

        csv_bytes = self.processor.dataframe_to_csv_bytes(df)

        assert isinstance(csv_bytes, bytes)
        assert b"sku,price" in csv_bytes
        assert b"A001" in csv_bytes

    def test_dataframe_from_csv_bytes(self):
        """Test loading DataFrame from CSV bytes"""
        csv_data = b"sku,price\nA001,19.99\nA002,29.99"

        df = self.processor.dataframe_from_csv_bytes(csv_data)

        assert len(df) == 2
        assert list(df.columns) == ["sku", "price"]


class TestUploadAPI:
    """Test upload API endpoints"""

    def setup_method(self):
        self.client = TestClient(app)

    def test_upload_endpoint_invalid_file_type(self):
        """Test upload with invalid file type"""
        files = {"file": ("test.txt", b"some content", "text/plain")}
        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400
        assert "Invalid file type" in response.json()["detail"]

    def test_upload_endpoint_invalid_filename(self):
        """Test upload with ambiguous filename"""
        csv_data = "sku,price\nA001,19.99"
        files = {"file": ("random.csv", csv_data.encode(), "text/csv")}

        response = self.client.post("/api/v1/upload", files=files)

        assert response.status_code == 400
        assert "Cannot determine dataset type" in response.json()["detail"]

    def test_list_datasets_endpoint(self):
        """Test list datasets endpoint"""
        response = self.client.get("/api/v1/datasets")

        assert response.status_code == 200
        data = response.json()
        assert "datasets" in data
        assert "count" in data
        assert isinstance(data["datasets"], list)

    def test_preview_dataset_not_found(self):
        """Test preview for non-existent dataset"""
        response = self.client.get("/api/v1/datasets/nonexistent/preview")

        assert response.status_code == 404

    def test_delete_dataset_not_found(self):
        """Test delete for non-existent dataset"""
        response = self.client.delete("/api/v1/datasets/nonexistent")

        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
