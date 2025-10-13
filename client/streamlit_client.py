import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Ocean Data Explorer",
    page_icon="🌊",
    layout="wide"
)

# API base URL - adjust this to match your API
API_BASE_URL = "http://localhost:8000"  # Change this to your API URL


# Load and combine CSV files
@st.cache_data
def load_csv_data():
    """Load and combine all CSV files from the data directory"""
    files = [
        "../data/2021-oct21.csv",
        "../data/2021-dec16.csv",
        "../data/2022-oct7.csv",
        "../data/2022-nov16.csv"
    ]

    dataframes = []
    for file in files:
        if os.path.exists(file):
            try:
                df = pd.read_csv(file)
                # Add source file column for reference
                df['source_file'] = os.path.basename(file)
                dataframes.append(df)
            except Exception as e:
                st.warning(f"Could not load {file}: {e}")

    if dataframes:
        combined_df = pd.concat(dataframes, ignore_index=True)

        # Create a unified datetime column from Date and Time
        if 'Date' in combined_df.columns and 'Time' in combined_df.columns:
            combined_df['datetime'] = pd.to_datetime(
                combined_df['Date'] + ' ' + combined_df['Time'],
                errors='coerce'
            )

        # Standardize column names for easier access
        column_mapping = {
            'Temperature (c)': 'temperature',
            'Salinity (ppt)': 'salinity',
            'ODO mg/L': 'odo',
            'Latitude': 'latitude',
            'Longitude': 'longitude',
            'Temp C': 'temp_c_sensor',
            'Sal ppt': 'sal_ppt_sensor'
        }

        for old_col, new_col in column_mapping.items():
            if old_col in combined_df.columns:
                combined_df[new_col] = combined_df[old_col]

        return combined_df
    else:
        return pd.DataFrame()


# Load the local CSV data
local_data = load_csv_data()

st.title("🌊 Ocean Observation Data Explorer")

# Data source selection
st.sidebar.header("📂 Data Source")

# Check if local data is available
has_local_data = not local_data.empty

if has_local_data:
    default_source = 0  # Local CSV Files
    st.sidebar.success(f"✅ {len(local_data)} records loaded from CSV files")
else:
    default_source = 1  # API Endpoints
    st.sidebar.warning("⚠️ No local CSV files found")

data_source = st.sidebar.radio(
    "Choose data source:",
    ["Local CSV Files", "API Endpoints"],
    index=default_source,
    help="Select 'Local CSV Files' to use the uploaded data, or 'API Endpoints' if you have an API running"
)

# Sidebar - Controls Panel
st.sidebar.header("🎛️ Controls Panel")

# Date range filter
st.sidebar.subheader("Date Range")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start Date",
        value=datetime(2021, 1, 1),
        key="start_date"
    )
with col2:
    end_date = st.date_input(
        "End Date",
        value=datetime(2022, 12, 31),
        key="end_date"
    )

# Temperature filter
st.sidebar.subheader("Temperature (°C)")
temp_col1, temp_col2 = st.sidebar.columns(2)
with temp_col1:
    min_temp = st.number_input("Min", value=-5.0, step=0.1, key="min_temp")
with temp_col2:
    max_temp = st.number_input("Max", value=35.0, step=0.1, key="max_temp")

# Salinity filter
st.sidebar.subheader("Salinity (PSU)")
sal_col1, sal_col2 = st.sidebar.columns(2)
with sal_col1:
    min_salinity = st.number_input("Min", value=0.0, step=0.1, key="min_sal")
with sal_col2:
    max_salinity = st.number_input("Max", value=40.0, step=0.1, key="max_sal")

# ODO filter
st.sidebar.subheader("ODO (mg/L)")
odo_col1, odo_col2 = st.sidebar.columns(2)
with odo_col1:
    min_odo = st.number_input("Min", value=0.0, step=0.1, key="min_odo")
with odo_col2:
    max_odo = st.number_input("Max", value=20.0, step=0.1, key="max_odo")

# Pagination controls
st.sidebar.subheader("Pagination")
limit = st.sidebar.slider("Records per page", min_value=10, max_value=1000, value=100, step=10)
offset = st.sidebar.number_input("Offset", min_value=0, value=0, step=limit)

# Fetch button
if data_source == "API Endpoints":
    fetch_data = st.sidebar.button("🔄 Fetch Data from API", type="primary")
else:
    fetch_data = st.sidebar.button("🔄 Apply Filters", type="primary")


