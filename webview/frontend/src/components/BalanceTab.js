import React, { useEffect, useState } from "react";
import { getBalance } from "../api/api";

export default function BalanceTab({ userId }) {
  const [balance, setBalance] = useState(0);
  const [daily, setDaily] = useState(0);

  useEffect(() => {
    getBalance(userId).then((data) => {
      setBalance(data.balance);
      setDaily(data.daily_income);
    });
  }, [userId]);

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">💼 Баланс</h2>
      <p>Текущий: {balance} ₽</p>
      <p>Сегодня начислено: +{daily} ₽</p>
      <button className="bg-teal-600 w-full py-2 mt-2 text-white rounded">
        📤 Вывести средства
      </button>
    </div>
  );
}