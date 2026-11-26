# Deployment Guide

This guide covers deploying the Smart Plant Care system to production environments.

## Overview

The system consists of two independent deployments:
1. **Frontend**: Static React app → Vercel
2. **Backend**: Python FastAPI server → Railway/Render/Heroku

This separation allows independent scaling and updates.

## Prerequisites

- Supabase project (database and authentication)
- GitHub repository push access
- Vercel account (free tier sufficient)
- Backend hosting account (Railway, Render, or Heroku)

## Environment Variables Reference

### Backend Environment Variables

```env
# Database Connection
DATABASE_URL=postgresql://user:password@host:5432/smartplant

# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
REQUIRE_AUTH=true

# Watering Logic
DAILY_WATERING_LIMIT=3
WATERING_COOLDOWN_MINUTES=60
WATERING_DURATION_SECONDS=30

# Server
CORS_ORIGINS=https://your-frontend-domain.vercel.app
```

### Frontend Environment Variables

```env
VITE_API_URL=https://your-backend-domain/api/v1
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_KEY=your-anon-key
```

## Frontend Deployment (Vercel)

### Option 1: Connect GitHub Repository (Recommended)

1. Go to https://vercel.com/new
2. Select your GitHub repository
3. Configure build settings:
   - **Framework**: Vite
   - **Root Directory**: `./frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`

4. Add environment variables:
   - `VITE_API_URL`
   - `VITE_SUPABASE_URL`
   - `VITE_SUPABASE_KEY`

5. Click "Deploy" - Vercel will auto-deploy on GitHub pushes

### Option 2: Deploy via CLI

```bash
# Install Vercel CLI
npm i -g vercel

# Navigate to frontend directory
cd frontend

# Deploy
vercel --prod
```

### Vercel Features

- **Auto-scaling**: Handles traffic automatically
- **CDN**: Global content delivery
- **Preview deployments**: Auto-preview on PR
- **Serverless functions**: For backend if needed
- **Custom domain**: Point your domain in Vercel dashboard

**Post-deployment:**
1. Update backend CORS_ORIGINS to match Vercel domain
2. Test login flow with Supabase
3. Test API connectivity

## Backend Deployment (Railway)

### Step 1: Prepare Repository

Ensure your repository root has:
- `Procfile` or `vercel.json` or `docker-compose.yml`
- Backend code in `backend/` directory

### Step 2: Deploy on Railway

1. Go to https://railway.app
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway auto-detects Python project
6. Add environment variables in Railway dashboard:
   - `DATABASE_URL`
   - `SUPABASE_URL`
   - `SUPABASE_KEY`
   - `REQUIRE_AUTH=true`

7. Click "Deploy" - Railway builds and deploys automatically

### Step 3: Configure Database

If using Supabase:
1. Create PostgreSQL database in Supabase
2. Copy connection string to `DATABASE_URL`
3. Run migrations via Railway CLI:
   ```bash
   railway run alembic upgrade head
   ```

### Railway Features

- **Easy GitHub integration**: Auto-deploy on push
- **Environment management**: Simple variable setup
- **Logs**: Real-time application logs
- **Monitoring**: CPU/memory usage
- **Scaling**: Adjust resources as needed

## Backend Deployment (Render)

### Step 1: Create New Web Service

1. Go to https://render.com
2. Click "New" → "Web Service"
3. Connect your GitHub account
4. Select the repository
5. Configure:
   - **Name**: `smart-plant-care-api`
   - **Environment**: `Python 3.11`
   - **Build Command**: `pip install -r backend/requirements.txt && cd backend && alembic upgrade head`
   - **Start Command**: `cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - **Root Directory**: Leave empty (project root)

### Step 2: Add Environment Variables

In Render dashboard, add all backend environment variables from the reference above.

### Step 3: Deploy

Render automatically deploys when you push to GitHub.

**Scaling:**
- Adjust CPU/RAM in service settings
- Set up auto-scaling based on metrics

## Database Setup

### Using Supabase (Recommended)

1. Create Supabase project: https://supabase.com
2. Get PostgreSQL connection string from project settings
3. Set `DATABASE_URL` in backend environment
4. Run migrations:
   ```bash
   alembic upgrade head
   ```

### Schema Migration

The database schema is automatically migrated via Alembic:

```bash
# Create migration (if needed)
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Check migration status
alembic current
```

## Health Checks

### Backend Health Endpoint

Configure your hosting to check:
```
GET /health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0"
}
```

### Frontend Health

Vercel automatically checks deployment status. Monitor from:
- Vercel dashboard: https://vercel.com/dashboard
- Railway dashboard: https://railway.app/dashboard
- Render dashboard: https://render.com/dashboard

## Monitoring & Logs

### Backend Logs

**Railway**: 
- View in Railway dashboard under "Logs" tab

**Render**:
- View in Render dashboard under "Logs" tab

**Example log queries:**
```bash
# View real-time logs
railway logs -f

