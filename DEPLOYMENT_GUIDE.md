# ServiceDesk Backend Deployment Guide

## Overview
Complete deployment guide for the ServiceDesk Backend API with Docker, PostgreSQL, and Redis.

## Prerequisites
- Docker and Docker Compose
- Git
- 4GB+ RAM
- 10GB+ disk space

## Quick Start

### 1. Clone Repository
```bash
git clone <repository-url>
cd servicedesk-backend
```

### 2. Environment Setup
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Docker Deployment
```bash
docker-compose up -d
```

### 4. Database Migration
```bash
docker-compose exec web flask db upgrade
```

## Configuration

### Environment Variables
- `SECRET_KEY` - Flask secret key
- `DATABASE_URL` - PostgreSQL connection string
- `REDIS_URL` - Redis connection string
- `MAIL_*` - Email configuration

### Database Setup
```bash
# Create database
docker-compose exec db createdb -U servicedesk servicedesk

# Run migrations
docker-compose exec web flask db init
docker-compose exec web flask db migrate
docker-compose exec web flask db upgrade
```

## Services

### Web Application
- **Port:** 5000
- **Health Check:** http://localhost:5000/health
- **API Docs:** http://localhost:5000/api/docs

### Database
- **Service:** PostgreSQL 13
- **Port:** 5432
- **Database:** servicedesk

### Cache
- **Service:** Redis 6
- **Port:** 6379

## Monitoring

### Logs
```bash
# Application logs
docker-compose logs web

# Database logs
docker-compose logs db

# All services
docker-compose logs
```

### Health Checks
- Application: `GET /health`
- Database: `docker-compose exec db pg_isready`
- Redis: `docker-compose exec redis redis-cli ping`

## Scaling

### Horizontal Scaling
```yaml
web:
  scale: 3
```

### Load Balancing
Configure Nginx upstream for multiple web instances.

## Backup

### Database Backup
```bash
docker-compose exec db pg_dump -U servicedesk servicedesk > backup.sql
```

### Redis Backup
```bash
docker-compose exec redis redis-cli BGSAVE
```

## Security

### Production Checklist
- [ ] Change default passwords
- [ ] Enable SSL/TLS
- [ ] Configure firewall
- [ ] Set up monitoring
- [ ] Enable log rotation
- [ ] Configure backup strategy

## Troubleshooting

### Common Issues
1. **Port conflicts** - Change ports in docker-compose.yml
2. **Memory issues** - Increase Docker memory limit
3. **Database connection** - Check DATABASE_URL
4. **Redis connection** - Verify REDIS_URL

### Debug Mode
```bash
# Enable debug logging
export FLASK_ENV=development
docker-compose up
```

## Performance Tuning

### Database
- Connection pooling
- Query optimization
- Index creation

### Redis
- Memory optimization
- Persistence configuration
- Cluster setup for high availability

### Application
- Gunicorn worker tuning
- Caching strategy
- Load balancing