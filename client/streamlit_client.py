"""
Streamlit client for water quality data visualization (optimized).
Connects to Flask API and provides interactive visualizations.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from functools import lru_cache
import time

# Configure page
st.set_page_config(
    page_title="Water Quality Dashboard",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_BASE_URL = "http://localhost:5002/api"

# Session state initialization
if 'last_fetch_time' not in st.session_state:
    st.session_state['last_fetch_time'] = {}
if 'cached_data' not in st.session_state:
    st.session_state['cached_data'] = {}

@st.cache_data(ttl=300, show_spinner=False)  # Cache for 5 minutes
def fetch_data(endpoint, params=None):
    """Fetch data from API with enhanced caching."""
    try:
        response = requests.get(
            f"{API_BASE_URL}/{endpoint}",
            params=params,
            timeout=15,
            headers={'Accept-Encoding': 'gzip'}  # Request compressed response
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"API Error: {e}")
        return None

@st.cache_data(ttl=60, show_spinner=False)
def check_api_health():
    """Check if API is running (cached)."""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    st.title("🌊 Water Quality Data Dashboard")
    st.markdown("Interactive visualization of water quality data from aquatic robots")
    
    # Check API health
    if not check_api_health():
        st.error("⚠️ API is not running. Please start the Flask API server first.")
        st.code("python api/flaskAPI.py")
        return
    
    # Sidebar controls
    st.sidebar.header("🔧 Controls")
    
    # Date range filter
    st.sidebar.subheader("📅 Date Range")
    date_col1, date_col2 = st.sidebar.columns(2)
    with date_col1:
        start_date = st.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    with date_col2:
        end_date = st.date_input("End Date", value=datetime.now())
    
    # Parameter filters
    st.sidebar.subheader("🌡️ Parameter Filters")
    
    # Temperature filter
    temp_col1, temp_col2 = st.sidebar.columns(2)
    with temp_col1:
        min_temp = st.number_input("Min Temperature (°C)", value=None, placeholder="No limit")
    with temp_col2:
        max_temp = st.number_input("Max Temperature (°C)", value=None, placeholder="No limit")
    
    # Salinity filter
    sal_col1, sal_col2 = st.sidebar.columns(2)
    with sal_col1:
        min_sal = st.number_input("Min Salinity (ppt)", value=None, placeholder="No limit")
    with sal_col2:
        max_sal = st.number_input("Max Salinity (ppt)", value=None, placeholder="No limit")
    
    # ODO filter
    odo_col1, odo_col2 = st.sidebar.columns(2)
    with odo_col1:
        min_odo = st.number_input("Min ODO (mg/L)", value=None, placeholder="No limit")
    with odo_col2:
        max_odo = st.number_input("Max ODO (mg/L)", value=None, placeholder="No limit")
    
    # Pagination controls
    st.sidebar.subheader("📊 Display Options")
    limit = st.sidebar.slider("Records per page", 10, 1000, 100)
    show_raw_data = st.sidebar.checkbox("Show Raw Data Table", value=False)
    
    # Build API parameters
    api_params = {
        "start": start_date.isoformat(),
        "end": end_date.isoformat(),
        "limit": limit
    }
    
    # Add filters if specified
    if min_temp is not None:
        api_params["min_temp"] = min_temp
    if max_temp is not None:
        api_params["max_temp"] = max_temp
    if min_sal is not None:
        api_params["min_sal"] = min_sal
    if max_sal is not None:
        api_params["max_sal"] = max_sal
    if min_odo is not None:
        api_params["min_odo"] = min_odo
    if max_odo is not None:
        api_params["max_odo"] = max_odo
    
    # Fetch data
    with st.spinner("Loading data..."):
        observations_data = fetch_data("observations", api_params)
        stats_data = fetch_data("stats")
        summary_data = fetch_data("data/summary")
    
    if not observations_data:
        st.error("Failed to load data from API")
        return
    
    # Display summary
    if summary_data:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Records", f"{summary_data['total_records']:,}")
        with col2:
            st.metric("Current Query", f"{observations_data['count']:,}")
        with col3:
            if summary_data.get('date_range'):
                date_range = summary_data['date_range']
                st.metric("Date Range", f"{date_range['min_date'][:10]} to {date_range['max_date'][:10]}")
        with col4:
            st.metric("API Status", "🟢 Connected")
    
    # Convert to DataFrame
    df = pd.DataFrame(observations_data['items'])
    
    if df.empty:
        st.warning("No data found for the selected filters")
        return
    
    # Convert timestamp to datetime
    if 'timestamp' in df.columns:
        df['timestamp'] = pd.to_datetime(df['timestamp'])
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs(["📊 Visualizations", "🗺️ Map", "📈 Statistics", "🔍 Outliers", "📋 Raw Data"])
    
    with tab1:
        st.header("Data Visualizations")

        # Optimize data for large datasets
        plot_df = df.copy()
        if len(plot_df) > 1000:
            st.info(f"Displaying {len(plot_df):,} data points. Charts may be slower with large datasets.")

        # Line charts
        col1, col2 = st.columns(2)

        with col1:
            if 'temperature' in plot_df.columns and 'timestamp' in plot_df.columns:
                with st.spinner("Creating temperature chart..."):
                    fig_temp = px.line(
                        plot_df, x='timestamp', y='temperature',
                        title='Temperature Over Time',
                        labels={'temperature': 'Temperature (°C)', 'timestamp': 'Time'},
                        render_mode='webgl' if len(plot_df) > 500 else 'svg'  # WebGL for large datasets
                    )
                    fig_temp.update_layout(height=400, hovermode='x unified')
                    st.plotly_chart(fig_temp, use_container_width=True, key='temp_line')

        with col2:
            if 'salinity' in plot_df.columns and 'timestamp' in plot_df.columns:
                with st.spinner("Creating salinity chart..."):
                    fig_sal = px.line(
                        plot_df, x='timestamp', y='salinity',
                        title='Salinity Over Time',
                        labels={'salinity': 'Salinity (ppt)', 'timestamp': 'Time'},
                        render_mode='webgl' if len(plot_df) > 500 else 'svg'
                    )
                    fig_sal.update_layout(height=400, hovermode='x unified')
                    st.plotly_chart(fig_sal, use_container_width=True, key='sal_line')

        # Histograms
        col3, col4 = st.columns(2)

        with col3:
            if 'temperature' in plot_df.columns:
                fig_temp_hist = px.histogram(
                    plot_df, x='temperature', nbins=30,
                    title='Temperature Distribution',
                    labels={'temperature': 'Temperature (°C)'}
                )
                fig_temp_hist.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_temp_hist, use_container_width=True, key='temp_hist')

        with col4:
            if 'salinity' in plot_df.columns:
                fig_sal_hist = px.histogram(
                    plot_df, x='salinity', nbins=30,
                    title='Salinity Distribution',
                    labels={'salinity': 'Salinity (ppt)'}
                )
                fig_sal_hist.update_layout(height=400, showlegend=False)
                st.plotly_chart(fig_sal_hist, use_container_width=True, key='sal_hist')

        # Scatter plots
        if 'temperature' in plot_df.columns and 'salinity' in plot_df.columns:
            color_col = 'odo' if 'odo' in plot_df.columns else None
            with st.spinner("Creating scatter plot..."):
                fig_scatter = px.scatter(
                    plot_df, x='temperature', y='salinity',
                    color=color_col,
                    title='Temperature vs Salinity',
                    labels={'temperature': 'Temperature (°C)', 'salinity': 'Salinity (ppt)'},
                    opacity=0.6,
                    render_mode='webgl' if len(plot_df) > 500 else 'svg'
                )
                if color_col:
                    fig_scatter.update_layout(coloraxis_colorbar_title_text=color_col.upper())
                fig_scatter.update_layout(height=500)
                st.plotly_chart(fig_scatter, use_container_width=True, key='scatter')
    
    with tab2:
        st.header("Geographic Map")
        
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Create map
            fig_map = px.scatter_mapbox(df, lat='latitude', lon='longitude',
                                      color='temperature' if 'temperature' in df.columns else None,
                                      size='odo' if 'odo' in df.columns else None,
                                      hover_data=['timestamp', 'temperature', 'salinity', 'odo'] if 'timestamp' in df.columns else None,
                                      mapbox_style="open-street-map",
                                      title="Water Quality Sampling Locations")
            
            fig_map.update_layout(
                height=600,
                mapbox=dict(
                    center=dict(lat=df['latitude'].mean(), lon=df['longitude'].mean()),
                    zoom=10
                )
            )
            st.plotly_chart(fig_map, use_container_width=True)
        else:
            st.warning("Latitude and longitude data not available")
    
    with tab3:
        st.header("Statistical Summary")
        
        if stats_data and 'statistics' in stats_data:
            stats = stats_data['statistics']
            
            # Create metrics for each parameter
            for param, stats_info in stats.items():
                if isinstance(stats_info, dict) and 'error' not in stats_info:
                    st.subheader(f"{param.title()} Statistics")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.metric("Count", f"{stats_info['count']:,}")
                    with col2:
                        st.metric("Mean", f"{stats_info['mean']:.2f}")
                    with col3:
                        st.metric("Min", f"{stats_info['min']:.2f}")
                    with col4:
                        st.metric("Max", f"{stats_info['max']:.2f}")
                    
                    # Percentiles
                    if 'percentiles' in stats_info:
                        st.write("**Percentiles:**")
                        perc_col1, perc_col2, perc_col3 = st.columns(3)
                        with perc_col1:
                            st.metric("25th", f"{stats_info['percentiles']['25%']:.2f}")
                        with perc_col2:
                            st.metric("50th (Median)", f"{stats_info['percentiles']['50%']:.2f}")
                        with perc_col3:
                            st.metric("75th", f"{stats_info['percentiles']['75%']:.2f}")
                    
                    st.divider()
        else:
            st.warning("Statistics not available")
    
    with tab4:
        st.header("Outlier Detection")
        
        # Outlier detection controls
        col1, col2, col3 = st.columns(3)
        with col1:
            outlier_field = st.selectbox("Field", ['temperature', 'salinity', 'odo', 'ph', 'depth'])
        with col2:
            outlier_method = st.selectbox("Method", ['iqr', 'zscore'])
        with col3:
            if outlier_method == 'iqr':
                k_value = st.number_input("IQR Multiplier (k)", value=1.5, min_value=0.1, max_value=5.0, step=0.1)
            else:
                z_threshold = st.number_input("Z-Score Threshold", value=3.0, min_value=1.0, max_value=5.0, step=0.1)
        
        if st.button("Detect Outliers"):
            outlier_params = {
                'field': outlier_field,
                'method': outlier_method
            }
            if outlier_method == 'iqr':
                outlier_params['k'] = k_value
            else:
                outlier_params['z_threshold'] = z_threshold
            
            outliers_data = fetch_data("outliers", outlier_params)
            
            if outliers_data:
                st.subheader(f"Outlier Detection Results for {outlier_field}")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Values", f"{outliers_data['total_values']:,}")
                with col2:
                    st.metric("Outliers Found", f"{outliers_data['outlier_count']:,}")
                with col3:
                    st.metric("Outlier %", f"{outliers_data['outlier_percentage']:.1f}%")
                
                if outliers_data['outliers']:
                    st.subheader("Outlier Details")
                    outliers_df = pd.DataFrame(outliers_data['outliers'])
                    st.dataframe(outliers_df, use_container_width=True)
                else:
                    st.success("No outliers detected!")
    
    with tab5:
        st.header("Raw Data")
        
        if show_raw_data:
            # Display raw data
            st.subheader(f"Data Table ({len(df)} records)")
            
            # Select columns to display
            available_cols = ['timestamp', 'latitude', 'longitude', 'temperature', 'salinity', 'odo', 'ph', 'depth']
            display_cols = [col for col in available_cols if col in df.columns]
            
            if display_cols:
                st.dataframe(df[display_cols], use_container_width=True)
            else:
                st.dataframe(df, use_container_width=True)
        else:
            st.info("Enable 'Show Raw Data Table' in the sidebar to view the data table")

if __name__ == "__main__":
    main()