#!/bin/bash
# Cross-platform setup script for Water Quality Data Pipeline
# Works on macOS, Linux, and Windows (via Git Bash)

echo "========================================="
echo "Water Quality Data Pipeline Setup"
echo "========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Found Python $python_version"

# Check if Python version is 3.9 or higher
required_version="3.9"
if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "ERROR: Python 3.9 or higher is required"
    echo "Please install Python 3.9+ from https://www.python.org/downloads/"
    exit 1
fi

echo "✓ Python version is compatible"
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d ".venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    source .venv/Scripts/activate
else
    # macOS and Linux
    source .venv/bin/activate
fi
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo "✓ All dependencies installed successfully"
else
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

# Run data cleaning
echo "Processing data..."
python data_cleaning.py
if [ $? -eq 0 ]; then
    echo "✓ Data cleaned successfully"
else
    echo "ERROR: Data cleaning failed"
    exit 1
fi
echo ""

# Setup database
echo "Setting up database..."
python database_setup.py
if [ $? -eq 0 ]; then
    echo "✓ Database setup complete"
else
    echo "ERROR: Database setup failed"
    exit 1
fi
echo ""

echo "========================================="
echo "Setup Complete!"
echo "========================================="
echo ""
echo "To start the application:"
echo ""
echo "1. Activate virtual environment:"
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    echo "   .venv\\Scripts\\activate  (Windows)"
else
    echo "   source .venv/bin/activate  (macOS/Linux)"
fi
echo ""
echo "2. Start the API server:"
echo "   python api/flaskAPI.py"
echo ""
echo "3. In a new terminal, start the dashboard:"
echo "   streamlit run client/streamlit_client.py"
echo ""
echo "4. Open your browser to:"
echo "   http://localhost:8501"
echo ""