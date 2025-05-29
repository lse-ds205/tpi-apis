# Technical Report

## Project Overview
This project focused on improving the documentation, robustness, and usability of the Transition Pathway Initiative (API). The primary goals were to: 

* Create comprehensive and accessible API documentation using MkDocs and FastAPI.
* Merge recent pull requests and bug fixes, and refactor into the active codebase.

## Clients
* Transition Pathway Initiative (TPI)
    * Jon Cardoso-Silva (LSE DSI)
    * Sylvan Lutz (Grantham Research Institute)
    * Barry Ledeatte (LSE DSI)

## Team
* Coleman Cochran
* Urvi Gaur
* Defne Ece Yavuz

## Duration
**April - May 2025**


## Project Goals

### 1. Writing comprehensive documentation

The primary goal of this documentation was to create a clear, structured, and user-friendly reference for the legacy codebase behind the TPI Assessment API. This resource is intended to serve both as a technical guide for developers and as an onboarding tool for analysts or stakeholders with varying levels of familiarity with the code.

Through this documentation, any user should be able to: 
* Understand the endpoints, their errors, response structures, and any general design notes to highlight the features of the API. 
* Explore the endpoints via the embedded Swagger-UI. 

### 2. Merging pull requests

| Merged PR | Description                                                   |
|:---------:|---------------------------------------------------------------|
| #43       | Improve error handling across the API                         |
| #41       | Add a robust test suite to test CP & MQ endpoints            |
| #42       | Add more query params as filters to the endpoints            |
| #39       | Implement comprehensive logging system across the API        |
| #38       | Data Input Sanitisation for Consistent API Querying          |
| #37       | Create comprehensive data dictionary                         |
| #36       | Add rate limits to our endpoints with the slowapi package    |
| #35       | Add a proof-of-concept API Authentication to POST a company |


## Meeting Timeline

| Date | Meeting |
|------|---------|
| 29/05/2025 | Everyone <> Barry |
| 29/05/2025 | Everyone |
| 29/05/2025 | Urvi <> Sylvan |
| 28/05/2025 | Coleman <> Defne |
| 27/05/2025 | Coleman <> Barry |
| 27/05/2025 | Coleman <> Urvi |
| 23/05/2025 | Coleman <> Urvi |
| 15/05/2025 | Defne <> Jon |
| 10/05/2025 | Everyone |
| 09/05/2025 | Coleman <> Jon |
| 25/04/2025 | Everyone <> Sylvan |
| 16/04/2025 | Everyone |

## Tools Used

* **Development:** GitHub, VSCode, Python, FastAPI
Documentation: MkDocs, ReadTheDocs
* **Communication:** Slack, Zoom, Google Meet, WhatsApp
* **Debugging:** ChatGPT, pytest

## Technical Limitations

* **Legacy Design:** Refactoring was needed due to different coding logic and methods, specifically when merging pull requests
* **Rate Limiting Integration:** The `slowapi` package conflicted with certain middleware and required careful registration order
* **Environment Variable Constraints:** During testing, missing `.env` values (e.g., `SECRET_KEY`) caused breakages that had to be mocked
* **Incomplete Test Fixtures:** Some test cases relied on specific file paths and static data that was not consistently present; although these were somewhat resolved via mocking static paths, it is ideal that the data source is dynamic to ensure the API is future-proof

## Challenges Encountered

* **Merge Conflicts:** Required careful sequencing and conflict resolving across branches #24 to #34 to preserve data handling logic.
* **Lack of Documentation:** No prior documentation existed (aside from the automatically generated FastAPI one). We had to reverse-engineer logic and explain endpoint workings

## Personal Contributions

**Coleman**

My contributions to our final project was mainly setting up `mkdocs` and resolving `issue #31` (query path audit). Once I set `mkdocs` up on our branch, I created the landing page which explained the function of the api at a high level and created the `“Getting Started”` page, which detailed the required steps to run the api. For resolving `issue #31`, I conducted an audit of all the endpoints on the api to ensure they followed a uniform naming convention and were structured logically. Additionally, I created a markdown file called `API_Design_Principles.md` which explains how future endpoints should be crafted/organised. Beyond my primary tasks, I assisted Defne and Urvi and scheduled meetings with Jon and Sylvan and team meetings.

