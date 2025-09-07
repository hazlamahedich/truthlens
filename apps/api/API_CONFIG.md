# API Configuration Guide

## Local Development Setup

1. **Get your NewsAPI key:**
   - Register at https://newsapi.org/register
   - Free tier includes 100 requests/day
   - Copy your API key from the dashboard

2. **Configure local environment:**
   ```bash
   cd apps/api
   cp .env.example .env
   # Edit .env and add your API key
   ```

3. **Set the NEWSAPI_KEY in your .env file:**
   ```
   NEWSAPI_KEY=your_actual_api_key_here
   ```

## Production Setup (Vercel)

1. **Add environment variable in Vercel Dashboard:**
   - Go to your project settings in Vercel
   - Navigate to "Environment Variables"
   - Add a new variable:
     - Key: `NEWSAPI_KEY`
     - Value: Your NewsAPI key
     - Environment: Production, Preview, Development

2. **Using Vercel CLI:**
   ```bash
   vercel env add NEWSAPI_KEY production
   # Paste your API key when prompted
   ```

## Security Best Practices

- **Never commit API keys** to version control
- **.env files** should be in .gitignore
- **Use different keys** for development and production
- **Monitor usage** regularly on NewsAPI dashboard
- **Rotate keys** periodically for security

## ✅ CONFIGURATION STATUS: ACTIVE

**NewsAPI.org Configuration Confirmed:**
- ✅ API Key: f500ed44...a6b5 (ACTIVE)
- ✅ Rate Limit: 100 requests/day  
- ✅ Environment File: `.env.local` (secured)
- ✅ Integration: Tested and working
- ✅ Tests: All 28 tests passing

## Testing the Configuration

To verify your API key is configured correctly:

```python
import os
key = os.getenv("NEWSAPI_KEY")
if key and key != "your_newsapi_key_here":
    print("✅ API key configured")
else:
    print("❌ API key not configured")
```

## Troubleshooting

- **Error: "News API configuration error"**
  - Check that NEWSAPI_KEY is set in environment
  - Verify the key is valid on NewsAPI dashboard

- **Error: "Service temporarily unavailable"**
  - You may have hit the rate limit (100 req/day on free tier)
  - Wait 24 hours or upgrade your plan

- **No results returned**
  - Check your query format
  - Verify API key permissions