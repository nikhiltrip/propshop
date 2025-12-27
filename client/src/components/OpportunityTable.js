import React, { useState } from 'react';
import './OpportunityTable.css';

function OpportunityTable({ opportunities }) {
  const [sortField, setSortField] = useState('edge');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterMinEdge, setFilterMinEdge] = useState(0);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getMaxEdge = (opp) => {
    return opp.qualifying_bets.length > 0
      ? Math.max(...opp.qualifying_bets.map(b => b.edge))
      : 0;
  };

  const getBestBet = (opp) => {
    if (opp.qualifying_bets.length === 0) return null;
    return opp.qualifying_bets.reduce((best, current) => 
      current.edge > best.edge ? current : best
    );
  };

  const sortedOpportunities = [...opportunities].sort((a, b) => {
    let aValue, bValue;
    
    switch(sortField) {
      case 'edge':
        aValue = getMaxEdge(a);
        bValue = getMaxEdge(b);
        break;
      case 'player':
        aValue = a.player.toLowerCase();
        bValue = b.player.toLowerCase();
        break;
      case 'line':
        aValue = a.line;
        bValue = b.line;
        break;
      default:
        return 0;
    }

    if (sortDirection === 'asc') {
      return aValue > bValue ? 1 : -1;
    } else {
      return aValue < bValue ? 1 : -1;
    }
  });

  const filteredOpportunities = sortedOpportunities.filter(
    opp => getMaxEdge(opp) >= filterMinEdge
  );

  return (
    <div className="opportunity-table-container">
      <div className="table-controls">
        <div className="filter-control">
          <label>Min Edge: {filterMinEdge}%</label>
          <input
            type="range"
            min="0"
            max="5"
            step="0.1"
            value={filterMinEdge}
            onChange={(e) => setFilterMinEdge(parseFloat(e.target.value))}
          />
        </div>
        <div className="results-count">
          Showing {filteredOpportunities.length} of {opportunities.length} opportunities
        </div>
      </div>

      <div className="table-wrapper">
        <table className="opportunity-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('player')}>
                Player {sortField === 'player' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Stat</th>
              <th onClick={() => handleSort('line')}>
                Line {sortField === 'line' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Direction</th>
              <th>Win %</th>
              <th>Odds</th>
              <th onClick={() => handleSort('edge')}>
                Max Edge {sortField === 'edge' && (sortDirection === 'asc' ? '↑' : '↓')}
              </th>
              <th>Best Bet Type</th>
              <th>All Qualifying Bets</th>
            </tr>
          </thead>
          <tbody>
            {filteredOpportunities.map((opp) => {
              const bestBet = getBestBet(opp);
              const maxEdge = getMaxEdge(opp);
              
              return (
                <tr key={opp.id} className="opp-row">
                  <td className="player-cell">
                    <strong>{opp.player}</strong>
                  </td>
                  <td>{opp.stat}</td>
                  <td className="line-cell">{opp.line}</td>
                  <td>
                    <span className={`direction-badge ${opp.direction}`}>
                      {opp.direction.toUpperCase()}
                    </span>
                  </td>
                  <td className="win-pct-cell">
                    {opp.direction === 'over' ? opp.no_vig_over.toFixed(2) : opp.no_vig_under.toFixed(2)}%
                  </td>
                  <td className="odds-cell">
                    <div>Over: {opp.over_odds > 0 ? '+' : ''}{opp.over_odds}</div>
                    <div>Under: {opp.under_odds > 0 ? '+' : ''}{opp.under_odds}</div>
                  </td>
                  <td className="edge-cell">
                    <span className={`edge-badge ${maxEdge > 2 ? 'high' : maxEdge > 1 ? 'medium' : 'low'}`}>
                      +{maxEdge.toFixed(2)}%
                    </span>
                  </td>
                  <td className="best-bet-cell">
                    {bestBet && (
                      <div className="best-bet">
                        <div className="bet-type">{bestBet.bet_type}</div>
                        <div className="bet-payout">{bestBet.payout}x payout</div>
                      </div>
                    )}
                  </td>
                  <td className="all-bets-cell">
                    <div className="qualifying-bets">
                      {opp.qualifying_bets.map((bet, idx) => (
                        <div key={idx} className="bet-chip">
                          {bet.bet_type}: +{bet.edge.toFixed(2)}%
                        </div>
                      ))}
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default OpportunityTable;
