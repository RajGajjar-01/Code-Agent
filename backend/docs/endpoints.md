# WordPress REST API Endpoints Documentation

This document lists all WordPress REST API endpoints used by the WordPress Agent backend.

## Base Configuration

- **Base URL**: Configured via `WP_BASE_URL` environment variable
- **API Base**: `{WP_BASE_URL}/wp-json/wp/v2`
- **Authentication**: HTTP Basic Auth using WordPress Application Password
  - Username: `WP_USERNAME`
  - App Password: `WP_APP_PASSWORD`

## Pages Endpoints

### List Pages
- **Endpoint**: `GET /wp-json/wp/v2/pages`
- **Description**: Retrieve a list of WordPress pages
- **Parameters**:
  - `per_page` (integer): Number of pages per request (default: 10)
  - `status` (string): Filter by status - `publish`, `draft`, `pending`, `private`, `trash`
- **Response Headers**:
  - `X-WP-Total`: Total number of pages
- **Implementation**: `WordPressClient.list_pages()`

### Get Page
- **Endpoint**: `GET /wp-json/wp/v2/pages/{page_id}`
- **Description**: Retrieve a specific page by ID
- **Parameters**:
  - `page_id` (integer, required): The page ID
- **Response**: Page object with title, content, and ACF fields
- **Implementation**: `WordPressClient.get_page()`

### Create Page
- **Endpoint**: `POST /wp-json/wp/v2/pages`
- **Description**: Create a new WordPress page
- **Body Parameters**:
  - `title` (string, required): Page title
  - `content` (string, required): Page HTML content
  - `status` (string): Page status - `publish` or `draft` (default: `publish`)
  - Additional fields supported by WordPress REST API
- **Response**: Created page object with ID, link, and status
- **Implementation**: `WordPressClient.create_page()`

### Update Page
- **Endpoint**: `POST /wp-json/wp/v2/pages/{page_id}`
- **Description**: Update an existing page
- **Parameters**:
  - `page_id` (integer, required): The page ID
- **Body Parameters**: Any page fields to update (title, content, etc.)
- **Response**: Updated page object with ID and link
- **Implementation**: `WordPressClient.update_page()`

### Delete Page
- **Endpoint**: `DELETE /wp-json/wp/v2/pages/{page_id}`
- **Description**: Delete a page
- **Parameters**:
  - `page_id` (integer, required): The page ID
  - `force` (boolean): Bypass trash and permanently delete (default: true)
- **Response**: Deletion confirmation
- **Implementation**: `WordPressClient.delete_page()`

## Posts Endpoints

### List Posts
- **Endpoint**: `GET /wp-json/wp/v2/posts`
- **Description**: Retrieve a list of WordPress posts
- **Parameters**:
  - `per_page` (integer): Number of posts per request (default: 10)
  - `status` (string): Filter by status - `publish`, `draft`, `pending`, `private`, `trash`
- **Response Headers**:
  - `X-WP-Total`: Total number of posts
- **Implementation**: `WordPressClient.list_posts()`

### Create Post
- **Endpoint**: `POST /wp-json/wp/v2/posts`
- **Description**: Create a new WordPress post
- **Body Parameters**:
  - `title` (string, required): Post title
  - `content` (string, required): Post HTML content
  - `status` (string): Post status - `publish` or `draft` (default: `publish`)
- **Response**: Created post object with ID, link, and status
- **Implementation**: `WordPressClient.create_post()`

### Delete Post
- **Endpoint**: `DELETE /wp-json/wp/v2/posts/{post_id}`
- **Description**: Delete a post
- **Parameters**:
  - `post_id` (integer, required): The post ID
  - `force` (boolean): Bypass trash and permanently delete (default: true)
- **Response**: Deletion confirmation
- **Implementation**: `WordPressClient.delete_post()`

## Media Endpoints

### Upload Media
- **Endpoint**: `POST /wp-json/wp/v2/media`
- **Description**: Upload a file to the WordPress media library
- **Headers**:
  - `Content-Disposition`: `attachment; filename="{filename}"`
  - `Content-Type`: MIME type of the file
- **Body**: Binary file content
- **Response**: Media object with ID and source URL
- **Post-Upload**: Optionally updates media title via `POST /wp-json/wp/v2/media/{media_id}`
- **Implementation**: `WordPressClient.upload_media()`

## ACF (Advanced Custom Fields) Endpoints

### Get ACF Fields
- **Endpoint**: `GET /wp-json/wp/v2/{post_type}/{post_id}`
- **Description**: Retrieve ACF field values for a page or post
- **Parameters**:
  - `post_type` (string): `pages` or `posts` (default: `pages`)
  - `post_id` (integer, required): The page/post ID
- **Response**: Object with ID, title, and ACF fields
- **Implementation**: `WordPressClient.get_acf_fields()`

