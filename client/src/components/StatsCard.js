import React from 'react';
import './StatsCard.css';

function StatsCard({ stats, lastUpdated }) {
  const formatDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: 'numeric',
      minute: '2-digit',
      hour12: true
    });
  };

  return (
    <div className="stats-card">
      <div className="stats-grid">
        <div className="stat-item">
          <div className="stat-label">Props Scanned</div>
          <div className="stat-value">{stats.total_props_scanned}</div>
        </div>
        <div className="stat-item highlight">
          <div className="stat-label">+EV Found</div>
          <div className="stat-value">{stats.plus_ev_found}</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Conversion Rate</div>
          <div className="stat-value">{stats.conversion_rate}%</div>
        </div>
        <div className="stat-item">
          <div className="stat-label">Avg Edge</div>
          <div className="stat-value">{stats.avg_edge}%</div>
        </div>
        <div className="stat-item highlight">
          <div className="stat-label">Best Edge</div>
          <div className="stat-value">{stats.best_edge}%</div>
        </div>
      </div>
      {lastUpdated && (
        <div className="last-updated">
          Last updated: {formatDate(lastUpdated)}
        </div>
      )}
    </div>
  );
}

export default StatsCard;
