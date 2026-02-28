# Design Document

## Overview

This design document outlines a production-ready JWT authentication system for a FastAPI backend and React TypeScript frontend. The system implements industry best practices including:

- **Access/Refresh Token Rotation**: Short-lived access tokens (15 minutes) with longer-lived refresh tokens (7 days) that rotate on each use
- **Secure Token Storage**: Access tokens in memory, refresh tokens in HttpOnly, Secure, SameSite=Strict cookies
- **Token Blacklisting**: Single-use refresh tokens with database-backed blacklist to prevent replay attacks
- **Password Security**: bcrypt hashing with cost factor 12, strong password requirements
- **Rate Limiting**: Protection against brute force attacks
- **Comprehensive Error Handling**: User-friendly messages without exposing sensitive information
- **Modern Frontend**: React Hook Form with Zod validation and shadcn/ui components

The architecture follows FastAPI's dependency injection pattern for authentication and uses Axios interceptors for automatic token refresh on the frontend.

## Architecture

### Backend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │ Auth Routes  │──────│ Dependencies │                     │
│  │              │      │              │                     │
│  │ /register    │      │ get_current_ │                     │
│  │ /login       │      │ user         │                     │
│  │ /refresh     │      │              │                     │
│  │ /logout      │      │ get_db       │                     │
│  │ /me          │      │              │                     │
│  └──────┬───────┘      └──────┬───────┘                     │
│         │                     │                              │
│         └─────────┬───────────┘                              │
│                   │                                          │
│         ┌─────────▼──────────┐                               │
│         │  Security Service  │                               │
│         │                    │                               │
│         │  - Token creation  │                               │
│         │  - Token validation│                               │
│         │  - Password hashing│                               │
│         │  - Token blacklist │                               │
│         └─────────┬──────────┘                               │
│                   │                                          │
│         ┌─────────▼──────────┐                               │
│         │   Database Layer   │                               │
│         │                    │                               │
│         │  - User model      │                               │
│         │  - RefreshToken    │                               │
│         │  - TokenBlacklist  │                               │
│         └────────────────────┘                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Frontend Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    React Application                         │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐      ┌──────────────┐                     │
│  │ Auth Pages   │──────│ Auth Store   │                     │
│  │              │      │ (Zustand)    │                     │
│  │ LoginPage    │      │              │                     │
│  │ SignupPage   │      │ - user       │                     │
│  │              │      │ - isAuth     │                     │
│  └──────┬───────┘      │ - login()    │                     │
│         │              │ - register() │                     │
│         │              │ - logout()   │                     │
│         │              └──────┬───────┘                     │
│         │                     │                              │
│         └─────────┬───────────┘                              │
│                   │                                          │
│         ┌─────────▼──────────┐                               │
│         │  Axios Instance    │                               │
│         │                    │                               │
│         │  Request           │                               │
│         │  Interceptor       │                               │
│         │  (Add token)       │                               │
│         │                    │                               │
│         │  Response          │                               │
│         │  Interceptor       │                               │
│         │  (Refresh on 401)  │                               │
│         └────────────────────┘                               │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Components and Interfaces

### Backend Components

#### 1. Database Models

**User Model** (`backend/app/models/user.py`)
```python
class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    hashed_password: Mapped[str] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
```

**RefreshToken Model** (`backend/app/models/token.py`)
```python
class RefreshToken(Base):
    __tablename__ = "refresh_tokens"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(Text, unique=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    expires_at: Mapped[datetime]
    created_at: Mapped[datetime]
    
    user: Mapped["User"] = relationship(back_populates="refresh_tokens")
```

**TokenBlacklist Model** (`backend/app/models/token.py`)
```python
class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    token: Mapped[str] = mapped_column(Text, unique=True, index=True)
    blacklisted_at: Mapped[datetime]
    expires_at: Mapped[datetime]
```

#### 2. Pydantic Schemas

**Auth Schemas** (`backend/app/schemas/auth.py`)
```python
class RegisterRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=255)
    password: str = Field(min_length=8)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    is_active: bool
```

#### 3. Security Service

