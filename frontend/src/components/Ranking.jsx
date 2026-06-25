import { useEffect, useState, useCallback } from "react";
import { api } from "../api/client";

export function Ranking({ refreshTrigger }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.getRanking(20);
      setData(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load, refreshTrigger]);

  const medals = ["🥇", "🥈", "🥉"];

  return (
    <div className="card">
      <div className="card-header-row">
        <div>
          <h2 className="card-title">Leaderboard</h2>
          <p className="card-sub">Multi-factor ranking: amount · frequency · recency</p>
        </div>
        <button className="btn-ghost" onClick={load} disabled={loading}>
          {loading ? "…" : "↻ Refresh"}
        </button>
      </div>

      {data?.scoring_formula && (
        <div className="formula-box">
          <code>{data.scoring_formula}</code>
        </div>
      )}

      {error && <div className="alert alert-error">{error}</div>}

      {!loading && data?.users?.length === 0 && (
        <p className="empty">No transactions yet. Submit one above!</p>
      )}

      {data?.users && data.users.length > 0 && (
        <div className="rank-table">
          <div className="rank-header">
            <span>Rank</span>
            <span>User</span>
            <span>Score</span>
            <span>Total</span>
            <span>Txns</span>
          </div>
          {data.users.map((u) => (
            <div key={u.user_id} className={`rank-row ${u.rank <= 3 ? "rank-top" : ""}`}>
              <span className="rank-num">
                {medals[u.rank - 1] || `#${u.rank}`}
              </span>
              <span className="rank-user">{u.user_id}</span>
              <span className="rank-score">{u.ranking_score.toFixed(4)}</span>
              <span>${u.total_amount.toLocaleString()}</span>
              <span>{u.transaction_count}</span>
            </div>
          ))}
        </div>
      )}

      {data && (
        <p className="rank-footer">{data.total_users} total users</p>
      )}
    </div>
  );
}