# View error logs
railway logs | grep ERROR
```

### Error Tracking

Monitor application errors:
1. Check deployment logs for startup issues
2. Monitor sensor ingestion errors (failed device auth)
3. Track watering logic errors
4. Monitor alert generation failures

### Database Monitoring

Via Supabase:
1. Go to Supabase dashboard
2. Check storage usage
3. Monitor connection pool
4. Review query logs if issues occur

## Domain Setup

### Add Custom Domain to Frontend (Vercel)

1. Go to Vercel project settings
2. Click "Domains"
3. Enter your domain
4. Update DNS records as instructed
5. Wait for DNS propagation (5-30 minutes)

### Add Custom Domain to Backend (Railway/Render)

**Railway:**
1. Go to service settings
2. Under "Networking", click "Custom Domains"
3. Add your domain
4. Update DNS records (CNAME to railway domain)

**Render:**
1. Go to service settings
2. Under "Domains", add custom domain
3. Update DNS records

## Deployment Checklist

- [ ] Backend environment variables configured
- [ ] Frontend environment variables configured
- [ ] Database migrations applied
- [ ] Health endpoints responding
- [ ] CORS properly configured
- [ ] Authentication working (can log in)
- [ ] Can create plants via UI
- [ ] Can register devices
- [ ] Sensor data ingestion working
- [ ] Alerts generating correctly
- [ ] Dashboard loading without errors

## Troubleshooting

### Common Issues

**Backend returns 401 Unauthorized:**
- Check `SUPABASE_URL` and `SUPABASE_KEY`
- Verify token is being sent in Authorization header
- Check Supabase auth configuration

**Device reads not ingesting:**
- Verify device is registered (check `/devices` endpoint)
- Confirm device status is "active"
- Check device_id matches exactly
- Verify backend is running and reachable

**Dashboard doesn't load:**
- Check `VITE_API_URL` matches backend URL
- Verify CORS allows frontend domain
- Check browser console for errors
- Test API directly with curl/Postman

**Sensor simulator errors:**
- Verify backend is running
- Check `.env` DEVICE_ID matches registered device
- Verify BACKEND_URL in simulator `.env`
- Check network connectivity

### Debug Commands

```bash
# Test backend health
curl https://your-backend-domain/health

# Test API endpoint
curl -H "Authorization: Bearer YOUR_TOKEN" \
  https://your-backend-domain/api/v1/plants

# Test sensor ingestion
curl -X POST https://your-backend-domain/api/v1/sensor-readings \
  -H "Content-Type: application/json" \
  -d '{"device_id":"sensor_001","soil_moisture":50.0,"temperature":22.0,"humidity":60.0}'
```

## Performance Optimization

### Frontend

- Pre-built assets are served from CDN
- JavaScript is minified and code-split
- Images optimized automatically by Vercel
- Monitor build size: `npm run build --report`

### Backend

- Use connection pooling (SQLAlchemy default)
- Optimize database queries (check migrations)
- Monitor slow queries via Supabase
- Scale workers as traffic increases

### Database

- Monitor disk usage in Supabase
- Keep index statistics updated
- Archive old readings if needed
- Use partitioning for very large datasets

## Security Checklist

- [ ] Never commit `.env` files
- [ ] Use strong Supabase JWT keys
- [ ] Enable Supabase row-level security (RLS) if needed
- [ ] Use HTTPS for all communication
- [ ] Rotate secrets regularly
- [ ] Keep dependencies updated: `npm audit`, `pip audit`
- [ ] Enable database backups
- [ ] Use environment-specific secrets

## Rollback Procedure

### Frontend (Vercel)

1. Go to Vercel project
2. Click "Deployments"
3. Find previous deployment
4. Click "Promote to Production"

### Backend (Railway/Render)

**Railway:**
1. Go to "Deployments" tab
2. Find previous deployment
3. Click "Redeploy"

**Render:**
1. Go to "Deploys" tab
2. Click "Deploy" on previous commit

## Scaling

### When to Scale

- API response time > 1 second
- Error rates increasing
- Database connections near limit
- CPU usage consistently > 70%
- Memory usage consistently > 80%

### Scaling Options

**Frontend:**
- Vercel handles auto-scaling automatically
- Upgrade to Pro for advanced features

**Backend:**
- Railway/Render: Increase CPU/RAM in settings
- Database: Increase Supabase plan
- Add read replicas if many concurrent reads

## Maintenance

### Regular Tasks

- Monitor logs weekly
- Review error rates monthly
- Update dependencies quarterly
- Run security audits quarterly
- Review database backups monthly

### Backup Strategy

- Supabase: Automatic daily backups
- Download backups: `Settings > Backups` in Supabase
- Keep local copy of migrations
- Test restore procedure quarterly

## Support & References

- [Vercel Docs](https://vercel.com/docs)
- [Railway Docs](https://docs.railway.app)
- [Render Docs](https://render.com/docs)
- [Supabase Docs](https://supabase.com/docs)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)

---

**Version**: 1.0  
**Last Updated**: November 2026