### Update ACF Fields
- **Endpoint**: `POST /wp-json/wp/v2/{post_type}/{post_id}`
- **Description**: Update ACF field values on a page or post
- **Parameters**:
  - `post_type` (string): `pages` or `posts` (default: `pages`)
  - `post_id` (integer, required): The page/post ID
- **Body Parameters**:
  - `acf` (object, required): Dictionary of field name → value pairs
- **Response**: Updated object with ID and ACF fields
- **Implementation**: `WordPressClient.update_acf_fields()`

### List ACF Field Groups
- **Endpoint**: `GET /wp-json/acf/v3/field-groups`
- **Description**: List all registered ACF field groups (requires ACF Pro)
- **Response**: Array of field group objects with ID, title, key, and fields
- **Fallback**: Returns empty array with note if ACF Pro REST API is unavailable
- **Implementation**: `WordPressClient.list_acf_field_groups()`

## Theme Endpoints

### List Themes
- **Endpoint**: `GET /wp-json/wp/v2/themes`
- **Description**: List all installed WordPress themes
- **Response**: Array of theme objects with slug, name, status, version, and template
- **Implementation**: `WordPressClient.list_themes()`

### Get Active Theme
- **Endpoint**: `GET /wp-json/wp/v2/themes?status=active`
- **Description**: Get details about the currently active theme
- **Response**: Active theme object with slug, name, version, template, and theme URI
- **Implementation**: `WordPressClient.get_active_theme()`

### Create/Update Theme File
- **Endpoint**: `POST /wp-json/wp/v2/themes/{theme_slug}`
- **Description**: Create or overwrite a file in a theme directory (WordPress 5.9+)
- **Parameters**:
  - `theme_slug` (string, required): Theme directory name
- **Body Parameters**:
  - `file` (string, required): Relative file path within theme
  - `content` (string, required): File content
- **Fallback**: If REST API fails, returns instructions for manual FTP/SSH upload
- **Implementation**: `WordPressClient.create_theme_file()`

### Read Theme File
- **Endpoint**: `GET /wp-json/wp/v2/themes/{theme_slug}?file={file_path}`
- **Description**: Read the contents of a theme file
- **Parameters**:
  - `theme_slug` (string, required): Theme directory name
  - `file` (string, required): Relative file path within theme
- **Response**: Object with theme_slug, file_path, and content
- **Implementation**: `WordPressClient.read_theme_file()`

### Activate Theme
- **Endpoint**: `POST /wp-json/wp/v2/themes/{theme_slug}`
- **Description**: Activate a theme by its slug
- **Parameters**:
  - `theme_slug` (string, required): Theme directory name
- **Body Parameters**:
  - `status` (string): Set to `active`
- **Response**: Confirmation with theme_slug and status
- **Implementation**: `WordPressClient.activate_theme()`

## Site Information Endpoints

### Get Site Info
- **Endpoint**: `GET /wp-json`
- **Description**: Get WordPress site overview information
- **Response**: Object with site name, description, and URL
- **Implementation**: `WordPressClient.get_site_info()`

## Error Handling

All endpoints implement consistent error handling:

- **HTTP Error Responses**: Automatically raised via `httpx.Response.raise_for_status()`
- **WordPress Error Messages**: Extracted from response JSON (`message` or `error` fields)
- **Custom Error Handler**: `_raise_for_status()` function provides detailed error messages
- **Exception Type**: Raises `ValueError` with formatted error message including status code

## Authentication

All requests use HTTP Basic Authentication:
```python
auth = (username, app_password)
```

Application Passwords can be generated in WordPress admin:
- Navigate to: Users → Profile → Application Passwords
- Generate a new application password
- Use the generated password (not your WordPress login password)

## Timeout Configuration

All requests have a 30-second timeout:
```python
timeout=30.0
```

## Client Lifecycle

The `WordPressClient` uses an async HTTP client that must be properly closed:
```python
await wp_client.close()
```

This is handled automatically in the FastAPI lifespan context manager.

## Validation Status

✅ **Validated Endpoints** (Standard WordPress REST API):
- All Pages endpoints
- All Posts endpoints
- Media upload endpoint
- Site info endpoint
- Theme listing and activation endpoints

⚠️ **Partially Validated** (Requires plugins/features):
- ACF endpoints (requires ACF plugin)
- ACF field groups listing (requires ACF Pro with REST API enabled)

⚠️ **Limited Support** (WordPress version dependent):
- Theme file editing (requires WordPress 5.9+, may require additional permissions)
- Theme file reading (may not be available on all WordPress installations)

## Notes

1. **ACF Support**: ACF endpoints require the Advanced Custom Fields plugin to be installed and activated
2. **Theme File Editing**: Direct theme file editing via REST API has limited support and may require FTP/SSH access
3. **Permissions**: All operations respect WordPress user roles and capabilities
4. **Rate Limiting**: WordPress may implement rate limiting on REST API endpoints
5. **CORS**: The backend handles CORS for frontend requests, but WordPress site must allow REST API access
