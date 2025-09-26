# Storage Backend Setup Guide

This guide will help you set up a reliable data storage solution for your contest application that can handle 50k+ responses.

## 🎯 Recommended Solutions (Ranked by Reliability)

### 1. **Supabase (Highly Recommended)**
- **Cost**: Free tier: 500MB storage, 2GB bandwidth, 50k monthly active users
- **Paid**: $25/month for 8GB storage, 250GB bandwidth
- **Capacity**: Easily handles 50k+ records with auto-scaling
- **Pros**: PostgreSQL-based, excellent API, real-time features, built-in auth
- **Setup Time**: 5 minutes

### 2. **Google Sheets API (Reliable Fallback)**
- **Cost**: Free for reasonable usage (100 requests/100 seconds)
- **Capacity**: Can handle 50k+ records (10M cells per sheet)
- **Pros**: Familiar interface, easy backup/export, no server setup
- **Setup Time**: 10 minutes

### 3. **PlanetScale (MySQL Alternative)**
- **Cost**: Free tier: 1GB storage, 1B reads/month
- **Paid**: $29/month for 5GB storage
- **Pros**: Serverless MySQL, excellent scaling, branching
- **Setup Time**: 10 minutes

## 🚀 Quick Setup Instructions

### Option 1: Supabase Setup (Recommended)

