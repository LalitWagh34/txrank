# TxRank — Transaction & Ranking API

A backend service + live frontend for idempotent transaction processing with multi-factor fair ranking.

## Live Demo

> Frontend: `https://txrank.vercel.app` (deploy your own — see below)
> Backend: Run locally or deploy to Railway / Render

---

## Quick Start

### Backend

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs available at: `http://localhost:8000/docs`

### Frontend

```bash
cd frontend
npm install

# Create .env.local
echo "VITE_API_URL=http://localhost:8000" > .env.local

npm run dev
```

---

## API Reference

### `POST /transaction`

Submit a financial transaction. Idempotent — safe to retry with the same key.

**Request body:**
```json
{
  "user_id": "alice",
  "amount": 250.00,
  "description": "optional note",
  "idempotency_key": "client-uuid-here"
}
```

**Rules:**
- `user_id`: alphanumeric + underscores/hyphens, max 64 chars
- `amount`: 0.01 – 1,000,000, rounded to 2 decimal places
- `idempotency_key`: optional — if omitted, one is auto-generated (non-retryable)

**Response:**
```json
{
  "id": "uuid",
  "user_id": "alice",
  "amount": 250.00,
  "idempotency_key": "...",
  "created_at": "2024-01-01T00:00:00Z",
  "was_duplicate": false
}
```

If `was_duplicate: true`, the original transaction is returned unchanged — no double processing.

---

### `GET /summary/:userId`

Returns aggregated stats for a user including their current rank.

**Response:**
```json
{
  "user_id": "alice",
  "total_amount": 750.00,
  "transaction_count": 3,
  "average_transaction": 250.00,
  "ranking_score": 0.7231,
  "rank": 2
}
```

---

### `GET /ranking?limit=20&offset=0`

Returns the paginated leaderboard sorted by ranking score.

**Response:**
```json
{
  "users": [
    { "rank": 1, "user_id": "bob", "ranking_score": 0.9102, "total_amount": 1200.00, "transaction_count": 8 }
  ],
  "total_users": 42,
  "scoring_formula": "score = 0.50 × (user_total / max_total) + 0.30 × (user_tx_count / max_tx_count) + 0.20 × exp(−days_since_last_tx / 30)"
}
```

---

## Ranking Formula

```
score = 0.50 × (user_total / max_total)
      + 0.30 × (user_tx_count / max_tx_count)
      + 0.20 × exp(−days_since_last_tx / 30)
```

| Component | Weight | Purpose |
|-----------|--------|---------|
| Normalised total amount | 50% | Rewards higher spend |
| Normalised frequency | 30% | Rewards consistent activity |
| Recency decay (30-day half-life) | 20% | Rewards recent activity; old bulk uploads decay |

All three components are in [0, 1] so the final score is also in [0, 1].

**Why this is fair:**
- A single $1M transaction won't dominate — amount is only 50% weight.
- A user who made 100 small transactions ranks higher than one who made 1 large one, all else equal.
- Rankings decay over time — you can't game the system with a one-time dump and hold rank forever.
- Normalisation is relative — absolute numbers don't matter, only your standing relative to others.

---

## Duplicate Prevention

Every transaction carries an `idempotency_key` (client-provided or auto-generated).

1. The key has a **unique database constraint** (`UNIQUE INDEX` on `idempotency_key`).
2. On insert, we use `db.flush()` to trigger the constraint **before committing**.
3. If two concurrent requests race with the same key, only one `INSERT` succeeds — the other gets a DB `IntegrityError` and returns the already-stored record with `was_duplicate: true`.
4. No application-level locking needed — the DB constraint is the single source of truth.

---

## Concurrency & Data Consistency

- SQLite runs in **WAL (Write-Ahead Logging)** mode — concurrent reads don't block writes.
- User summary totals are updated with **atomic SQL `UPDATE`** statements (not read-modify-write in Python), preventing race conditions.
- After every transaction, all users' ranking scores are **renormalised** so the leaderboard stays consistent.

---

## Abuse Prevention

- **Rate limiting:** Max 20 transactions per user per 60 seconds (sliding window middleware).
- **Amount cap:** Single transaction capped at $1,000,000.
- **Input validation:** `user_id` must be alphanumeric — no SQL injection vectors.
- **Recency decay:** Prevents holding top rank via historical bulk uploads.

---

## Schema

```sql
-- transactions: append-only log
CREATE TABLE transactions (
  id              TEXT PRIMARY KEY,
  idempotency_key TEXT UNIQUE NOT NULL,  -- duplicate prevention
  user_id         TEXT NOT NULL,
  amount          REAL NOT NULL,
  description     TEXT,
  created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- user_summaries: denormalised for O(1) reads
CREATE TABLE user_summaries (
  user_id             TEXT PRIMARY KEY,
  total_amount        REAL NOT NULL,
  transaction_count   INTEGER NOT NULL,
  first_transaction_at TIMESTAMP,
  last_transaction_at  TIMESTAMP,
  ranking_score       REAL NOT NULL      -- precomputed, updated on every write
);
```

## Deploying the Frontend to Vercel

```bash
cd frontend
npm run build
# Push to GitHub, import repo in vercel.com
# Set env var: VITE_API_URL=https://your-backend-url.com
```

## Assumptions & Trade-offs

- **SQLite** is used for simplicity. In production, replace with PostgreSQL + Redis for the rate limiter.
- **Renormalisation on every write** is O(n users) — fine for this scale, would move to a background job at scale.
- Rate limiter is **in-process** — won't work across multiple backend instances. Replace with Redis for production.
