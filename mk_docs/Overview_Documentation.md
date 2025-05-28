# API Endpoints Overview

Welcome to the **v1** API Endpoints guide for the TPI Assessment API. This section is your centralized reference for every read-only route available under the `/v1` prefix. Here you will find:

- A concise catalog of all endpoint groups (ASCOR, Company, CP, MQ) and their individual operations.  
- Clear descriptions of each route’s intent, input parameters, and output shape—without the noise of installation, authentication, or internal data structures.  
- Consistent formatting across sections so you can quickly locate how to list resources, fetch single items, apply filters, and handle errors.  

Whether you are integrating TPI data into your application, prototyping dashboards, or building automated workflows, this overview ensures you understand:

1. **Who** each endpoint serves (sovereigns vs. companies).  
2. **What** data each group returns (country assessments, carbon alignments, governance scores).  
3. **How** to interact in a standard way—uniform URL patterns, pagination, filtering, and error semantics.  

Use this guide as your roadmap: first skim the high-level group summaries below, then dive into the detailed markdown pages for concrete parameter tables, `curl` examples, response schemas, and design notes. By following these conventions, you’ll integrate smoothly and avoid surprises as TPI evolves to future versions.  

--- 

## Versioning and Base URL 

* All endpoints live under the `/v1` prefix. 
* Versioning ensures that future changes (e.g. `/v2`) will not break existing integrations.

--- 

## Common Conventions 
1. **HTTP methods**
    * `GET` for all read-only operations.

2. **Path parameters**
    * Always lowercase and URL-safe (e.g. `acme_corp`, `france`).
    * Normalization is applied server-side (trim, lowercase, underscores).

3. **Query parameters & filtering**
    * Pagination: nearly every “list” endpoint supports `page` (1-based) and `per_page` (1–100).
    * Company filters (applies to Company, CP, MQ lists and histories):
    `geography`, `geography_code`, `sector`, `ca100_focus_company`, `large_medium_classification`, `isins`, `sedol`.
    * MQ-specific filters: `assessment_year`, `mq_levels`, `level`.
    * No filtering on the ASCOR “list countries” endpoint—only on the Company/CP/MQ groups.

4. **Response models**
    * Defined via Pydantic schemas.
    * Guarantee consistent field names, types, and default values.
    * Enables automatic Swagger/OpenAPI documentation.

5. **Error handling**
    * **404 Not Found** when a resource (country or company) does not exist.
    * **422 Unprocessable Entity** for invalid query values (e.g. bad MQ level).
    * **500 Internal Server Error** for any unexpected failure.
    * **503 Service Unavailable** when a required data column or file is missing.
    * All errors return `{ "detail": "…" }`.

6. **Rate limits**
    * Default: **100 requests/minute** per IP.
    * CP “latest” endpoint: stricter at **2 requests/minute** to curb heavy full-dataset scans.

---

### Endpoints

1. [**ASCOR Endpoints**](Ascor_EP.md)

    **Purpose:** Serve sovereign climate assessments (three pillars: EP, CP, CF) at the country level.

    * `GET /v1/countries`
    List all countries with any ASCOR data.
    * `GET /v1/country-data/{country}/{year}`
    Fetch pillar-and-indicator details for a single country & assessment year.

2. [**Company Endpoints**](Company_EP.md)

    **Purpose:** Expose combined Management Quality (MQ) & Carbon Performance (CP) scores for listed companies.

    * `GET /v1/companies`
    Paginated list of companies + latest assessment year + basic info.
    * `GET /v1/company/{company_id}`
    Latest MQ score, 2035 CP alignment, and emissions trend for one company.
    * `GET /v1/company/{company_id}/history`
    Full chronological MQ & CP record for one company.
    * `GET /v1/company/{company_id}/performance-comparison`
    Year-over-year comparison of the two most recent MQ & CP assessments.

3. [**CP Endpoints**](CP_EP.md)

    **Purpose:** Focus purely on decadal Carbon Performance metrics for each company.

    * `GET /v1/cp/latest`
    Latest alignment status (2025, 2027, 2035, 2050) for every company, paginated.
    * `GET /v1/cp/company/{company_id}`
    Entire CP time-series for one company.
    * `GET /v1/cp/company/{company_id}/alignment`
    Quick map of latest CP alignment by target year.
    * `GET /v1/cp/company/{company_id}/comparison`
    Compare the two most recent CP cycles for a specified company.

4. [**MQ Endpoints**](MQ_EP.md)

    **Purpose:** Deliver governance-focused STAR-based ratings (0–5) from successive MQ cycles.

    * `GET /v1/mq/latest`
    Latest STAR score per company, numeric-mapped and paginated.
    * `GET /v1/mq/methodology/{id}`
    All MQ ratings for a specific research methodology cycle.
    * `GET /v1/mq/trends/sector/{sector_id}`
    Sequence of MQ scores over time for companies in one sector.
