import React, { useEffect, useState } from "react";
import { getReferralInfo } from "../api/api";

export default function ReferralTab({ userId }) {
  const [info, setInfo] = useState(null);

  useEffect(() => {
    getReferralInfo(userId).then(setInfo);
  }, [userId]);

  return (
    <div className="p-4 space-y-2">
      <h2 className="text-lg font-bold">👥 Партнёрка</h2>
      {info && (
        <>
          <p>Ваша ссылка:</p>
          <div className="bg-gray-800 p-2 rounded">{info.link}</div>
          <p>Приглашено: {info.count}</p>
          <p>Доход: {info.earned} ₽</p>
        </>
      )}
    </div>
  );
}