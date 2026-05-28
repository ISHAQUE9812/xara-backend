# XARA Backend - Deployment Guide

## Prerequisites

- Server with Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed
- Domain name (optional, for HTTPS)
- MongoDB instance (managed service or Docker)

## Deployment Methods

### Method 1: Docker Compose (Recommended for Development)

1. **Clone Repository**
```bash
git clone <repository-url>
cd xara-backend
```

2. **Create .env file**
```bash
cp .env.example .env
# Edit .env with production values
```

3. **Build and Run**
```bash
docker-compose up -d
```

4. **Verify Deployment**
```bash
curl http://localhost:8000/health
```

### Method 2: Manual Deployment

1. **System Dependencies**
```bash
sudo apt-get update
sudo apt-get install -y python3.9 python3-pip mongodb
```

2. **Setup Virtual Environment**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

3. **Create .env file**
```bash
cp .env.example .env
# Edit with production settings
```

4. **Run with Supervisor/Systemd**

Create `/etc/systemd/system/xara-api.service`:
```ini
[Unit]
Description=XARA Smart Signage API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/path/to/xara-backend
Environment="PATH=/path/to/xara-backend/venv/bin"
ExecStart=/path/to/xara-backend/venv/bin/python run.py
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable xara-api
sudo systemctl start xara-api
```

### Method 3: Heroku Deployment

1. **Create Procfile**
```
web: python run.py
```

2. **Create runtime.txt**
```
python-3.9.0
```

3. **Deploy**
```bash
heroku create xara-api
git push heroku main
```

## Nginx Configuration

Create `/etc/nginx/sites-available/xara-api`:

```nginx
upstream xara_api {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.xara.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.xara.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    client_max_body_size 100M;

    location / {
        proxy_pass http://xara_api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /path/to/xara-backend/static;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/xara-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

## SSL/TLS with Let's Encrypt

```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d api.xara.com
```

## MongoDB Setup

### Remote MongoDB Atlas

1. Create account at https://www.mongodb.com/cloud/atlas
2. Create cluster and database
3. Get connection string
4. Update `MONGODB_URL` in .env

### Self-hosted MongoDB

```bash
# Docker
docker run -d \
  -p 27017:27017 \
  -e MONGO_INITDB_ROOT_USERNAME=admin \
  -e MONGO_INITDB_ROOT_PASSWORD=securepassword \
  -v mongo_data:/data/db \
  mongo:6.0

# Or install locally
sudo apt-get install -y mongodb-org
sudo systemctl start mongod
```

## Environment Variables

Production `.env`:
```
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
DATABASE_NAME=xara_db_prod
SECRET_KEY=<generate-strong-key>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=3000
ENVIRONMENT=production
DEBUG=False
```

Generate SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Performance Optimization

### 1. Database Indexing
```python
# Run once to create indexes
db.screens.create_index([("screen_id", 1)])
db.campaigns.create_index([("assigned_screens", 1)])
db.analytics.create_index([("screen_id", 1), ("timestamp", -1)])
```

### 2. Gunicorn Configuration

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app.main:app
```

### 3. Redis Caching (Optional)

```bash
docker run -d -p 6379:6379 redis:7
```

Update app to use Redis for caching.

## Monitoring & Logging

### Logs
```bash
# View application logs
sudo journalctl -u xara-api -f

# Docker logs
docker-compose logs -f api
```

### Monitoring Tools
- **Prometheus**: Metrics collection
- **Grafana**: Visualization
- **ELK Stack**: Log aggregation

### Health Check
```bash
curl https://api.xara.com/health
```

## Backup Strategy

### MongoDB Backup
```bash
# Backup
mongodump --uri="mongodb://user:password@host:27017/xara_db" --out=/path/to/backup

# Restore
mongorestore --uri="mongodb://user:password@host:27017" /path/to/backup
```

### Automated Backup (cron)
```bash
0 2 * * * /path/to/backup-script.sh
```

## Security Checklist

- [ ] Change all default passwords
- [ ] Enable firewall (ufw/iptables)
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure CORS properly
- [ ] Implement rate limiting
- [ ] Enable MongoDB authentication
- [ ] Regular security updates
- [ ] Monitor logs for suspicious activity
- [ ] Setup automated backups
- [ ] Use environment variables for secrets
- [ ] Enable API key rotation
- [ ] Setup DDoS protection (CloudFlare, AWS Shield)

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Build Docker image
        run: docker build -t xara-api .
      
      - name: Run tests
        run: docker-compose run api pytest
      
      - name: Push to Docker Hub
        run: docker push xara-api
      
      - name: Deploy
        run: |
          ssh user@server 'cd xara-backend && docker-compose pull && docker-compose up -d'
```

## Troubleshooting

### Service won't start
```bash
# Check logs
docker-compose logs api

# Verify configuration
python -c "from app.core.config import settings; print(settings.MONGODB_URL)"
```

### High memory usage
```bash
# Check running processes
docker stats

# Optimize MongoDB
# Add indexes, remove old analytics data
```

### Connection timeouts
- Check network connectivity
- Verify firewall rules
- Check MongoDB connection string
- Increase timeout values

## Scaling

### Load Balancing
- Use HAProxy or Nginx to distribute traffic
- Run multiple API instances

### Database Optimization
- Implement read replicas
- Use MongoDB sharding for large datasets
- Implement caching layer (Redis)

### WebSocket Scaling
- Use Redis Pub/Sub for multi-instance WebSocket
- Implement load balancing for WebSocket connections

## Monitoring Queries

Get connected screens:
```javascript
db.screens.find({status: "online"}).count()
```

Top campaigns by impressions:
```javascript
db.analytics.aggregate([
  {$group: {_id: "$campaign_id", total: {$sum: "$impressions"}}},
  {$sort: {total: -1}}
])
```

## Support

For issues, check:
1. Application logs
2. MongoDB status
3. Network connectivity
4. Environment variables
5. API documentation at `/docs`

---

**XARA Backend Deployment Guide v1.0**
