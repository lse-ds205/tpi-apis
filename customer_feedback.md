### Current changes needs (ORDER BY PRIORITY)
1. change from company_name to ISINs as unique identifier
2. new endpoints with filter for region and sector
3. add CP endpoint with assessment data and sectoral benchmark
4. add endpoint to serve banking data
5. serve graph
6. link datasets to allow for calling ASCOR indicators in a Country with companies from that country. 
7. other functionality like chatbot as discussed before

### Pull request that is useful
- `#43` improved error handling
- `#42` added more filter to CP and MP, may resolve task 3 above
- `#40` adding data handler to CP and MQ


### Pull request that might act as barrier
- `#37` the data dictionary and usage guiadance needs to be updated after our change
- `#36` rate limiting might slow things down


### **Reflection from First Meeting**

**Meeting Time:** 12th May, 15:15–15:45 BST  
**Meeting Goal:** Understand customer needs and outline the required steps to meet them

---

### **Key Questions Answered**

#### 1. What key use cases should this API support?  
(For example: listing metrics, company profiles, sector data, etc.)

- The goal is to help data users better filter and use the dataset for their own needs.
- The **primary endpoint** is **entity-level data** (Company or Country).
- This should be broken down into different methodologies:
  - **CP** and **MQ** for companies.
- Results should be served by entity with the associated metrics.
- Users should ideally be able to specify which metrics they're interested in (all or specific ones).  
  **Example:**  
  - All metrics for German companies.  
  - All level 4 MQ metrics and CP alignment for Chinese companies.

#### 2. Which datasets from the TPI website are we building against?  
(If multiple datasets are needed, how should the API handle interactions between them?)

- Focus: **CP** and **MQ** (potentially link with **ASCOR** and **Banking**, depending on scope and time).
- Ideally, datasets will be **linked by entity** and other identifiers.  
  **Example:**  
  - Link through the geography code to the ASCOR dataset, allowing users to download ASCOR indicators alongside companies headquartered in that jurisdiction.

#### 3. How will you query these endpoints?  
(What filters and parameters are required? How should the API handle missing/incomplete data?)

- The API should return a **“data not available”** or **relevant description** when data is missing.
- If a reason for missing data exists (e.g. insufficient company disclosure), it should be included in the response.

#### 4. Do you need chart images or raw data, or both?  
(If raw data is enough, which formats are preferred?)

- One of the **key goals** is to **include both graphs and underlying data** directly in the API.

---

### **List of Priorities After the Meeting**

1. Solve any remaining bugs that affect the rest of the work
2. Add filters for mass calls by region and sector.
3. Add the underlying CP assessment data for each company:
   - Use data from:
     - `CP Assessment.xlsx`
     - `CP Assessment Regional.xlsx`
     - Benchmarks from `Sector Benchmark.xlsx` (for Electric Utilities sector).
4. Use the data to create graphs on the website (see example at bottom of the page).
5. Add endpoints to serve **Banking data**.
6. Link datasets to allow:
   - Calling **ASCOR indicators** in a Country
   - Fetching companies headquartered in that country
7. Add other functionality as discussed and as time/interests allow, subject to **Jon's confirmation** (e.g. chatbot).

---

**Next Meeting Date Arranged:**  
**19th May, 14:30 – 15:30 BST**
