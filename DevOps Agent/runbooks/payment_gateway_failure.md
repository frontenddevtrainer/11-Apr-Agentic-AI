# Runbook: Payment Gateway Failure

## Error Pattern
`Failed to process payment: gateway timeout from stripe/paypal/square`

## Severity
ERROR / CRITICAL

## Symptoms
- Payment processing failing for customers
- Timeout errors from payment gateway APIs
- Orders stuck in "pending payment" state
- Revenue impact - transactions not completing

## Root Causes
1. **Gateway outage**: Payment provider experiencing downtime
2. **API rate limiting**: Exceeding the payment provider's rate limits
3. **Network issues**: Connectivity problems to external payment APIs
4. **Invalid credentials**: API keys expired or rotated
5. **Malformed requests**: Data validation failing at the gateway

## Resolution Steps

### Step 1: Check gateway status
```bash
# Check provider status pages
curl -s https://status.stripe.com/api/v2/status.json | python3 -m json.tool
# Test API connectivity
curl -v https://api.stripe.com/v1/charges -u sk_test_xxx:
# Check for rate limiting headers in responses
```

### Step 2: Review recent errors
```bash
# Check payment service logs
docker logs payment-service --tail 500 | grep -i "payment\|stripe\|error"
# Look for specific error codes
docker logs payment-service --tail 500 | grep -E "rate_limit|authentication|timeout"
```

### Step 3: Verify API credentials
```bash
# Check environment variables
docker exec payment-service env | grep -i stripe
# Verify API key validity (test mode)
curl https://api.stripe.com/v1/balance -u $STRIPE_SECRET_KEY:
```

### Step 4: Implement fallback
```bash
# Switch to backup payment provider if available
# Update feature flag or configuration
# Enable payment queue for retry processing
```

## Prevention
- Implement payment gateway failover (primary + backup provider)
- Set up webhook monitoring for payment events
- Cache and retry failed payments with idempotency keys
- Monitor gateway response times and error rates
- Set up alerts on payment failure rate exceeding 1%
