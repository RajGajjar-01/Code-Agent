# Implementation Plan

- [x] 1. Set up database models and migrations
  - Create User, RefreshToken, and TokenBlacklist models with SQLAlchemy
  - Create Alembic migration for all three tables with proper indexes
  - _Requirements: 1.4, 1.7, 2.8, 3.7, 4.2, 4.3, 10.3_

- [x] 2. Implement core security utilities
  - Create password hashing and verification functions using bcrypt with cost factor 12
  - Create password strength validation function
  - Create JWT token generation functions for access and refresh tokens
  - Create JWT token decoding and validation functions
  - _Requirements: 1.2, 1.3, 1.4, 2.2, 2.5, 2.6, 5.3, 5.4, 6.1, 6.2_

- [ ]* 2.1 Write property test for password validation
  - **Property 2: Password validation**
  - **Validates: Requirements 1.2, 1.3**

- [ ]* 2.2 Write property test for password hashing
  - **Property 3: Password hashing**
  - **Validates: Requirements 1.4**

- [ ]* 2.3 Write property test for token expiration
  - **Property 9: Access token expiration on login**
  - **Property 10: Refresh token expiration on login**
  - **Validates: Requirements 2.5, 2.6**

- [ ]* 2.4 Write property test for no plaintext passwords
  - **Property 25: No plaintext passwords**
  - **Validates: Requirements 6.1**

- [x] 3. Implement token service for blacklist and storage
  - Create functions to add tokens to blacklist
  - Create function to check if token is blacklisted
  - Create functions to store, retrieve, and delete refresh tokens
  - Create function to delete all refresh tokens for a user
  - Create function to cleanup expired tokens
  - _Requirements: 1.7, 2.7, 2.8, 3.4, 3.7, 3.8, 4.2, 4.3, 10.1, 10.4, 10.5_

- [ ]* 3.1 Write property test for single-use refresh tokens
  - **Property 17: Single-use refresh tokens**
  - **Validates: Requirements 3.7, 10.5**

- [ ]* 3.2 Write property test for token blacklist check
  - **Property 14: Refresh token blacklist check**
  - **Validates: Requirements 3.4, 10.4**

- [x] 4. Create Pydantic schemas for authentication
  - Create RegisterRequest, LoginRequest, TokenResponse, and UserResponse schemas
  - Add email validation using EmailStr
  - Add field validation for name and password
  - _Requirements: 1.1, 1.2, 6.7_

- [ ]* 4.1 Write property test for email validation
  - **Property 1: Email validation**
  - **Validates: Requirements 1.1**

- [ ]* 4.2 Write property test for input validation
  - **Property 27: Input validation with Pydantic**
  - **Validates: Requirements 6.7**

- [x] 5. Implement authentication dependencies
  - Create get_current_user dependency that validates access tokens
  - Create get_current_active_user dependency that checks user is active
  - Use FastAPI's OAuth2PasswordBearer for token extraction
  - _Requirements: 5.2, 5.3, 5.4, 5.5, 5.6, 5.7, 10.2_

- [ ]* 5.1 Write property test for token signature validation
  - **Property 21: Token signature validation for protected endpoints**
  - **Validates: Requirements 5.3**

- [ ]* 5.2 Write property test for token expiration validation
  - **Property 22: Token expiration validation**
  - **Validates: Requirements 5.4, 5.7**

- [ ]* 5.3 Write property test for user extraction from token
  - **Property 23: User extraction from token**
  - **Validates: Requirements 5.5**

- [ ]* 5.4 Write property test for user existence validation
  - **Property 24: User existence and active status validation**
  - **Validates: Requirements 5.6**

- [x] 6. Implement registration endpoint
  - Create POST /api/auth/register endpoint
  - Validate email format and password strength
  - Check for duplicate email and return 409 if exists
  - Hash password and create user in database
  - Generate access and refresh tokens
  - Store refresh token in database
  - Set refresh token in HttpOnly, Secure, SameSite=Strict cookie
  - Return access token in response body
  - Add logging for registration events
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 6.3, 6.4, 6.5, 9.2_

- [ ]* 6.1 Write property test for token generation on registration
  - **Property 4: Token generation on registration**
  - **Validates: Requirements 1.6, 1.8**

- [ ]* 6.2 Write property test for refresh token storage on registration
  - **Property 5: Refresh token storage on registration**
  - **Validates: Requirements 1.7**

- [ ]* 6.3 Write property test for cookie security attributes
  - **Property 12: Cookie security attributes**
  - **Validates: Requirements 2.9, 6.3, 6.4, 6.5**

