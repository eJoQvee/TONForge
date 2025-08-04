import React, { useState } from "react";
import { generateLabel } from "../api/api";

export default function DepositTab({ userId }) {
  const [amount, setAmount] = useState("");
  const [method, setMethod] = useState("TON");
  const [label, setLabel] = useState(null);

  const handleGenerate = () => {
    generateLabel(userId, method, amount).then(setLabel);
  };

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">💸 Пополнение</h2>
      <select className="w-full bg-gray-800 p-2 rounded" onChange={(e) => setMethod(e.target.value)}>
        <option value="TON">TON</option>
        <option value="USDT">USDT (TRC20)</option>
      </select>
      <input
        type="number"
        placeholder="Сумма"
        className="w-full bg-gray-800 p-2 rounded"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <button onClick={handleGenerate} className="w-full bg-teal-600 py-2 text-white rounded">
        🚀 Получить адрес
      </button>
      {label && <p className="text-green-400">Адрес: {label.address}<br />Label: {label.label}</p>}
    </div>
  );
}