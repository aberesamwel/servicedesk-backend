# ServiceDesk Backend API Documentation

## Overview
Complete REST API for IT ServiceDesk management system with advanced analytics, reporting, and notification features.

## Base URL
```
http://localhost:5000/api
```

## Authentication
All protected endpoints require JWT token in Authorization header:
```
Authorization: Bearer <jwt_token>
```

## Endpoints

### Analytics
- `GET /analytics/dashboard` - Dashboard metrics
- `GET /analytics/ticket-status-counts` - Ticket counts by status
- `GET /analytics/agent-workload` - Agent workload distribution
- `GET /analytics/trends?days=30` - Ticket trends
- `GET /analytics/forecasting` - Volume forecasting
- `GET /analytics/performance-metrics?days=30` - Performance metrics

### Reports
- `GET /reports/summary?days=30` - Summary report
- `GET /reports/agent-performance?days=30` - Agent performance
- `GET /reports/sla-compliance?days=30` - SLA compliance
- `GET /reports/cache/stats` - Cache statistics
- `POST /reports/cache/clear` - Clear cache

### Export
- `GET /export/tickets/excel` - Export tickets to CSV
- `GET /export/tickets/pdf` - Export tickets to PDF
- `GET /export/templates` - Available export templates

### SLA Management
- `GET /sla/dashboard` - SLA dashboard
- `GET /sla/violations` - Current violations
- `GET /sla/forecast?hours=24` - Violation forecast
- `GET /sla/trends?days=30` - SLA trends

### Users
- `GET /users/` - Get all users
- `GET /users/<user_id>` - Get specific user
- `POST /users/` - Create user
- `PUT /users/<user_id>` - Update user
- `DELETE /users/<user_id>` - Delete user
- `GET /users/<user_id>/notifications/preferences` - Get preferences
- `PUT /users/<user_id>/notifications/preferences` - Update preferences
- `POST /users/<user_id>/notifications/test` - Send test notification

## Query Parameters

### Common Filters
- `status` - Filter by ticket status
- `priority` - Filter by priority level
- `category` - Filter by category
- `assigned_to` - Filter by assigned agent
- `start_date` - Start date (ISO format)
- `end_date` - End date (ISO format)
- `days` - Number of days for reports

### Pagination
- `page` - Page number (default: 1)
- `per_page` - Items per page (default: 20)

## Response Format

### Success Response
```json
{
  "data": {...},
  "status": "success",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### Error Response
```json
{
  "error": "Error Type",
  "message": "Detailed error message",
  "status_code": 400
}
```

## Status Codes
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Rate Limit Exceeded
- `500` - Internal Server Error

## Rate Limiting
- 100 requests per minute per IP
- 1000 requests per hour per authenticated user

## Caching
- Analytics endpoints cached for 1 hour
- Reports cached for 30 minutes
- Cache can be cleared via `/reports/cache/clear`