const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

async function request(method, path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  postTransaction: (payload) => request("POST", "/transaction", payload),
  getSummary: (userId) => request("GET", `/summary/${userId}`),
  getRanking: (limit = 20) => request("GET", `/ranking?limit=${limit}`),
};