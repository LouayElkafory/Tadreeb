import type { Conversation } from '@/types'

const STORAGE_KEY = 'tadreeb.conversations.v1'

export function loadConversations(): Conversation[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Conversation[]
    if (!Array.isArray(parsed)) return []
    return parsed
  } catch {
    return []
  }
}

export function saveConversations(conversations: Conversation[]) {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(conversations))
  } catch {
    // Storage may be unavailable (private mode, quota). Fail silently.
  }
}

export function makeId(prefix = 'id'): string {
  return `${prefix}_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 9)}`
}

export function titleFromMessage(message: string): string {
  const trimmed = message.trim().replace(/\s+/g, ' ')
  if (trimmed.length <= 42) return trimmed
  return `${trimmed.slice(0, 42)}…`
}
