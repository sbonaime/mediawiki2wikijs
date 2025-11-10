# Wiki.js GraphQL API Contract

**Feature**: 001-mediawiki-wikijs-migration
**API**: Wiki.js GraphQL API
**Target Version**: Wiki.js 2.x
**Documentation**: https://docs.requarks.io/dev/api

## Overview

This contract defines the Wiki.js GraphQL mutations and queries used by the import script. All requests use HTTPS with API key authentication via the `Authorization` header.

---

## Authentication

### API Key Authentication

**Headers**:
```http
Authorization: Bearer YOUR_API_KEY
Content-Type: application/json
```

**Notes**:
- API key must have `write:pages` and `write:assets` permissions
- Generate API key in Wiki.js Admin UI: Administration → API Access
- Timeout after 5 minutes of inactivity (re-authenticate by creating new key)

---

## Schema Overview

### GraphQL Endpoint

**URL**: `https://wikijs.example.com/graphql`
**Method**: `POST`

**Request Structure**:
```json
{
  "query": "mutation or query string",
  "variables": {
    "var1": "value1"
  }
}
```

---

## Page Operations

### Create Page

**Mutation**: `pages.create`

**GraphQL**:
```graphql
mutation CreatePage($input: PageCreateInput!) {
  pages {
    create(
      content: $input.content
      description: $input.description
      editor: $input.editor
      isPublished: $input.isPublished
      isPrivate: $input.isPrivate
      locale: $input.locale
      path: $input.path
      publishEndDate: $input.publishEndDate
      publishStartDate: $input.publishStartDate
      scriptCss: $input.scriptCss
      scriptJs: $input.scriptJs
      tags: $input.tags
      title: $input.title
    ) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
      page {
        id
        path
        hash
        title
        description
        isPrivate
        isPublished
        privateNS
        publishStartDate
        publishEndDate
        tags {
          id
          tag
          title
        }
        content
        render
        contentType
        createdAt
        updatedAt
        editor
        locale
        scriptCss
        scriptJs
        authorId
        authorName
        authorEmail
        creatorId
        creatorName
        creatorEmail
      }
    }
  }
}
```

**Variables**:
```json
{
  "input": {
    "content": "# Getting Started\n\nWelcome to the documentation...",
    "description": "Introduction to the platform",
    "editor": "markdown",
    "isPublished": true,
    "isPrivate": false,
    "locale": "en",
    "path": "getting-started",
    "tags": ["documentation", "tutorial"],
    "title": "Getting Started"
  }
}
```

**Response (Success)**:
```json
{
  "data": {
    "pages": {
      "create": {
        "responseResult": {
          "succeeded": true,
          "errorCode": 0,
          "slug": "getting-started",
          "message": "Page created successfully."
        },
        "page": {
          "id": 1,
          "path": "getting-started",
          "hash": "abc123def456",
          "title": "Getting Started",
          "description": "Introduction to the platform",
          "isPrivate": false,
          "isPublished": true,
          "tags": [
            {
              "id": 1,
              "tag": "documentation",
              "title": "Documentation"
            },
            {
              "id": 2,
              "tag": "tutorial",
              "title": "Tutorial"
            }
          ],
          "content": "# Getting Started\n\nWelcome to the documentation...",
          "contentType": "markdown",
          "createdAt": "2025-11-10T12:00:00.000Z",
          "updatedAt": "2025-11-10T12:00:00.000Z",
          "editor": "markdown",
          "locale": "en"
        }
      }
    }
  }
}
```

**Response (Failure)**:
```json
{
  "data": {
    "pages": {
      "create": {
        "responseResult": {
          "succeeded": false,
          "errorCode": 1001,
          "slug": null,
          "message": "Page already exists at this path."
        },
        "page": null
      }
    }
  }
}
```

**Notes**:
- `path` must be unique within locale
- `editor` must match content format: "markdown" for converted content
- `isPublished=false` creates draft page (not visible to readers)
- Use `tags` array to preserve MediaWiki categories
- Collision handling: Check `succeeded` field; if false and errorCode=1001, log warning and skip

---

### Update Page

**Mutation**: `pages.update`

**GraphQL**:
```graphql
mutation UpdatePage($id: Int!, $input: PageUpdateInput!) {
  pages {
    update(
      id: $id
      content: $input.content
      description: $input.description
      editor: $input.editor
      isPrivate: $input.isPrivate
      isPublished: $input.isPublished
      locale: $input.locale
      path: $input.path
      publishEndDate: $input.publishEndDate
      publishStartDate: $input.publishStartDate
      scriptCss: $input.scriptCss
      scriptJs: $input.scriptJs
      tags: $input.tags
      title: $input.title
    ) {
      responseResult {
        succeeded
        errorCode
        slug
        message
      }
      page {
        id
        path
        title
        updatedAt
      }
    }
  }
}
```

