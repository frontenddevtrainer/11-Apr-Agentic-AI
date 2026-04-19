# Runbook: Disk Full Error

## Error Pattern
`Disk full on /var/log: write failed with errno 28 (No space left on device)`

## Severity
ERROR / CRITICAL

## Symptoms
- Applications unable to write logs or data
- Database write operations failing
- Container unable to start due to no disk space
- `errno 28` or `No space left on device` in logs

## Root Causes
1. **Log file accumulation**: Logs growing unbounded without rotation
2. **Temporary files not cleaned up**: Build artifacts or temp files filling disk
3. **Docker images/volumes**: Unused Docker images consuming space
4. **Database WAL files**: Write-ahead log files accumulating

## Resolution Steps

### Step 1: Check disk usage
```bash
# Check overall disk usage
df -h
# Find largest directories
du -sh /* | sort -rh | head -20
# Check Docker disk usage
docker system df
```

### Step 2: Clean up log files
```bash
# Truncate large log files (preserves file descriptors)
truncate -s 0 /var/log/large-log-file.log
# Remove old rotated logs
find /var/log -name "*.gz" -mtime +7 -delete
```

### Step 3: Clean up Docker resources
```bash
# Remove unused containers, networks, images
docker system prune -a --volumes
# Remove dangling volumes
docker volume prune
```

### Step 4: Expand storage if needed
```bash
# Check available volumes (cloud)
# Resize EBS volume (AWS) or persistent disk (GCP)
# Extend filesystem
resize2fs /dev/xvda1
```

## Prevention
- Configure log rotation with size and time-based policies
- Set up disk usage alerts at 70% and 85% thresholds
- Schedule regular Docker cleanup via cron
- Implement log retention policies (max 7-14 days)
- Monitor disk I/O and growth trends in Grafana