My main takeaway from this project could be summarised as the following: complexity compounds over itself. When dealing with an increasingly large codebase, the ability for things to go wrong and conflict increasingly becomes more probable and becomes harder to resolve. I encountered this issue firsthand when resolving `issue #31` (each time main was updated it required me to review/change my work). Additionally while working on the documentation side, our work was predicated on the work of others - meaning constant review and updates were necessary. I dealt with this problem by becoming much more comfortable with Github (tracking branches, changes, etc.) and by scheduling meetings with those who knew more than me about the api (Jon, Berry) and my teammates (who helped me get up to date on how the api functioned). I now feel more confident in my ability to work in a team on larger coding projects and specifically for creating informative documentation.


**Urvi**

My main contributions were writing the API endpoint documentation after all the merges and changes had been made to the base code. Some of the more detailed aspects of all of this were: 

* Writing up markdowns that explain all the endpoints 
* Investigating integration of swagger-ui into mkdocs and better ways to have a interactive API in the documentation 
* Editing and adding to the markdowns specific ‘try it out’ parts which, when run alongside the FastAPI, would let the user try out the API endpoints in real time

There are a lot of aspects that have ultimately led to the combination of this documentation and the codebase for the API. I think one of the most important aspects and learning curves for this entire project for me was collaborating through GitHub. I think coding, mostly, can be supplemented easily via LLMs and other tools online - however, it seems like collaborating on certain ideas, getting those ideas across to the team, and then actually working together on those ideas was the tougher bit. 

Another keypoint in all of this is the idea that all of the efforts from this project and especially the API building will actually have an ultimate use-case. Often assignments and summatives end up getting discarded after the final grade. However, the idea that ultimately whatever I am working on will be used by someone else in the future really got me thinking about the practicalities of my work. Alongside how easily interpretable it was.  

**Defne**

My main contribution to the project was updating and stabilizing the legacy codebase through merging most of the pre-existing pull requests. This involved carefully integrating multiple feature branches and resolving conflicting and overlapping updates to ensure a clean, functional and scalable main branch (I worked on the branch ‘dev’ before merging that to `main`). As part of this process, I updated outdated or conflicting logic, standardized data access layers, and ensured consistent API behaviour across endpoints.

Beyond the merge, as part of my Summative 1 feedback, I had already worked on improving error handling within the API. I further focused on this while merging, in order to fix immediate bugs (especially when running tests) but also to improve the API’s long-term maintainability and reliability on the developers’ side.

Working with Urvi and Coleman, we had structured, frequent meetings, to catch up everyone on team updates but also to work through or clarify issues one of us was facing. Additionally, we consulted Jon, Barry, and Sylvan for when we were unsure or unclear on how to proceed, which improved our quality of work and helped us gain a deeper understanding of the scope of our end products. Frequently collaborating through our branches and video calls, we managed to produce a comprehensive, robust product on both the client- and developer-facing sides, hitting all of our main goals and most of our side quests.

Overall, this project deepened my understanding of collaborative API development, version control at a large scale, and the importance of documentation and testing in building client-facing tools. It was a very rewarding experience (especially getting to work on an actual, real-life API and data, getting to solve real bugs and issues), which I believe will be immensely useful in my further education.

## Key Achievements

* ✅ Merged and stabilized 8 pull requests to branch ‘dev’

* ✅ Launched a live documentation site on mkdocs

* ✅ Standardized naming convention for present and future endpoint requests

## Recommendations for Future Development

* 🧪 Expand test suite for authenticated and error-prone edge cases
* 📈 Add performance monitoring and cache layer for large queries
* 📚 Migrate to OpenAPI 3.1 with stricter schema validation
* 🔁 Convert duplicated logic into shared decorators/middleware
* 💻 Fix endpoint and data source issues within the codebase that were out of this project’s scope

## Conclusion
This project was a successful addition to the TPI API. We stabilized routes, improved how data is accessed and served, and created clear, user-friendly documentation. The result is a more stable and accessible API that’s ready for wider use, that is built to grow, scale, and support transparent access to corporate climate transition data.