**Token Management** (`backend/app/core/security.py`)
```python
# Constants
ACCESS_TOKEN_EXPIRE_MINUTES = 15
REFRESH_TOKEN_EXPIRE_DAYS = 7
ALGORITHM = "HS256"
COOKIE_NAME = "refresh_token"

# Functions
def create_access_token(data: dict) -> str
def create_refresh_token(data: dict) -> str
def decode_access_token(token: str) -> dict | None
def decode_refresh_token(token: str) -> dict | None
def hash_password(password: str) -> str
def verify_password(plain: str, hashed: str) -> bool
def validate_password_strength(password: str) -> bool
```

**Token Blacklist Service** (`backend/app/services/token_service.py`)
```python
async def add_to_blacklist(db: AsyncSession, token: str, expires_at: datetime)
async def is_blacklisted(db: AsyncSession, token: str) -> bool
async def cleanup_expired_tokens(db: AsyncSession)
async def store_refresh_token(db: AsyncSession, token: str, user_id: int, expires_at: datetime)
async def get_refresh_token(db: AsyncSession, token: str) -> RefreshToken | None
async def delete_refresh_token(db: AsyncSession, token: str)
async def delete_user_refresh_tokens(db: AsyncSession, user_id: int)
```

#### 4. Dependencies

**Authentication Dependencies** (`backend/app/api/dependencies.py`)
```python
async def get_current_user(
    token: str = Depends(OAuth2PasswordBearer(tokenUrl="/api/auth/login")),
    db: AsyncSession = Depends(get_db)
) -> User

async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User
```

#### 5. Auth Routes

**Endpoints** (`backend/app/api/routes/auth.py`)
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login with credentials
- `POST /api/auth/refresh` - Refresh access token
- `POST /api/auth/logout` - Logout and invalidate tokens
- `GET /api/auth/me` - Get current user info

### Frontend Components

#### 1. Axios Configuration

**API Client** (`frontendReact/src/lib/api.ts`)
```typescript
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add access token
api.interceptors.request.use((config) => {
  const token = useUserStore.getState().accessToken
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Response interceptor - handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config
    
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true
      
      try {
        const { data } = await axios.post('/api/auth/refresh', {}, {
          withCredentials: true
        })
        
        useUserStore.getState().setAccessToken(data.access_token)
        originalRequest.headers.Authorization = `Bearer ${data.access_token}`
        
        return api(originalRequest)
      } catch (refreshError) {
        useUserStore.getState().logout()
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }
    
    return Promise.reject(error)
  }
)
```

#### 2. Auth Store

**Zustand Store** (`frontendReact/src/stores/user-store.ts`)
```typescript
interface UserState {
  user: User | null
  accessToken: string | null
  isAuthenticated: boolean
  isLoading: boolean
  
  login: (email: string, password: string) => Promise<void>
  register: (email: string, name: string, password: string) => Promise<void>
  logout: () => Promise<void>
  checkSession: () => Promise<void>
  setAccessToken: (token: string) => void
}
```

#### 3. Auth Forms

**Login Form** (`frontendReact/src/pages/login-page.tsx`)
- Uses react-hook-form with Zod validation
- shadcn/ui Input, Button components
- Password visibility toggle
- Error handling and loading states

**Register Form** (`frontendReact/src/pages/signup-page.tsx`)
- Uses react-hook-form with Zod validation
- Password strength validation
- Confirm password matching
- shadcn/ui components

#### 4. Form Validation Schemas

**Zod Schemas** (`frontendReact/src/lib/validations/auth.ts`)
```typescript
const loginSchema = z.object({
  email: z.string().email('Invalid email address'),
  password: z.string().min(1, 'Password is required'),
})

const registerSchema = z.object({
  name: z.string().min(1, 'Name is required').max(255),
  email: z.string().email('Invalid email address'),
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain an uppercase letter')
    .regex(/[a-z]/, 'Password must contain a lowercase letter')
    .regex(/[0-9]/, 'Password must contain a number')
    .regex(/[^A-Za-z0-9]/, 'Password must contain a special character'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
})
```

## Data Models

### Database Schema

