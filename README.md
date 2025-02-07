# ASCOR API

Welcome to the ASCOR API repository! This project is part of the [DS205 course](https://lse-dsi.github.io/DS205) and is designed to help you build and deploy APIs for analysing and serving the ASCOR dataset.

## Getting Started

### 1. Clone the Repository
To get started, clone this repository to your local machine:
```bash
git clone https://github.com/lse-ds205/ascor-api.git
cd ascor-api
```

### 2. (Optional but Recommended) Create a Virtual Environment

First of all, ensure you have Python 3.10+ installed.

It is recommended to create a virtual environment to manage dependencies for this project. You can create a virtual environment using the following command:

```bash
python -m venv ascor-env
```

Then, whenever you are running the project, activate the virtual environment using the following command:

```bash
# If on Mac or Linux (e.g. Nuvolos)
source ascor-env/bin/activate

# If on Windows
ascor-env\Scripts\activate
```

You can configure VS Code to always use this virtual environment by Ctrl + P and then `Python: Select Interpreter` and choose the `ascor-env` folder.


### 3. Install Dependencies

Ensure you have Python 3.10+ installed. Use the following command to install all required dependencies:

```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI App
Navigate to the `v1/` folder and start the server:
```bash
cd v1
uvicorn app:app --reload
```

Visit `http://127.0.0.1:8000` in your browser to test the default endpoint. You can explore the interactive API documentation at `http://127.0.0.1:8000/docs`.


## Collaborator Access

Students who are currently enrolled in the DS205 course (or auditing) are eligible to contribute to this repository. To be granted push permission on this repository, please send a message to Jon on Slack with your GitHub username. Once approved, you'll receive an invite to contribute.

## Need Help?
For issues or questions:
- Post in the `#help` channel on Slack.
- Check out the [FastAPI Documentation](https://fastapi.tiangolo.com/).
- Contact Jon directly if you face persistent issues.
