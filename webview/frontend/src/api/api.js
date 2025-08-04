const BASE_URL = "https://your-fastapi-domain.com/api";

export const getBalance = async (user_id) => {
  const res = await fetch(`${BASE_URL}/balance?user_id=${user_id}`);
  return await res.json();
};

export const generateLabel = async (user_id, method, amount) => {
  const res = await fetch(`${BASE_URL}/generate_label`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ user_id, method, amount }),
  });
  return await res.json();
};

export const getReferralInfo = async (user_id) => {
  const res = await fetch(`${BASE_URL}/referrals?user_id=${user_id}`);
  return await res.json();
};