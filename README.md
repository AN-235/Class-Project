#optimi Water Quality Data Pipeline

A comprehensive data pipeline for processing, storing, and visualizing water quality data collected by aquatic robots. This project implements a complete ETL (Extract, Transform, Load) pipeline with a REST API and interactive web dashboard.

## 🏗️ Architecture

```
CSV Files → Data Cleaning → Database → REST API → Streamlit Dashboard
```

## 📁 Project Structure

```
Class-Project/
├── data/                          # Raw and cleaned CSV files
│   ├── 2021-dec16.csv
│   ├── 2021-oct21.csv
│   ├── 2022-nov16.csv
│   ├── 2022-oct7.csv
│   ├── cleaned_water_quality_data.csv
│   └── cleaning_report.json
├── api/                          # Flask REST API
│   └── flaskAPI.py
├── client/                       # Streamlit dashboard
│   └── streamlit_client.py
├── data_cleaning.py             # Data preprocessing and outlier removal
├── database_setup.py           # Database connection and setup
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- pip package manager

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd Class-Project
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Process the data:**
   ```bash
   python data_cleaning.py
   ```

4. **Set up the database:**
   ```bash
   python database_setup.py
   ```

5. **Start the API server:**
   ```bash
   python api/flaskAPI.py
   ```

6. **Launch the dashboard:**
   ```bash
   streamlit run client/streamlit_client.py
   ```

## 📊 Features

### Data Processing
- **CSV Loading**: Automatically loads multiple CSV files
- **Data Cleaning**: Z-score outlier removal (configurable threshold)
- **Data Standardization**: Unified column names and data types
- **Database Storage**: MongoDB or mongomock support

### REST API Endpoints
- `GET /api/health` - Health check
- `GET /api/observations` - Query observations with filters
- `GET /api/stats` - Statistical summaries
- `GET /api/outliers` - Outlier detection (IQR/Z-score)
- `GET /api/data/summary` - Dataset overview

### Interactive Dashboard
- **Data Visualization**: Line charts, histograms, scatter plots
- **Geographic Maps**: Interactive location mapping
- **Statistical Analysis**: Summary statistics and percentiles
- **Outlier Detection**: Real-time outlier identification
- **Filtering**: Date range, parameter value filters
- **Pagination**: Efficient data loading

## 🔧 API Documentation

### Health Check
```http
GET /api/health
```
Returns API status and database connection status.

### Observations
```http
GET /api/observations?start=2021-01-01&end=2021-12-31&min_temp=20&max_temp=30&limit=100
```

**Query Parameters:**
- `start`, `end`: ISO timestamp range
- `min_temp`, `max_temp`: Temperature range (°C)
- `min_sal`, `max_sal`: Salinity range (ppt)
- `min_odo`, `max_odo`: Dissolved oxygen range (mg/L)
- `limit`: Maximum records (default: 100, max: 1000)
- `skip`: Pagination offset

**Response:**
```json
{
  "count": 503,
  "total_count": 1500,
  "items": [
    {
      "timestamp": "2021-12-16T14:18:24",
      "latitude": 25.91276817,
      "longitude": -80.13791017,
      "temperature": 25.95,
      "salinity": 49.56,
      "odo": 5.44
    }
  ]
}
```

### Statistics
```http
GET /api/stats
```
Returns statistical summaries for all numeric fields.

### Outliers
```http
GET /api/outliers?field=temperature&method=iqr&k=1.5
GET /api/outliers?field=temperature&method=zscore&z_threshold=3.0
```

**Parameters:**
- `field`: Parameter to analyze (temperature, salinity, odo, ph, depth)
- `method`: Detection method (iqr, zscore)
- `k`: IQR multiplier (for IQR method)
- `z_threshold`: Z-score threshold (for z-score method)

## 🧹 Data Cleaning

The data cleaning process uses z-score outlier detection:

1. **Load CSV files** from the data directory
2. **Standardize columns** (timestamp, coordinates, water parameters)
3. **Calculate z-scores** for numeric fields
4. **Remove outliers** where |z-score| > threshold (default: 3.0)
5. **Generate report** with cleaning statistics

### Cleaning Report Example
```json
{
  "original_rows": 10000,
  "rows_removed": 150,
  "rows_remaining": 9850,
  "removal_percentage": 1.5,
  "outlier_details": {
    "temperature": {
      "outlier_count": 45,
      "outlier_percentage": 0.45
    }
  }
}
```

## 🗄️ Database

### MongoDB (Production)
- Database: `water_quality_data`
- Collection: `asv_1`
- Indexes: timestamp, temperature, salinity, odo, location

### mongomock (Development)
- In-memory database for testing
- No installation required
- Automatic fallback if MongoDB unavailable

## 📈 Visualizations

### Line Charts
- Temperature over time
- Salinity over time
- Parameter trends

### Histograms
- Parameter distributions
- Data quality assessment

### Scatter Plots
- Temperature vs Salinity
- Parameter correlations
- Color-coded by additional variables

### Maps
- Geographic sampling locations
- Parameter value visualization
- Interactive hover information

## 🛠️ Configuration

### Environment Variables
- `MONGODB_URL`: MongoDB connection string
- `API_HOST`: API server host (default: 0.0.0.0)
- `API_PORT`: API server port (default: 5000)

### Data Parameters
- Z-score threshold: 3.0 (configurable)
- Batch size: 1000 records
- API limit: 1000 records max

## 🧪 Testing

### API Testing
```bash
# Health check
curl http://localhost:5000/api/health

# Get observations
curl "http://localhost:5000/api/observations?limit=10"

# Get statistics
curl http://localhost:5000/api/stats
```

### Data Validation
- Automatic data type conversion
- Missing value handling
- Outlier detection validation
- API response validation

## 📋 Requirements

### Python Packages
- Flask 3.1.2
- pandas 2.3.3
- pymongo 4.9.2
- mongomock 4.1.2
- streamlit 1.50.0
- plotly 6.0.0
- numpy 1.24.3
- scipy 1.11.4

### System Requirements
- Python 3.9+
- 4GB RAM minimum
- 1GB disk space

## 🚨 Troubleshooting

### Common Issues

1. **API Connection Error**
   - Ensure Flask API is running on port 5000
   - Check firewall settings
   - Verify API health endpoint

2. **Database Connection Error**
   - MongoDB not running (use mongomock)
   - Connection string incorrect
   - Network connectivity issues

3. **Data Loading Issues**
   - CSV files in correct format
   - Required columns present
   - File permissions

4. **Memory Issues**
   - Reduce batch size
   - Use pagination
   - Increase system RAM

## 📚 Learning Outcomes

This project demonstrates:

- **ETL Pipeline**: Extract, Transform, Load data processing
- **REST API Design**: Flask API with proper endpoints
- **Database Integration**: MongoDB with indexing and queries
- **Data Visualization**: Interactive charts and maps
- **Outlier Detection**: Statistical methods for data quality
- **Client-Server Architecture**: API communication patterns

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📞 Support

For questions or issues:
- Create an issue in the repository
- Check the troubleshooting section
- Review the API documentation

---

*Water Quality Data Pipeline - From CSV to Interactive Dashboard*