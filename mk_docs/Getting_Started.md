# Getting Started with TPI Assessment API

This guide will walk you through everything you need to know to get the TPI Assessment API up and running on your local machine.

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

This command reads the `requirements.txt` file and installs FastAPI, pandas, and all other necessary libraries.

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

### Step 4: Start the API Server

Navigate to your project's root directory and run:

```bash
uvicorn main:app --reload
```

You should see output similar to:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
```

The `--reload` flag automatically restarts the server when you make code changes during development.

### Step 5: Verify Everything Works

Open your web browser and visit these URLs to confirm the API is running:

**Base API URL:**
- http://127.0.0.1:8000/

**Interactive Documentation:**
- http://127.0.0.1:8000/docs - Swagger UI interface where you can test all API endpoints

## Understanding the API

### Your API Endpoints

The TPI Assessment API provides access to three main types of data:

- **ASCOR Assessments** - Sovereign climate-related opportunities and risks
- **Management Quality (MQ)** - Corporate climate governance assessments  
- **Carbon Performance (CP)** - Corporate carbon emissions performance
- **Company Assessments** - Climate related information about companies

### Testing Your First API Call

Once your server is running, try making your first API call:

1. Go to http://127.0.0.1:8000/docs
2. Look for available endpoints in the interactive documentation
3. Click on any endpoint to expand it
4. Click "Try it out" to test the endpoint
5. Fill in any required parameters
6. Click "Execute" to see the response

### Stopping the Server

When you're done working with the API, stop the server by pressing:

```
CTRL + C
```

in your terminal.

### Next Steps

Now that your API is running:

1. **[Read the API Documentation](Overview_Documentation.md)** - Learn about request/response formats and parameters
2. **Test Different Endpoints** - Visit http://127.0.0.1:8000/docs to see all available endpoints

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
- If port 8000 is busy, start the server on a different port:
  
  ```
  uvicorn main:app --reload --port 8001
  ```

**Environment variables not loading:**
- Make sure your `.env` file is in the same directory as `main.py`
- Check that there are no spaces around the `=` sign in your `.env` file

---

**Ready to start using the API?** Head over to the [Documentation Overview](Overview_Documentation.md) to learn about all available endpoints and how to use them effectively.