```sql
-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    hashed_password TEXT NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Refresh tokens table
CREATE TABLE refresh_tokens (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX idx_refresh_tokens_expires_at ON refresh_tokens(expires_at);

-- Token blacklist table
CREATE TABLE token_blacklist (
    id SERIAL PRIMARY KEY,
    token TEXT UNIQUE NOT NULL,
    blacklisted_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL
);

CREATE INDEX idx_token_blacklist_token ON token_blacklist(token);
CREATE INDEX idx_token_blacklist_expires_at ON token_blacklist(expires_at);
```

### JWT Token Structure

**Access Token Payload**
```json
{
  "sub": "user@example.com",
  "user_id": 123,
  "type": "access",
  "iat": 1234567890,
  "exp": 1234568790
}
```

**Refresh Token Payload**
```json
{
  "sub": "user@example.com",
  "user_id": 123,
  "type": "refresh",
  "jti": "unique-token-id",
  "iat": 1234567890,
  "exp": 1235172690
}
```


## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property Reflection

After analyzing all acceptance criteria, I identified several areas where properties can be consolidated:

- Password validation properties (1.2, 1.3) can be combined into a single comprehensive password validation property
- Token generation properties for registration and login (1.6, 2.5, 2.6) share similar validation logic
- Cookie security properties (6.3, 6.4, 6.5) can be combined into a single cookie security property
- Token storage properties (1.7, 2.8, 3.8) follow the same pattern and can be validated together

### Registration Properties

Property 1: Email validation
*For any* string input submitted as an email during registration, the system should accept only strings that conform to RFC 5322 email format standards
**Validates: Requirements 1.1**

Property 2: Password validation
*For any* password submitted during registration, the system should reject passwords that are less than 8 characters OR lack an uppercase letter OR lack a lowercase letter OR lack a number OR lack a special character
**Validates: Requirements 1.2, 1.3**

Property 3: Password hashing
*For any* valid password used during registration, the stored password hash should be a valid bcrypt hash with cost factor 12 that verifies against the original password
**Validates: Requirements 1.4**

Property 4: Token generation on registration
*For any* successful registration, the response should contain both an access token in the response body and a refresh token in an HttpOnly cookie
**Validates: Requirements 1.6, 1.8**

Property 5: Refresh token storage on registration
*For any* successful registration, the database shotain a refresh token record associated with the user's ID and with  expiration timestamp approximately 7 days in the future
**ates: Requirements 1.7**

### Login Properties

Propl verification on login
*For ain attempt with a non-existent email, the system should return a 401 Unauthorized status
**Validates: Requirements 2.1**

Property 7: Password verification on login
*For any* login attempt with an incorrect password, the system should return a 401 Unauthorized status
**Validates: Requirements 2.2**

Property 8: Generic error messages
*For any* failed login attempt (invalid email or password), the error message should not reveal whether the email or password was incorrect
**Validates: Requirements 2.3**

Property 9: Access token expiration on login
*For any* successful login, the generated access token should have an expiration time approximately 15 minutes from the issued-at time
**Validates: Requirements 2.5**

Property 10: Refresh token expiration on login
*For any* successful login, the generated refresh token should have an expiration time approximately 7 days from the issued-at time
**Validates: Requirements 2.6**

Property 11: Old token invalidation on login
*For any* user who logs in twice, the refresh token from the first login should no longer be valid after the second login
**Validates: Requirements 2.7**

Property 12: Cookie security attributes
*For any* response that sets a refresh token cookie, the cookie should have the HttpOnly, Secure, and SameSite=Strict flags set
**Validates: Requirements 2.9, 6.3, 6.4, 6.5**

### Token Refresh Properties

Property 13: Refresh token signature validation
*For any* refresh request with an invalid token signature, the system should return a 401 Unauthorized status
**Validates: Requirements 3.3**

Property 14: Refresh token blacklist check
*For any* refresh request with a blacklisted token, the system should return a 401 Unauthorized status
**Validates: Requirements 3.4, 10.4**

Property 15: Token rotation on refresh
*For any* successful token refresh, the system should generate a new access token and a new refresh token, and the old refresh token should be added to the blacklist
**Validates: Requirements 3.5, 3.6, 3.7, 10.5**

