import { useState } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Copy, Check, RefreshCw, ThumbsUp, ThumbsDown, AlertCircle } from "lucide-react";
import type { ChatMessage } from "../types";
import SuggestedQuestions from "./SuggestedQuestions";

interface MessageBubbleProps {
  message: ChatMessage;
  onRegenerate?: () => void;
  onLike?: (liked: boolean) => void;
  onSuggestionClick?: (question: string) => void;
  isLastAssistant?: boolean;
  onShowSources?: () => void;
  sourcesCount?: number;
}

export default function MessageBubble({
  message,
  onRegenerate,
  onLike,
  onSuggestionClick,
  isLastAssistant,
  onShowSources,
  sourcesCount,
}: MessageBubbleProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(message.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 1600);
    } catch {
      // clipboard unavailable
    }
  };

  if (message.role === "user") {
    return (
      <div className="flex justify-end animate-bubble-in">
        <div className="max-w-[85%] sm:max-w-[70%] bg-primary text-white px-4 py-3 rounded-2xl rounded-tl-md sm:rounded-tl-2xl sm:rounded-se-md leading-relaxed text-sm sm:text-[15px]">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className="flex justify-start animate-bubble-in">
      <div className="max-w-[92%] sm:max-w-[78%] w-full">
        <div
          className={`px-4 py-3.5 sm:px-5 sm:py-4 rounded-2xl rounded-tr-md sm:rounded-ss-md text-sm sm:text-[15px] ${
            message.isError
              ? "bg-red-50 border border-red-100 text-red-700"
              : "bg-white border border-soft-blue text-deep-navy"
          }`}
        >
          {message.isError && (
            <div className="flex items-center gap-2 mb-1.5 text-red-600 font-semibold text-xs">
              <AlertCircle size={14} />
              حدث خطأ
            </div>
          )}
          <div className="prose-tadreeb">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{message.content}</ReactMarkdown>
          </div>
        </div>

        {!message.isError && (
          <div className="flex items-center gap-1 mt-2 px-1">
            <button
              onClick={handleCopy}
              className="p-1.5 rounded-lg text-text-secondary hover:text-primary hover:bg-baby-blue transition-colors"
              aria-label="نسخ"
              title="نسخ"
            >
              {copied ? <Check size={15} /> : <Copy size={15} />}
            </button>
            {isLastAssistant && onRegenerate && (
              <button
                onClick={onRegenerate}
                className="p-1.5 rounded-lg text-text-secondary hover:text-primary hover:bg-baby-blue transition-colors"
                aria-label="إعادة توليد الإجابة"
                title="إعادة توليد"
              >
                <RefreshCw size={15} />
              </button>
            )}
            {onLike && (
              <>
                <button
                  onClick={() => onLike(true)}
                  className={`p-1.5 rounded-lg transition-colors ${
                    message.liked === true
                      ? "text-primary bg-baby-blue"
                      : "text-text-secondary hover:text-primary hover:bg-baby-blue"
                  }`}
                  aria-label="إعجاب"
                  title="مفيد"
                >
                  <ThumbsUp size={15} />
                </button>
                <button
                  onClick={() => onLike(false)}
                  className={`p-1.5 rounded-lg transition-colors ${
                    message.liked === false
                      ? "text-red-500 bg-red-50"
                      : "text-text-secondary hover:text-red-500 hover:bg-red-50"
                  }`}
                  aria-label="عدم إعجاب"
                  title="غير مفيد"
                >
                  <ThumbsDown size={15} />
                </button>
              </>
            )}
            {!!sourcesCount && onShowSources && (
              <button
                onClick={onShowSources}
                className="mr-1 flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium text-primary bg-baby-blue hover:bg-soft-blue transition-colors lg:hidden"
              >
                {sourcesCount} مصادر
              </button>
            )}
            {copied && <span className="text-xs text-primary">تم النسخ</span>}
          </div>
        )}

        {message.suggestedQuestions && message.suggestedQuestions.length > 0 && onSuggestionClick && (
          <div className="mt-3">
            <SuggestedQuestions questions={message.suggestedQuestions} onSelect={onSuggestionClick} />
          </div>
        )}
      </div>
    </div>
  );
}
