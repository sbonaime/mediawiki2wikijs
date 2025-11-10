# Security Policy

## Supported Versions

We release patches for security vulnerabilities. Currently supported versions:

| Version | Supported          |
| ------- | ------------------ |
| 0.9.x   | :white_check_mark: |
| < 0.9   | :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability, please do the following:

1. **Do NOT create a public GitHub issue**
2. Email the maintainers at [bonaime@ipgp.fr]
3. Include the following information:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond within 48 hours and provide a timeline for a fix.

## Security Considerations

### Credentials Storage

- **Never commit `.env` files** to version control
- Use `.env.example` as a template only
- Store credentials securely (password managers, secret stores)
- Rotate API keys regularly

### Network Security

- Always use HTTPS for MediaWiki and Wiki.js connections
- Verify SSL certificates in production
- Use API keys instead of username/password when possible
- Implement rate limiting to avoid overwhelming servers

### Data Protection

- Exported data contains full wiki content - protect accordingly
- Use appropriate file system permissions on export directories
- Consider encrypting sensitive exports at rest
- Delete temporary exports after successful migration

### Dependencies

We regularly update dependencies to patch security vulnerabilities:

- `requests` - HTTP library with security patches
- `mwclient` - MediaWiki client with authentication handling
- `gql` - GraphQL client with transport security
- `pypandoc` - Pandoc wrapper (requires system Pandoc)

Run `pip list --outdated` to check for updates.

## Best Practices

### For Developers

1. **Input Validation**: Validate all user inputs
2. **Error Handling**: Don't expose sensitive information in error messages
3. **Logging**: Sanitize logs to remove credentials
4. **Dependencies**: Keep dependencies updated
5. **Code Review**: All PRs require review before merge

### For Users

1. **Test First**: Use dry-run mode before production migration
2. **Backup**: Backup both source and target before migration
3. **Review**: Check exported data before import
4. **Monitor**: Watch logs during migration
5. **Verify**: Use verification tools after import

## Disclosure Policy

We follow responsible disclosure:

1. Security issue reported privately
2. Fix developed and tested
3. Patch released
4. Public disclosure after users have time to update (typically 30 days)

Thank you for helping keep this project secure!