- [x] 7. Implement login endpoint with rate limiting
  - Create POST /api/auth/login endpoint
  - Add rate limiting middleware to prevent brute force attacks
  - Verify email exists and password matches
  - Return 401 with generic message for invalid credentials
  - Check if user account is active, return 403 if deactivated
  - Invalidate all existing refresh tokens for the user
  - Generate new access and refresh tokens
  - Store refresh token in database
  - Set refresh token in HttpOnly, Secure, SameSite=Strict cookie
  - Return access token in response body
  - Add logging for login events and failed attempts
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5, 2.6, 2.7, 2.8, 2.9, 6.3, 6.4, 6.5, 6.6, 9.2, 9.4, 10.2_

- [ ]* 7.1 Write property test for email verification on login
  - **Property 6: Email verification on login**
  - **Validates: Requirements 2.1**

- [ ]* 7.2 Write property test for password verification on login
  - **Property 7: Password verification on login**
  - **Validates: Requirements 2.2**

- [ ]* 7.3 Write property test for generic error messages
  - **Property 8: Generic error messages**
  - **Validates: Requirements 2.3**

- [ ]* 7.4 Write property test for old token invalidation
  - **Property 11: Old token invalidation on login**
  - **Validates: Requirements 2.7**

- [ ]* 7.5 Write property test for rate limiting
  - **Property 26: Rate limiting on failed logins**
  - **Validates: Requirements 6.6**

- [ ]* 7.6 Write property test for deactivated account prevention
  - **Property 34: Deactivated account authentication prevention**
  - **Validates: Requirements 10.2**

- [x] 8. Implement token refresh endpoint
  - Create POST /api/auth/refresh endpoint
  - Extract refresh token from HttpOnly cookie
  - Validate refresh token signature and expiration
  - Check if refresh token is blacklisted
  - Verify refresh token exists in database
  - Generate new access and refresh tokens
  - Add old refresh token to blacklist
  - Store new refresh token in database
  - Set new refresh token in HttpOnly, Secure, SameSite=Strict cookie
  - Return new access token in response body
  - Return 401 for invalid or expired tokens
  - Add logging for refresh events
  - _Requirements: 3.2, 3.3, 3.4, 3.5, 3.6, 3.7, 3.8, 3.9, 3.10, 6.3, 6.4, 6.5, 9.3, 10.4, 10.5_

- [ ]* 8.1 Write property test for refresh token signature validation
  - **Property 13: Refresh token signature validation**
  - **Validates: Requirements 3.3**

- [ ]* 8.2 Write property test for token rotation on refresh
  - **Property 15: Token rotation on refresh**
  - **Validates: Requirements 3.5, 3.6, 3.7, 10.5**

- [ ]* 8.3 Write property test for refresh token storage on refresh
  - **Property 16: Refresh token storage on refresh**
  - **Validates: Requirements 3.8**

- [x] 9. Implement logout endpoint
  - Create POST /api/auth/logout endpoint
  - Extract refresh token from HttpOnly cookie
  - Add refresh token to blacklist
  - Delete refresh token from database
  - Clear refresh token cookie by setting expired date
  - Return success response
  - _Requirements: 4.1, 4.2, 4.3, 4.4_

- [ ]* 9.1 Write property test for token blacklisting on logout
  - **Property 18: Token blacklisting on logout**
  - **Validates: Requirements 4.2**

- [ ]* 9.2 Write property test for token deletion on logout
  - **Property 19: Token deletion on logout**
  - **Validates: Requirements 4.3**

- [ ]* 9.3 Write property test for cookie clearing on logout
  - **Property 20: Cookie clearing on logout**
  - **Validates: Requirements 4.4**

- [x] 10. Implement get current user endpoint
  - Create GET /api/auth/me endpoint
  - Use get_current_active_user dependency
  - Return user information (id, email, name, is_active)
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6, 5.8, 7.1_

- [x] 11. Add comprehensive error handling and logging
  - Implement custom exception handlers for authentication errors
  - Ensure error messages don't expose sensitive information
  - Add logging for all authentication events without logging sensitive data
  - Add logging for security events with IP and user agent
  - _Requirements: 6.8, 9.1, 9.2, 9.3, 9.4_

- [ ]* 11.1 Write property test for no sensitive data in error messages
  - **Property 28: No sensitive data in error messages**
  - **Validates: Requirements 6.8**

- [ ]* 11.2 Write property test for no sensitive data in logs
  - **Property 29: No sensitive data in logs**
  - **Validates: Requirements 9.1**

- [ ]* 11.3 Write property test for token generation logging
  - **Property 30: Token generation logging**
  - **Validates: Requirements 9.2**

- [ ]* 11.4 Write property test for token refresh logging
  - **Property 31: Token refresh logging**
  - **Validates: Requirements 9.3**

- [ ]* 11.5 Write property test for security event logging
  - **Property 32: Security event logging**
  - **Validates: Requirements 9.4**

