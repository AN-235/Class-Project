# Setup Guide - Water Quality Data Pipeline

This guide provides detailed setup instructions for **Windows**, **macOS**, and **Linux**.

## Prerequisites

### All Operating Systems
- **Python 3.9 or higher** (Python 3.9-3.13 supported)
- **Git** (for cloning the repository)
- **4GB RAM minimum**
- **1GB disk space**

### Install Python

#### Windows
1. Download Python from [python.org/downloads](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation:
   ```cmd
   python --version
   ```

#### macOS
```bash
# Using Homebrew (recommended)
brew install python3

# Or download from python.org
# Verify installation:
python3 --version
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
python3 --version
```

#### Linux (Fedora/RHEL)
```bash
sudo dnf install python3 python3-pip
python3 --version
```

---

## Quick Start (Automated Setup)

### Windows
1. Clone the repository:
   ```cmd
   git clone <repository-url>
   cd Class-Project
   ```

2. Run the setup script:
   ```cmd
   setup.bat
   ```

3. The script will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Clean the data
   - Set up the database

### macOS / Linux
1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd Class-Project
   ```

2. Run the setup script:
   ```bash
   ./setup.sh
   ```

3. The script will automatically:
   - Create a virtual environment
   - Install all dependencies
   - Clean the data
   - Set up the database

---

## Manual Setup

If you prefer manual installation or the automated script fails:

### Step 1: Clone Repository
```bash
git clone <repository-url>
cd Class-Project
```

### Step 2: Create Virtual Environment

#### Windows
```cmd
python -m venv .venv
.venv\Scripts\activate
```

#### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install Dependencies
```bash
# Upgrade pip first
pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

### Step 4: Process Data
```bash
python data_cleaning.py
```

### Step 5: Setup Database
```bash
python database_setup.py
```

---

## Running the Application

### Option 1: Run Both Services (Recommended for Development)

#### Terminal 1 - Start API Server
```bash
# Activate virtual environment first
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Start Flask API
python api/flaskAPI.py
```

The API will be available at: `http://localhost:5000` or `http://localhost:5002`

#### Terminal 2 - Start Dashboard
```bash
# Activate virtual environment first
source .venv/bin/activate  # macOS/Linux
.venv\Scripts\activate     # Windows

# Start Streamlit dashboard
streamlit run client/streamlit_client.py
```

The dashboard will be available at: `http://localhost:8501`

### Option 2: Run Services in Background

#### macOS / Linux
```bash
# Start API in background
nohup python api/flaskAPI.py > api.log 2>&1 &

# Start Streamlit in background
nohup streamlit run client/streamlit_client.py > streamlit.log 2>&1 &
```

#### Windows (PowerShell)
```powershell
# Start API in background
Start-Process python -ArgumentList "api/flaskAPI.py" -WindowStyle Hidden

# Start Streamlit in background
Start-Process streamlit -ArgumentList "run","client/streamlit_client.py" -WindowStyle Hidden
```

---

## Troubleshooting

### Issue: `python` command not found

**Solution:**
- On macOS/Linux, use `python3` instead of `python`
- On Windows, ensure Python is added to PATH during installation

### Issue: Permission denied when running setup.sh

**Solution (macOS/Linux):**
```bash
chmod +x setup.sh
./setup.sh
```

### Issue: Port already in use

**Solution:**
1. Check if another service is using the port:
   ```bash
   # macOS/Linux
   lsof -i :5000
   lsof -i :8501

   # Windows
   netstat -ano | findstr :5000
   netstat -ano | findstr :8501
   ```

2. Kill the process or change the port in the application code

### Issue: Package installation fails

**Solution:**
```bash
# Clear pip cache
pip cache purge

# Try installing again
pip install -r requirements.txt

# If specific package fails, try installing it individually
pip install <package-name> --no-cache-dir
```

### Issue: MongoDB connection errors

**Solution:**
The application automatically falls back to **mongomock** (in-memory database) if MongoDB is not installed. This is normal and the application will work fine.

To use real MongoDB:
1. Install MongoDB: [mongodb.com/try/download/community](https://www.mongodb.com/try/download/community)
2. Start MongoDB service
3. The application will automatically connect

### Issue: Virtual environment activation fails on Windows

**Solution:**
If you get an execution policy error:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Issue: Data files not found

**Solution:**
Ensure the `data/` directory contains the CSV files:
- 2021-dec16.csv
- 2021-oct21.csv
- 2022-nov16.csv
- 2022-oct7.csv

### Issue: Streamlit not opening in browser

**Solution:**
Manually open your browser and go to: `http://localhost:8501`

---

## OS-Specific Notes

### Windows
- Use `\` for file paths
- Use Command Prompt or PowerShell
- Git Bash also works for bash scripts
- Some packages may require Microsoft C++ Build Tools

### macOS
- Use `/` for file paths
- Xcode Command Line Tools may be required:
  ```bash
  xcode-select --install
  ```
- For better Streamlit performance:
  ```bash
  pip install watchdog
  ```

### Linux
- Use `/` for file paths
- May need to install additional system packages:
  ```bash
  # Ubuntu/Debian
  sudo apt install build-essential python3-dev

  # Fedora/RHEL
  sudo dnf install gcc python3-devel
  ```

---

## Verifying Installation

### Test API
```bash
# In a terminal with the API running
curl http://localhost:5000/api/health

# Or open in browser:
# http://localhost:5000/api/health
```

Expected response:
```json
{
  "status": "ok",
  "database": "connected",
  "timestamp": "2024-01-01T00:00:00.000000"
}
```

### Test Dashboard
Open browser to: `http://localhost:8501`

You should see the Water Quality Data Dashboard with visualizations.

---

## Deactivating Virtual Environment

When you're done working:
```bash
deactivate
```

---

## Getting Help

If you encounter issues:

1. Check this SETUP.md guide
2. Check the main README.md troubleshooting section
3. Ensure Python version is 3.9 or higher: `python --version`
4. Ensure virtual environment is activated (you should see `(.venv)` in terminal)
5. Try manual setup instead of automated scripts
6. Create an issue on GitHub with:
   - Your operating system
   - Python version
   - Error message
   - Steps you've tried

---

## Next Steps

After successful setup:

1. Review the [README.md](README.md) for API documentation
2. Explore the dashboard at `http://localhost:8501`
3. Try the API endpoints at `http://localhost:5000/api/`
4. Review the code in:
   - `data_cleaning.py` - Data processing
   - `database_setup.py` - Database configuration
   - `api/flaskAPI.py` - REST API
   - `client/streamlit_client.py` - Dashboard

---

**Happy coding!** 🚀