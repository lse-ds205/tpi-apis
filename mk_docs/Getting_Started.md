# Getting Started with TPI Assessment API

This guide will walk you through everything you need to know to get the TPI Assessment API and its documentation up and running on your local machine.

## What You'll Need

Before we begin, make sure you have the following installed on your system:

- **Python 3.10 or higher** - Check your version with `python --version` or `python3 --version`
- **pip (Python package manager)** - Verify installation with `pip --version`

## Steps

### Step 1: Set Up Your Environment

#### Create a Virtual Environment

First, create an isolated Python environment for this project. This keeps your project dependencies separate from other Python projects.

```bash
python -m venv tpi-env
```

#### Activate Your Virtual Environment

Now activate the environment you just created:

**On Mac/Linux (including Nuvolos):**
```bash
source tpi-env/bin/activate
```

**On Windows:**
```bash
tpi-env\Scripts\activate
```

> ⚠️ **Important**: You'll need to activate this virtual environment every time you work with the API. If you see `(tpi-env)` at the beginning of your terminal prompt, you know it's active.

### Step 2: Install Dependencies

With your virtual environment activated, install all required packages:

```bash
pip install -r requirements.txt
```

This command reads the `requirements.txt` file and installs FastAPI, MkDocs, pandas, and all other necessary libraries.

### Step 3: Configure Environment Variables

Create a `.env` file in your project's root directory (the same folder where `main.py` is located):

```bash
SECRET_KEY=your_secret_key_here
```

Replace `your_secret_key_here` with any random string. This is used for the experimental POST endpoints in the API.

**Example `.env` file:**
```
SECRET_KEY=somerandomstringherefornow
```

### Step 4: Start the Servers

> 📝 **Note**: You'll need to run both the FastAPI server and the MkDocs documentation server on different ports. We recommend opening two terminal windows or tabs for this.

#### Terminal 1: Start the FastAPI Server

Navigate to your project's root directory and run:

```bash
uvicorn main:app --reload
```

This will start the API server on port 8000. You should see output similar to:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

The `--reload` flag automatically restarts the server when you make code changes during development.

#### Terminal 2: Start the MkDocs Documentation Server

Open a new terminal window/tab, activate your virtual environment again, navigate to your project directory, and run:

```bash
mkdocs serve -a 127.0.0.1:8001
```

This will start the documentation server on port 8001. You should see output similar to:
```
INFO     -  Building documentation...
INFO     -  Cleaning site directory
INFO     -  Documentation built in X.XX seconds
INFO     -  [HH:MM:SS] Serving on http://127.0.0.1:8001/
```

### Step 5: Verify Everything Works

With both servers running, open your web browser and visit these URLs:

**FastAPI Server (Port 8000):**
- http://127.0.0.1:8000/ - Base API URL
- http://127.0.0.1:8000/docs - Swagger UI interface where you can test all API endpoints

**MkDocs Documentation Server (Port 8001):**
- http://127.0.0.1:8001/ - Full project documentation

> 💡 **Tip**: Keep both servers running while you work. The FastAPI server handles your API requests, while the MkDocs server provides comprehensive documentation.

## Understanding the API

### Your API Endpoints

The TPI Assessment API provides access to three main types of data:

- **ASCOR Assessments** - Sovereign climate-related opportunities and risks
- **Management Quality (MQ)** - Corporate climate governance assessments  
- **Carbon Performance (CP)** - Corporate carbon emissions performance
- **Company Assessments** - Climate related information about companies

### Testing Your First API Call

Once your FastAPI server is running, try making your first API call:

1. Go to http://127.0.0.1:8000/docs
2. Look for available endpoints in the interactive documentation
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint
5. Fill in any required parameters
6. Click "Execute" to see the response

### Stopping the Servers

When you're done working:

1. **Stop the FastAPI server**: Press `CTRL + C` in the first terminal
2. **Stop the MkDocs server**: Press `CTRL + C` in the second terminal

### Next Steps

Now that both servers are running:

1. **Browse the MkDocs Documentation** - Visit http://127.0.0.1:8001/ for comprehensive guides
2. **Test API Endpoints** - Visit http://127.0.0.1:8000/docs to interact with the API
3. **[Read the API Documentation](Overview_Documentation.md)** - Learn about request/response formats and parameters

## Troubleshooting

### Common Issues

**"Command not found" errors:**
- Make sure Python 3.10+ is installed
- Try using `python3` instead of `python` if you're on Mac/Linux

**Import errors:**
- Ensure your virtual environment is activated (you should see `(tpi-env)` in your terminal)
- Re-run the installation command:
  
  ```
  pip install -r requirements.txt
  ```

**Port already in use:**
- If port 8000 is busy (FastAPI), start the server on a different port:
  
  ```
  uvicorn main:app --reload --port 8002
  ```

- If port 8001 is busy (MkDocs), start the documentation on a different port:
  
  ```
  mkdocs serve -a 127.0.0.1:8002
  ```

**MkDocs not found:**
- Make sure MkDocs is included in your `requirements.txt`
- Install it manually if needed:
  
  ```
  pip install mkdocs
  ```

**Environment variables not loading:**
- Make sure your `.env` file is in the same directory as `main.py`
- Check that there are no spaces around the `=` sign in your `.env` file

---

**Ready to start using the API?** Make sure both servers are running, then explore the MkDocs documentation at http://127.0.0.1:8001/ and test the API endpoints at http://127.0.0.1:8000/docs.