interface ApiResponse {
  status: number;
}

export function handleResponse(resp: ApiResponse): string {
  if (resp.status === 200) {
    const data = (resp as any).data;
    return String(data);
  }
  return "error";
}
