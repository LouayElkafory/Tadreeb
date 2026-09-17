import type { ChatApiResponse } from "../types";
import type { Language } from "../types";
import { generateMockResponse } from "../data/mockChat";

const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== "false";
// Strip any trailing slash so `${API_URL}/api/chat` never produces a double slash.
const API_URL = (import.meta.env.VITE_API_URL || "http://localhost:8000").replace(/\/+$/, "");

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export class ChatApiError extends Error {}

export interface ChatHistoryTurn {
  role: string;
  content: string;
}

/**
 * Sends a user message to the Tadreeb AI backend (or local mock)
 * along with previous conversation history turns for multi-turn memory.
 */
export async function sendChatMessage(
  message: string,
  conversationId?: string,
  language: Language = "ar",
  history: ChatHistoryTurn[] = []
): Promise<ChatApiResponse> {
  if (USE_MOCK) {
    // Simulate network + "thinking" latency
    await delay(600 + Math.random() * 400);
    return generateMockResponse(message, language, history);
  }

  try {
    const response = await fetch(`${API_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        conversation_id: conversationId,
        language,
        history,
      }),
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
