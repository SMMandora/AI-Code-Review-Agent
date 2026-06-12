export function renderComment(el: HTMLElement, comment: string): void {
  el.innerHTML = comment;
}

export function renderName(el: HTMLElement, name: string): void {
  el.textContent = name;
}
