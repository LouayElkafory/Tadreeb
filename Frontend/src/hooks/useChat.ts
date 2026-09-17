import { useCallback, useMemo, useState } from "react";
import type { ChatMessage, Conversation } from "../types";
import { useLocalStorage } from "./useLocalStorage";
import { sendChatMessage, ChatApiError } from "../services/chatApi";
import { useLanguage } from "./useLanguage";

function makeId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

function titleFromMessage(message: string) {
  const trimmed = message.trim();
  return trimmed.length > 40 ? `${trimmed.slice(0, 40)}…` : trimmed;
}

export function useChat() {
  const { language, t } = useLanguage();
  const [conversations, setConversations] = useLocalStorage<Conversation[]>(
    "tadreeb-conversations",
    []
  );
  const [activeId, setActiveId] = useLocalStorage<string | null>(
    "tadreeb-active-conversation",
    null
  );
  const [isLoading, setIsLoading] = useState(false);

  const activeConversation = useMemo(
    () => conversations.find((c) => c.id === activeId) ?? null,
    [conversations, activeId]
  );

  const createConversation = useCallback(() => {
    const newConversation: Conversation = {
      id: makeId(),
      title: t("chat.defaultTitle"),
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };
    setConversations((prev) => [newConversation, ...prev]);
    setActiveId(newConversation.id);
    return newConversation.id;
  }, [setConversations, setActiveId, t]);

  const deleteConversation = useCallback(
    (id: string) => {
      setConversations((prev) => prev.filter((c) => c.id !== id));
      if (activeId === id) setActiveId(null);
    },
    [setConversations, activeId, setActiveId]
  );

  const clearAll = useCallback(() => {
    setConversations([]);
    setActiveId(null);
  }, [setConversations, setActiveId]);

  const updateMessage = useCallback(
    (conversationId: string, messageId: string, updates: Partial<ChatMessage>) => {
      setConversations((prev) =>
        prev.map((c) =>
          c.id === conversationId
            ? {
                ...c,
                messages: c.messages.map((m) => (m.id === messageId ? { ...m, ...updates } : m)),
              }
            : c
        )
      );
    },
    [setConversations]
  );

  const sendMessage = useCallback(
    async (text: string, conversationIdOverride?: string) => {
      const trimmed = text.trim();
      if (!trimmed || isLoading) return;

      let conversationId = conversationIdOverride ?? activeId;

      const userMessage: ChatMessage = {
        id: makeId(),
        role: "user",
        content: trimmed,
        createdAt: new Date().toISOString(),
      };

      if (!conversationId) {
        const newConversation: Conversation = {
          id: makeId(),
          title: titleFromMessage(trimmed),
          messages: [userMessage],
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString(),
        };
        conversationId = newConversation.id;
        setConversations((prev) => [newConversation, ...prev]);
        setActiveId(newConversation.id);
      } else {
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? {
                  ...c,
                  title: c.messages.length === 0 ? titleFromMessage(trimmed) : c.title,
                  messages: [...c.messages, userMessage],
                  updatedAt: new Date().toISOString(),
                }
              : c
          )
        );
      }

      setIsLoading(true);
      try {
        const currentConv = conversations.find((c) => c.id === conversationId);
        const history = currentConv
          ? currentConv.messages.map((m) => ({ role: m.role, content: m.content }))
          : [];

        const response = await sendChatMessage(trimmed, conversationId, language, history);
        const assistantMessage: ChatMessage = {
          id: makeId(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          suggestedQuestions: response.suggested_questions,
          createdAt: new Date().toISOString(),
        };
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, assistantMessage], updatedAt: new Date().toISOString() }
              : c
          )
        );
      } catch (err) {
        const isApiError = err instanceof ChatApiError;
        const errorMessage: ChatMessage = {
          id: makeId(),
          role: "assistant",
          content: isApiError
            ? t("chat.apiError")
            : t("chat.unknownError"),
          createdAt: new Date().toISOString(),
          isError: true,
        };
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, errorMessage], updatedAt: new Date().toISOString() }
              : c
          )
        );
      } finally {
        setIsLoading(false);
      }

      return conversationId;
    },
    [activeId, conversations, isLoading, language, setConversations, setActiveId, t]
  );

  const regenerateLast = useCallback(
    async (conversationId: string) => {
      const conv = conversations.find((c) => c.id === conversationId);
      if (!conv || isLoading) return;
      const lastUserMessage = [...conv.messages].reverse().find((m) => m.role === "user");
      if (!lastUserMessage) return;

      // remove trailing assistant message(s) after the last user message
      const lastUserIndex = conv.messages.map((m) => m.id).lastIndexOf(lastUserMessage.id);
      const trimmedMessages = conv.messages.slice(0, lastUserIndex + 1);
      const history = trimmedMessages.slice(0, -1).map((m) => ({ role: m.role, content: m.content }));

      setConversations((prev) =>
        prev.map((c) => (c.id === conversationId ? { ...c, messages: trimmedMessages } : c))
      );

      setIsLoading(true);
      try {
        const response = await sendChatMessage(lastUserMessage.content, conversationId, language, history);
        const assistantMessage: ChatMessage = {
          id: makeId(),
          role: "assistant",
          content: response.answer,
          sources: response.sources,
          suggestedQuestions: response.suggested_questions,
          createdAt: new Date().toISOString(),
        };
        setConversations((prev) =>
          prev.map((c) =>
            c.id === conversationId
              ? { ...c, messages: [...c.messages, assistantMessage], updatedAt: new Date().toISOString() }
              : c
          )
        );
      } finally {
        setIsLoading(false);
      }
    },
    [conversations, isLoading, language, setConversations]
  );


  return {
    conversations,
    activeConversation,
    activeId,
    isLoading,
    setActiveId,
    createConversation,
    deleteConversation,
    clearAll,
    sendMessage,
    regenerateLast,
    updateMessage,
  };
}
