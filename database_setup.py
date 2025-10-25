"""
Database setup module for water quality data.
Supports both MongoDB and mongomock for development.
"""

import os
import json
from pathlib import Path
import pandas as pd
from datetime import datetime
import logging

# Try to import MongoDB client, fall back to mongomock
try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure
    MONGODB_AVAILABLE = True
except ImportError:
    MONGODB_AVAILABLE = False

try:
    import mongomock
    MONGOMOCK_AVAILABLE = True
except ImportError:
    MONGOMOCK_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WaterQualityDatabase:
    def __init__(self, use_mongodb=True, connection_string=None, max_pool_size=50):
        """
        Initialize database connection (optimized).

        Args:
            use_mongodb (bool): If True, try to use MongoDB. If False or MongoDB unavailable, use mongomock.
            connection_string (str): MongoDB connection string. If None, uses default localhost.
            max_pool_size (int): Maximum connection pool size for MongoDB.
        """
        self.use_mongodb = use_mongodb and MONGODB_AVAILABLE
        self.connection_string = connection_string or "mongodb://localhost:27017/"
        self.max_pool_size = max_pool_size
        self.client = None
        self.db = None
        self.collection = None
        self.is_mongomock = False

        self._connect()

    def _connect(self):
        """Establish database connection with optimized settings."""
        if self.use_mongodb:
            try:
                # Use connection pool for better performance
                self.client = MongoClient(
                    self.connection_string,
                    serverSelectionTimeoutMS=5000,
                    connectTimeoutMS=10000,
                    maxPoolSize=self.max_pool_size,
                    retryWrites=True,
                    w='majority'  # Write concern for durability
                )
                # Test connection
                self.client.admin.command('ping')
                self.db = self.client['water_quality_data']
                self.collection = self.db['asv_1']
                self.is_mongomock = False
                logger.info("Connected to MongoDB successfully")
            except (ConnectionFailure, Exception) as e:
                logger.warning(f"Failed to connect to MongoDB: {e}")
                logger.info("Falling back to mongomock")
                self._use_mongomock()
        else:
            self._use_mongomock()

    def _use_mongomock(self):
        """Use mongomock for in-memory database."""
        if not MONGOMOCK_AVAILABLE:
            raise ImportError("Neither MongoDB nor mongomock is available. Please install pymongo and mongomock.")

        self.client = mongomock.MongoClient()
        self.db = self.client['water_quality_data']
        self.collection = self.db['asv_1']
        self.is_mongomock = True
        logger.info("Using mongomock for in-memory database")
    
    def create_indexes(self):
        """Create indexes for better query performance."""
        try:
            # Create indexes on commonly queried fields
            self.collection.create_index("timestamp")
            self.collection.create_index("temperature")
            self.collection.create_index("salinity")
            self.collection.create_index("odo")
            self.collection.create_index([("latitude", 1), ("longitude", 1)])  # Compound index for location
            logger.info("Database indexes created successfully")
        except Exception as e:
            logger.warning(f"Failed to create indexes: {e}")
    
    def insert_data(self, df):
        """
        Insert cleaned data into the database (optimized).

        Args:
            df (pandas.DataFrame): Cleaned water quality data
        """
        if df is None or df.empty:
            logger.warning("No data to insert")
            return 0

        logger.info(f"Inserting {len(df):,} records into database...")

        # Pre-process the dataframe for optimal performance
        df_copy = df.copy()

        # Convert timestamps to ISO strings in vectorized operation
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].dt.strftime('%Y-%m-%dT%H:%M:%S')

        # Convert DataFrame to list of dictionaries (optimized)
        # Using 'records' orient is faster than iterating
        records = df_copy.to_dict('records', into=dict)

        # Clean up NaN values in a single pass
        import math
        for record in records:
            for key in list(record.keys()):
                val = record[key]
                # Handle NaN, None, and numpy types
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    record[key] = None
                elif hasattr(val, 'item'):  # numpy types
                    record[key] = val.item()

        try:
            # Adaptive batch size based on database type
            batch_size = 5000 if not self.is_mongomock else 1000
            total_inserted = 0
            num_batches = (len(records) + batch_size - 1) // batch_size

            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                # ordered=False allows parallel inserts for better performance
                result = self.collection.insert_many(batch, ordered=False)
                total_inserted += len(result.inserted_ids)
                batch_num = i // batch_size + 1
                logger.info(f"Inserted batch {batch_num}/{num_batches}: {len(result.inserted_ids):,} records")

            logger.info(f"Successfully inserted {total_inserted:,} records")
            return total_inserted

        except Exception as e:
            logger.error(f"Failed to insert data: {e}")
            raise
    
    def get_collection_stats(self):
        """Get basic statistics about the collection."""
        try:
            total_docs = self.collection.count_documents({})
            logger.info(f"Total documents in collection: {total_docs}")
            return {"total_documents": total_docs}
        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {"error": str(e)}
    
    def close_connection(self):
        """Close database connection."""
        if self.client:
            self.client.close()
            logger.info("Database connection closed")
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_connection()


def setup_database_from_cleaned_data(data_file_path="data/cleaned_water_quality_data.csv", 
                                   use_mongodb=True, connection_string=None):
    """
    Set up database with cleaned water quality data.
    
    Args:
        data_file_path (str): Path to cleaned CSV file
        use_mongodb (bool): Whether to use MongoDB or mongomock
        connection_string (str): MongoDB connection string
    
    Returns:
        WaterQualityDatabase: Database instance
    """
    data_path = Path(data_file_path)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Cleaned data file not found: {data_path}")
    
    logger.info(f"Loading cleaned data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Initialize database
    with WaterQualityDatabase(use_mongodb=use_mongodb, connection_string=connection_string) as db:
        # Create indexes
        db.create_indexes()
        
        # Insert data
        inserted_count = db.insert_data(df)
        
        # Get stats
        stats = db.get_collection_stats()
        
        logger.info("Database setup complete!")
        logger.info(f"Inserted {inserted_count} records")
        logger.info(f"Collection stats: {stats}")
        
        return db


if __name__ == "__main__":
    # Example usage
    try:
        # Try to use MongoDB first
        db = setup_database_from_cleaned_data(use_mongodb=True)
    except Exception as e:
        logger.warning(f"MongoDB setup failed: {e}")
        logger.info("Trying with mongomock...")
        # Fall back to mongomock
        db = setup_database_from_cleaned_data(use_mongodb=False)