1. **Create Supabase Account**
   - Go to [supabase.com](https://supabase.com)
   - Sign up and create a new project
   - Choose a region close to your users

2. **Get Your Credentials**
   - Go to Settings → API
   - Copy your `Project URL` and `anon public` key

3. **Create the Table**
   - Go to SQL Editor in Supabase dashboard
   - Run this SQL:
   ```sql
   CREATE TABLE submissions (
     id TEXT PRIMARY KEY,
     name TEXT NOT NULL,
     email TEXT NOT NULL,
     answer TEXT NOT NULL,
     timestamp TIMESTAMPTZ DEFAULT NOW()
   );
   ```

4. **Configure Environment Variables**
   - In Render dashboard, add these environment variables:
   ```
   STORAGE_BACKEND=supabase
   SUPABASE_URL=https://osegrqquvjvdudwqyjtl.supabase.co
   SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im9zZWdycXF1dmp2ZHVkd3F5anRsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTg3MTg1OTMsImV4cCI6MjA3NDI5NDU5M30.ZyCGAPqXMitlNnCNl_vthgr13zRhtrQqact2CFT2mjU
   ```

### Option 2: Google Sheets Setup (Fallback)

1. **Create Google Sheet**
   - Create a new Google Sheet
   - Add headers in row 1: `ID`, `Name`, `Email`, `Answer`, `Timestamp`
   - Copy the Sheet ID from the URL

2. **Enable Google Sheets API**
   - Go to [Google Cloud Console](https://console.cloud.google.com)
   - Create a new project or select existing
   - Enable Google Sheets API
   - Create credentials (API Key)
   - Restrict the API key to Google Sheets API

3. **Configure Environment Variables**
   ```
   STORAGE_BACKEND=sheets
   GOOGLE_SHEETS_API_KEY=your-api-key
   GOOGLE_SHEET_ID=your-sheet-id
   GOOGLE_SHEET_RANGE=Sheet1!A:E
   ```

### Option 3: PlanetScale Setup (MySQL)

1. **Create PlanetScale Account**
   - Go to [planetscale.com](https://planetscale.com)
   - Create a new database

2. **Create the Table**
   ```sql
   CREATE TABLE submissions (
     id VARCHAR(255) PRIMARY KEY,
     name VARCHAR(255) NOT NULL,
     email VARCHAR(255) NOT NULL,
     answer TEXT NOT NULL,
     timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```

3. **Get Connection String**
   - Go to your database → Connect
   - Copy the connection string

4. **Configure Environment Variables**
   ```
   STORAGE_BACKEND=postgres
   DATABASE_URL=your-planetscale-connection-string
   ```

## 🔧 Deployment Configuration

### Render.com Deployment

1. **Update render.yaml** (already done in your project)
2. **Set Environment Variables** in Render dashboard:
   - `STORAGE_BACKEND`: Choose your preferred backend
   - Add the specific credentials for your chosen backend

### Environment Variables Reference

```bash
# Storage backend selection
STORAGE_BACKEND=supabase  # or 'sheets', 'postgres', 'memory'

# Supabase (recommended)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key

# Google Sheets (fallback)
GOOGLE_SHEETS_API_KEY=your-api-key
GOOGLE_SHEET_ID=your-sheet-id
GOOGLE_SHEET_RANGE=Sheet1!A:E

# PostgreSQL (legacy)
DATABASE_URL=postgresql://user:pass@host:port/db

# CORS
FRONTEND_ORIGINS=https://your-frontend.vercel.app
CORS_ALLOW_ORIGIN_REGEX=https://.*\.vercel\.app
```

## 🧪 Testing Your Setup

1. **Health Check**
   ```bash
   curl https://your-backend.onrender.com/health
   ```
   Should return:
   ```json
   {
     "status": "healthy",
     "database": "connected",
     "storage_method": "supabase"
   }
   ```

2. **Test Submission**
   ```bash
   curl -X POST https://your-backend.onrender.com/submit \
     -H "Content-Type: application/json" \
     -d '{
       "name": "Test User",
       "email": "test@example.com",
       "answer": "This is a test submission"
     }'
   ```

3. **Check Count**
   ```bash
   curl https://your-backend.onrender.com/submissions/count
   ```

## 📊 Capacity Planning

### Supabase
- **Free Tier**: 500MB storage ≈ 100k-200k submissions
- **Pro Tier**: 8GB storage ≈ 1.6M-3.2M submissions
- **Auto-scaling**: Handles traffic spikes automatically

### Google Sheets
- **Limits**: 10M cells per sheet
- **Your Data**: 5 columns × 50k rows = 250k cells
- **Headroom**: 9.75M cells remaining
- **Rate Limits**: 100 requests per 100 seconds

### PlanetScale
- **Free Tier**: 1GB storage ≈ 200k-400k submissions
- **Pro Tier**: 5GB storage ≈ 1M-2M submissions
- **Serverless**: Scales automatically

## 🔄 Fallback Strategy

The new backend automatically falls back through this order:
1. **Supabase** (if configured)
2. **Google Sheets** (if configured)
3. **PostgreSQL** (if configured)
4. **In-memory storage** (always works, but data is lost on restart)

## 🚨 Troubleshooting

### Common Issues

1. **"Storage backend failed"**
   - Check environment variables are set correctly
   - Verify credentials are valid
   - Check network connectivity

2. **"CORS errors"**
   - Update `FRONTEND_ORIGINS` with your Vercel URL
   - Check `CORS_ALLOW_ORIGIN_REGEX` is set

3. **"Database connection failed"**
   - Verify connection strings
   - Check SSL requirements
   - Ensure database is accessible from Render

### Debug Mode

Enable debug logging:
```bash
ENVIRONMENT=development
```

## 📈 Monitoring

Monitor your storage usage:
- **Supabase**: Dashboard shows usage metrics
- **Google Sheets**: Check sheet size and API quotas
- **PlanetScale**: Dashboard shows connection and usage stats

## 💡 Recommendations

1. **Start with Supabase** - Most reliable and feature-rich
2. **Keep Google Sheets as backup** - Easy to export data
3. **Monitor usage** - Upgrade before hitting limits
4. **Test fallbacks** - Ensure your app works even if primary storage fails

## 🆘 Support

If you encounter issues:
1. Check the logs in Render dashboard
2. Test with the health endpoint
3. Verify environment variables
4. Try the fallback storage options

The new multi-storage backend ensures your contest will work reliably even if one storage option fails!