Property 16: Refresh token storage on refresh
*For any* successful token refresh, the database should contain the new refresh token record with correct user association and expiration
**Validates: Requirements 3.8**

Property 17: Single-use refresh tokens
*For any* refresh token that has been used once, attempting to use it a second time should result in a 401 Unauthorized status
**Validates: Requirements 3.7, 10.5**

### Logout Properties

Property 18: Token blacklisting on logout
*For any* logout request, the refresh token should be added to the blacklist table
**Validates: Requirements 4.2**

Property 19: Token deletion on logout
*For any* logout request, the refresh token should be removed from the refresh_tokens table
**Validates: Requirements 4.3**

Property 20: Cookie clearing on logout
*For any* logout response, the Set-Cookie header should set the refresh token cookie with an expired date
**Validates: Requirements 4.4**

### Protected Endpoint Properties

Property 21: Token signature validation for protected endpoints
*For any* request to a protected endpoint with an invalid token signature, the system should return a 401 Unauthorized status
**Validates: Requirements 5.3**

Property 22: Token expiration validation
*For any* request to a protected endpoint with an expired token, the system should return a 401 Unauthorized status
**Validates: Requirements 5.4, 5.7**

Property 23: User extraction from token
*For any* valid access token, the system should correctly extract the user email from the token payload
**Validates: Requirements 5.5**

Property 24: User existence and active status validation
*For any* access token for a non-existent or inactive user, the system should return a 401 Unauthorized status
**Validates: Requirements 5.6**

### Security Properties

Property 25: No plaintext passwords
*For any* user record in the database, the password field should be a bcrypt hash, not a plaintext password
**Validates: Requirements 6.1**

Property 26: Rate limiting on failed logins
*For any* sequence of failed login attempts from the same source exceeding the threshold, subsequent attempts should be blocked with a 429 Too Many Requests status
**Validates: Requirements 6.6**

Property 27: Input validation with Pydantic
*For any* authentication request with invalid data types or formats, the system should return a 422 Unprocessable Entity status with validation errors
**Validates: Requirements 6.7**

Property 28: No sensitive data in error messages
*For any* error response, the message should not contain sensitive information such as stack traces, database details, or internal system information
**Validates: Requirements 6.8**

### Logging Properties

Property 29: No sensitive data in logs
*For any* log entry related to authentication errors, the log should not contain passwords, tokens, or other sensitive credentials
**Validates: Requirements 9.1**

Property 30: Token generation logging
*For any* token generation event, a log entry should exist with the user email and timestamp
**Validates: Requirements 9.2**

Property 31: Token refresh logging
*For any* token refresh event, a log entry should exist with the user email and timestamp
**Validates: Requirements 9.3**

Property 32: Security event logging
*For any* suspicious activity (e.g., multiple failed logins, blacklisted token usage), a log entry should exist with IP address and user agent
**Validates: Requirements 9.4**

### Session Management Properties

Property 33: Token invalidation on password change
*For any* user who changes their password, all existing refresh tokens for that user should be invalidated
**Validates: Requirements 10.1**

Property 34: Deactivated account authentication prevention
*For any* user with is_active=False, login attempts should return a 403 Forbidden status
**Validates: Requirements 10.2**

Property 35: Refresh token metadata
*For any* refresh token stored in the database, the record should include created_at, expires_at, and user_id fields
**Validates: Requirements 10.3**

## Error Handling

### Backend Error Handling

**Authentication Errors**
- Invalid credentials: 401 Unauthorized with generic message "Invalid email or password"
- Expired token: 401 Unauthorized with message "Token has expired"
- Invalid token: 401 Unauthorized with message "Invalid token"
- Blacklisted token: 401 Unauthorized with message "Token has been revoked"
- Deactivated account: 403 Forbidden with message "Account is deactivated"
- Duplicate email: 409 Conflict with message "Email already registered"
- Rate limit exceeded: 429 Too Many Requests with message "Too many attempts, please try again later"

**Validation Errors**
- Pydantic validation failures: 422 Unprocessable Entity with detailed field errors
- Password strength failures: 400 Bad Request with specific requirements

