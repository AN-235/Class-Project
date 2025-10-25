"""
Flask REST API for water quality data (optimized).
Provides endpoints for querying observations, statistics, and outliers.
"""

from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask_compress import Compress
from functools import lru_cache, wraps
import os
import json
import logging
from datetime import datetime, timedelta
import numpy as np
from scipy import stats
from pathlib import Path
import time

# Import our database module
import sys
sys.path.append(str(Path(__file__).parent.parent))
from database_setup import WaterQualityDatabase

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
Compress(app)  # Enable gzip compression for responses

# Global database instance
db_instance = None

# Cache configuration
CACHE_TIMEOUT = 300  # 5 minutes

# Simple in-memory cache
_cache = {}
_cache_timestamps = {}

def cache_response(timeout=CACHE_TIMEOUT):
    """Simple cache decorator for API responses."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and request args
            cache_key = f"{func.__name__}:{request.url}"

            # Check if cached and not expired
            if cache_key in _cache:
                cached_time = _cache_timestamps.get(cache_key, 0)
                if time.time() - cached_time < timeout:
                    logger.debug(f"Cache hit for {cache_key}")
                    return _cache[cache_key]

            # Call function and cache result
            result = func(*args, **kwargs)
            _cache[cache_key] = result
            _cache_timestamps[cache_key] = time.time()

            # Cleanup old cache entries (keep cache size manageable)
            if len(_cache) > 100:
                oldest_key = min(_cache_timestamps, key=_cache_timestamps.get)
                del _cache[oldest_key]
                del _cache_timestamps[oldest_key]

            return result
        return wrapper
    return decorator

def get_database():
    """Get or create database instance."""
    global db_instance
    if db_instance is None:
        try:
            # Try MongoDB first
            db_instance = WaterQualityDatabase(use_mongodb=True)
        except Exception as e:
            logger.warning(f"MongoDB connection failed: {e}")
            # Fall back to mongomock
            db_instance = WaterQualityDatabase(use_mongodb=False)
        
        # Load data if database is empty
        try:
            stats = db_instance.get_collection_stats()
            if stats.get('total_documents', 0) == 0:
                logger.info("Database is empty, loading data...")
                from pathlib import Path
                data_path = Path("data/cleaned_water_quality_data.csv")
                if data_path.exists():
                    import pandas as pd
                    df = pd.read_csv(data_path)
                    db_instance.create_indexes()
                    db_instance.insert_data(df)
                    logger.info(f"Loaded {len(df)} records into database")
                else:
                    logger.warning("Cleaned data file not found")
        except Exception as e:
            logger.error(f"Failed to load data: {e}")
    
    return db_instance

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    try:
        db = get_database()
        # Test database connection
        db.get_collection_stats()
        return jsonify({
            "status": "ok",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route('/api/observations', methods=['GET'])
def get_observations():
    """Get water quality observations with optional filters (optimized)."""
    try:
        db = get_database()
        collection = db.collection

        # Parse query parameters
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        min_temp = request.args.get('min_temp', type=float)
        max_temp = request.args.get('max_temp', type=float)
        min_sal = request.args.get('min_sal', type=float)
        max_sal = request.args.get('max_sal', type=float)
        min_odo = request.args.get('min_odo', type=float)
        max_odo = request.args.get('max_odo', type=float)
        limit = min(request.args.get('limit', 100, type=int), 1000)  # Max 1000
        skip = max(request.args.get('skip', 0, type=int), 0)  # Prevent negative skip

        # Build MongoDB query
        query = {}

        # Date range filter
        if start_time or end_time:
            date_filter = {}
            if start_time:
                date_filter['$gte'] = start_time
            if end_time:
                date_filter['$lte'] = end_time
            query['timestamp'] = date_filter

        # Temperature filter
        if min_temp is not None or max_temp is not None:
            temp_filter = {}
            if min_temp is not None:
                temp_filter['$gte'] = min_temp
            if max_temp is not None:
                temp_filter['$lte'] = max_temp
            query['temperature'] = temp_filter

        # Salinity filter
        if min_sal is not None or max_sal is not None:
            sal_filter = {}
            if min_sal is not None:
                sal_filter['$gte'] = min_sal
            if max_sal is not None:
                sal_filter['$lte'] = max_sal
            query['salinity'] = sal_filter

        # ODO filter
        if min_odo is not None or max_odo is not None:
            odo_filter = {}
            if min_odo is not None:
                odo_filter['$gte'] = min_odo
            if max_odo is not None:
                odo_filter['$lte'] = max_odo
            query['odo'] = odo_filter

        # Projection - only fetch fields we need (optimization)
        projection = {
            'timestamp': 1, 'latitude': 1, 'longitude': 1,
            'temperature': 1, 'salinity': 1, 'odo': 1, 'ph': 1, 'depth': 1
        }

        # Execute query with projection
        cursor = collection.find(query, projection).skip(skip).limit(limit)
        observations = list(cursor)

        # Convert ObjectId to string for JSON serialization
        for obs in observations:
            if '_id' in obs:
                obs['_id'] = str(obs['_id'])

        # Get total count (use estimated count for better performance if no filters)
        if not query:
            total_count = collection.estimated_document_count()
        else:
            total_count = collection.count_documents(query)

        return jsonify({
            "count": len(observations),
            "total_count": total_count,
            "items": observations,
            "query_params": {
                "start": start_time,
                "end": end_time,
                "min_temp": min_temp,
                "max_temp": max_temp,
                "min_sal": min_sal,
                "max_sal": max_sal,
                "min_odo": min_odo,
                "max_odo": max_odo,
                "limit": limit,
                "skip": skip
            }
        })

    except Exception as e:
        logger.error(f"Error in get_observations: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_statistics():
    """Get summary statistics for numeric fields."""
    try:
        db = get_database()
        collection = db.collection
        
        # Get all numeric fields
        numeric_fields = ['temperature', 'salinity', 'odo', 'ph', 'depth']
        stats_result = {}
        
        for field in numeric_fields:
            # Get all non-null values for this field
            pipeline = [
                {"$match": {field: {"$exists": True, "$ne": None}}},
                {"$group": {
                    "_id": None,
                    "count": {"$sum": 1},
                    "mean": {"$avg": f"${field}"},
                    "min": {"$min": f"${field}"},
                    "max": {"$max": f"${field}"}
                }}
            ]
            
            result = list(collection.aggregate(pipeline))
            if result:
                stats_data = result[0]
                # Calculate percentiles and std using numpy
                values = [doc[field] for doc in collection.find({field: {"$exists": True, "$ne": None}})]
                if values:
                    percentiles = np.percentile(values, [25, 50, 75])
                    std_dev = np.std(values, ddof=0)  # Population standard deviation
                    stats_result[field] = {
                        "count": stats_data["count"],
                        "mean": round(stats_data["mean"], 3),
                        "min": stats_data["min"],
                        "max": stats_data["max"],
                        "std": round(std_dev, 3),
                        "percentiles": {
                            "25%": round(percentiles[0], 3),
                            "50%": round(percentiles[1], 3),
                            "75%": round(percentiles[2], 3)
                        }
                    }
                else:
                    stats_result[field] = {"error": "No data available"}
            else:
                stats_result[field] = {"error": "No data available"}
        
        return jsonify({
            "statistics": stats_result,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/outliers', methods=['GET'])
def get_outliers():
    """Get outliers using specified method and parameters."""
    try:
        db = get_database()
        collection = db.collection
        
        # Parse parameters
        field = request.args.get('field', 'temperature')
        method = request.args.get('method', 'iqr')  # 'iqr' or 'zscore'
        k = float(request.args.get('k', 1.5))  # For IQR method
        z_threshold = float(request.args.get('z_threshold', 3.0))  # For z-score method
        
        # Validate field
        valid_fields = ['temperature', 'salinity', 'odo', 'ph', 'depth']
        if field not in valid_fields:
            return jsonify({"error": f"Invalid field. Must be one of: {valid_fields}"}), 400
        
        # Get all data for the field
        data = list(collection.find({field: {"$exists": True, "$ne": None}}, {field: 1, "_id": 1}))
        values = [doc[field] for doc in data if doc[field] is not None]
        
        if not values:
            return jsonify({"error": f"No data available for field '{field}'"}), 400
        
        outliers = []
        
        if method == 'iqr':
            # IQR method
            q1 = np.percentile(values, 25)
            q3 = np.percentile(values, 75)
            iqr = q3 - q1
            lower_bound = q1 - k * iqr
            upper_bound = q3 + k * iqr
            
            for i, value in enumerate(values):
                if value < lower_bound or value > upper_bound:
                    outliers.append({
                        "index": i,
                        "value": value,
                        "reason": f"Outside IQR bounds [{lower_bound:.3f}, {upper_bound:.3f}]"
                    })
        
        elif method == 'zscore':
            # Z-score method
            z_scores = np.abs(stats.zscore(values))
            
            for i, (value, z_score) in enumerate(zip(values, z_scores)):
                if z_score > z_threshold:
                    outliers.append({
                        "index": i,
                        "value": value,
                        "z_score": round(z_score, 3),
                        "reason": f"Z-score {z_score:.3f} > {z_threshold}"
                    })
        
        else:
            return jsonify({"error": "Invalid method. Must be 'iqr' or 'zscore'"}), 400
        
        return jsonify({
            "field": field,
            "method": method,
            "parameters": {
                "k": k if method == 'iqr' else None,
                "z_threshold": z_threshold if method == 'zscore' else None
            },
            "total_values": len(values),
            "outlier_count": len(outliers),
            "outlier_percentage": round(len(outliers) / len(values) * 100, 2),
            "outliers": outliers
        })
        
    except Exception as e:
        logger.error(f"Error in get_outliers: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/data/summary', methods=['GET'])
def get_data_summary():
    """Get a summary of the dataset."""
    try:
        db = get_database()
        collection = db.collection
        
        # Get total count
        total_count = collection.count_documents({})
        
        # Get date range
        date_pipeline = [
            {"$group": {
                "_id": None,
                "min_date": {"$min": "$timestamp"},
                "max_date": {"$max": "$timestamp"}
            }}
        ]
        date_result = list(collection.aggregate(date_pipeline))
        
        # Get field availability
        fields = ['temperature', 'salinity', 'odo', 'ph', 'depth', 'latitude', 'longitude']
        field_counts = {}
        for field in fields:
            count = collection.count_documents({field: {"$exists": True, "$ne": None}})
            field_counts[field] = count
        
        return jsonify({
            "total_records": total_count,
            "date_range": date_result[0] if date_result else None,
            "field_availability": field_counts,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error in get_data_summary: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Initialize database connection
    try:
        db = get_database()
        logger.info("Database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        logger.info("API will start but may not function properly")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5002)
