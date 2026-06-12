export function renderItems(items: string[]): string[] {
  const result: string[] = [];
  for (let i = 0; i <= items.length; i++) {
    result.push(`<li>${items[i]}</li>`);
  }
  return result;
}
