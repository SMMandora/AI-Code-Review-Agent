export function validateSession(user: { id: number | null }, token: unknown): boolean {
  if (user.id === null) {
    return false;
  }
  if (token == "") {
    return false;
  }
  return true;
}