# Function to filter local data
def filter_local_data(df, params):
    """Filter local CSV data based on parameters"""
    filtered_df = df.copy()

    # Date filtering
    if 'datetime' in filtered_df.columns:
        start = pd.to_datetime(params['start_date'])
        end = pd.to_datetime(params['end_date']) + pd.Timedelta(days=1)
        filtered_df = filtered_df[
            (filtered_df['datetime'] >= start) &
            (filtered_df['datetime'] < end)
            ]

    # Temperature filtering
    if 'temperature' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['temperature'] >= params['min_temp']) &
            (filtered_df['temperature'] <= params['max_temp'])
            ]

    # Salinity filtering
    if 'salinity' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['salinity'] >= params['min_salinity']) &
            (filtered_df['salinity'] <= params['max_salinity'])
            ]

    # ODO filtering
    if 'odo' in filtered_df.columns:
        filtered_df = filtered_df[
            (filtered_df['odo'] >= params['min_odo']) &
            (filtered_df['odo'] <= params['max_odo'])
            ]

    # Pagination
    offset = params['offset']
    limit = params['limit']
    filtered_df = filtered_df.iloc[offset:offset + limit]

    return filtered_df


# Function to calculate statistics from local data
def calculate_stats(df):
    """Calculate statistics from dataframe"""
    stats = {
        'total_records': len(df)
    }

    if 'temperature' in df.columns:
        stats['temperature'] = {
            'mean': df['temperature'].mean(),
            'min': df['temperature'].min(),
            'max': df['temperature'].max(),
            'std': df['temperature'].std()
        }

    if 'salinity' in df.columns:
        stats['salinity'] = {
            'mean': df['salinity'].mean(),
            'min': df['salinity'].min(),
            'max': df['salinity'].max(),
            'std': df['salinity'].std()
        }

    if 'odo' in df.columns:
        stats['odo'] = {
            'mean': df['odo'].mean(),
            'min': df['odo'].min(),
            'max': df['odo'].max(),
            'std': df['odo'].std()
        }

    return stats


# Function to detect outliers using IQR method
def detect_outliers(df):
    """Detect outliers using IQR method"""
    outliers_df = pd.DataFrame()

    numeric_cols = ['temperature', 'salinity', 'odo']
    available_cols = [col for col in numeric_cols if col in df.columns]

    for col in available_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        col_outliers = df[(df[col] < lower_bound) | (df[col] > upper_bound)]
        outliers_df = pd.concat([outliers_df, col_outliers])

    # Remove duplicates
    outliers_df = outliers_df.drop_duplicates()

    return outliers_df


