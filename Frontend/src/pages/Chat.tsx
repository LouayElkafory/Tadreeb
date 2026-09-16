import { useEffect, useRef, useState } from "react";
import { useLocation } from "react-router-dom";
import { MessageCircleQuestion } from "lucide-react";
import ChatHeader from "../components/ChatHeader";
import ConversationSidebar from "../components/ConversationSidebar";
import SourcesPanel from "../components/SourcesPanel";
import MessageBubble from "../components/MessageBubble";
import ChatInput from "../components/ChatInput";
import LoadingIndicator from "../components/LoadingIndicator";
import SuggestedQuestions from "../components/SuggestedQuestions";
import MobileDrawer from "../components/MobileDrawer";
import { useChat } from "../hooks/useChat";
import { useLanguage } from "../hooks/useLanguage";

export default function Chat() {
  const {
    conversations,
    activeConversation,
    activeId,
    isLoading,
    setActiveId,
    createConversation,
    deleteConversation,
    sendMessage,
    regenerateLast,
    updateMessage,
  } = useChat();
  const { t } = useLanguage();

  const [input, setInput] = useState("");
  const [historyOpen, setHistoryOpen] = useState(false);
  const [sourcesOpen, setSourcesOpen] = useState(false);
  const [sourcesDrawerOpen, setSourcesDrawerOpen] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const location = useLocation();
  const autoSentRef = useRef(false);

  const messages = activeConversation?.messages ?? [];
  const emptyStateSuggestions = [
    t("chat.suggestion.iti"),
    t("chat.suggestion.business"),
    t("chat.suggestion.ai"),
    t("chat.suggestion.free"),
  ];

  // handle prefill/autosend coming from landing page
  useEffect(() => {
    const state = location.state as { prefill?: string; autoSend?: boolean } | null;
    if (state?.prefill && !autoSentRef.current) {
      autoSentRef.current = true;
      if (state.autoSend) {
        sendMessage(state.prefill);
      } else {
        setInput(state.prefill);
      }
      window.history.replaceState({}, document.title);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages.length, isLoading]);

  const handleSend = (text?: string) => {
    const message = text ?? input;
    if (!message.trim() || isLoading) return;
    sendMessage(message, activeId ?? undefined);
    setInput("");
  };

  const allSources = [...messages].reverse().find((m) => m.sources && m.sources.length > 0)?.sources ?? [];
  const lastAssistantId = [...messages].reverse().find((m) => m.role === "assistant")?.id;

  return (
    <div className="h-screen flex flex-col bg-white overflow-hidden">
      <ChatHeader
        onOpenHistory={() => setHistoryOpen(true)}
        onToggleSources={() => setSourcesOpen((v) => !v)}
        onNewChat={() => {
          createConversation();
          setInput("");
        }}
        sourcesOpen={sourcesOpen}
      />

      <div className="flex flex-1 min-h-0">
        {/* Desktop sidebar */}
        <aside className="hidden lg:block w-72 shrink-0 border-e border-soft-blue">
          <ConversationSidebar
            conversations={conversations}
            activeId={activeId}
            onSelect={setActiveId}
            onNew={createConversation}
            onDelete={deleteConversation}
          />
        </aside>

        {/* Center chat column */}
        <div className="flex-1 flex flex-col min-w-0">
          <div ref={scrollRef} className="flex-1 overflow-y-auto">
            <div className="max-w-2xl mx-auto px-4 sm:px-6 py-6 sm:py-8 flex flex-col gap-5">
              {messages.length === 0 ? (
                <div className="flex flex-col items-center text-center py-10 sm:py-16 animate-fade-up">
                  <div className="w-16 h-16 rounded-2xl bg-baby-blue text-primary flex items-center justify-center mb-5">
                    <MessageCircleQuestion size={28} />
                  </div>
                  <h2 className="text-xl sm:text-2xl font-extrabold text-deep-navy mb-2">
                    {t("chat.welcomeTitle")}
                  </h2>
                  <p className="text-text-secondary max-w-sm mb-8">
                    {t("chat.welcomeBody")}
                  </p>
                  <div className="w-full max-w-md">
                    <SuggestedQuestions
                      questions={emptyStateSuggestions}
                      onSelect={handleSend}
                      variant="cards"
                    />
                  </div>
                </div>
              ) : (
                messages.map((message) => (
                  <MessageBubble
                    key={message.id}
                    message={message}
                    isLastAssistant={message.id === lastAssistantId}
                    onRegenerate={
                      message.id === lastAssistantId && activeId
                        ? () => regenerateLast(activeId)
                        : undefined
                    }
                    onLike={
                      message.role === "assistant" && activeId
                        ? (liked) =>
                            updateMessage(activeId, message.id, {
                              liked: message.liked === liked ? null : liked,
                            })
                        : undefined
                    }
                    onSuggestionClick={handleSend}
                    sourcesCount={message.sources?.length}
                    onShowSources={() => setSourcesDrawerOpen(true)}
                  />
                ))
              )}
              {isLoading && <LoadingIndicator />}
            </div>
          </div>

          <div className="border-t border-soft-blue bg-white/90 backdrop-blur px-4 sm:px-6 py-4 shrink-0">
            <div className="max-w-2xl mx-auto">
              <ChatInput
                value={input}
                onChange={setInput}
                onSubmit={() => handleSend()}
                isLoading={isLoading}
              />
              <p className="text-[11px] text-text-secondary text-center mt-2">
                {t("chat.disclaimer")}
              </p>
            </div>
          </div>
        </div>

        {/* Desktop sources panel */}
        {sourcesOpen && (
          <aside className="hidden lg:block w-80 shrink-0 border-s border-soft-blue">
            <SourcesPanel sources={allSources} onClose={() => setSourcesOpen(false)} />
          </aside>
        )}
      </div>

      {/* Mobile history drawer */}
      <MobileDrawer open={historyOpen} onClose={() => setHistoryOpen(false)} title={t("chat.historyTitle")} side="start">
        <ConversationSidebar
          conversations={conversations}
          activeId={activeId}
          onSelect={(id) => {
            setActiveId(id);
            setHistoryOpen(false);
          }}
          onNew={() => {
            createConversation();
            setHistoryOpen(false);
          }}
          onDelete={deleteConversation}
        />
      </MobileDrawer>

      {/* Mobile sources drawer */}
      <MobileDrawer
        open={sourcesDrawerOpen}
        onClose={() => setSourcesDrawerOpen(false)}
        title={t("chat.sourcesTitle")}
        side="end"
      >
        <SourcesPanel sources={allSources} />
      </MobileDrawer>
    </div>
  );
}
