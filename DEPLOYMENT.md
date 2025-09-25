# ANYTIME Contest Landing Page - Deployment Guide (Vercel + Render)

## Project Structure

```
lnd/
├── Frontend (Static Files)
│   ├── index.html          # Main landing page
│   ├── script.js           # Frontend JavaScript
│   ├── config.js           # Configuration file
│   ├── style.css           # Additional styles (if used)
│   ├── logo.png            # Logo image
│   ├── vercel.json         # Vercel configuration
│   └── package.json        # Node.js package info
│
├── Backend (FastAPI + PostgreSQL)
│   ├── app.py              # FastAPI application
│   ├── requirements.txt    # Python dependencies
│   ├── Procfile           # Heroku deployment (optional)
│   ├── runtime.txt        # Python version (optional)
│   └── env.example        # Environment variables template
│
├── Serverless (Vercel Functions)
│   └── api/index.py       # Vercel Python function that imports FastAPI app
│
└── Documentation
    └── DEPLOYMENT.md      # This file
```

## Final Architecture

- Frontend: Static site on Vercel from repo root. API calls to `/api/*` are rewritten to Render backend.
- Backend: FastAPI on Render under `backend/`, pooled PostgreSQL connections.
- Database: Supabase or Render PostgreSQL via `DATABASE_URL`.

## Deploy Backend on Render

1. Push repo to GitHub.
2. Create a Web Service on Render with this repo. Render reads `backend/render.yaml`.
3. Set environment variables:
   - `DATABASE_URL`: your Postgres connection string (Supabase/Render)
   - `ENVIRONMENT`: `production`
   - `FRONTEND_ORIGIN`: your Vercel domain, e.g. `https://yourapp.vercel.app`
   - `DB_POOL_MAX_SIZE`: `20` (optional)
4. Deploy. Render builds with `pip install -r backend/requirements.txt` and starts `uvicorn backend.main:app`.

## Deploy Frontend on Vercel

1. Import repo into Vercel as a static project.
2. Edit `vercel.json`: replace `RENDER_BACKEND_URL` with your Render hostname.
3. Deploy. `config.js` uses `/api` in production, which Vercel rewrites to the backend.

### Prerequisites
- Vercel account (free tier available)
- GitHub repository with your code

### Steps

1. **No frontend URL change needed**
   - `config.js` is already set to use `/api` in production, which matches Vercel serverless routes.

2. **Deploy to Vercel**
   ```bash
   # Install Vercel CLI
   npm i -g vercel
   
   # Deploy
   vercel
   
   # Or connect your GitHub repo to Vercel dashboard
   ```

3. **Configure Environment Variables** (required)
   - Go to Vercel Dashboard → Project → Settings → Environment Variables
   - Add and apply to Preview and Production:
     - `ENVIRONMENT = production`
     - `DATABASE_URL = postgresql://USER:PASSWORD@HOST:PORT/DBNAME?sslmode=require`
     - `ALLOW_ALL_ORIGINS = true` (or set explicit origins)

4. **Provision PostgreSQL**
   - Use a managed Postgres provider (Neon, Supabase, Render, Railway, Heroku Postgres, RDS, etc.)
   - Ensure your `DATABASE_URL` includes `sslmode=require` for serverless providers
   - The app will auto-create the `submissions` table on first run

5. **Redeploy**
   - Trigger a redeploy so the new environment variables take effect.

## Backend Deployment Options

### Option 1: Railway

If you host the backend outside Vercel, Railway provides easy Python deployment with automatic scaling.

