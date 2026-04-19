# Runbook: SSL/TLS Handshake Failure

## Error Pattern
`SSL/TLS handshake failed: certificate verify failed`

## Severity
ERROR

## Symptoms
- HTTPS connections failing between services
- `certificate verify failed` errors in logs
- External API integrations returning SSL errors
- Browser showing certificate warnings

## Root Causes
1. **Expired certificate**: TLS certificate has passed its expiration date
2. **Self-signed certificate**: Certificate not signed by a trusted CA
3. **Wrong certificate for domain**: Certificate CN/SAN doesn't match the requested domain
4. **Missing intermediate certificates**: Certificate chain is incomplete

## Resolution Steps

### Step 1: Check certificate details
```bash
# Check certificate expiration
echo | openssl s_client -connect <domain>:443 2>/dev/null | openssl x509 -noout -dates
# Check full certificate chain
echo | openssl s_client -connect <domain>:443 -showcerts
# Check certificate subject and SANs
echo | openssl s_client -connect <domain>:443 2>/dev/null | openssl x509 -noout -subject -ext subjectAltName
```

### Step 2: Renew certificate if expired
```bash
# Using certbot (Let's Encrypt)
certbot renew --cert-name <domain>
# Or generate new certificate
certbot certonly --standalone -d <domain>
```

### Step 3: Update certificate in service
```bash
# Copy new certificates
cp /etc/letsencrypt/live/<domain>/fullchain.pem /app/certs/
cp /etc/letsencrypt/live/<domain>/privkey.pem /app/certs/
# Restart service to pick up new cert
docker restart <service-container>
```

### Step 4: Verify fix
```bash
# Test the connection
curl -v https://<domain>/health
# Check certificate validity
echo | openssl s_client -connect <domain>:443 2>/dev/null | openssl x509 -noout -checkend 0
```

## Prevention
- Set up certificate expiration monitoring (alert at 30, 14, 7 days)
- Automate certificate renewal with certbot cron job
- Use certificate management tools (cert-manager in Kubernetes)
- Monitor certificate transparency logs