- [x] 12. Implement password change functionality
  - Create endpoint for password change
  - Validate old password
  - Validate new password strength
  - Hash new password
  - Update user password in database
  - Invalidate all existing refresh tokens for the user
  - _Requirements: 10.1_

- [ ]* 12.1 Write property test for token invalidation on password change
  - **Property 33: Token invalidation on password change**
  - **Validates: Requirements 10.1**

- [x] 13. Checkpoint - Ensure all backend tests pass
  - Ensure all tests pass, ask the user if questions arise.

- [x] 14. Set up frontend Axios configuration
  - Create Axios instance with baseURL and withCredentials
  - Implement request interceptor to add Authorization header with access token
  - Implement response interceptor to handle 401 errors and trigger token refresh
  - Implement automatic retry of failed requests after successful token refresh
  - Handle refresh failures by clearing auth state and redirecting to login
  - _Requirements: 3.1, 3.2, 3.10, 3.11, 5.1, 7.4, 7.5, 7.6, 7.7_

- [ ]* 14.1 Write integration tests for Axios interceptors
  - Test request interceptor adds Authorization header
  - Test response interceptor handles 401 and refreshes token
  - Test response interceptor redirects on refresh failure
  - Test response interceptor retries original request after refresh

- [x] 15. Create Zustand auth store
  - Create user store with state for user, accessToken, isAuthenticated, isLoading
  - Implement login action that calls API and updates state
  - Implement register action that calls API and updates state
  - Implement logout action that calls API and clears state
  - Implement checkSession action that calls /api/auth/me on app load
  - Implement setAccessToken action for token refresh
  - _Requirements: 4.5, 7.1, 7.2, 7.6_

- [ ]* 15.1 Write unit tests for auth store
  - Test login action updates state correctly
  - Test register action updates state correctly
  - Test logout action clears state
  - Test setAccessToken updates token

- [x] 16. Create Zod validation schemas
  - Create loginSchema with email and password validation
  - Create registerSchema with name, email, password, and confirmPassword validation
  - Add password strength validation rules (min 8 chars, uppercase, lowercase, number, special char)
  - Add password confirmation matching validation
  - _Requirements: 1.2, 1.3, 8.3_

- [ ]* 16.1 Write unit tests for form validation
  - Test email validation with valid/invalid emails
  - Test password validation with various passwords
  - Test password confirmation matching

- [x] 17. Build login page with react-hook-form
  - Create LoginPage component with shadcn/ui form components
  - Integrate react-hook-form with Zod loginSchema
  - Add email and password input fields
  - Add password visibility toggle
  - Add loading state during form submission
  - Display inline validation errors
  - Display API error messages
  - Call auth store login action on form submit
  - Navigate to home page on successful login
  - _Requirements: 2.1, 2.2, 2.3, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ]* 17.1 Write integration tests for login form
  - Test login form submission with valid credentials
  - Test login form validation errors
  - Test password visibility toggle

- [x] 18. Build registration page with react-hook-form
  - Create SignupPage component with shadcn/ui form components
  - Integrate react-hook-form with Zod registerSchema
  - Add name, email, password, and confirmPassword input fields
  - Add password visibility toggle for both password fields
  - Add loading state during form submission
  - Display inline validation errors including password strength requirements
  - Display API error messages
  - Call auth store register action on form submit
  - Navigate to home page on successful registration
  - _Requirements: 1.1, 1.2, 1.3, 1.5, 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7_

- [ ]* 18.1 Write integration tests for registration form
  - Test register form submission with valid data
  - Test register form password mismatch error
  - Test password visibility toggle

- [x] 19. Implement protected route wrapper
  - Create ProtectedRoute component that checks authentication state
  - Redirect to login page if user is not authenticated
  - Show loading state while checking session
  - _Requirements: 7.3_

- [x] 20. Add session check on app initialization
  - Call checkSession action when app loads
  - Store user data in auth store if session is valid
  - Handle session check failures gracefully
  - _Requirements: 7.1, 7.2_

- [x] 21. Implement logout functionality in UI
  - Add logout button/link in navigation or user menu
  - Call auth store logout action on click
  - Clear access token from memory
  - Redirect to login page after logout
  - _Requirements: 4.5, 4.6_

- [x] 22. Add user-friendly error handling in frontend
  - Display appropriate error messages for different error codes
  - Ensure technical details are not exposed to users
  - Add error logging for debugging
  - _Requirements: 9.5, 9.6_

- [ ]* 22.1 Write property test for refresh token metadata
  - **Property 35: Refresh token metadata**
  - **Validates: Requirements 10.3**

- [x] 23. Final Checkpoint - Ensure all tests pass
  - Ensure all tests pass, ask the user if questions arise.
