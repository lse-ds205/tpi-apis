# ASCOR API

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115.7-green.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)


Welcome to the ASCOR API repository!

This project, led by Dr [Jon Cardoso-Silva](https://jonjoncardoso.github.io) in collaboration with Sylvan Lutz, is part of the LSE Data Science Institute's <img src="./icons/DS205_2024_25_icon_200px.png" alt="Image Created with AI Designer" role="presentation" style="object-fit: cover;width:1em;height:1em;vertical-align: middle;padding-bottom: 0.2em;"/> [DS205 course](https://lse-dsi.github.io/DS205) (Winter Term 2024/2025) and is in collaboration with the [Transition Pathway Initiative Centre](https://www.transitionpathwayinitiative.org/) (TPI Centre). It provides a fully functional API for serving data from the [ASCOR](https://www.transitionpathwayinitiative.org/ascor)[^1] assessment framework developed by the TPI Centre.

**A partnership:**

<div style="display: flex; justify-content: top; vertical-align: middle; align-items: center; gap: 2em; margin: 2em 0;">
<a href="https://lse.ac.uk/dsi"><img src="./icons/LSE_DSI.png" alt="LSE Data Science Institute" role="presentation" style="object-fit: contain;height:3em;margin-right:2em"/></a>

<a href="https://www.transitionpathwayinitiative.org/"><img src="./icons/TPI.png" alt="Transition Pathway Initiative" role="presentation" style="object-fit: contain;height:3em;"/></a>

<a href="https://lse-dsi.github.io/DS205" style="align-items:middle"><img src="./icons/DS205_2024_25_icon_200px.png" alt="DS205 Students" role="presentation" style="object-fit: contain;height:3em;"><span style="display:block;float:right">DS205 students <br>(Winter Term 2024/25)</span></a>
</div>


[^1]: **ASCOR** stands for "**A**ssessing **S**overeign **C**limate-related **O**pportunities and **R**isks". You can read more about their methodology [here](https://www.transitionpathwayinitiative.org/publications/2024-ascor-framework-methodology-note-version-1-1).


## How to Run

After [setting up your Python environment](CONTRIBUTING.md#development-setup), you can run the API locally using the following command:

```bash
cd ascor-api

uvicorn v1.app:app --reload
```

This will start the API server on `http://127.0.0.1:8000`. You can then use the API by making requests to the endpoints documented in the API Documentation (visible at `http://127.0.0.1:8000/docs`).

## 🗄️ Data Model

(WIP)

## 📟 Contact

If you want to discuss new ideas or have questions, use the [Discussions](https://github.com/lse-ds205/ascor-api/discussions) feature on GitHub. To report bugs, use the [Issues](https://github.com/lse-ds205/ascor-api/issues) feature on GitHub.

As a <img src="./icons/DS205_2024_25_icon_200px.png" alt="Image Created with AI Designer" role="presentation" style="object-fit: cover;width:1em;height:1em;vertical-align: middle;padding-bottom: 0.2em;"/> [DS205 course](https://lse-dsi.github.io/DS205) (Winter Term 2024/2025) student, you can also contact Jon directly on Slack.

## 🤝 Contributing

We welcome contributions from DS205 students! Please see our [Contributing Guidelines](CONTRIBUTING.md) for detailed instructions on how to get started.

## 📝 License

This project is licensed under the MIT License. This means that you are free to use, modify, and distribute the code as long as you provide attribution to the original authors. We do not provide any warranty or guarantee of any kind, so use it at your own risk. See the [LICENSE](LICENSE) file for details.
