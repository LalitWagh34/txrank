import { useState } from "react";
import { api } from "../api/client";

export function UserSummary() {
  const [userId, setUserId] = useState("");
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const lookup = async () => {
    if (!userId.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const res = await api.getSummary(userId.trim());
      setData(res);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">User Summary</h2>
      <p className="card-sub">Look up aggregated stats for any user.</p>

      <div className="inline-search">
        <input
          placeholder="Enter user ID…"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && lookup()}
        />
        <button className="btn-primary" onClick={lookup} disabled={loading}>
          {loading ? "…" : "Lookup"}
        </button>
      </div>

      {error && <div className="alert alert-error">{error}</div>}

      {data && (
        <div className="stats-grid">
          <Stat label="Rank" value={`#${data.rank}`} accent />
          <Stat label="Total Amount" value={`$${data.total_amount.toLocaleString()}`} />
          <Stat label="Transactions" value={data.transaction_count} />
          <Stat label="Avg Transaction" value={`$${data.average_transaction.toLocaleString()}`} />
          <Stat label="Ranking Score" value={data.ranking_score.toFixed(4)} />
          <Stat
            label="Last Active"
            value={data.last_transaction_at
              ? new Date(data.last_transaction_at).toLocaleDateString()
              : "—"}
          />
        </div>
      )}
    </div>
  );
}

function Stat({ label, value, accent }) {
  return (
    <div className={`stat-box ${accent ? "stat-accent" : ""}`}>
      <span className="stat-val">{value}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}