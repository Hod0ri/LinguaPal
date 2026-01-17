# LinguaPal API Guide v1

## Base URL
```
http://localhost:8000/api/v1
```

## Response Format

All API responses follow a standardized format:

### Success Response
```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    // Response data here
  }
}
```

### Error Response
```json
{
  "success": false,
  "message": "Error message",
  "data": {
    "error_code": "ERROR_CODE"
  }
}
```

### Validation Error Response
```json
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "errors": {
      "field_name": ["Error message"]
    }
  }
}
```

## HTTP Status Codes

- `200 OK`: Successful GET, PATCH request
- `201 Created`: Successful POST request
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

## Authentication

Most endpoints require JWT authentication. Include the token in the Authorization header:

```http
Authorization: Bearer {access_token}
```

## API Endpoints

### 1. Authentication APIs

#### 1.1 Get Google OAuth Config
Get Google OAuth Client ID for frontend

**Endpoint:** `GET /api/v1/auth/google/config`

**Authentication:** Not required

**Response:**
```json
{
  "success": true,
  "message": "Google OAuth configuration retrieved",
  "data": {
    "client_id": "your-google-client-id"
  }
}
```

#### 1.2 Google Login
Login with Google OAuth ID token

**Endpoint:** `POST /api/v1/auth/google/login`

**Authentication:** Not required

**Request Body:**
```json
{
  "access_token": "google-id-token"
}
```

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "jwt-access-token",
    "refresh_token": "jwt-refresh-token",
    "user": {
      "id": 1,
      "email": "user@example.com",
      "username": "user",
      "profile_image": "https://...",
      "google_id": "123456789",
      "date_joined": "2026-01-17T12:00:00Z",
      "has_profile": true,
      "profile": {
        "id": 1,
        "user_email": "user@example.com",
        "nickname": "MyNickname",
        "country": {...},
        "learning_languages": [...],
        "created_at": "2026-01-17T12:00:00Z",
        "updated_at": "2026-01-17T12:00:00Z"
      }
    }
  }
}
```

**Error Responses:**
```json
// Invalid token (400)
{
  "success": false,
  "message": "Invalid token: ...",
  "data": {
    "error_code": "INVALID_TOKEN"
  }
}

// Token expired (400)
{
  "success": false,
  "message": "Token has expired",
  "data": {
    "error_code": "TOKEN_EXPIRED"
  }
}

// Too many requests (429)
{
  "success": false,
  "message": "Too many requests. Please try again later.",
  "data": {
    "error_code": "TOO_MANY_REQUESTS"
  }
}
```

### 2. User APIs

#### 2.1 Get Current User
Get currently logged-in user information

**Endpoint:** `GET /api/v1/users/me`

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "User information retrieved",
  "data": {
    "id": 1,
    "email": "user@example.com",
    "username": "user",
    "profile_image": "https://...",
    "google_id": "123456789",
    "date_joined": "2026-01-17T00:00:00Z",
    "has_profile": true,
    "profile": {
      "id": 1,
      "user_email": "user@example.com",
      "nickname": "MyNickname",
      "country": {
        "id": 1,
        "code": "KR",
        "name_ko": "대한민국",
        "name_en": "South Korea"
      },
      "learning_languages": [
        {
          "id": 1,
          "code": "en",
          "name_ko": "영어",
          "name_en": "English"
        }
      ],
      "created_at": "2026-01-17T12:00:00Z",
      "updated_at": "2026-01-17T12:00:00Z"
    }
  }
}
```

#### 2.2 Get User Profile
Get user profile information

**Endpoint:** `GET /api/v1/users/me/profile`

**Authentication:** Required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile retrieved",
  "data": {
    "id": 1,
    "user_email": "user@example.com",
    "nickname": "MyNickname",
    "country": {
      "id": 1,
      "code": "KR",
      "name_ko": "대한민국",
      "name_en": "South Korea"
    },
    "learning_languages": [
      {
        "id": 1,
        "code": "en",
        "name_ko": "영어",
        "name_en": "English"
      },
      {
        "id": 2,
        "code": "ja",
        "name_ko": "일본어",
        "name_en": "Japanese"
      }
    ],
    "created_at": "2026-01-17T12:00:00Z",
    "updated_at": "2026-01-17T12:00:00Z"
  }
}
```

**Error Response (404 Not Found):**
```json
{
  "success": false,
  "message": "Profile not found",
  "data": {
    "error_code": "PROFILE_NOT_FOUND"
  }
}
```

#### 2.3 Create User Profile
Create a new user profile

**Endpoint:** `POST /api/v1/users/me/profile`

**Authentication:** Required

**Request Body:**
```json
{
  "nickname": "MyNickname",
  "country": 1,
  "learning_language_ids": [1, 2, 3]
}
```

**Success Response (201 Created):**
```json
{
  "success": true,
  "message": "Profile created successfully",
  "data": {
    "id": 1,
    "user_email": "user@example.com",
    "nickname": "MyNickname",
    "country": {
      "id": 1,
      "code": "KR",
      "name_ko": "대한민국",
      "name_en": "South Korea"
    },
    "learning_languages": [...],
    "created_at": "2026-01-17T12:00:00Z",
    "updated_at": "2026-01-17T12:00:00Z"
  }
}
```

**Error Responses:**
```json
// Profile already exists (400)
{
  "success": false,
  "message": "Profile already exists",
  "data": {
    "error_code": "PROFILE_ALREADY_EXISTS"
  }
}

