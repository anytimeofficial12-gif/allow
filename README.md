# ANYTIME Contest Landing Page

A modern, responsive landing page for the ANYTIME contest with a FastAPI backend hosted on Render and PostgreSQL (Supabase/Render).

## 🚀 Quick Start

### Local Development

1. **Setup Environment**
   ```bash
   python setup_local.py
   ```

2. **Start Backend**
   ```bash
   pip install -r backend/requirements.txt
   uvicorn backend.main:app --reload
   ```

3. **Open Frontend**
   - Open `index.html` in your browser, or
   - Use a local server: `python -m http.server 3000`

### Production Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for detailed deployment instructions.

**Quick Deploy:**
- **Frontend**: Deploy to Vercel (static)
- **Backend**: Deploy to Render (FastAPI)
- **Set**: `DATABASE_URL` env var on your platform
- **Update**: Backend URL in `config.js` only if backend is on a different origin

## 📁 Project Structure

```
├── Frontend Files
│   ├── index.html          # Main landing page
│   ├── script.js           # Frontend logic
│   ├── config.js           # Configuration
│   └── anytime-logo.png    # Logo
│
├── Backend Files
│   ├── backend/main.py     # FastAPI server (Render)
│   ├── backend/requirements.txt    # Backend dependencies
│   └── backend/render.yaml # Render config
│
└── Documentation
    ├── DEPLOYMENT.md       # Deployment guide
    └── README.md          # This file
```

## ⚙️ Configuration

### Frontend Configuration (`config.js`)
```javascript
const CONFIG = {
    API_BASE_URL: 'http://localhost:8000',  // Backend URL for local dev; '/api' on Vercel
    // ... other settings
};
```

### Backend Configuration
Set environment variables:
- `ENVIRONMENT=production`
- `DATABASE_URL=postgresql://USER:PASSWORD@HOST:PORT/DBNAME`

## 🔧 Features

- ✅ Responsive design
- ✅ Form validation
- ✅ PostgreSQL integration
- ✅ Error handling
- ✅ Loading states
- ✅ Accessibility features
- ✅ SEO optimized
- ✅ Production ready

## 🛠️ Tech Stack

**Frontend:**
- HTML5, CSS3, JavaScript (ES6+)
- Responsive design
- Modern CSS animations

**Backend:**
- Python 3.8+
- FastAPI
- psycopg 3 (PostgreSQL)
- CORS enabled

## 📱 Browser Support

- Chrome 60+
- Firefox 60+
- Safari 12+
- Edge 79+

## 🔒 Security

- Input validation
- CORS configuration
- Environment variables for secrets
- HTTPS in production

## 📊 Monitoring

- Health check endpoint: `/health`
- Error logging
- Performance monitoring

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details

## 🆘 Support

For issues or questions:
1. Check [DEPLOYMENT.md](DEPLOYMENT.md) for deployment help
2. Review the troubleshooting section
3. Check application logs
4. Open an issue on GitHub

## 🎯 Contest Details

- **Prize**: ₹500 for top 10 accurate guesses
- **Duration**: September 20 - October 5, 2025
- **App Launch**: October 6, 2025

---

**ANYTIME** - Revolutionary Service Platform
