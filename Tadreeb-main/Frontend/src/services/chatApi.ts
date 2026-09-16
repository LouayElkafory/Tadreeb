import type { ChatApiResponse } from "../types";
import type { Language } from "../types";
import { generateMockResponse } from "../data/mockChat";

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== "false";
const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class ChatApiError extends Error {}

/**
 * Sends a user message to the Tadreeb AI backend (or a local mock)
 * and returns the assistant's answer, sources, and follow-up suggestions.
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string,
  language: Language = "ar"
): Promise<ChatApiResponse> {
  if (USE_MOCK) {
    // Simulate network + "thinking" latency
    await delay(900 + Math.random() * 700);
    return generateMockResponse(message, language);
  }

  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message, conversation_id: conversationId, language }),
    });

    if (!response.ok) {
      throw new ChatApiError(`Request failed with status ${response.status}`);
    }

    const data = (await response.json()) as ChatApiResponse;
    return data;
  } catch (err) {
    if (err instanceof ChatApiError) throw err;
    throw new ChatApiError("تعذر الاتصال بالخادم");
  }
}
