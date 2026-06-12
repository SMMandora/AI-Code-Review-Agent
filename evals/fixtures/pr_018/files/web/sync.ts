async function syncToBackend(data: object): Promise<void> {
  const resp = await fetch("/api/sync", {
    method: "POST",
    body: JSON.stringify(data),
  });
  if (!resp.ok) {
    throw new Error("sync failed");
  }
}

export async function safeSync(data: object): Promise<void> {
  try {
    await syncToBackend(data);
  } catch (e) {}
}