// Validation error (400)
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "errors": {
      "nickname": ["This nickname is already in use."],
      "learning_language_ids": ["At least one language must be selected."]
    }
  }
}
```

#### 2.4 Update User Profile
Update user profile (nickname and learning languages only)

**Endpoint:** `PATCH /api/v1/users/me/profile`

**Authentication:** Required

**Request Body:**
```json
{
  "nickname": "NewNickname",
  "learning_language_ids": [1, 3, 4]
}
```

**Note:** You can update only nickname, only languages, or both. Country cannot be updated.

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "data": {
    "id": 1,
    "user_email": "user@example.com",
    "nickname": "NewNickname",
    "country": {...},
    "learning_languages": [...],
    "created_at": "2026-01-17T12:00:00Z",
    "updated_at": "2026-01-17T12:30:00Z"
  }
}
```

**Error Responses:**
```json
// Profile not found (404)
{
  "success": false,
  "message": "Profile not found",
  "data": {
    "error_code": "PROFILE_NOT_FOUND"
  }
}

// Validation error (400)
{
  "success": false,
  "message": "Validation failed",
  "data": {
    "errors": {
      "nickname": ["This nickname is already in use."]
    }
  }
}
```

### 3. Master Data APIs

#### 3.1 Get Languages
Get list of all available languages

**Endpoint:** `GET /api/v1/master/languages`

**Authentication:** Not required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Languages retrieved",
  "data": {
    "languages": [
      {
        "id": 1,
        "code": "en",
        "name_ko": "영어",
        "name_en": "English"
      },
      {
        "id": 2,
        "code": "ja",
        "name_ko": "일본어",
        "name_en": "Japanese"
      }
    ],
    "total_count": 14
  }
}
```

#### 3.2 Get Countries
Get list of all available countries

**Endpoint:** `GET /api/v1/master/countries`

**Authentication:** Not required

**Success Response (200 OK):**
```json
{
  "success": true,
  "message": "Countries retrieved",
  "data": {
    "countries": [
      {
        "id": 1,
        "code": "KR",
        "name_ko": "대한민국",
        "name_en": "South Korea"
      },
      {
        "id": 2,
        "code": "US",
        "name_ko": "미국",
        "name_en": "United States"
      }
    ],
    "total_count": 19
  }
}
```

## Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_TOKEN` | Invalid or malformed Google ID token |
| `TOKEN_EXPIRED` | Google ID token has expired |
| `TOKEN_ALREADY_USED` | Token has been used before (replay attack prevention) |
| `INVALID_AUDIENCE` | Token audience doesn't match client ID |
| `INVALID_ISSUER` | Token issuer is not Google |
| `EMAIL_NOT_VERIFIED` | Email not verified by Google |
| `UNAUTHORIZED` | Authentication required or invalid JWT |
| `TOO_MANY_REQUESTS` | Rate limit exceeded (10 requests per minute per IP) |
| `PROFILE_NOT_FOUND` | User profile does not exist |
| `PROFILE_ALREADY_EXISTS` | User already has a profile |
| `DUPLICATE_NICKNAME` | Nickname is already in use |
| `VALIDATION_ERROR` | Input validation failed |
| `INVALID_INPUT` | Invalid input data |
| `INTERNAL_ERROR` | Internal server error |
| `AUTHENTICATION_FAILED` | Authentication process failed |

## Validation Rules

### Nickname
- Minimum length: 2 characters
- Maximum length: 50 characters
- Must be unique across all users

### Country
- Required when creating profile
- Cannot be changed after profile creation
- Must be a valid country ID from master data

### Learning Languages
- At least 1 language required
- Multiple languages can be selected
- Can be updated anytime
- Must be valid language IDs from master data

