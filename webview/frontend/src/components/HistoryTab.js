import React, { useEffect, useState } from "react";
import { getOperations } from "../api/api";

export default function HistoryTab({ userId }) {
  const [ops, setOps] = useState({ deposits: [], withdrawals: [] });

  useEffect(() => {
    getOperations(userId).then(setOps);
  }, [userId]);

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">📜 История</h2>
      <div>
        <h3 className="font-semibold">Депозиты</h3>
        {ops.deposits.map((d, idx) => (
          <div key={idx} className="text-sm">
            {d.amount} {d.currency}
          </div>
        ))}
      </div>
      <div>
        <h3 className="font-semibold mt-2">Выводы</h3>
        {ops.withdrawals.map((w, idx) => (
          <div key={idx} className="text-sm">
            {w.amount} {w.currency}
          </div>
        ))}
      </div>
    </div>
  );
}