**Server Errors**
- Database errors: 500 Internal Server Error with generic message "An error occurred"
- Token generation errors: 500 Internal Server Error with generic message "An error occurred"

### Frontend Error Handling

**API Error Handling**
```typescript
try {
  await api.post('/api/auth/login', credentials)
} catch (error) {
  if (axios.isAxiosError(error)) {
    if (error.response?.status === 401) {
      setError('Invalid email or password')
    } else if (error.response?.status === 429) {
      setError('Too many attempts. Please try again later.')
    } else if (error.response?.data?.detail) {
      setError(error.response.data.detail)
    } else {
      setError('An error occurred. Please try again.')
    }
  }
}
```

**Token Refresh Error Handling**
- If refresh fails with 401: Clear auth state and redirect to login
- If refresh fails with network error: Retry once, then redirect to login
- If refresh succeeds: Update access token and retry original request

## Testing Strategy

### Backend Testing

#### Unit Tests

**Password Hashing Tests**
- Test bcrypt hashing with various passwords
- Test password verification with correct and incorrect passwords
- Test cost factor is set to 12

**Token Generation Tests**
- Test access token creation with correct expiration
- Test refresh token creation with correct expiration
- Test token payload contains required fields
- Test token signing with secret key

**Token Validation Tests**
- Test valid token decoding
- Test expired token rejection
- Test invalid signature rejection
- Test malformed token rejection

**Password Validation Tests**
- Test minimum length requirement
- Test uppercase letter requirement
- Test lowercase letter requirement
- Test number requirement
- Test special character requirement

#### Property-Based Tests

We will use **Hypothesis** for Python property-based testing. Each property-based test should run a minimum of 100 iterations.

**Property Test 1: Email Validation** (Property 1)
```python
@given(st.text())
@settings(max_examples=100)
def test_email_validation_property(email: str):
    # Test that only valid RFC 5322 emails are accepted
    is_valid = validate_email_format(email)
    if is_valid:
        assert re.match(RFC_5322_REGEX, email)
```

**Property Test 2: Password Validation** (Property 2)
```python
@given(st.text(min_size=1, max_size=100))
@settings(max_examples=100)
def test_password_validation_property(password: str):
    # Test password requirements
    result = validate_password_strength(password)
    if result.valid:
        assert len(password) >= 8
        assert any(c.isupper() for c in password)
        assert any(c.islower() for c in password)
        assert any(c.isdigit() for c in password)
        assert any(not c.isalnum() for c in password)
```

**Property Test 3: Password Hashing** (Property 3)
```python
@given(st.text(min_size=8, max_size=100))
@settings(max_examples=100)
def test_password_hashing_property(password: str):
    # Test that hashed passwords verify correctly
    hashed = hash_password(password)
    assert hashed.startswith('$2b$12$')  # bcrypt with cost 12
    assert verify_password(password, hashed)
    assert not verify_password(password + 'x', hashed)
```

**Property Test 4: Token Expiration** (Properties 9, 10)
```python
@given(st.integers(min_value=1, max_value=1000000))
@settings(max_examples=100)
def test_token_expiration_property(user_id: int):
    # Test access token expiration is ~15 minutes
    access_token = create_access_token({'user_id': user_id})
    payload = decode_access_token(access_token)
    exp_delta = payload['exp'] - payload['iat']
    assert 14 * 60 <= exp_delta <= 16 * 60  # 14-16 minutes tolerance
    
    # Test refresh token expiration is ~7 days
    refresh_token = create_refresh_token({'user_id': user_id})
    payload = decode_refresh_token(refresh_token)
    exp_delta = payload['exp'] - payload['iat']
    assert 6.9 * 24 * 60 * 60 <= exp_delta <= 7.1 * 24 * 60 * 60
```

**Property Test 5: Token Rotation** (Property 15)
```python
@given(st.integers(min_value=1, max_value=1000000))
@settings(max_examples=100)
async def test_token_rotation_property(user_id: int):
    # Test that refresh creates new tokens and blacklists old one
    old_refresh = create_refresh_token({'user_id': user_id})
    
    response = await refresh_tokens(old_refresh)
    
    assert response.access_token != old_refresh
    assert response.refresh_token != old_refresh
    assert await is_blacklisted(old_refresh)
```

