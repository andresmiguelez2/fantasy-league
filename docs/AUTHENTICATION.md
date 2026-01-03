# Authentication Setup Guide

This guide explains how to set up and use the JWT authentication system for the Fantasy League application.

## Overview

The Fantasy League application uses JWT (JSON Web Signature) tokens for secure user authentication. This implementation includes:

- Password hashing with bcrypt
- JWT token generation and validation
- Protected routes in the frontend
- Stateless authentication (no session storage on server)

## Backend Setup

### 1. Install Dependencies

The required packages are already in `requirements.txt`:
- `pyjwt` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `python-multipart` - Form data handling

Install them with:
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables

**Important:** Set a secure JWT secret key in production:

```bash
export JWT_SECRET_KEY="your-secure-random-secret-key-here"
```

**Warning:** If you don't set this environment variable, the application will use an insecure default key and log a warning. This is only acceptable for development!

To generate a secure secret key, you can use:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 3. Database Setup

Run the database setup script to create the users table:

```bash
cd app
python aux/setup_auth_db.py
```

This script will:
- Create the `users` table in PostgreSQL
- Optionally migrate users from `/secrets/users.env` if it exists

#### Users Table Schema

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    player_id INTEGER REFERENCES player(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
```

### 4. Create Users

#### Option A: Migrate from File

If you have a `/secrets/users.env` file with the format:
```
username:password:player_id
```

The setup script will automatically migrate these users to the database.

#### Option B: Create Users Programmatically

```python
from aux.setup_auth_db import create_user

create_user("john_doe", "secure_password", player_id=1)
```

## Frontend Setup

The frontend authentication is already configured with:

1. **AuthContext** - Manages authentication state
2. **ProtectedRoute** - Guards routes requiring authentication
3. **Login Page** - User login form

No additional setup is required.

## API Endpoints

### Login
```
POST /auth/login
Content-Type: application/json

{
  "username": "john_doe",
  "password": "secure_password"
}

Response:
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "token_type": "bearer",
  "player_id": 1,
  "username": "john_doe"
}
```

### Get Current User
```
GET /auth/me
Authorization: Bearer <token>

Response:
{
  "id": 1,
  "username": "john_doe",
  "player_id": 1
}
```

### Logout
```
POST /auth/logout
Authorization: Bearer <token>
```

Note: Logout is primarily handled client-side by removing the token from localStorage.

## Usage

### Frontend Usage

#### Accessing Authentication State

```typescript
import { useAuth } from '@/contexts/AuthContext';

function MyComponent() {
  const { user, isAuthenticated, login, logout } = useAuth();
  
  if (!isAuthenticated) {
    return <div>Please log in</div>;
  }
  
  return <div>Welcome, {user.username}!</div>;
}
```

#### Protected Routes

Routes are automatically protected when wrapped with `<ProtectedRoute>`:

```typescript
<Route path="/squad" element={<ProtectedRoute><Squad /></ProtectedRoute>} />
```

### Backend Usage

#### Protecting Endpoints

Use the `get_current_user_from_token` dependency to protect endpoints:

```python
from server_requests.auth import get_current_user_from_token
from fastapi import Depends

@router.get("/protected-endpoint")
def protected_endpoint(current_user: dict = Depends(get_current_user_from_token)):
    return {"message": f"Hello, {current_user['username']}!"}
```

## Security Considerations

1. **JWT Secret Key**: Always use a strong, random secret key in production
2. **Token Expiration**: Tokens expire after 24 hours by default
3. **HTTPS**: Use HTTPS in production to protect tokens in transit
4. **Password Storage**: Passwords are hashed with bcrypt (industry standard)
5. **Token Storage**: Tokens are stored in localStorage (consider httpOnly cookies for enhanced security)

## Troubleshooting

### "JWT_SECRET_KEY environment variable not set"
Set the environment variable before starting the application.

### "User not found" or "Invalid password"
Check that:
1. The users table exists and contains users
2. Passwords are correctly hashed in the database
3. The username and password are correct

### "Invalid authentication credentials"
The token may be:
- Expired (valid for 24 hours)
- Malformed
- Generated with a different secret key

Try logging in again to get a new token.

## Development vs Production

### Development
- Default secret key with warning is acceptable
- HTTP is acceptable for localhost
- Token in localStorage is acceptable

### Production
- **Must** set JWT_SECRET_KEY environment variable
- **Must** use HTTPS
- Consider using httpOnly cookies instead of localStorage
- Consider implementing token refresh mechanism
- Consider implementing token blacklist for logout

## Testing

Run the authentication tests:

```bash
python -m unittest tests.test_auth -v
```

All tests should pass:
- Password hashing and verification
- JWT token creation and validation
- User authentication logic
