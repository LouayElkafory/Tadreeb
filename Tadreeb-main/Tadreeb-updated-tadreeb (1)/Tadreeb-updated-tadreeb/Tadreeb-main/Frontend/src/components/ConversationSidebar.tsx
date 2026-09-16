import { MessageSquarePlus, Trash2, MessageSquare } from "lucide-react";
import Logo from "./Logo";
import EmptyState from "./EmptyState";
import type { Conversation } from "../types";
import { useLanguage } from "../hooks/useLanguage";

interface ConversationSidebarProps {
  conversations: Conversation[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
}

export default function ConversationSidebar({
  conversations,
  activeId,
  onSelect,
  onNew,
  onDelete,
}: ConversationSidebarProps) {
  const { t } = useLanguage();

  return (
    <div className="flex flex-col h-full bg-baby-blue/30">
      <div className="p-4 border-b border-soft-blue shrink-0">
        <Logo />
      </div>
      <div className="p-3 shrink-0">
        <button
          onClick={onNew}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-white bg-primary hover:bg-primary-dark transition-colors shadow-sm"
        >
          <MessageSquarePlus size={17} />
          {t("chat.new")}
        </button>
      </div>
      <div className="flex-1 overflow-y-auto px-3 pb-4">
        {conversations.length === 0 ? (
          <EmptyState
            icon={<MessageSquare size={22} />}
            title={t("chat.emptyHistoryTitle")}
            description={t("chat.emptyHistoryBody")}
          />
        ) : (
          <div className="space-y-1">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group flex items-center gap-2 px-3 py-2.5 rounded-xl cursor-pointer transition-colors ${
                  conv.id === activeId ? "bg-white shadow-sm" : "hover:bg-white/60"
                }`}
                onClick={() => onSelect(conv.id)}
              >
                <MessageSquare
                  size={15}
                  className={conv.id === activeId ? "text-primary shrink-0" : "text-text-secondary shrink-0"}
                />
                <span
                  className={`flex-1 min-w-0 truncate text-sm ${
                    conv.id === activeId ? "text-deep-navy font-semibold" : "text-text-secondary"
                  }`}
                >
                  {conv.title || t("chat.defaultTitle")}
                </span>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDelete(conv.id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 rounded-md text-text-secondary hover:text-red-500 hover:bg-red-50 transition-all shrink-0"
                  aria-label={t("chat.deleteConversation")}
                >
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
