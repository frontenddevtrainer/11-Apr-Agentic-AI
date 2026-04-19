# Runbook: Database Connection Failure

## Error Pattern
`Database connection failed: ConnectionRefusedError`

## Severity
ERROR / CRITICAL

## Symptoms
- Application logs show `ConnectionRefusedError` with database host and port
- API requests returning 500 errors
- Health checks failing on services that depend on the database

## Root Causes
1. **Database server is down**: The PostgreSQL/MySQL instance has crashed or been stopped
2. **Network connectivity issues**: Firewall rules blocking traffic, network partition
3. **Connection pool exhaustion**: All connections in the pool are in use and none are being released
4. **Wrong credentials or host**: Configuration drift after deployment

## Resolution Steps

### Step 1: Verify database server status
```bash
# Check if the database container is running
docker ps | grep postgres
# Check database logs
docker logs <db-container-id> --tail 100
```

### Step 2: Test direct connectivity
```bash
# Test TCP connectivity
nc -zv <db-host> <db-port>
# Try direct connection
psql -h <db-host> -p <db-port> -U <user> -d <database>
```

### Step 3: Check connection pool
```bash
# Check active connections in PostgreSQL
psql -c "SELECT count(*) FROM pg_stat_activity;"
# Kill idle connections if pool is exhausted
psql -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state = 'idle' AND query_start < now() - interval '10 minutes';"
```

### Step 4: Restart the service
```bash
docker restart <service-container>
# Or via kubernetes
kubectl rollout restart deployment/<service-name>
```

## Prevention
- Set up connection pool monitoring with alerts
- Configure connection timeouts and retry policies
- Use connection health checks in the pool configuration
- Implement circuit breaker pattern for database calls