**Property Test 6: Single-Use Refresh Tokens** (Property 17)
```python
@given(st.integers(min_value=1, max_value=1000000))
@settings(max_examples=100)
async def test_single_use_refresh_token_property(user_id: int):
    # Test that refresh tokens can only be used once
    refresh_token = create_refresh_token({'user_id': user_id})
    
    # First use should succeed
    response1 = await refresh_tokens(refresh_token)
    assert response1.status_code == 200
    
    # Second use should fail
    response2 = await refresh_tokens(refresh_token)
    assert response2.status_code == 401
```

**Property Test 7: Cookie Security** (Property 12)
```python
@given(st.integers(min_value=1, max_value=1000000))
@settings(max_examples=100)
async def test_cookie_security_property(user_id: int):
    # Test that all cookies have security flags
    response = await login_user(user_id)
    
    cookie_header = response.headers.get('Set-Cookie')
    assert 'HttpOnly' in cookie_header
    assert 'Secure' in cookie_header
    assert 'SameSite=Strict' in cookie_header
```

**Property Test 8: No Plaintext Passwords** (Property 25)
```python
@given(st.text(min_size=8, max_size=100))
@settings(max_examples=100)
async def test_no_plaintext_passwords_property(password: str):
    # Test that passwords are never stored in plaintext
    user = await create_user(password=password)
    
    db_user = await get_user_from_db(user.id)
    assert db_user.hashed_password != password
    assert db_user.hashed_password.startswith('$2b$')
```

**Property Test 9: Generic Error Messages** (Property 8)
```python
@given(st.emails(), st.text(min_size=1, max_size=100))
@settings(max_examples=100)
async def test_generic_error_messages_property(email: str, password: str):
    # Test that error messages don't leak information
    response = await login(email, password)
    
    if response.status_code == 401:
        assert 'email' not in response.json()['detail'].lower()
        assert 'password' not in response.json()['detail'].lower()
        assert response.json()['detail'] == 'Invalid email or password'
```

**Property Test 10: Rate Limiting** (Property 26)
```python
@given(st.emails(), st.integers(min_value=6, max_value=20))
@settings(max_examples=100)
async def test_rate_limiting_property(email: str, attempts: int):
    # Test that rate limiting kicks in after threshold
    for i in range(attempts):
        response = await login(email, 'wrong_password')
        
        if i < 5:
            assert response.status_code == 401
        else:
            assert response.status_code == 429
```

#### Integration Tests

- Test complete registration flow: register → verify tokens → access protected endpoint
- Test complete login flow: login → verify tokens → access protected endpoint
- Test token refresh flow: login → wait for expiration → refresh → access protected endpoint
- Test logout flow: login → logout → verify tokens are invalid
- Test password change flow: login → change password → verify old tokens are invalid

### Frontend Testing

#### Unit Tests

**Auth Store Tests**
- Test login action updates state correctly
- Test register action updates state correctly
- Test logout action clears state
- Test setAccessToken updates token

**Form Validation Tests**
- Test email validation with valid/invalid emails
- Test password validation with various passwords
- Test password confirmation matching

#### Integration Tests

**Axios Interceptor Tests**
- Test request interceptor adds Authorization header
- Test response interceptor handles 401 and refreshes token
- Test response interceptor redirects on refresh failure
- Test response interceptor retries original request after refresh

**Auth Flow Tests**
- Test login flow: submit form → API call → state update → navigation
- Test register flow: submit form → API call → state update → navigation
- Test logout flow: click logout → API call → state clear → navigation
- Test protected route access: unauthenticated → redirect to login
- Test session check on app load: valid session → load user data

**Form Tests**
- Test login form submission with valid credentials
- Test login form validation errors
- Test register form submission with valid data
- Test register form password mismatch error
- Test password visibility toggle

### End-to-End Tests

- Test complete user journey: register → login → access protected pages → logout
- Test token refresh during active session
- Test session persistence across page reloads
- Test multiple failed login attempts trigger rate limiting
- Test deactivated account cannot login

