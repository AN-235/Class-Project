"""
Data cleaning module for water quality data.
Implements z-score outlier removal and data preprocessing.
"""

import pandas as pd
import numpy as np
import os
from pathlib import Path
from scipy import stats
import json


class WaterQualityDataCleaner:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.cleaned_data = None
        self.cleaning_report = {}
        
    def load_csv_files(self):
        """Load all CSV files from the data directory (optimized)."""
        # Skip already cleaned files
        csv_files = [f for f in self.data_dir.glob("*.csv")
                     if 'cleaned' not in f.name.lower()]

        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {self.data_dir}")

        dataframes = []
        total_rows = 0

        for file_path in csv_files:
            print(f"Loading {file_path.name}...")
            try:
                # Use low_memory=False to prevent dtype warnings
                # Use date parsing optimization
                df = pd.read_csv(file_path, low_memory=False)
                row_count = len(df)
                total_rows += row_count
                print(f"  Loaded {row_count:,} rows")
                dataframes.append(df)
            except Exception as e:
                print(f"  Warning: Failed to load {file_path.name}: {e}")
                continue

        if not dataframes:
            raise ValueError("No CSV files could be loaded successfully")

        # Combine all dataframes efficiently
        print("Combining dataframes...")
        combined_df = pd.concat(dataframes, ignore_index=True, copy=False)
        print(f"Loaded {len(combined_df):,} total rows from {len(dataframes)} files")

        # Memory optimization: delete intermediate dataframes
        del dataframes

        return combined_df
    
    def standardize_columns(self, df):
        """Standardize column names and create timestamp."""
        # Create a standardized timestamp column
        if 'Date' in df.columns and 'Time' in df.columns:
            # Combine date and time columns
            df['timestamp'] = pd.to_datetime(df['Date'] + ' ' + df['Time'], errors='coerce')
        elif 'Date m/d/y' in df.columns and 'Time hh:mm:ss' in df.columns:
            df['timestamp'] = pd.to_datetime(df['Date m/d/y'] + ' ' + df['Time hh:mm:ss'], errors='coerce')
        else:
            # Try to find any date/time columns
            date_cols = [col for col in df.columns if 'date' in col.lower() or 'time' in col.lower()]
            if date_cols:
                df['timestamp'] = pd.to_datetime(df[date_cols[0]], errors='coerce')
            else:
                # Create a dummy timestamp if none found
                df['timestamp'] = pd.date_range('2021-01-01', periods=len(df), freq='1min')
        
        # Standardize coordinate columns
        if 'Latitude' in df.columns:
            df['latitude'] = pd.to_numeric(df['Latitude'], errors='coerce')
        if 'Longitude' in df.columns:
            df['longitude'] = pd.to_numeric(df['Longitude'], errors='coerce')
        
        # Standardize water quality parameters
        if 'Temperature (c)' in df.columns:
            df['temperature'] = pd.to_numeric(df['Temperature (c)'], errors='coerce')
        elif 'Temp C' in df.columns:
            df['temperature'] = pd.to_numeric(df['Temp C'], errors='coerce')
        
        if 'Salinity (ppt)' in df.columns:
            df['salinity'] = pd.to_numeric(df['Salinity (ppt)'], errors='coerce')
        elif 'Sal ppt' in df.columns:
            df['salinity'] = pd.to_numeric(df['Sal ppt'], errors='coerce')
        
        if 'ODO mg/L' in df.columns:
            df['odo'] = pd.to_numeric(df['ODO mg/L'], errors='coerce')
        
        if 'pH' in df.columns:
            df['ph'] = pd.to_numeric(df['pH'], errors='coerce')
        
        if 'Total Water Column (m)' in df.columns:
            df['depth'] = pd.to_numeric(df['Total Water Column (m)'], errors='coerce')
        elif 'Depth feet' in df.columns:
            df['depth'] = pd.to_numeric(df['Depth feet'], errors='coerce') * 0.3048  # Convert feet to meters
        
        return df
    
    def clean_data_with_zscore(self, df, z_threshold=3.0):
        """Clean data using z-score method to remove outliers (optimized)."""
        print("Starting data cleaning with z-score method...")

        # Get numeric columns for outlier detection
        numeric_columns = ['temperature', 'salinity', 'odo', 'ph', 'depth']
        available_columns = [col for col in numeric_columns if col in df.columns]

        if not available_columns:
            print("No numeric columns found for outlier detection")
            return df, {}

        print(f"Checking outliers in columns: {available_columns}")

        # Vectorized z-score calculation for all columns at once
        outlier_mask = pd.Series(False, index=df.index)
        outlier_details = {}

        # Calculate z-scores for all available columns in one pass
        for col in available_columns:
            if col not in df.columns:
                continue

            # Get non-null values
            non_null_mask = df[col].notna()

            if non_null_mask.sum() == 0:
                continue

            # Vectorized z-score calculation (much faster than scipy.stats.zscore)
            col_data = df.loc[non_null_mask, col]
            mean = col_data.mean()
            std = col_data.std()

            if std == 0:  # Avoid division by zero
                continue

            # Calculate z-scores
            z_scores = np.abs((col_data - mean) / std)

            # Find outliers (|z| > threshold)
            col_outliers = z_scores > z_threshold
            outlier_count = col_outliers.sum()

            if outlier_count > 0:
                # Mark outliers in the main mask
                outlier_indices = col_data.index[col_outliers]
                outlier_mask.loc[outlier_indices] = True

                outlier_details[col] = {
                    'outlier_count': int(outlier_count),
                    'outlier_percentage': float(outlier_count / len(col_data) * 100),
                    'mean': float(mean),
                    'std': float(std)
                }

                print(f"  {col}: {outlier_count} outliers ({outlier_count/len(col_data)*100:.1f}%)")

        # Remove rows with outliers in any column
        original_count = len(df)
        cleaned_df = df.loc[~outlier_mask].copy()
        removed_count = original_count - len(cleaned_df)

        # Create cleaning report
        cleaning_report = {
            'original_rows': int(original_count),
            'rows_removed': int(removed_count),
            'rows_remaining': int(len(cleaned_df)),
            'removal_percentage': float(removed_count / original_count * 100) if original_count > 0 else 0,
            'outlier_details': outlier_details,
            'z_threshold': z_threshold
        }

        print(f"Data cleaning complete:")
        print(f"  Original rows: {original_count}")
        print(f"  Rows removed: {removed_count} ({removed_count/original_count*100:.1f}%)")
        print(f"  Rows remaining: {len(cleaned_df)}")

        # Memory optimization: explicitly delete large temporary objects
        del outlier_mask

        return cleaned_df, cleaning_report
    
    def process_all_data(self, z_threshold=3.0):
        """Load, standardize, and clean all data."""
        print("=== Water Quality Data Processing ===")
        
        # Load data
        raw_df = self.load_csv_files()
        
        # Standardize columns
        standardized_df = self.standardize_columns(raw_df)
        
        # Clean data
        cleaned_df, report = self.clean_data_with_zscore(standardized_df, z_threshold)
        
        # Store results
        self.cleaned_data = cleaned_df
        self.cleaning_report = report
        
        # Save cleaned data
        output_path = self.data_dir / "cleaned_water_quality_data.csv"
        cleaned_df.to_csv(output_path, index=False)
        print(f"Cleaned data saved to: {output_path}")
        
        # Save cleaning report
        report_path = self.data_dir / "cleaning_report.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"Cleaning report saved to: {report_path}")
        
        return cleaned_df, report
    
    def get_cleaning_summary(self):
        """Get a summary of the cleaning process."""
        if not self.cleaning_report:
            return "No cleaning has been performed yet."
        
        report = self.cleaning_report
        summary = f"""
Data Cleaning Summary:
- Original rows: {report['original_rows']:,}
- Rows removed: {report['rows_removed']:,} ({report['removal_percentage']:.1f}%)
- Rows remaining: {report['rows_remaining']:,}
- Z-score threshold: {report['z_threshold']}

Outlier details by column:
"""
        for col, details in report['outlier_details'].items():
            summary += f"- {col}: {details['outlier_count']} outliers ({details['outlier_percentage']:.1f}%)\n"
        
        return summary


if __name__ == "__main__":
    # Example usage
    cleaner = WaterQualityDataCleaner()
    cleaned_data, report = cleaner.process_all_data()
    print(cleaner.get_cleaning_summary())
