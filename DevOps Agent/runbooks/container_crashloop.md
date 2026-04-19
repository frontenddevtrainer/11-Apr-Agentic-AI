# Runbook: Container CrashLoopBackOff

## Error Pattern
`Container CrashLoopBackOff: restart count exceeding threshold`

## Severity
ERROR / CRITICAL

## Symptoms
- Pod status showing `CrashLoopBackOff`
- Container restart count increasing rapidly
- Service unavailable or degraded
- Exponential backoff delays between restarts

## Root Causes
1. **Application crash on startup**: Missing config, bad environment variables, or dependency not available
2. **Liveness probe failure**: Health check endpoint not responding in time
3. **Resource limits too low**: Container OOM killed immediately on start
4. **Image issues**: Wrong image tag, missing entrypoint, or corrupted image
5. **Volume mount failures**: PersistentVolume not available or permissions wrong

## Resolution Steps

### Step 1: Check container logs
```bash
# Docker
docker logs <container-id> --tail 200
# Kubernetes - current and previous container logs
kubectl logs <pod-name> --previous
kubectl logs <pod-name>
# Check events
kubectl describe pod <pod-name>
```

### Step 2: Check configuration
```bash
# Verify environment variables
docker exec <container-id> env
kubectl exec <pod-name> -- env
# Check mounted volumes
kubectl describe pod <pod-name> | grep -A10 "Volumes:"
# Verify config maps and secrets exist
kubectl get configmap,secret -n <namespace>
```

### Step 3: Test the container locally
```bash
# Run the container interactively to debug
docker run -it --entrypoint /bin/sh <image>:<tag>
# Check if the application starts
docker run --rm <image>:<tag>
```

### Step 4: Fix and redeploy
```bash
# If config issue, update and restart
kubectl rollout restart deployment/<name>
# If image issue, update image
kubectl set image deployment/<name> <container>=<image>:<new-tag>
# Watch rollout
kubectl rollout status deployment/<name>
```

## Prevention
- Implement proper startup probes with generous initial delay
- Use init containers for dependency checks
- Set appropriate resource requests and limits
- Test container images in staging before production
- Use readiness probes to prevent traffic to unhealthy pods
