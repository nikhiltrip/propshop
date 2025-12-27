# PropShop Web Dashboard

## Quick Start

### 1. Install Dependencies

#### Backend (Node.js/Express):
```bash
cd server
npm install
```

#### Frontend (React):
```bash
cd client
npm install
```

### 2. Start the Servers

#### Terminal 1 - Backend API:
```bash
cd server
npm run dev
```
Server will run on http://localhost:3001

#### Terminal 2 - Frontend:
```bash
cd client
npm start
```
Frontend will run on http://localhost:3000

### 3. View the Dashboard
Open your browser to http://localhost:3000

## Current Status

**SKELETON ONLY** - Currently using fake data for demonstration purposes.

The dashboard shows:
- ✅ Stats overview (total props scanned, +EV found, conversion rate, etc.)
- ✅ Sortable/filterable table of opportunities
- ✅ Edge percentage highlighting
- ✅ Best bet type recommendations
- ✅ All qualifying bet types for each prop
- ✅ Auto-refresh every 60 seconds

## Next Steps to Connect to Real Python Engine

1. **Create Python API endpoint** in `main.py`:
   - Add Flask or FastAPI to serve data as JSON
   - Return opportunities in the same format as `server.js` fake data

2. **Update `server.js`** to proxy to Python backend:
   - Change `/api/opportunities` to fetch from Python instead of fake data
   - Python runs on port 5000, Node proxies requests

3. **Alternative**: Save Python output to JSON file:
   - Modify `main.py` to write `opportunities.json`
   - Have Node.js read from that file
   - Simpler but no real-time updates

## Tech Stack

- **Backend**: Node.js + Express.js
- **Frontend**: React 18
- **Styling**: Pure CSS (no framework needed)
- **Data**: Currently fake, will connect to Python engine

## Features

### Stats Dashboard
- Total props scanned
- +EV opportunities found
- Conversion rate
- Average edge percentage
- Best edge found

### Opportunity Table
- Sortable by player, line, or edge
- Filter by minimum edge threshold
- Color-coded edge badges (high/medium/low)
- Shows best bet type for each prop
- Displays all qualifying bet types
- Direction indicators (Over/Under)
- No-vig win percentages

### UI Features
- Responsive design
- Auto-refresh data
- Manual refresh button
- Loading states
- Error handling
- Beautiful gradient background
- Glass-morphism cards
