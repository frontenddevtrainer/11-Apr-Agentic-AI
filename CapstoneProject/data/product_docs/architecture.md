# TaskFlow Pro — System Architecture

## Overview
TaskFlow Pro is a B2C mobile productivity app with ~10,000 active users. It is available on both Google Play and the Apple App Store.

## Client Apps
- **Android**: Native Kotlin app, minimum SDK 26 (Android 8.0), targets SDK 34 (Android 14)
- **iOS**: Native Swift/SwiftUI app, minimum iOS 16, targets iOS 17
- **Web**: React SPA hosted on Azure App Service

## Backend
- **API Server**: Python FastAPI running on Azure Container Instances
- **Database**: PostgreSQL 15 on Azure Database for PostgreSQL
- **Cache**: Redis 7 on Azure Cache for Redis
- **File Storage**: Azure Blob Storage for user attachments
- **Push Notifications**: Firebase Cloud Messaging (Android), Apple Push Notification Service (iOS)
- **Search**: Elasticsearch 8.x for full-text task search

## Authentication
- OAuth 2.0 with PKCE flow
- JWT tokens with 15-minute access token expiry, 30-day refresh tokens
- Password hashing via bcrypt
- Multi-factor authentication (optional, TOTP-based)

## Data Sync
- Real-time sync via WebSocket connections
- Conflict resolution: last-write-wins with server timestamp
- Offline mode: local SQLite database on mobile, syncs on reconnect
- Sync protocol: delta-based, only changed fields transmitted

## API Endpoints
- `POST /api/v1/auth/login` — User authentication
- `POST /api/v1/auth/register` — User registration
- `GET /api/v1/tasks` — List tasks with pagination
- `POST /api/v1/tasks` — Create task
- `PUT /api/v1/tasks/{id}` — Update task
- `DELETE /api/v1/tasks/{id}` — Delete task
- `POST /api/v1/tasks/{id}/attachments` — Upload attachment (max 10MB)
- `GET /api/v1/projects` — List projects
- `GET /api/v1/notifications` — Get notification feed
- `POST /api/v1/search` — Full-text search across tasks and projects

## Infrastructure
- CI/CD: GitHub Actions
- Monitoring: Azure Monitor + Application Insights
- Logging: Structured JSON logs → Azure Log Analytics
- CDN: Azure Front Door for static assets
