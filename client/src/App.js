import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';
import OpportunityTable from './components/OpportunityTable';
import StatsCard from './components/StatsCard';

function App() {
  const [opportunities, setOpportunities] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [error, setError] = useState(null);
  const [isStale, setIsStale] = useState(false);
  const [refreshing, setRefreshing] = useState(false);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [oppsResponse, statsResponse] = await Promise.all([
        axios.get('/api/opportunities'),
        axios.get('/api/stats')
      ]);

      setOpportunities(oppsResponse.data.opportunities);
      setLastUpdated(oppsResponse.data.last_updated);
      setStats(statsResponse.data.stats);
      setIsStale(oppsResponse.data.is_stale || false);
    } catch (err) {
      setError('Failed to fetch data. Make sure the server is running on port 3001.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  const triggerManualScrape = async () => {
    if (refreshing) return;
    
    try {
      setRefreshing(true);
      setError(null);
      
      await axios.post('/api/trigger-scrape');
      
      // Poll for completion (check every 5 seconds for 5 minutes max)
      let attempts = 0;
      const maxAttempts = 60; // 5 minutes
      
      const pollInterval = setInterval(async () => {
        attempts++;
        
        try {
          const response = await axios.get('/api/opportunities');
          if (!response.data.is_stale || attempts >= maxAttempts) {
            clearInterval(pollInterval);
            setRefreshing(false);
            fetchData();
          }
        } catch (e) {
          // Keep polling
        }
        
        if (attempts >= maxAttempts) {
          clearInterval(pollInterval);
          setRefreshing(false);
          setError('Scraping took too long. Check back in a few minutes.');
        }
      }, 5000);
      
    } catch (err) {
      setRefreshing(false);
      setError('Failed to trigger data refresh: ' + err.message);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Check for updates every 30 seconds (just to show if data changed)
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="App">
      <header className="App-header">
        <div className="header-content">
          <div>
            <h1>💰 PropShop</h1>
            <p className="subtitle">+EV Sports Betting Opportunities</p>
          </div>
          {isStale && (
            <button className="refresh-btn warning" onClick={triggerManualScrape} disabled={refreshing}>
              {refreshing ? '⏳ Scraping (2-3 min)...' : '⚠️ Refresh Stale Data'}
            </button>
          )}
        </div>
        {isStale && (
          <div className="stale-banner">
            ⚠️ Data is more than 24 hours old. Lines may have moved. Click "Refresh Stale Data" to update.
          </div>
        )}
      </header>

      <main className="main-content">
        {error && (
          <div className="error-banner">
            ⚠️ {error}
          </div>
        )}

        {stats && <StatsCard stats={stats} lastUpdated={lastUpdated} />}

        {loading && !opportunities.length ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Scanning for opportunities...</p>
          </div>
        ) : opportunities.length > 0 ? (
          <OpportunityTable opportunities={opportunities} />
        ) : (
          <div className="empty-state">
            <h2>No +EV Opportunities Found</h2>
            <p>Keep checking back - opportunities appear throughout the day!</p>
          </div>
        )}
      </main>

      <footer className="App-footer">
        <p>Built with Python (Analysis Engine) + Node.js + React</p>
        <p className="disclaimer">⚠️ For educational purposes only. Gamble responsibly.</p>
      </footer>
    </div>
  );
}

export default App;
