const express = require('express');
const cors = require('cors');
const fs = require('fs');
const path = require('path');
const { spawn } = require('child_process');

const app = express();
const PORT = 3001;
const DATA_FILE = path.join(__dirname, '..', 'data', 'opportunities.json');
const PYTHON_VENV = path.join(__dirname, '..', 'venv', 'bin', 'python');
const SCRAPER_SCRIPT = path.join(__dirname, '..', 'daily_scraper.py');

app.use(cors());
app.use(express.json());

let isScrapingInProgress = false; // Prevent multiple simultaneous scrapes

// Helper function to read data from JSON file
function readDataFile() {
  try {
    if (!fs.existsSync(DATA_FILE)) {
      return null;
    }
    const data = fs.readFileSync(DATA_FILE, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error('❌ Error reading data file:', error.message);
    return null;
  }
}

// Helper function to check if data is stale (> 24 hours old)
function isDataStale(data) {
  if (!data || !data.last_updated) return true;
  const lastUpdate = new Date(data.last_updated);
  const now = new Date();
  const hoursSinceUpdate = (now - lastUpdate) / (1000 * 60 * 60);
  return hoursSinceUpdate > 24;
}

// Legacy fake data for fallback (kept for reference)
const fakeopportunities = [
  {
    id: 1,
    player: "Luka Doncic",
    stat: "Points",
    line: 32.5,
    over_odds: -125,
    under_odds: -105,
    no_vig_over: 55.81,
    no_vig_under: 44.19,
    direction: "over",
    qualifying_bets: [
      { bet_type: "6-Pick Flex", edge: 1.60, payout: 25 },
      { bet_type: "5-Pick Flex", edge: 1.55, payout: 10 },
      { bet_type: "3-Pick Power", edge: 0.76, payout: 6 }
    ],
    timestamp: new Date().toISOString()
  },
  {
    id: 2,
    player: "Nikola Jokic",
    stat: "Rebounds",
    line: 12.5,
    over_odds: -130,
    under_odds: -100,
    no_vig_over: 56.52,
    no_vig_under: 43.48,
    direction: "over",
    qualifying_bets: [
      { bet_type: "4-Pick Power", edge: 0.29, payout: 10 },
      { bet_type: "6-Pick Flex", edge: 2.31, payout: 25 }
    ],
    timestamp: new Date().toISOString()
  },
  {
    id: 3,
    player: "Stephen Curry",
    stat: "3-Pointers Made",
    line: 4.5,
    over_odds: -115,
    under_odds: -115,
    no_vig_over: 50.00,
    no_vig_under: 50.00,
    direction: null,
    qualifying_bets: [],
    timestamp: new Date().toISOString()
  },
  {
    id: 4,
    player: "Giannis Antetokounmpo",
    stat: "Points",
    line: 30.5,
    over_odds: -140,
    under_odds: +110,
    no_vig_over: 58.33,
    no_vig_under: 41.67,
    direction: "over",
    qualifying_bets: [
      { bet_type: "2-Pick Power", edge: 0.59, payout: 3 },
      { bet_type: "3-Pick Flex", edge: 0.59, payout: 3 },
      { bet_type: "6-Pick Flex", edge: 4.12, payout: 25 },
      { bet_type: "5-Pick Flex", edge: 4.07, payout: 10 }
    ],
    timestamp: new Date().toISOString()
  },
  {
    id: 5,
    player: "Joel Embiid",
    stat: "Rebounds",
    line: 11.5,
    over_odds: -122,
    under_odds: -108,
    no_vig_over: 54.95,
    no_vig_under: 45.05,
    direction: "over",
    qualifying_bets: [
      { bet_type: "6-Pick Flex", edge: 0.74, payout: 25 }
    ],
    timestamp: new Date().toISOString()
  },
  {
    id: 6,
    player: "Jayson Tatum",
    stat: "Assists",
    line: 4.5,
    over_odds: +105,
    under_odds: -135,
    no_vig_over: 45.24,
    no_vig_under: 54.76,
    direction: "under",
    qualifying_bets: [
      { bet_type: "6-Pick Flex", edge: 0.55, payout: 25 }
    ],
    timestamp: new Date().toISOString()
  }
];

// API Routes
app.get('/api/opportunities', (req, res) => {
  try {
    // Read from JSON file
    const data = readDataFile();
    
    if (!data) {
      // No data file exists yet
      return res.json({
        success: true,
        count: 0,
        opportunities: [],
        stats: {
          total_scanned: 0,
          plus_ev_found: 0,
          conversion_rate: 0,
          avg_edge: 0,
          best_edge: 0
        },
        last_updated: null,
        message: 'No data available yet. Run daily scraper or trigger manual refresh.'
      });
    }
    
    res.json({
      success: true,
      count: data.opportunities.length,
      opportunities: data.opportunities,
      stats: data.stats,
      last_updated: data.last_updated,
      date: data.date,
      is_stale: isDataStale(data)
    });
  } catch (error) {
    console.error('❌ Error serving opportunities:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

app.get('/api/opportunities/:id', (req, res) => {
  // Check cache or fake data for specific opportunity
  const data = readDataFile();
  const opportunities = data ? data.opportunities : fakeopportunities;
  const opp = opportunities.find(o => o.id === parseInt(req.params.id));
  if (opp) {
    res.json({ success: true, opportunity: opp });
  } else {
    res.status(404).json({ success: false, message: 'Opportunity not found' });
  }
});

app.get('/api/stats', (req, res) => {
  try {
    const data = readDataFile();
    
    if (!data) {
      return res.json({
        success: true,
        stats: {
          total_scanned: 0,
          plus_ev_found: 0,
          conversion_rate: 0,
          avg_edge: 0,
          best_edge: 0
        }
      });
    }

    res.json({
      success: true,
      stats: data.stats
    });
  } catch (error) {
    console.error('❌ Error fetching stats:', error.message);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

// Manual trigger endpoint for refreshing data
app.post('/api/trigger-scrape', (req, res) => {
  if (isScrapingInProgress) {
    return res.status(202).json({
      success: false,
      message: 'Scraping already in progress. Please wait 2-3 minutes.',
      in_progress: true
    });
  }

  console.log('🔄 Manual scrape triggered...');
  isScrapingInProgress = true;

  // Spawn Python scraper process
  const scraper = spawn(PYTHON_VENV, [SCRAPER_SCRIPT]);

  let output = '';
  let errorOutput = '';

  scraper.stdout.on('data', (data) => {
    output += data.toString();
    console.log(data.toString());
  });

  scraper.stderr.on('data', (data) => {
    errorOutput += data.toString();
    console.error(data.toString());
  });

  scraper.on('close', (code) => {
    isScrapingInProgress = false;
    
    if (code === 0) {
      console.log('✅ Scraping completed successfully');
      res.json({
        success: true,
        message: 'Data refreshed successfully',
        data: readDataFile()
      });
    } else {
      console.error(`❌ Scraping failed with exit code ${code}`);
      res.status(500).json({
        success: false,
        message: 'Scraping failed. Check server logs for details.',
        error: errorOutput
      });
    }
  });

  // Send initial response
  res.status(202).json({
    success: true,
    message: 'Scraping started. This will take 2-3 minutes.',
    in_progress: true
  });
});

app.listen(PORT, () => {
  console.log(`🚀 PropShop API Server running on http://localhost:${PORT}`);
  console.log(`📊 Dashboard: http://localhost:3000`);
  console.log(`📁 Data file: ${DATA_FILE}`);
  console.log(`\n💡 Daily scraper runs at midnight via cron`);
  console.log(`💡 Manual trigger: POST http://localhost:${PORT}/api/trigger-scrape\n`);
});