**Variables**:
```json
{
  "id": 1,
  "input": {
    "content": "# Updated Content\n\nThis has been updated...",
    "title": "Updated Title"
  }
}
```

**Notes**:
- Requires page `id` from previous query or create response
- Only specified fields are updated (partial update)

---

### List Pages

**Query**: `pages.list`

**GraphQL**:
```graphql
query ListPages($limit: Int, $offset: Int, $locale: String, $tags: [String]) {
  pages {
    list(
      limit: $limit
      orderBy: PATH
      orderByDirection: ASC
      locale: $locale
      tags: $tags
    ) {
      id
      path
      hash
      title
      description
      isPrivate
      isPublished
      locale
      contentType
      createdAt
      updatedAt
      tags {
        id
        tag
        title
      }
    }
  }
}
```

**Variables**:
```json
{
  "limit": 50,
  "offset": 0,
  "locale": "en"
}
```

**Response**:
```json
{
  "data": {
    "pages": {
      "list": [
        {
          "id": 1,
          "path": "getting-started",
          "hash": "abc123",
          "title": "Getting Started",
          "description": "Introduction",
          "isPrivate": false,
          "isPublished": true,
          "locale": "en",
          "contentType": "markdown",
          "createdAt": "2025-11-10T12:00:00.000Z",
          "updatedAt": "2025-11-10T12:00:00.000Z",
          "tags": [
            {
              "id": 1,
              "tag": "documentation",
              "title": "Documentation"
            }
          ]
        }
      ]
    }
  }
}
```

**Notes**:
- Use for verification phase to check imported pages
- Supports pagination with `limit` and `orderBy`
- Filter by `locale` to match MediaWiki language

---

### Get Page by Path

**Query**: `pages.single`

**GraphQL**:
```graphql
query GetPage($id: Int, $path: String, $locale: String) {
  pages {
    single(id: $id, path: $path, locale: $locale) {
      id
      path
      hash
      title
      description
      isPrivate
      isPublished
      locale
      content
      render
      contentType
      createdAt
      updatedAt
      editor
      tags {
        id
        tag
        title
      }
    }
  }
}
```

**Variables**:
```json
{
  "path": "getting-started",
  "locale": "en"
}
```

**Notes**:
- Use to check if page exists before import (collision detection)
- Can query by `id` or `path`

---

## Asset Operations

### Upload Asset

**Mutation**: `assets.createAsset`

**GraphQL**:
```graphql
mutation UploadAsset($input: AssetCreateInput!) {
  assets {
    createAsset(
      file: $input.file
      folderId: $input.folderId
    ) {
      responseResult {
        succeeded
        errorCode
        message
      }
      asset {
        id
        filename
        hash
        ext
        kind
        mime
        fileSize
        metadata
        createdAt
        updatedAt
        folder {
          id
          name
          slug
        }
        author {
          id
          name
          email
        }
      }
    }
  }
}
```

**Variables** (Multipart Upload):
```json
{
  "input": {
    "file": null,
    "folderId": 1
  }
}
```

**Multipart Request**:
```http
POST /graphql HTTP/1.1
Authorization: Bearer YOUR_API_KEY
Content-Type: multipart/form-data; boundary=----Boundary

------Boundary
Content-Disposition: form-data; name="operations"

{"query": "mutation UploadAsset($file: Upload!, $folderId: Int) { assets { createAsset(file: $file, folderId: $folderId) { responseResult { succeeded errorCode message } asset { id filename hash ext } } } }", "variables": {"file": null, "folderId": 1}}
------Boundary
Content-Disposition: form-data; name="map"

{"0": ["variables.file"]}
------Boundary
Content-Disposition: form-data; name="0"; filename="main-page-logo.png"
Content-Type: image/png

[BINARY IMAGE DATA]
------Boundary--
```

**Response (Success)**:
```json
{
  "data": {
    "assets": {
      "createAsset": {
        "responseResult": {
          "succeeded": true,
          "errorCode": 0,
          "message": "Asset uploaded successfully."
        },
        "asset": {
          "id": 1,
          "filename": "main-page-logo.png",
          "hash": "def456abc789",
          "ext": "png",
          "kind": "IMAGE",
          "mime": "image/png",
          "fileSize": 45678,
          "createdAt": "2025-11-10T12:00:00.000Z",
          "folder": {
            "id": 1,
            "name": "images",
            "slug": "images"
          }
        }
      }
    }
  }
}
```

