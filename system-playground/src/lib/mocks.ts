const MOCK_DATA: Record<string, unknown> = {
  "/api/v1/admin/auth/login": {
    ok: true,
    username: "playground-mock",
  },
};

export async function getMockResponse<T>(path: string): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 200));

  if (path in MOCK_DATA) {
    return MOCK_DATA[path] as T;
  }

  throw new Error(`[MOCK] No mock data found for ${path}`);
}