## Rate Limiting

Google login endpoint is rate-limited to **10 requests per minute per IP address**.

When rate limit is exceeded, you will receive:
```json
{
  "success": false,
  "message": "Too many requests. Please try again later.",
  "data": {
    "error_code": "TOO_MANY_REQUESTS"
  }
}
```
HTTP Status: `429 Too Many Requests`

## Google Cloud Console Setup

### Required Settings

1. **Authorized JavaScript origins**:
   ```
   http://localhost:3000
   http://localhost:8000
   ```

2. **Authorized redirect URIs** (if needed):
   ```
   http://localhost:3000
   http://localhost:8000
   ```

## Usage Examples

### Example 1: Complete User Registration Flow

```javascript
// 1. Get Google config
const configResponse = await fetch('http://localhost:8000/api/v1/auth/google/config');
const config = await configResponse.json();
// config.data.client_id

// 2. User logs in with Google (frontend)
// ... Google Sign-In popup ...
// Receive Google ID token

// 3. Send token to backend
const loginResponse = await fetch('http://localhost:8000/api/v1/auth/google/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ access_token: googleIdToken })
});
const loginResult = await loginResponse.json();

if (loginResult.success) {
  const accessToken = loginResult.data.access_token;
  const hasProfile = loginResult.data.user.has_profile;

  if (!hasProfile) {
    // 4. Create profile
    const profileResponse = await fetch('http://localhost:8000/api/v1/users/me/profile', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      },
      body: JSON.stringify({
        nickname: 'MyNickname',
        country: 1,
        learning_language_ids: [1, 2]
      })
    });
    const profileResult = await profileResponse.json();

    if (profileResult.success) {
      console.log('Profile created:', profileResult.data);
    }
  }
}
```

### Example 2: Update Profile

```javascript
const token = localStorage.getItem('access_token');

const response = await fetch('http://localhost:8000/api/v1/users/me/profile', {
  method: 'PATCH',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    nickname: 'NewNickname',
    learning_language_ids: [1, 3, 4]
  })
});

const result = await response.json();

if (result.success) {
  console.log('Profile updated:', result.data);
} else {
  console.error('Error:', result.message);
  if (result.data.errors) {
    console.error('Validation errors:', result.data.errors);
  }
}
```

## Testing

### Using curl

```bash
# Get Google config
curl http://localhost:8000/api/v1/auth/google/config

# Get languages
curl http://localhost:8000/api/v1/master/languages

# Get current user (with authentication)
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     http://localhost:8000/api/v1/users/me

# Create profile
curl -X POST \
     -H "Authorization: Bearer YOUR_JWT_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"nickname":"Test","country":1,"learning_language_ids":[1,2]}' \
     http://localhost:8000/api/v1/users/me/profile
```

### Using Test Frontend

1. Start HTTP server for test pages:
   ```bash
   cd test_frontend
   python -m http.server 3000
   ```

2. Open browser:
   ```
   http://localhost:3000
   ```

3. Test flow:
   - Click "Google Login" → Login with Google
   - Click "Profile Management" → Create/Update profile

## Initial Data Setup

### Load Master Data (Languages & Countries)

The system needs initial language and country data before users can create profiles.

**Load initial data:**
```bash
# In Docker container
docker-compose -f docker/docker-compose.dev.yml exec web python manage.py load_initial_data

# Local development
python manage.py load_initial_data
```

This command will:
- ✅ Create 4 basic languages: Korean, English, Japanese, Spanish
- ✅ Fetch all countries (~250) from [REST Countries API](https://restcountries.com/) with Korean translations
- ✅ Update existing data if run again

**Skip country fetching (languages only):**
```bash
python manage.py load_initial_data --skip-countries
```

**Adding more languages:**

Admins can add more languages through the Django Admin panel:
1. Go to `/admin/accounts/language/`
2. Click "Add Language"
3. Fill in: code (e.g., 'fr'), name_ko ('프랑스어'), name_en ('French')

## Migration from Old API

If you're migrating from the old API (`/api/accounts/*`), see [API_MIGRATION_GUIDE.md](test_frontend/API_MIGRATION_GUIDE.md) for detailed migration instructions.

## Changelog

### v1 (2026-01-17)
- Standardized response format with `success`, `message`, `data`
- RESTful URI structure: `/api/v1/{resource}/{action}`
- All messages in English
- Added error codes for better error handling
- Added `total_count` to list endpoints
- Changed token field names: `access` → `access_token`, `refresh` → `refresh_token`
- Master data endpoints return data in nested structure
- Improved error responses with validation details