**Notes**:
- Assets uploaded via GraphQL multipart request (see https://github.com/jaydenseric/graphql-multipart-request-spec)
- Rename files to `{page-slug}-{original-name}` format before upload
- Use `folderId` to organize images (create folders via Admin UI first)
- Collision handling: If asset exists, Wiki.js will overwrite or error based on settings

---

### List Assets

**Query**: `assets.list`

**GraphQL**:
```graphql
query ListAssets($folderId: Int, $kind: AssetKind) {
  assets {
    list(folderId: $folderId, kind: $kind) {
      id
      filename
      hash
      ext
      kind
      mime
      fileSize
      metadata
      createdAt
      updatedAt
      folder {
        id
        name
        slug
      }
    }
  }
}
```

**Variables**:
```json
{
  "folderId": 1,
  "kind": "IMAGE"
}
```

**Notes**:
- Use for verification phase
- Filter by `kind`: IMAGE, BINARY, DOCUMENT, VIDEO, AUDIO, OTHER

---

### Get Asset Folders

**Query**: `assets.folders`

**GraphQL**:
```graphql
query GetFolders {
  assets {
    folders {
      id
      name
      slug
      parentId
    }
  }
}
```

**Response**:
```json
{
  "data": {
    "assets": {
      "folders": [
        {
          "id": 1,
          "name": "images",
          "slug": "images",
          "parentId": null
        }
      ]
    }
  }
}
```

**Notes**:
- Query before upload to get `folderId` for asset organization
- Folders must be created manually via Admin UI (no mutation available in API)

---

## Error Responses

### GraphQL Error Format

```json
{
  "errors": [
    {
      "message": "You are not authorized to perform this action.",
      "locations": [{"line": 2, "column": 3}],
      "path": ["pages", "create"],
      "extensions": {
        "code": "FORBIDDEN",
        "exception": {
          "stacktrace": ["..."]
        }
      }
    }
  ],
  "data": null
}
```

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `UNAUTHENTICATED` | API key invalid or expired | Generate new API key |
| `FORBIDDEN` | Insufficient permissions | Check API key has `write:pages` and `write:assets` |
| `BAD_USER_INPUT` | Invalid input parameters | Validate input against schema |
| 1001 | Page path already exists | Skip or update existing page |
| 1002 | Invalid page path format | Sanitize path (alphanumeric, hyphens) |

---

## Rate Limiting

- **Recommendation**: Limit to 5 mutations/second to avoid overloading server
- **Batch operations**: Wiki.js GraphQL API does not support batching; process pages sequentially
- **Large uploads**: Images >5MB may timeout; implement retry logic

---

## Testing Contract

### Contract Tests Should Verify

1. Page creation succeeds with valid markdown content
2. Page creation returns `id` and `path` fields
3. Page collision returns `succeeded=false` with errorCode=1001
4. Asset upload succeeds with multipart request
5. Asset upload returns `id` and `filename` fields
6. List pages query returns array with expected fields
7. Get page by path returns correct content
8. Error responses include `message` field

### Mock Response Examples

See `tests/contract/fixtures/wikijs_responses.json` for complete mock data.

---

## GraphQL Schema Types

### PageCreateInput

```graphql
input PageCreateInput {
  content: String!
  description: String
  editor: String!
  isPublished: Boolean
  isPrivate: Boolean
  locale: String!
  path: String!
  publishEndDate: Date
  publishStartDate: Date
  scriptCss: String
  scriptJs: String
  tags: [String]
  title: String!
}
```

### PageUpdateInput

```graphql
input PageUpdateInput {
  content: String
  description: String
  editor: String
  isPrivate: Boolean
  isPublished: Boolean
  locale: String
  path: String
  publishEndDate: Date
  publishStartDate: Date
  scriptCss: String
  scriptJs: String
  tags: [String]
  title: String
}
```

### AssetCreateInput

```graphql
input AssetCreateInput {
  file: Upload!
  folderId: Int
}
```

### AssetKind Enum

```graphql
enum AssetKind {
  IMAGE
  BINARY
  DOCUMENT
  VIDEO
  AUDIO
  OTHER
}
```

---

## Compatibility Notes (Wiki.js 2.x)

**Supported Features**:
- ✅ pages.create, pages.update, pages.list, pages.single
- ✅ assets.createAsset, assets.list, assets.folders
- ✅ API key authentication
- ✅ Multipart file uploads
- ✅ Tag management

**Limitations**:
- ❌ No bulk page creation mutation
- ❌ Folder creation via API (must use Admin UI)
- ❌ No GraphQL subscription support

**Mitigation**: Process pages sequentially with progress checkpointing every 10 pages.