#### Steps:
1. **Create Railway Account**
   - Go to [railway.app](https://railway.app)
   - Sign up with GitHub

2. **Deploy Backend**
   ```bash
   # Install Railway CLI
   npm install -g @railway/cli
   
   # Login and deploy
   railway login
   railway init
   railway up
   ```

3. **Configure Environment Variables**
   - Go to Railway Dashboard → Variables
   - Add the following variables:
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/railway
   ALLOW_ALL_ORIGINS=true
   ```

4. **Get Backend URL**
   - Railway will provide a URL like: `https://your-app.railway.app`
   - If frontend stays on Vercel only, update `API_BASE_URL` in `config.js` to this URL.

### Option 2: Render

Render offers free tier for Python applications.

#### Steps:
1. **Create Render Account**
   - Go to [render.com](https://render.com)
   - Sign up with GitHub

2. **Create Web Service**
   - Connect your GitHub repository
   - Choose "Web Service"
   - Configure:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`

3. **Configure Environment Variables**
   - Add:
   ```
   ENVIRONMENT=production
   DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
   ALLOW_ALL_ORIGINS=true
   ```

### Option 3: Heroku

Heroku provides reliable hosting with easy deployment.

#### Steps:
1. **Create Heroku Account**
   - Go to [heroku.com](https://heroku.com)
   - Install Heroku CLI

2. **Deploy**
   ```bash
   # Login to Heroku
   heroku login
   
   # Create app
   heroku create your-app-name
   
   # Add Postgres addon (or use external DB URL)
   heroku addons:create heroku-postgresql:mini

   # Set environment variables
   heroku config:set ENVIRONMENT=production
   # If using external Postgres, set DATABASE_URL explicitly; otherwise Heroku sets it automatically
   # heroku config:set DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME
   
   # Deploy
   git push heroku main
   ```

## Database Setup (PostgreSQL)

The application auto-creates the `submissions` table if it doesn't exist. To initialize manually, run:

```sql
CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  email TEXT NOT NULL,
  answer TEXT NOT NULL,
  timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

## Configuration Updates

### Frontend Configuration (`config.js`)
```javascript
const CONFIG = {
    API_BASE_URL: 'https://your-backend-url.railway.app', // Update this
    // ... other settings
};
```

### Backend CORS Configuration (`app.py`)
```python
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Local development
    "https://your-frontend-url.vercel.app",  # Update this
]
```

## Testing Deployment

### 1. Test Backend (Render)
```bash
# Health check
curl https://your-backend.onrender.com/health

# Expected response:
{
  "status": "healthy",
  "environment": "production",
  "database": "connected",
  "cors_origins": [...],
  "timestamp": "..."
}
```

### 2. Test Frontend
1. Visit your Vercel URL
2. Open browser developer tools
3. Check console for any errors
4. Test form submission

### 3. Test Integration
1. Fill out the contest form
2. Submit and verify success message
3. Verify the record exists in your Postgres database (`submissions` table)

## Troubleshooting

### Common Issues

1. **CORS Errors**
   - Ensure frontend URL is in backend's `ALLOWED_ORIGINS`
   - Check that backend is running and accessible

2. **Database Connection Failed**
   - Verify `DATABASE_URL` is correct and reachable
   - Ensure SSL requirements are met (`sslmode=require` if needed)
   - Check database user permissions for creating tables and inserting rows

3. **Form Submission Fails**
   - Check browser network tab for error details
   - Verify backend URL in `config.js`
   - Ensure backend is running and healthy

4. **Static Assets Not Loading**
   - Verify all file paths are relative
   - Check that all files are included in deployment

### Debug Mode
Enable debug mode by setting `ENVIRONMENT=development` in backend environment variables.

## Security Considerations

1. **Environment Variables**
   - Never commit sensitive data to version control
   - Use environment variables for all secrets
   - Rotate service account keys regularly

2. **CORS Configuration**
   - Only allow necessary origins in production
   - Avoid using wildcard (*) in production

3. **Input Validation**
   - Backend validates all form inputs
   - Frontend provides user-friendly error messages

## Monitoring

### Backend Health
- Use `/health` endpoint for monitoring
- Check logs for errors and performance issues

### Frontend Performance
- Monitor page load times
- Check for JavaScript errors in browser console
- Verify form submissions are working

## Updates and Maintenance

### Frontend Updates
1. Update code in your repository
2. Vercel will automatically redeploy
3. Test the updated site

### Backend Updates
1. Update code in your repository
2. Redeploy using your chosen platform's method
3. Test API endpoints

### Configuration Changes
1. Update environment variables in your deployment platform
2. Restart the application
3. Test functionality

## Support

For issues or questions:
- Check the troubleshooting section above
- Review platform-specific documentation
- Check application logs for error details

## Cost Considerations

### Free Tiers
- **Vercel**: Free for personal projects
- **Railway**: $5/month after free tier
- **Render**: Free tier available
- **Heroku**: No longer offers free tier

### Scaling
- Monitor usage and upgrade plans as needed
- Consider caching strategies for high traffic
- Optimize images and assets for better performance
