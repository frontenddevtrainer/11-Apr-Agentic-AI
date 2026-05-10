# TaskFlow Pro — Known Bugs & Technical Debt

## Active Bugs

### BUG-101: Settings page crash on Android (v3.2.1)
- **Severity**: Critical
- **Affected**: Android devices, v3.2.1
- **Root cause**: Null pointer exception in AccountSettingsFragment when user profile image URL is null
- **Workaround**: None
- **Fix ETA**: v3.2.2 hotfix

### BUG-102: Authentication failure after password reset (v3.2.1)
- **Severity**: Critical
- **Affected**: All platforms, v3.2.1
- **Root cause**: Token refresh endpoint not invalidating old refresh tokens after password change; cached JWT persists
- **Workaround**: Clear app data and re-login
- **Fix ETA**: v3.2.2 hotfix

### BUG-103: Data sync intermittent failures
- **Severity**: High
- **Affected**: All platforms
- **Root cause**: WebSocket reconnection logic has a race condition when switching between WiFi and cellular. Delta sync sometimes drops updates during reconnection window.
- **Workaround**: Force-close and reopen app
- **Fix ETA**: v3.3.0

### BUG-104: Dashboard slow loading (v3.2.0+)
- **Severity**: High
- **Affected**: Users with >100 tasks
- **Root cause**: Dashboard queries are not paginated; loads all tasks with full attachment metadata. N+1 query issue on analytics chart data.
- **Workaround**: Archive completed tasks to reduce count
- **Fix ETA**: v3.2.2

### BUG-105: Push notifications not delivered (iOS)
- **Severity**: High
- **Affected**: iOS 17.3+, v3.2.0
- **Root cause**: APNS certificate expired on 2026-02-28 and was not auto-renewed. Notification registration succeeds but delivery silently fails.
- **Workaround**: None
- **Fix ETA**: v3.2.2 hotfix (certificate renewal)

### BUG-106: File attachment crash >5MB
- **Severity**: High
- **Affected**: Android, v3.2.1
- **Root cause**: Memory allocation issue — entire file loaded into memory before chunked upload. OOM on devices with <6GB RAM for files >5MB.
- **Workaround**: Compress files to <5MB before attaching
- **Fix ETA**: v3.3.0

### BUG-107: Search returning wrong results
- **Severity**: Medium
- **Affected**: All platforms, v3.2.0
- **Root cause**: Elasticsearch index mapping was changed in v3.2.0 migration but old index was not reindexed. Search hits stale index for tasks created before v3.2.0.
- **Workaround**: None
- **Fix ETA**: v3.2.2

### BUG-108: Notification badge count incorrect
- **Severity**: Low
- **Affected**: Android, v3.2.1
- **Root cause**: Badge count decremented on notification dismiss but not on in-app read. Counter drift accumulates over time.
- **Workaround**: Clear all notifications
- **Fix ETA**: v3.3.0

### BUG-109: Startup crash on OnePlus devices (v3.2.1)
- **Severity**: Critical
- **Affected**: OnePlus 12, OnePlus Nord CE, Android 14, v3.2.1
- **Root cause**: OnePlus OxygenOS 14 aggressive memory management kills foreground activity during splash screen database migration. SQLite write-ahead log not properly closed.
- **Workaround**: Disable battery optimization for TaskFlow Pro
- **Fix ETA**: v3.2.2 hotfix

## Technical Debt
- Authentication module uses deprecated OAuth library (needs migration to latest)
- No database connection pooling (causes intermittent 503 under load)
- Attachment upload is synchronous (should be async with progress callback)
- Notification system tightly coupled to Firebase SDK (no abstraction layer)
- Search index rebuild requires full downtime (no zero-downtime reindex)
- Accessibility audit incomplete — many UI elements missing ARIA/accessibility labels
