async function saveDraft(content: string): Promise<void> {
  await fetch("/api/draft", { method: "POST", body: content });
}

async function autoSave(content: string): Promise<void> {
  saveDraft(content);
  console.log("auto-save triggered");
}
