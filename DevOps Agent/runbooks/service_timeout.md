# Runbook: Service Timeout

## Error Pattern
`Timeout waiting for response from service: exceeded deadline`

## Severity
ERROR

## Symptoms
- Upstream service calls timing out
- Increased latency across dependent services
- 504 Gateway Timeout responses
- Request queues building up

## Root Causes
1. **Downstream service overloaded**: Target service can't handle the request volume
2. **Network issues**: Packet loss, DNS resolution delays, or routing problems
3. **Resource contention**: CPU or I/O saturation on the target service
4. **Deadlock or thread starvation**: Application threads blocked waiting on locks
5. **Slow database queries**: Unoptimized queries or missing indexes

## Resolution Steps

### Step 1: Check target service health
```bash
# Check service status
docker ps | grep <service-name>
kubectl get pods -l app=<service-name>
# Check resource usage
docker stats <container-id>
kubectl top pod -l app=<service-name>
```

### Step 2: Check network connectivity
```bash
# Test latency to service
ping <service-host>
# Check DNS resolution
nslookup <service-host>
# Test HTTP endpoint directly
curl -w "@curl-format.txt" -o /dev/null -s http://<service-host>:<port>/health
```

### Step 3: Check for slow queries or locks
```bash
# PostgreSQL: check long-running queries
psql -c "SELECT pid, now() - pg_stat_activity.query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;"
# Check for locks
psql -c "SELECT * FROM pg_locks WHERE NOT granted;"
```

### Step 4: Scale or restart
```bash
# Scale up the service
kubectl scale deployment/<service-name> --replicas=5
# Or restart to clear stuck state
kubectl rollout restart deployment/<service-name>
```

## Prevention
- Implement circuit breaker pattern (e.g., resilience4j, Hystrix)
- Set appropriate timeout values with retries and backoff
- Use connection pooling and request queuing
- Set up latency monitoring and alerting (p95, p99)
- Implement request deadlines that propagate across service calls
