import { useState } from "react";
import { TransactionForm } from "./components/TransactionForm";
import { UserSummary } from "./components/UserSummary";
import { Ranking } from "./components/Ranking";

export default function App() {
  const [refresh, setRefresh] = useState(0);

  return (
    <div className="app">
      <header className="header">
        <div className="header-inner">
          <div className="logo">
            <span className="logo-mark">Tx</span>Rank
          </div>
          <p className="tagline">Idempotent transactions · Fair multi-factor ranking</p>
        </div>
      </header>

      <main className="main">
        <div className="col-left">
          <TransactionForm onSuccess={() => setRefresh((r) => r + 1)} />
          <UserSummary />
        </div>
        <div className="col-right">
          <Ranking refreshTrigger={refresh} />
        </div>
      </main>
    </div>
  );
}