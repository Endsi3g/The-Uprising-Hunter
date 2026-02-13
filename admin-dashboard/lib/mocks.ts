type MockValue = unknown

const MOCK_DATA: Record<string, MockValue> = {
  "/api/v1/admin/auth/login": {
    ok: true,
    username: "admin-mock",
  },
  "/api/v1/admin/assistant/prospect/runs": {
    items: [
      {
        id: "run-mock-1",
        prompt: "Find dentists in Lyon",
        status: "completed",
        actor: "system",
        summary: "Found 20 leads",
        action_count: 5,
        created_at: new Date().toISOString(),
        finished_at: new Date().toISOString(),
      },
      {
        id: "run-mock-2",
        prompt: "Contact leads via LinkedIn",
        status: "running",
        actor: "user",
        summary: "Processing...",
        action_count: 0,
        created_at: new Date().toISOString(),
      },
    ],
    total: 2,
  },
  "/api/v1/admin/assistant/prospect/execute": {
    id: "run-mock-new",
    prompt: "New execution",
    status: "running",
    actor: "user",
    config: {},
    created_at: new Date().toISOString(),
    actions: [],
  },
  "/api/v1/admin/assistant/prospect/confirm": {
    ok: true,
  },
}

export async function getMockResponse<T>(path: string): Promise<T> {
  await new Promise((resolve) => setTimeout(resolve, 200))

  const exactMatch = MOCK_DATA[path]
  if (exactMatch !== undefined) {
    return exactMatch as T
  }

  const prefixKey = Object.keys(MOCK_DATA).find((key) => path.startsWith(key))
  if (prefixKey) {
    return MOCK_DATA[prefixKey] as T
  }

  throw new Error(`[MOCK] No mock data found for ${path}`)
}
