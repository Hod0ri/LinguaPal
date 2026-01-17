# API Migration Guide - v1

## Response Format Changes

### Before (Old Format)
```javascript
// Success
const data = await response.json();
// data = { id: 1, nickname: "test", ... }

// Error
const error = await response.json();
// error = { error: "Profile not found" }
```

### After (New Format v1)
```javascript
// Success
const result = await response.json();
// result = {
//   success: true,
//   message: "Profile retrieved",
//   data: { id: 1, nickname: "test", ... }
// }

// Error
const result = await response.json();
// result = {
//   success: false,
//   message: "Profile not found",
//   data: { error_code: "PROFILE_NOT_FOUND" }
// }
```

## Endpoint Changes

| Old Endpoint | New Endpoint (v1) |
|--------------|-------------------|
| `/api/accounts/google/config/` | `/api/v1/auth/google/config` |
| `/api/accounts/google/login/` | `/api/v1/auth/google/login` |
| `/api/accounts/me/` | `/api/v1/users/me` |
| `/api/accounts/profile/` | `/api/v1/users/me/profile` |
| `/api/accounts/languages/` | `/api/v1/master/languages` |
| `/api/accounts/countries/` | `/api/v1/master/countries` |

## Code Update Examples

### 1. Google Login

**Before:**
```javascript
const response = await fetch('http://localhost:8000/api/accounts/google/login/', {
    method: 'POST',
    body: JSON.stringify({ access_token: token })
});
const data = await response.json();

if (response.ok) {
    const accessToken = data.access;  // Direct access
}
```

**After:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/auth/google/login', {
    method: 'POST',
    body: JSON.stringify({ access_token: token })
});
const result = await response.json();

if (result.success) {
    const accessToken = result.data.access_token;  // Access through data
}
```

### 2. Profile Get

**Before:**
```javascript
const response = await fetch('http://localhost:8000/api/accounts/profile/', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const profile = await response.json();

if (response.ok) {
    console.log(profile.nickname);  // Direct access
}
```

**After:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/users/me/profile', {
    headers: { 'Authorization': `Bearer ${token}` }
});
const result = await response.json();

if (result.success) {
    console.log(result.data.nickname);  // Access through data
}
```

### 3. Languages List

**Before:**
```javascript
const response = await fetch('http://localhost:8000/api/accounts/languages/');
const languages = await response.json();
// languages = [{ id: 1, code: "en", ... }, ...]
```

**After:**
```javascript
const response = await fetch('http://localhost:8000/api/v1/master/languages');
const result = await response.json();

if (result.success) {
    const languages = result.data.languages;  // Array in data.languages
    const total = result.data.total_count;
}
```

### 4. Error Handling

**Before:**
```javascript
try {
    const response = await fetch(url);
    const data = await response.json();

    if (response.ok) {
        // Success
    } else {
        console.error(data.error);  // { error: "message" }
    }
} catch (error) {
    console.error(error);
}
```

**After:**
```javascript
try {
    const response = await fetch(url);
    const result = await response.json();

    if (result.success) {
        // Success
        console.log(result.data);
    } else {
        // Error
        console.error(result.message);  // Error message
        console.error(result.data.error_code);  // Error code
    }
} catch (error) {
    console.error(error);
}
```

### 5. Validation Errors

**Before:**
```javascript
// Response (400)
{
  "nickname": ["This nickname is already in use."],
  "learning_language_ids": ["At least one language must be selected."]
}
```

**After:**
```javascript
// Response (400)
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

## Quick Fix for Existing Code

### Pattern 1: Simple Data Access
```javascript
// Old
const data = await response.json();
console.log(data.nickname);

// New
const result = await response.json();
console.log(result.data.nickname);
```

### Pattern 2: Array Access (Languages/Countries)
```javascript
// Old
const languages = await response.json();
languages.forEach(lang => ...)

// New
const result = await response.json();
result.data.languages.forEach(lang => ...)
```

### Pattern 3: Error Handling
```javascript
// Old
if (response.ok) {
    const data = await response.json();
} else {
    const error = await response.json();
    alert(error.error);
}

// New
const result = await response.json();
if (result.success) {
    // Use result.data
} else {
    alert(result.message);
}
```

## Error Codes Reference

| Error Code | Description |
|------------|-------------|
| `INVALID_TOKEN` | Invalid or malformed token |
| `TOKEN_EXPIRED` | Token has expired |
| `TOKEN_ALREADY_USED` | Token has been used before |
| `INVALID_AUDIENCE` | Token audience mismatch |
| `INVALID_ISSUER` | Token issuer invalid |
| `EMAIL_NOT_VERIFIED` | Email not verified by Google |
| `UNAUTHORIZED` | Unauthorized access |
| `TOO_MANY_REQUESTS` | Rate limit exceeded |
| `PROFILE_NOT_FOUND` | Profile does not exist |
| `PROFILE_ALREADY_EXISTS` | Profile already created |
| `DUPLICATE_NICKNAME` | Nickname already in use |
| `VALIDATION_ERROR` | Validation failed |
| `INVALID_INPUT` | Invalid input data |
| `INTERNAL_ERROR` | Server error |
| `AUTHENTICATION_FAILED` | Authentication failed |
