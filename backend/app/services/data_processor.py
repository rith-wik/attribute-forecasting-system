"""Data processing service for CSV/XLSX files with duplicate detection"""
import logging
from typing import BinaryIO, Dict, List, Tuple, Optional, Literal
from io import BytesIO
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class DataProcessor:
    """Process and merge CSV/XLSX dataset files"""

    # Define schemas and primary keys for each dataset type
    SCHEMAS = {
        "products": {
            "required_columns": ["sku", "style_code", "style_desc", "color_name", "size", "category", "price"],
            "primary_key": ["sku"],
            "optional_columns": ["color_hex", "image_path"]
        },
        "sales": {
            "required_columns": ["date", "store_id", "channel", "sku", "units_sold", "price"],
            "primary_key": ["date", "store_id", "sku"],
            "optional_columns": ["promo_flag"]
        },
        "inventory": {
            "required_columns": ["date", "store_id", "sku", "on_hand"],
            "primary_key": ["date", "store_id", "sku"],
            "optional_columns": ["on_order", "lead_time_days"]
        }
    }

    def __init__(self):
        pass

    @staticmethod
    def detect_file_type(filename: str) -> Optional[str]:
        """
        Detect dataset type from filename

        Args:
            filename: Name of the file

        Returns:
            Dataset type ('products', 'sales', 'inventory') or None
        """
        filename_lower = filename.lower()

        if "product" in filename_lower:
            return "products"
        elif "sale" in filename_lower:
            return "sales"
        elif "inventory" in filename_lower or "stock" in filename_lower:
            return "inventory"

        return None

    @staticmethod
    def read_file(file_data: BinaryIO, filename: str) -> pd.DataFrame:
        """
        Read CSV or XLSX file into pandas DataFrame

        Args:
            file_data: File-like object
            filename: Name of the file (to detect format)

        Returns:
            pandas DataFrame

        Raises:
            ValueError: If file format is not supported
        """
        file_ext = filename.lower().split('.')[-1]

        try:
            if file_ext == 'csv':
                # Try different encodings
                try:
                    file_data.seek(0)
                    df = pd.read_csv(file_data, encoding='utf-8')
                except UnicodeDecodeError:
                    file_data.seek(0)
                    df = pd.read_csv(file_data, encoding='latin-1')
            elif file_ext in ['xlsx', 'xls']:
                file_data.seek(0)
                df = pd.read_excel(file_data, engine='openpyxl')
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            logger.info(f"Successfully read file {filename} with {len(df)} rows")
            return df

        except Exception as e:
            logger.error(f"Failed to read file {filename}: {e}")
            raise ValueError(f"Failed to parse file: {str(e)}")

    def validate_schema(self, df: pd.DataFrame, dataset_type: str) -> Tuple[bool, List[str]]:
        """
        Validate DataFrame against expected schema

        Args:
            df: DataFrame to validate
            dataset_type: Type of dataset ('products', 'sales', 'inventory')

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        if dataset_type not in self.SCHEMAS:
            return False, [f"Unknown dataset type: {dataset_type}"]

        schema = self.SCHEMAS[dataset_type]
        errors = []

        # Check required columns
        missing_columns = set(schema["required_columns"]) - set(df.columns)
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check for empty DataFrame
        if df.empty:
            errors.append("DataFrame is empty")

        # Dataset-specific validations
        if dataset_type == "products":
            if "sku" in df.columns and df["sku"].isna().any():
                errors.append("SKU column contains null values")
            if "sku" in df.columns and df["sku"].duplicated().any():
                errors.append(f"SKU column contains {df['sku'].duplicated().sum()} duplicates")

        elif dataset_type in ["sales", "inventory"]:
            if "date" in df.columns:
                try:
                    pd.to_datetime(df["date"])
                except Exception as e:
                    errors.append(f"Invalid date format in 'date' column: {str(e)}")

        is_valid = len(errors) == 0
        return is_valid, errors

    def merge_data(
        self,
        existing_df: pd.DataFrame,
        new_df: pd.DataFrame,
        dataset_type: str
    ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Merge new data with existing data, handling duplicates

        Args:
            existing_df: Existing DataFrame
            new_df: New DataFrame to merge
            dataset_type: Type of dataset

        Returns:
            Tuple of (merged_df, statistics_dict)
        """
        schema = self.SCHEMAS[dataset_type]
        primary_key = schema["primary_key"]

        stats = {
            "total_new_rows": len(new_df),
            "rows_added": 0,
            "rows_updated": 0,
            "rows_skipped": 0
        }

        if existing_df.empty:
            # No existing data, all rows are new
            stats["rows_added"] = len(new_df)
            return new_df, stats

        # Identify duplicates based on primary key
        existing_df["_exists"] = True
        merged = new_df.merge(
            existing_df[primary_key + ["_exists"]],
            on=primary_key,
            how="left",
            indicator=True
        )

        # Separate new and existing records
        new_records = merged[merged["_exists"].isna()].drop(columns=["_exists", "_merge"])
        update_records = merged[merged["_exists"] == True].drop(columns=["_exists", "_merge"])

        # Update existing records (remove old, add new)
        if not update_records.empty:
            # Create a mask for records to keep from existing_df
            existing_df = existing_df.drop(columns=["_exists"])

            # For update strategy: remove old records and add updated ones
            merge_key_str = existing_df[primary_key].astype(str).agg('_'.join, axis=1)
            update_key_str = update_records[primary_key].astype(str).agg('_'.join, axis=1)

            # Keep records that are not being updated
            existing_df = existing_df[~merge_key_str.isin(update_key_str)]

            stats["rows_updated"] = len(update_records)

        # Concatenate all data
        result_df = pd.concat([existing_df, new_records, update_records], ignore_index=True)

        stats["rows_added"] = len(new_records)

        logger.info(
            f"Merge complete for {dataset_type}: "
            f"{stats['rows_added']} added, {stats['rows_updated']} updated"
        )

        return result_df, stats

    def process_upload(
        self,
        file_data: BinaryIO,
        filename: str,
        dataset_type: Optional[str] = None,
        existing_data: Optional[pd.DataFrame] = None
    ) -> Dict:
        """
        Complete upload processing pipeline

        Args:
            file_data: Uploaded file data
            filename: Name of the file
            dataset_type: Optional dataset type (auto-detected if not provided)
            existing_data: Optional existing DataFrame to merge with

        Returns:
            Dictionary with processing results
        """
        # Auto-detect dataset type if not provided
        if not dataset_type:
            dataset_type = self.detect_file_type(filename)
            if not dataset_type:
                raise ValueError(
                    f"Cannot determine dataset type from filename: {filename}. "
                    f"Please include 'product', 'sales', or 'inventory' in the filename."
                )

        # Read file
        df = self.read_file(file_data, filename)

        # Validate schema
        is_valid, errors = self.validate_schema(df, dataset_type)
        if not is_valid:
            raise ValueError(f"Schema validation failed: {'; '.join(errors)}")

        # Merge with existing data if provided
        stats = {
            "total_new_rows": len(df),
            "rows_added": len(df),
            "rows_updated": 0,
            "rows_skipped": 0
        }

        if existing_data is not None and not existing_data.empty:
            df, stats = self.merge_data(existing_data, df, dataset_type)

        return {
            "success": True,
            "dataset_type": dataset_type,
            "filename": filename,
            "processed_df": df,
            "statistics": stats,
            "columns": list(df.columns),
            "total_rows": len(df)
        }

    @staticmethod
    def dataframe_to_csv_bytes(df: pd.DataFrame) -> bytes:
        """
        Convert DataFrame to CSV bytes

        Args:
            df: DataFrame to convert

        Returns:
            CSV data as bytes
        """
        return df.to_csv(index=False).encode('utf-8')

    @staticmethod
    def dataframe_from_csv_bytes(data: bytes) -> pd.DataFrame:
        """
        Load DataFrame from CSV bytes

        Args:
            data: CSV data as bytes

        Returns:
            pandas DataFrame
        """
        return pd.read_csv(BytesIO(data))


# Singleton instance
_data_processor: Optional[DataProcessor] = None


def get_data_processor() -> DataProcessor:
    """Get or create DataProcessor singleton instance"""
    global _data_processor
    if _data_processor is None:
        _data_processor = DataProcessor()
    return _data_processor
