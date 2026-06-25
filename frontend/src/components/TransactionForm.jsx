import { useState } from "react";
import { api } from "../api/client";

export function TransactionForm({ onSuccess }) {
  const [form, setForm] = useState({ user_id: "", amount: "", description: "" });
  const [status, setStatus] = useState(null); // {type: 'success'|'error'|'duplicate', message, data}
  const [loading, setLoading] = useState(false);

  const handleChange = (e) =>
    setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const handleSubmit = async () => {
    if (!form.user_id.trim() || !form.amount) {
      setStatus({ type: "error", message: "User ID and amount are required." });
      return;
    }
    setLoading(true);
    setStatus(null);
    try {
      const data = await api.postTransaction({
        user_id: form.user_id.trim(),
        amount: parseFloat(form.amount),
        description: form.description || undefined,
      });
      setStatus({
        type: data.was_duplicate ? "duplicate" : "success",
        message: data.was_duplicate
          ? `Duplicate detected — original tx returned (ID: ${data.id.slice(0, 8)}…)`
          : `Transaction processed! ID: ${data.id.slice(0, 8)}…`,
        data,
      });
      onSuccess?.();
    } catch (e) {
      setStatus({ type: "error", message: e.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="card-title">New Transaction</h2>
      <p className="card-sub">Amounts between $0.01 and $1,000,000. Supply the same idempotency key to retry safely.</p>

      <div className="field-group">
        <div className="field">
          <label>User ID</label>
          <input
            name="user_id"
            placeholder="e.g. alice_99"
            value={form.user_id}
            onChange={handleChange}
          />
        </div>
        <div className="field">
          <label>Amount ($)</label>
          <input
            name="amount"
            type="number"
            placeholder="0.00"
            min="0.01"
            max="1000000"
            step="0.01"
            value={form.amount}
            onChange={handleChange}
          />
        </div>
        <div className="field full">
          <label>Description (optional)</label>
          <input
            name="description"
            placeholder="What's this for?"
            value={form.description}
            onChange={handleChange}
          />
        </div>
      </div>

      <button className="btn-primary" onClick={handleSubmit} disabled={loading}>
        {loading ? "Processing…" : "Submit Transaction"}
      </button>

      {status && (
        <div className={`alert alert-${status.type}`}>
          {status.type === "duplicate" && <span className="badge">DUPLICATE</span>}
          {status.message}
        </div>
      )}
    </div>
  );
}