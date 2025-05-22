# 🔐 Authentication Flow 

This document outlines how authentication is implemented and used in the API using OAuth2 with password flow and Bearer tokens.

---

## 🛡️ Setup: Secure SECRET_KEY

Instead of hardcoding  `SECRET_KEY`, store it securely in a `.env` file and load it dynamically using `python-dotenv`.

### 🔧 `.env` file (added in .gitignore)

## 🔑 1. Get a Token (Login)

**Endpoint (using v1 as default version):**

```
POST /v1/auth/token
```

**Request (example from simulate dataset):**

```http
Content-Type: application/x-www-form-urlencoded

username=tom
password=tompassword
```

**Response:**

```json
{
  "access_token": "<JWT_TOKEN>",
  "token_type": "bearer"
}

---

## 📥 2. Use the Token

Include the token as a Bearer token in the `Authorization` header:

```
Authorization: Bearer <access_token>
```

🔹 On Swagger UI at /docs, use the `Authorize` button on the top right, enter the user name and password to access subsequent requests with authentication.

## 🏢 3. Access Protected Endpoint: `POST /auth/company`

**Endpoint example (using v1 as default version):**

```
POST /v1/auth/company
```

**Headers:**

```http
Authorization: Bearer <access_token>
Content-Type: application/json
```

**Request Body:**

```json
{
  "name": "Acme Corporation",
  "industry": "Tech",
  "size": 250
}
```

**Response:**

```json
{
  "message": "Company data received from tom.",
  "company": {
    "name": "Acme Corporation",
    "industry": "Tech",
    "size": 250
  }
}
```

---

## 🧪 Quick Test with `curl`

```bash
# 1. Get the token
curl -X POST http://127.0.0.1:8000/v1/auth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=tom&password=tompassword"

# 2. Call the protected /v1/auth/company route, enter the token generated in bracket under the Authorization header
curl -X POST http://127.0.0.1:8000/v1/auth/company \
  -H "Authorization: Bearer {Token}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp", "industry": "Energy", "size": 200}'
```

---

## ✅ Summary Flow

```text
Client
  │
  ├── POST /auth/token  →  get access_token
  │
  └── (send token in Authorization header)
         ↓
  └── POST /auth/company
         ↓
     ✅ Token validated, request body validated
```