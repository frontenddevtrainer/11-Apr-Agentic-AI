# Runbook: Out of Memory (OOM) Error

## Error Pattern
`OutOfMemoryError: Java heap space - container killed by OOM`

## Severity
ERROR / CRITICAL

## Symptoms
- Container restarting unexpectedly
- `OOMKilled` status in Kubernetes pod descriptions
- Sudden drop in request throughput
- Java heap space errors in application logs

## Root Causes
1. **Memory leak**: Application code not releasing references to objects
2. **Undersized container limits**: Memory limits set too low for the workload
3. **Traffic spike**: Sudden increase in concurrent requests consuming more memory
4. **Large payload processing**: Processing unusually large files or datasets in memory

## Resolution Steps

### Step 1: Check container memory status
```bash
# Check current memory usage
docker stats <container-id>
# Check if OOM killed
docker inspect <container-id> | grep -i oom
# Kubernetes: check pod events
kubectl describe pod <pod-name> | grep -A5 "Events"
```

### Step 2: Analyze heap dump (Java services)
```bash
# Generate heap dump
docker exec <container> jmap -dump:format=b,file=/tmp/heap.hprof <pid>
# Copy heap dump out
docker cp <container>:/tmp/heap.hprof ./heap.hprof
# Analyze with Eclipse MAT or jhat
```

### Step 3: Increase memory limits (temporary fix)
```bash
# Update docker-compose
# memory: 512m -> memory: 1g

# Kubernetes: patch deployment
kubectl patch deployment <name> -p '{"spec":{"template":{"spec":{"containers":[{"name":"<container>","resources":{"limits":{"memory":"1Gi"}}}]}}}}'
```

### Step 4: Restart affected containers
```bash
docker restart <container-id>
kubectl delete pod <pod-name>  # Let deployment recreate it
```

## Prevention
- Set JVM heap size to 75% of container memory limit
- Configure `-XX:+HeapDumpOnOutOfMemoryError` for automatic heap dumps
- Set up memory usage alerts at 80% threshold
- Implement request payload size limits
- Use streaming for large file processing instead of loading into memory
