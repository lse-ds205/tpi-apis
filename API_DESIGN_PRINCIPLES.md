# API Design Principles: The Ten Commandments of Parameter Usage

## Introduction

This document establishes the core principles for consistent parameter usage across our API endpoints. These principles are designed to ensure intuitive, maintainable, and developer-friendly APIs that follow industry best practices. By adhering to these guidelines, we aim to create a unified experience for API consumers while maintaining the flexibility needed for diverse use cases.

The following "Ten Commandments" represent our commitment to thoughtful API design, specifically focusing on the usage of path and query parameters. These principles are based on extensive research of industry best practices and are tailored to our specific needs as a carbon assessment platform.

## The Ten Commandments of API Parameter Design

### 1. Resource Identification Through Path Parameters

Path parameters shall be used exclusively for identifying specific resources or collections of resources. They represent the hierarchical structure of our data model and provide a clear, intuitive way to navigate our API.

**Example:**
- `/cp/companies/{company_id}` - Identifies a specific company
- `/mq/assessments/{assessment_id}` - Identifies a specific assessment

**Rationale:** Path parameters improve URL readability and make the API self-documenting. They clearly communicate the resource being accessed, making the API more intuitive for developers to understand and use.

### 2. Optional Behavior Modification Through Query Parameters

Query parameters shall be used for optional modifications to the request, such as filtering, sorting, pagination, and specifying response format or fields. They should never be required for basic resource access.

**Example:**
- `/cp/companies?sector=energy&region=europe` - Filters companies by sector and region
- `/mq/assessments?sort=date&order=desc&page=2&limit=20` - Sorts and paginates assessment results

**Rationale:** Query parameters are designed to be optional by nature. Keeping them optional ensures backward compatibility when new parameters are added and provides flexibility for different use cases.

### 3. Consistent Parameter Naming Conventions

Parameter names shall follow consistent naming conventions across all endpoints. Use camelCase for query parameters and snake_case for path parameters. Parameter names should be descriptive, concise, and avoid abbreviations unless they are widely understood.

**Example:**
- Path: `/cp/companies/{company_id}/assessments/{assessment_id}`
- Query: `/mq/assessments?sortBy=date&orderDirection=desc`

**Rationale:** Consistent naming conventions reduce cognitive load for API consumers and make the API more predictable. This improves developer experience and reduces the likelihood of errors.

### 4. Hierarchical Resource Relationships Through Nested Paths

Nested resources shall be represented through hierarchical path structures, clearly indicating parent-child relationships between resources.

**Example:**
- `/cp/companies/{company_id}/assessments` - All assessments for a specific company
- `/cp/companies/{company_id}/assessments/{assessment_id}` - A specific assessment for a specific company

**Rationale:** Hierarchical paths naturally express the relationships between resources, making the API more intuitive and easier to understand. This approach aligns with REST principles and improves discoverability.

### 5. Standardized Query Parameter Patterns for Common Operations

Common operations shall use standardized query parameter patterns across all endpoints:

- Pagination: `page` and `limit` or `offset` and `limit`
- Sorting: `sortBy` and `orderDirection` (values: `asc` or `desc`)
- Filtering: parameter name matching the field being filtered
- Field selection: `fields` with comma-separated values
- Search: `q` for general search terms

**Example:**
- `/cp/companies?page=2&limit=20&sortBy=name&orderDirection=asc`
- `/mq/assessments?fields=id,date,score&sector=energy`

**Rationale:** Standardized patterns create a consistent experience across the API, making it more intuitive and reducing the learning curve for developers.

### 6. Secure Handling of Sensitive Parameters

Sensitive data shall never be included in URL parameters (path or query). Instead, use request headers or request body for authentication tokens, credentials, or other sensitive information.

**Example:**
- Use Authorization header for authentication tokens
- Use request body for password changes or sensitive operations

**Rationale:** URL parameters are visible in browser history, server logs, and referrer headers, making them inappropriate for sensitive data. This principle protects user privacy and security.

### 7. Array and Complex Data Handling

Arrays in query parameters shall be represented using one of the following consistent approaches across all endpoints:

1. Repeated parameters: `?color=red&color=blue`
2. Comma-separated values: `?colors=red,blue,green`

For complex filtering operations, use dot notation to represent relationships:
- `?price.gt=100&price.lt=200` (price greater than 100 and less than 200)

**Example:**
- `/cp/companies?sectors=energy,manufacturing&regions=europe,asia`
- `/mq/assessments?score.gt=75&date.gte=2023-01-01`

**Rationale:** Consistent handling of complex data types improves developer experience and ensures predictable behavior across the API.

### 8. Explicit Versioning Strategy

API versioning shall be handled through URL path prefixing rather than query parameters. All endpoints should include a version indicator to ensure backward compatibility as the API evolves.

**Example:**
- `/v1/cp/companies/{company_id}`
- `/v2/mq/assessments?sector=energy`

**Rationale:** Explicit versioning in the path makes it immediately clear which version of the API is being used and ensures that breaking changes don't affect existing clients.

### 9. Descriptive Error Responses for Parameter Issues

All parameter validation errors shall return descriptive error messages that clearly indicate which parameter failed validation and why. HTTP status code 400 (Bad Request) should be used for invalid parameters.

**Example:**
```json
{
  "error": "Invalid parameter",
  "message": "The 'limit' parameter must be a positive integer less than or equal to 100",
  "parameter": "limit",
  "value": "500"
}
```

**Rationale:** Clear error messages help developers quickly identify and fix issues with their API requests, improving the overall developer experience.

### 10. Documentation and Examples for All Parameters

All parameters shall be thoroughly documented with:
- Clear description of purpose
- Data type and format
- Constraints or validation rules
- Default values
- Examples of valid usage

**Example:**
```
GET /cp/companies

Query Parameters:
- sector (string, optional): Filter by industry sector. Example: "energy"
- region (string, optional): Filter by geographic region. Example: "europe"
- page (integer, optional): Page number for pagination, starting from 1. Default: 1
- limit (integer, optional): Number of results per page, max 100. Default: 20
```

**Rationale:** Comprehensive documentation reduces the learning curve for new developers and serves as a reference for experienced users, improving the overall usability of the API.

## Implementation Guidelines

When implementing these principles, consider the following:

1. **Consistency is key**: Apply these principles uniformly across all endpoints.
2. **Backward compatibility**: Consider existing clients when making changes.
3. **Developer experience**: Always prioritize making the API intuitive and easy to use.
4. **Performance implications**: Be mindful of how parameter choices affect caching and performance.
5. **Testability**: Ensure all parameter combinations can be easily tested.

## References

These principles are based on research from the following sources:

1. Apidog Blog: "When to Select Path Parameters VS Query Parameters?" (May 13, 2025)
   https://apidog.com/blog/path-param-vs-query-param/

2. Moesif Blog: "REST API Design Best Practices for Parameter and Query String Usage" (March 31, 2022)
   https://www.moesif.com/blog/technical/api-design/REST-API-Design-Best-Practices-for-Parameters-and-Query-String-Usage/

3. Dev.to: "Path vs. Query Parameters: Choosing the Right Approach for API Requests" (September 8, 2024)
   https://dev.to/farhatsharifh/path-vs-query-parameters-choosing-the-right-approach-for-api-requests-2lah

## Conclusion

By following these ten principles, we aim to create a consistent, intuitive, and developer-friendly API that stands the test of time. These guidelines should be considered during the design of new endpoints and when refactoring existing ones to ensure a cohesive experience across our entire API surface.
