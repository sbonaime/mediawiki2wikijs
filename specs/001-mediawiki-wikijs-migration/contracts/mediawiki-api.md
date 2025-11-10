# MediaWiki API Contract

**Feature**: 001-mediawiki-wikijs-migration
**API**: MediaWiki Action API
**Minimum Version**: MediaWiki 1.13.5
**Documentation**: https://www.mediawiki.org/wiki/API:Main_page

## Overview

This contract defines the MediaWiki API endpoints and parameters used by the export script. All endpoints support both HTTP and HTTPS. Authentication is required for most operations.

---

## Authentication

### Login

**Endpoint**: `POST /api.php`

**Parameters**:
- `action=login` (required)
- `lgname` (required): Username
- `lgpassword` (required): Password
- `format=json` (required)

**Request Example**:
```http
POST /api.php HTTP/1.1
Content-Type: application/x-www-form-urlencoded

action=login&lgname=BotUser&lgpassword=BotPassword&format=json
```

**Response (Success)**:
```json
{
  "login": {
    "result": "Success",
    "lguserid": 123,
    "lgusername": "BotUser",
    "lgtoken": "abc123def456",
    "cookieprefix": "wiki",
    "sessionid": "xyz789"
  }
}
```

**Response (Failure)**:
```json
{
  "login": {
    "result": "Failed",
    "reason": "Invalid credentials"
  }
}
```

**Notes**:
- Session cookies must be preserved for subsequent requests
- Token may be required for second login attempt (NeedToken response)
- Timeout after 5 minutes of inactivity (re-login required)

---

## Page Operations

### List All Pages

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `list=allpages` (required)
- `aplimit` (optional): Number of pages to return (default: 10, max: 500)
- `apnamespace` (optional): Namespace ID (0=Main, 1=Talk, 2=User, etc.)
- `apcontinue` (optional): Continuation token for pagination
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&list=allpages&aplimit=50&apnamespace=0&format=json
```

**Response**:
```json
{
  "query": {
    "allpages": [
      {
        "pageid": 1,
        "ns": 0,
        "title": "Main Page"
      },
      {
        "pageid": 2,
        "ns": 0,
        "title": "Getting Started"
      }
    ]
  },
  "continue": {
    "apcontinue": "Installation",
    "continue": "-||"
  }
}
```

**Notes**:
- Use `apcontinue` token for pagination
- Available since MW 1.13.5
- Filter by namespace to process specific content types

---

### Get Page Content

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `prop=revisions` (required)
- `rvprop=content|timestamp|user` (required): Properties to retrieve
- `pageids` or `titles` (required): Page identifier
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&prop=revisions&rvprop=content|timestamp|user&titles=Main%20Page&format=json
```

**Response**:
```json
{
  "query": {
    "pages": {
      "1": {
        "pageid": 1,
        "ns": 0,
        "title": "Main Page",
        "revisions": [
          {
            "user": "Admin",
            "timestamp": "2025-11-10T12:00:00Z",
            "*": "Welcome to the wiki!\n\n== Getting Started ==\n..."
          }
        ]
      }
    }
  }
}
```

**Notes**:
- `*` field contains page wikitext content
- Multiple pages can be queried in single request (use `|` separator)
- Available since MW 1.13.5

---

### Get Page Links

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `prop=links` (required)
- `pageids` or `titles` (required)
- `pllimit` (optional): Max links to return (default: 10, max: 500)
- `plcontinue` (optional): Continuation token
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&prop=links&titles=Main%20Page&pllimit=500&format=json
```

**Response**:
```json
{
  "query": {
    "pages": {
      "1": {
        "pageid": 1,
        "title": "Main Page",
        "links": [
          {
            "ns": 0,
            "title": "Getting Started"
          },
          {
            "ns": 0,
            "title": "Installation"
          }
        ]
      }
    }
  }
}
```

---

### Get Page Categories

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `prop=categories` (required)
- `pageids` or `titles` (required)
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&prop=categories&titles=Main%20Page&format=json
```

**Response**:
```json
{
  "query": {
    "pages": {
      "1": {
        "pageid": 1,
        "title": "Main Page",
        "categories": [
          {
            "ns": 14,
            "title": "Category:Documentation"
          }
        ]
      }
    }
  }
}
```

---

## Image Operations

### Get Page Images

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `prop=images` (required)
- `pageids` or `titles` (required)
- `imlimit` (optional): Max images (default: 10, max: 500)
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&prop=images&titles=Main%20Page&imlimit=500&format=json
```

**Response**:
```json
{
  "query": {
    "pages": {
      "1": {
        "pageid": 1,
        "title": "Main Page",
        "images": [
          {
            "ns": 6,
            "title": "File:Logo.png"
          },
          {
            "ns": 6,
            "title": "File:Screenshot.jpg"
          }
        ]
      }
    }
  }
}
```

---

### Get Image Info

**Endpoint**: `GET /api.php`

**Parameters**:
- `action=query` (required)
- `prop=imageinfo` (required)
- `iiprop=url|size|mime` (required)
- `titles` (required): Image filename (e.g., "File:Logo.png")
- `format=json` (required)

**Request Example**:
```http
GET /api.php?action=query&prop=imageinfo&iiprop=url|size|mime&titles=File:Logo.png&format=json
```

**Response**:
```json
{
  "query": {
    "pages": {
      "-1": {
        "title": "File:Logo.png",
        "imageinfo": [
          {
            "url": "https://wiki.example.com/images/a/ab/Logo.png",
            "descriptionurl": "https://wiki.example.com/wiki/File:Logo.png",
            "mime": "image/png",
            "size": 45678,
            "width": 200,
            "height": 100
          }
        ]
      }
    }
  }
}
```

**Notes**:
- Use `url` field to download image
- Available since MW 1.13.5

---

## Error Responses

### Common Error Format

```json
{
  "error": {
    "code": "error_code",
    "info": "Human-readable error message"
  }
}
```

### Common Error Codes

| Code | Meaning | Action |
|------|---------|--------|
| `notloggedin` | Session expired or not authenticated | Re-login |
| `badtoken` | Invalid or expired token | Request new token |
| `nosuchpageid` | Page ID doesn't exist | Skip page |
| `missingtitle` | Page title not found | Skip page |
| `readapidenied` | Read access denied | Check permissions |

---

## Rate Limiting

- **Recommendation**: Limit to 10 requests/second to avoid overloading server
- **Batch operations**: Use multi-value parameters (`titles=Page1|Page2|Page3`) where possible
- **Pagination**: Process in chunks using continuation tokens

---

## Compatibility Notes (MW 1.13.5)

**Supported Features**:
- ✅ action=login
- ✅ action=query with list=allpages
- ✅ prop=revisions, prop=links, prop=categories, prop=images
- ✅ prop=imageinfo
- ✅ Basic pagination with continue tokens

**Limitations**:
- ❌ `prop=pageprops` (added in MW 1.16)
- ❌ `generator` queries (limited in 1.13.5)
- ❌ Some advanced filtering options

**Mitigation**: Feature detection via API meta queries; graceful degradation for optional features.

---

## Testing Contract

### Contract Tests Should Verify

1. Authentication succeeds with valid credentials
2. Page listing returns expected fields (pageid, ns, title)
3. Page content retrieval includes wikitext in `*` field
4. Links property returns array of linked pages
5. Images property returns array of image filenames
6. Image info includes downloadable URL
7. Pagination continues with correct tokens
8. Error responses match expected format

### Mock Response Examples

See `tests/contract/fixtures/mediawiki_responses.json` for complete mock data.