# Function to fetch observations from API
@st.cache_data(ttl=300)
def fetch_observations(params):
    try:
        response = requests.get(f"{API_BASE_URL}/api/observations", params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching observations: {e}")
        return pd.DataFrame()


# Function to fetch statistics from API
@st.cache_data(ttl=300)
def fetch_stats(params):
    try:
        response = requests.get(f"{API_BASE_URL}/api/stats", params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching statistics: {e}")
        return {}


# Function to fetch outliers from API
@st.cache_data(ttl=300)
def fetch_outliers(params):
    try:
        response = requests.get(f"{API_BASE_URL}/api/outliers", params=params)
        response.raise_for_status()
        data = response.json()
        return pd.DataFrame(data)
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching outliers: {e}")
        return pd.DataFrame()


# Build query parameters
params = {
    "start_date": start_date.strftime("%Y-%m-%d"),
    "end_date": end_date.strftime("%Y-%m-%d"),
    "min_temp": min_temp,
    "max_temp": max_temp,
    "min_salinity": min_salinity,
    "max_salinity": max_salinity,
    "min_odo": min_odo,
    "max_odo": max_odo,
    "limit": limit,
    "offset": offset
}

# Fetch data
if fetch_data or 'df' not in st.session_state:
    with st.spinner("Processing data..."):
        if data_source == "API Endpoints":
            # Use API
            st.session_state.df = fetch_observations(params)
            st.session_state.stats = fetch_stats(params)
            st.session_state.outliers = fetch_outliers(params)
        else:
            # Use local CSV files
            if not local_data.empty:
                st.session_state.df = filter_local_data(local_data, params)
                # Calculate stats on full filtered dataset (before pagination)
                full_filtered = filter_local_data(local_data, {**params, 'offset': 0, 'limit': len(local_data)})
                st.session_state.stats = calculate_stats(full_filtered)
                st.session_state.outliers = detect_outliers(full_filtered)
            else:
                st.error("No local CSV files found. Please check the file paths.")

# Main content area
if 'df' in st.session_state and not st.session_state.df.empty:
    df = st.session_state.df

    # Ensure datetime column exists
    if 'datetime' in df.columns:
        df['date'] = df['datetime']
    elif 'date' in df.columns:
        df['date'] = pd.to_datetime(df['date'])
    elif 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df['date'] = df['timestamp']

    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Visualizations", "📋 Data Table", "📈 Statistics", "⚠️ Outliers"])

    with tab1:
        st.header("Visualizations")

        # Line chart - Temperature over time
        st.subheader("Temperature Over Time")
        if 'date' in df.columns and 'temperature' in df.columns:
            fig_line = px.line(
                df.sort_values('date'),
                x='date',
                y='temperature',
                title='Temperature Trend',
                labels={'date': 'Date', 'temperature': 'Temperature (°C)'}
            )
            fig_line.update_traces(line_color='#FF6B6B')
            st.plotly_chart(fig_line, use_container_width=True)
        else:
            st.warning("Temperature or date column not found in data")

        # Create two columns for histogram and scatter plot
        col1, col2 = st.columns(2)

        with col1:
            # Histogram - Salinity distribution
            st.subheader("Salinity Distribution")
            if 'salinity' in df.columns:
                fig_hist = px.histogram(
                    df,
                    x='salinity',
                    nbins=30,
                    title='Salinity Distribution',
                    labels={'salinity': 'Salinity (PSU)', 'count': 'Frequency'}
                )
                fig_hist.update_traces(marker_color='#4ECDC4')
                st.plotly_chart(fig_hist, use_container_width=True)
            else:
                st.warning("Salinity column not found in data")

        with col2:
            # Scatter plot - Temperature vs Salinity, colored by ODO
            st.subheader("Temperature vs Salinity")
            if all(col in df.columns for col in ['temperature', 'salinity', 'odo']):
                fig_scatter = px.scatter(
                    df,
                    x='temperature',
                    y='salinity',
                    color='odo',
                    title='Temperature vs Salinity (colored by ODO)',
                    labels={
                        'temperature': 'Temperature (°C)',
                        'salinity': 'Salinity (PSU)',
                        'odo': 'ODO (mg/L)'
                    },
                    color_continuous_scale='Viridis'
                )
                st.plotly_chart(fig_scatter, use_container_width=True)
            else:
                st.warning("Temperature, salinity, or ODO column not found in data")

        # Map - Location visualization
        st.subheader("Observation Locations")
        if all(col in df.columns for col in ['latitude', 'longitude']):
            # Create hover text
            hover_cols = [col for col in ['date', 'temperature', 'salinity', 'odo'] if col in df.columns]
            hover_text = df[hover_cols].apply(
                lambda row: '<br>'.join([f"{col}: {val}" for col, val in row.items()]),
                axis=1
            )

            fig_map = px.scatter_mapbox(
                df,
                lat='latitude',
                lon='longitude',
                color='temperature' if 'temperature' in df.columns else None,
                size='odo' if 'odo' in df.columns else None,
                hover_name=hover_text,
                title='Observation Path',
                zoom=5,
                height=500,
                color_continuous_scale='RdYlBu_r'
            )
            fig_map.update_layout(mapbox_style="open-street-map")
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Latitude and longitude columns not found in data")

    with tab2:
        st.header("Data Table")
        st.info(f"Showing {len(df)} records (Offset: {offset}, Limit: {limit})")
        st.dataframe(df, use_container_width=True, height=600)

        # Download button
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Data as CSV",
            data=csv,
            file_name=f"ocean_data_{start_date}_{end_date}.csv",
            mime="text/csv"
        )

    with tab3:
        st.header("Statistics Panel")
        if 'stats' in st.session_state and st.session_state.stats:
            stats = st.session_state.stats

            # Display statistics in columns
            col1, col2, col3 = st.columns(3)

            with col1:
                st.metric("Total Records", stats.get('total_records', 'N/A'))
                if 'temperature' in stats:
                    st.subheader("🌡️ Temperature")
                    st.write(f"**Mean:** {stats['temperature'].get('mean', 'N/A'):.2f} °C")
                    st.write(f"**Min:** {stats['temperature'].get('min', 'N/A'):.2f} °C")
                    st.write(f"**Max:** {stats['temperature'].get('max', 'N/A'):.2f} °C")
                    st.write(f"**Std Dev:** {stats['temperature'].get('std', 'N/A'):.2f} °C")

            with col2:
                if 'salinity' in stats:
                    st.subheader("💧 Salinity")
                    st.write(f"**Mean:** {stats['salinity'].get('mean', 'N/A'):.2f} PSU")
                    st.write(f"**Min:** {stats['salinity'].get('min', 'N/A'):.2f} PSU")
                    st.write(f"**Max:** {stats['salinity'].get('max', 'N/A'):.2f} PSU")
                    st.write(f"**Std Dev:** {stats['salinity'].get('std', 'N/A'):.2f} PSU")

            with col3:
                if 'odo' in stats:
                    st.subheader("🫧 ODO")
                    st.write(f"**Mean:** {stats['odo'].get('mean', 'N/A'):.2f} mg/L")
                    st.write(f"**Min:** {stats['odo'].get('min', 'N/A'):.2f} mg/L")
                    st.write(f"**Max:** {stats['odo'].get('max', 'N/A'):.2f} mg/L")
                    st.write(f"**Std Dev:** {stats['odo'].get('std', 'N/A'):.2f} mg/L")

            # Show full statistics as JSON
            with st.expander("View Raw Statistics"):
                st.json(stats)
        else:
            st.warning("No statistics available. Click 'Fetch Data' to load statistics.")

    with tab4:
        st.header("Outliers Detection")
        if 'outliers' in st.session_state and not st.session_state.outliers.empty:
            outliers_df = st.session_state.outliers
            st.warning(f"⚠️ Found {len(outliers_df)} outlier records")
            st.dataframe(outliers_df, use_container_width=True, height=600)

            # Visualize outliers
            if all(col in outliers_df.columns for col in ['temperature', 'salinity', 'odo']):
                st.subheader("Outlier Visualization")
                fig_outliers = px.scatter_3d(
                    outliers_df,
                    x='temperature',
                    y='salinity',
                    z='odo',
                    title='3D View of Outliers',
                    labels={
                        'temperature': 'Temperature (°C)',
                        'salinity': 'Salinity (PSU)',
                        'odo': 'ODO (mg/L)'
                    },
                    color_discrete_sequence=['red']
                )
                st.plotly_chart(fig_outliers, use_container_width=True)
        else:
            st.info("No outliers detected in the current dataset.")

else:
    # Display information based on data source
    if data_source == "Local CSV Files":
        if not local_data.empty:
            st.success(f"✅ Loaded {len(local_data)} total records from CSV files")
            st.info("👈 Configure your filters in the sidebar and click 'Apply Filters' to explore the data!")

            # Show data summary
            st.subheader("Data Summary")
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Records", len(local_data))
            with col2:
                if 'datetime' in local_data.columns:
                    st.metric("Date Range",
                              f"{local_data['datetime'].min().date()} to {local_data['datetime'].max().date()}")
            with col3:
                st.metric("CSV Files", local_data['source_file'].nunique())
            with col4:
                st.metric("Columns", len(local_data.columns))

            # Show available columns
            with st.expander("View Available Columns"):
                st.write(list(local_data.columns))
        else:
            st.error("❌ Could not load CSV files. Please check the file paths in the code.")
            st.info(
                "Expected files: ../data/2021-oct21.csv, ../data/2021-dec16.csv, ../data/2022-oct7.csv, ../data/2022-nov16.csv")
    else:
        st.info(
            "👈 Configure your filters in the sidebar and click 'Fetch Data from API' to begin exploring ocean observations!")

        # Display sample configuration
        st.markdown("""
        ### Getting Started with API

        This application can connect to your Ocean Data API. Make sure:

        1. Your API is running at `http://localhost:8000` (or update `API_BASE_URL` in the code)
        2. The following endpoints are available:
           - `/api/observations` - Returns observation data
           - `/api/stats` - Returns statistical summaries
           - `/api/outliers` - Returns outlier records
        3. Your API accepts the following query parameters:
           - `start_date`, `end_date`
           - `min_temp`, `max_temp`
           - `min_salinity`, `max_salinity`
           - `min_odo`, `max_odo`
           - `limit`, `offset`
        """)

# Footer
st.sidebar.markdown("---")
st.sidebar.info("🌊 Ocean Data Explorer v1.0")