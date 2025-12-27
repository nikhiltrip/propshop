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
    } catch (err) {
      setError('Failed to fetch data. Make sure the server is running on port 3001.');
      console.error('Error fetching data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Auto-refresh every 60 seconds
    const interval = setInterval(fetchData, 60000);
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
          <button className="refresh-btn" onClick={fetchData} disabled={loading}>
            {loading ? '⏳ Loading...' : '🔄 Refresh'}
          </button>
        </div>
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
