import React, { useState } from "react";
import BalanceTab from "./components/BalanceTab";
import DepositTab from "./components/DepositTab";
import ReferralTab from "./components/ReferralTab";

export default function App() {
  const [tab, setTab] = useState("balance");
  const userId = new URLSearchParams(window.location.search).get("user_id");

  return (
    <div className="min-h-screen bg-black text-white p-4">
      <div className="flex justify-around mb-4">
        <button onClick={() => setTab("balance")}>💼 Баланс</button>
        <button onClick={() => setTab("deposit")}>💸 Пополнить</button>
        <button onClick={() => setTab("referral")}>👥 Партнёрка</button>
      </div>

      {tab === "balance" && <BalanceTab userId={userId} />}
      {tab === "deposit" && <DepositTab userId={userId} />}
      {tab === "referral" && <ReferralTab userId={userId} />}
    </div>
  );
}