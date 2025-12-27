const express = require('express');
const cors = require('cors');

const app = express();
const PORT = 3001;

app.use(cors());
app.use(express.json());

// Fake data - will be replaced with real Python engine data later
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
  // Filter out non-+EV opportunities for the main view
  const plusEvOpportunities = fakeopportunities.filter(
    opp => opp.qualifying_bets.length > 0
  );
  
  res.json({
    success: true,
    count: plusEvOpportunities.length,
    total_scanned: fakeopportunities.length,
    opportunities: plusEvOpportunities,
    last_updated: new Date().toISOString()
  });
});

app.get('/api/opportunities/:id', (req, res) => {
  const opp = fakeopportunities.find(o => o.id === parseInt(req.params.id));
  if (opp) {
    res.json({ success: true, opportunity: opp });
  } else {
    res.status(404).json({ success: false, message: 'Opportunity not found' });
  }
});

app.get('/api/stats', (req, res) => {
  const plusEvCount = fakeopportunities.filter(o => o.qualifying_bets.length > 0).length;
  const avgEdge = fakeopportunities
    .filter(o => o.qualifying_bets.length > 0)
    .reduce((sum, o) => {
      const maxEdge = Math.max(...o.qualifying_bets.map(b => b.edge));
      return sum + maxEdge;
    }, 0) / plusEvCount;

  res.json({
    success: true,
    stats: {
      total_props_scanned: fakeopportunities.length,
      plus_ev_found: plusEvCount,
      conversion_rate: ((plusEvCount / fakeopportunities.length) * 100).toFixed(2),
      avg_edge: avgEdge.toFixed(2),
      best_edge: Math.max(
        ...fakeopportunities
          .filter(o => o.qualifying_bets.length > 0)
          .map(o => Math.max(...o.qualifying_bets.map(b => b.edge)))
      ).toFixed(2)
    }
  });
});

app.listen(PORT, () => {
  console.log(`🚀 PropShop API Server running on http://localhost:${PORT}`);
  console.log(`📊 View opportunities at http://localhost:3000`);
});
