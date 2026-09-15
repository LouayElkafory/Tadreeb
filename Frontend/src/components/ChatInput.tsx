import { useRef, type KeyboardEvent } from "react";
import { ArrowUp, Mic } from "lucide-react";

interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  isLoading?: boolean;
  placeholder?: string;
  size?: "lg" | "md";
  autoFocus?: boolean;
}

export default function ChatInput({
  value,
  onChange,
  onSubmit,
  isLoading,
  placeholder = "اكتب سؤالك عن التدريب...",
  size = "md",
  autoFocus = false,
}: ChatInputProps) {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      if (value.trim() && !isLoading) onSubmit();
    }
  };

  const isLarge = size === "lg";

  return (
    <div
      className={`flex items-end gap-2 bg-white rounded-3xl border border-soft-blue shadow-[0_8px_30px_rgba(16,43,87,0.08)] focus-within:border-primary transition-colors ${
        isLarge ? "p-2.5" : "p-2"
      }`}
    >
      <button
        type="button"
        className={`shrink-0 flex items-center justify-center rounded-full text-text-secondary hover:text-primary hover:bg-baby-blue transition-colors ${
          isLarge ? "w-11 h-11" : "w-9 h-9"
        }`}
        aria-label="إدخال صوتي (قريبًا)"
        tabIndex={-1}
      >
        <Mic size={isLarge ? 19 : 17} />
      </button>
      <textarea
        ref={textareaRef}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        placeholder={placeholder}
        autoFocus={autoFocus}
        rows={1}
        dir="rtl"
        className={`flex-1 resize-none bg-transparent outline-none text-deep-navy placeholder:text-text-secondary/70 py-2.5 max-h-32 ${
          isLarge ? "text-base" : "text-sm"
        }`}
        style={{ minHeight: isLarge ? "1.75rem" : "1.5rem" }}
      />
      <button
        type="button"
        onClick={onSubmit}
        disabled={!value.trim() || isLoading}
        className={`shrink-0 flex items-center justify-center rounded-full transition-all ${
          isLarge ? "w-11 h-11" : "w-9 h-9"
        } ${
          value.trim() && !isLoading
            ? "bg-primary text-white hover:bg-primary-dark shadow-sm"
            : "bg-baby-blue text-text-secondary/50 cursor-not-allowed"
        }`}
        aria-label="إرسال"
      >
        <ArrowUp size={isLarge ? 19 : 17} />
      </button>
    </div>
  );
}
