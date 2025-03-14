# Contributing to ASCOR API

This guide will help you get started with contributing to the ASCOR API project.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/lse-ds205/ascor-api.git
cd ascor-api
```

### 2. Set Up Virtual Environment
It is recommended to create a virtual environment to manage dependencies for this project:

```bash
python -m venv ascor-env
```

Activate the virtual environment:
```bash
# If on Mac or Linux (e.g. Nuvolos)
source ascor-env/bin/activate

# If on Windows
ascor-env\Scripts\activate
```

You can configure VS Code to always use this virtual environment by:

1. Press `Ctrl + P` (or `Cmd + P` on Mac)
2. Type `Python: Select Interpreter`
3. Choose the `ascor-env` folder

### 3. Install Dependencies

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

## Contributing Guidelines

### 1. Getting Access

**General Public Contributors**

This is a public repository and anyone can send a pull request to the repository. If you don't have push access, you will have to [fork the repository](https://docs.github.com/en/get-started/quickstart/fork-a-repo) and send a pull request from your fork.

**DS205 Students**

Students who are currently enrolled in the <img src="./icons/DS205_2024_25_icon_200px.png" alt="Image Created with AI Designer" role="presentation" style="object-fit: cover;width:1em;height:1em;vertical-align: middle;padding-bottom: 0.2em;"/> [DS205 course](https://lse-dsi.github.io/DS205) (Winter Term 2024/2025) (or auditing) are eligible to contribute directly to this repository without the need for a fork.

To be granted push permission:

1. Send a message to Jon on Slack with your GitHub username
2. Once approved, you'll receive an invite to contribute

### 2. Making Changes

1. Create a new branch for your feature/fix
2. Make your changes
3. Write tests if applicable
4. Update documentation
5. Submit a pull request describing why you made the changes and how to test them

### 3. Code Style

- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings to functions and classes
- Keep functions focused and single-purpose

### 4. Testing

- Write unit tests for new features
- Ensure all tests pass before submitting PR
- Include integration tests for API endpoints

### 5. Documentation

- Update relevant documentation
- Add comments for complex logic
- Keep README.md up to date

## Contact

If you want to discuss new ideas or have questions, use the [Discussions](https://github.com/lse-ds205/ascor-api/discussions) feature on GitHub. To report bugs, use the [Issues](https://github.com/lse-ds205/ascor-api/issues) feature on GitHub.
