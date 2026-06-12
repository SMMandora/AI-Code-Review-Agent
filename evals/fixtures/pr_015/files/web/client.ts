const API_TOKEN = "sk-live-abc123secrettoken456";

export function createHeaders(): Record<string, string> {
  return {
    Authorization: `Bearer ${API_TOKEN}`,
    "Content-Type": "application/json",
  };
}
