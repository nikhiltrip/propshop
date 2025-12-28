import React, { useState } from 'react';
import './OpportunityTable.css';

function OpportunityTable({ opportunities }) {
  const [sortField, setSortField] = useState('edge');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterMinEdge, setFilterMinEdge] = useState(-100);
  const [searchPlayer, setSearchPlayer] = useState('');
  const [filterSport, setFilterSport] = useState('All');
  const [editedOpportunities, setEditedOpportunities] = useState({});

  // Function to convert American odds to decimal
  const americanToDecimal = (americanOdds) => {
    if (americanOdds > 0) {
      return (americanOdds / 100) + 1;
    } else {
      return (100 / Math.abs(americanOdds)) + 1;
    }
  };

  // Function to recalculate edge based on new line
  const recalculateEdge = (opp, newLine) => {
    // Get the odds for the direction (PrizePicks odds)
    const prizePicksOdds = opp.odds;
    const decimalOdds = americanToDecimal(prizePicksOdds);
    const impliedProb = (1 / decimalOdds) * 100;

    // For simplicity, assume win probability scales linearly with line change
    // In reality, you'd need the full probability distribution
    const lineChange = ((newLine - opp.line) / opp.line) * 100;
    
    // Rough estimate: each 1% line change affects win prob by ~2-5%
    // This is a simplification; real calculation would need the full model
    let adjustedWinProb = parseFloat(opp.no_vig_win_pct || 50);
    
    if (opp.direction === 'over') {
      adjustedWinProb = adjustedWinProb - (lineChange * 2); // Harder to hit
    } else {
      adjustedWinProb = adjustedWinProb + (lineChange * 2); // Easier to hit
    }
    
    // Clamp between 1 and 99
    adjustedWinProb = Math.max(1, Math.min(99, adjustedWinProb));
    
    const newEdge = adjustedWinProb - impliedProb;
    
    return {
      newWinProb: adjustedWinProb,
      newEdge: newEdge
    };
  };

  const handleLineEdit = (oppId, newLine) => {
    const opp = opportunities.find(o => o.id === oppId);
    if (!opp) return;

    const { newWinProb, newEdge } = recalculateEdge(opp, parseFloat(newLine));
    
    setEditedOpportunities(prev => ({
      ...prev,
      [oppId]: {
        line: parseFloat(newLine),
        no_vig_win_pct: newWinProb,
        edge: newEdge
      }
    }));
  };

  // Get unique sports from opportunities
  const availableSports = ['All', ...new Set(opportunities.map(opp => opp.sport || 'Other'))];

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getMaxEdge = (opp) => {
    // Check if manually edited
    if (editedOpportunities[opp.id]?.edge !== undefined) {
      return editedOpportunities[opp.id].edge;
    }
    // Handle both old format (qualifying_bets) and new format (edge)
    if (opp.edge !== undefined) {
      return opp.edge;
    }
    return opp.qualifying_bets?.length > 0
      ? Math.max(...opp.qualifying_bets.map(b => b.edge))
      : 0;
  };

  const getBestBet = (opp) => {
    // Handle new format with best_bet_type
    if (opp.best_bet_type) {
      return {
        bet_type: opp.best_bet_type,
        edge: opp.edge,
        payout: opp.payout
      };
    }
    // Fallback to old format
    if (!opp.qualifying_bets || opp.qualifying_bets.length === 0) return null;
    return opp.qualifying_bets.reduce((best, current) => 
      current.edge > best.edge ? current : best
    );
  };

  const getAllQualifyingBets = (opp) => {
    // Handle new format with all_qualifying_bets
    if (opp.all_qualifying_bets) {
      return opp.all_qualifying_bets;
    }
    // Fallback to old format
    return opp.qualifying_bets || [];
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

  const filteredOpportunities = sortedOpportunities.filter(opp => {
    const meetsEdgeFilter = getMaxEdge(opp) >= filterMinEdge;
    const meetsPlayerFilter = opp.player.toLowerCase().includes(searchPlayer.toLowerCase());
    const meetsSportFilter = filterSport === 'All' || opp.sport === filterSport;
    return meetsEdgeFilter && meetsPlayerFilter && meetsSportFilter;
  });

  return (
    <div className="opportunity-table-container">
      <div className="table-controls">
        <div className="filter-control">
          <label>Min Edge: {filterMinEdge}%</label>
          <input
            type="range"
            min="-100"
            max="10"
            step="0.5"
            value={filterMinEdge}
            onChange={(e) => setFilterMinEdge(parseFloat(e.target.value))}
          />
        </div>
        
        <div className="filter-control">
          <label>Sport:</label>
          <select value={filterSport} onChange={(e) => setFilterSport(e.target.value)}>
            {availableSports.map(sport => (
              <option key={sport} value={sport}>{sport}</option>
            ))}
          </select>
        </div>
        
        <div className="filter-control search-control">
          <label>Search Player:</label>
          <input
            type="text"
            placeholder="Enter player name..."
            value={searchPlayer}
            onChange={(e) => setSearchPlayer(e.target.value)}
          />
          {searchPlayer && (
            <button className="clear-search" onClick={() => setSearchPlayer('')}>✕</button>
          )}
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
              <th>Sport</th>
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
              const qualifyingBets = getAllQualifyingBets(opp);
              
              return (
                <tr key={opp.id} className="opp-row">
                  <td className="player-cell">
                    <strong>{opp.player}</strong>
                  </td>
                  <td className="sport-cell">
                    <span className={`sport-badge ${opp.sport?.toLowerCase()}`}>
                      {opp.sport || 'Other'}
                    </span>
                  </td>
                  <td>{opp.stat}</td>
                  <td className="line-cell">
                    <input
                      type="number"
                      step="0.5"
                      className="line-edit-input"
                      value={editedOpportunities[opp.id]?.line ?? opp.line}
                      onChange={(e) => handleLineEdit(opp.id, e.target.value)}
                      title="Edit line to recalculate edge"
                    />
                  </td>
                  <td>
                    <span className={`direction-badge ${opp.direction}`}>
                      {opp.direction?.toUpperCase() || 'N/A'}
                    </span>
                  </td>
                  <td className="win-pct-cell">
                    {(editedOpportunities[opp.id]?.no_vig_win_pct ?? opp.no_vig_win_pct ?? (opp.direction === 'over' ? opp.no_vig_over : opp.no_vig_under)).toFixed(2)}%
                  </td>
                  <td className="odds-cell">
                    {opp.odds ? (
                      <div>{opp.direction === 'over' ? 'Over' : 'Under'}: {opp.odds > 0 ? '+' : ''}{opp.odds}</div>
                    ) : (
                      <>
                        <div>Over: {opp.over_odds > 0 ? '+' : ''}{opp.over_odds}</div>
                        <div>Under: {opp.under_odds > 0 ? '+' : ''}{opp.under_odds}</div>
                      </>
                    )}
                  </td>
                  <td className="edge-cell">
                    <span className={`edge-badge ${maxEdge > 2 ? 'high' : maxEdge > 1 ? 'medium' : 'low'}`}>
                      +{maxEdge.toFixed(2)}%
                    </span>
                  </td>
                  <td className="best-bet-cell">
                    {bestBet && (
                      <div className="best-bet">
                        <div className="bet-type">{bestBet.bet_type || bestBet.type}</div>
                        <div className="bet-payout">{bestBet.payout}x payout</div>
                      </div>
                    )}
                  </td>
                  <td className="all-bets-cell">
                    <div className="qualifying-bets">
                      {qualifyingBets.map((bet, idx) => (
                        <div key={idx} className="bet-chip">
                          {bet.bet_type || bet.type}: +{bet.edge.toFixed(2)}%
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
