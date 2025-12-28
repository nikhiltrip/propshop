# PropShop Dashboard - Quick Start Guide

## 🚀 Complete Setup (3 Steps)

### Step 1: Start Python FastAPI Server
```bash
python main.py --api
```
This runs the Python analysis engine with FastAPI on **port 5000**
- Automatic API docs available at: http://localhost:5000/docs
- Analysis endpoint: http://localhost:5000/api/analyze

### Step 2: Start Node.js Proxy Server
```bash
cd server
npm start
```
This runs the Node.js proxy/cache layer on **port 3001**
- Caches Python results for 5 minutes
- Fallback to fake data if Python API unavailable

### Step 3: Start React Frontend
```bash
cd client
npm start
```
This runs the React dashboard on **port 3000**
- Auto-opens in browser: http://localhost:3000
- Auto-refreshes data every 60 seconds

## 🔧 Architecture

```
React Frontend (3000)
    ↓ HTTP GET /api/opportunities
Node.js Proxy (3001)
    ↓ HTTP GET /api/analyze (cached 5min)
Python FastAPI (5000)
    ↓ Playwright Browser Automation
PrizePicks + FanDuel APIs
```

## 💡 Resume-Worthy Features Implemented

### FastAPI Integration
- **Async-native** API design using Python 3.12+ asyncio
- **Type hints** and Pydantic models (implicit via FastAPI)
- **Automatic API documentation** via Swagger UI at `/docs`
- **CORS middleware** for cross-origin requests
- **Error handling** with proper HTTP status codes (503, 500)

### Microservices Architecture
- **Separation of concerns**: Python (data), Node (proxy/cache), React (UI)
- **Cache layer**: 5-minute TTL to reduce scraping load
- **Graceful fallback**: Node serves fake data if Python unavailable
- **Concurrent processing**: Async scrapers run in parallel

### Production-Ready Patterns
- **Health checks**: Root endpoint returns service status
- **Timeout handling**: 3-minute timeout for long scraping operations
- **Data formatting**: Python formats JSON to match frontend contract
- **Dual-mode execution**: CLI tool (`python main.py`) or API server (`python main.py --api`)

## 🎯 Interview Talking Points

1. **Why FastAPI over Flask?**
   - Native async support (no threading/Celery needed)
   - Automatic OpenAPI docs generation
   - Modern Python type hints
   - Better performance for I/O-bound operations (scraping)

2. **Why Node.js proxy layer?**
   - Caching reduces expensive scraping operations
   - Graceful degradation (fallback data)
   - Can scale horizontally if needed
   - Separates presentation logic from data pipeline

3. **Why keep both CLI and API modes?**
   - CLI for development/testing individual runs
   - API for production dashboard with caching
   - Demonstrates versatility of Python architecture

## 🐛 Troubleshooting

**Python API won't start:**
```bash
# Ensure FastAPI installed
pip install fastapi "uvicorn[standard]"
```

**CAPTCHA issues:**
- Run scrapers during off-peak hours (2-6 AM EST)
- Consider proxies (see CAPTCHA_SOLUTIONS.md)

**Port conflicts:**
- Python: Change port in `uvicorn.run(app, port=5000)`
- Node: Change `PORT = 3001` in server.js
- React: Change in package.json proxy

## 📊 Testing the Integration

1. Start Python API: `python main.py --api`
2. Wait for "Application startup complete"
3. Test endpoint manually:
   ```bash
   curl http://localhost:5000/api/analyze
   ```
4. Should return JSON with opportunities and stats
5. Start Node + React to see dashboard

## ⚡ Performance Notes

- First request: 2-3 minutes (full scraping)
- Cached requests: < 100ms
- Cache TTL: 5 minutes (adjustable in server.js)
- Playwright browsers: ~150MB RAM each
