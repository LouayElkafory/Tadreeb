interface SuggestedQuestionsProps {
  questions: string[];
  onSelect: (question: string) => void;
  variant?: "chips" | "cards";
}

export default function SuggestedQuestions({ questions, onSelect, variant = "chips" }: SuggestedQuestionsProps) {
  if (questions.length === 0) return null;

  if (variant === "cards") {
    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {questions.map((q) => (
          <button
            key={q}
            onClick={() => onSelect(q)}
            className="text-start p-4 rounded-2xl border border-soft-blue bg-white hover:border-primary hover:bg-baby-blue/40 hover:shadow-sm transition-all text-sm text-deep-navy font-medium"
          >
            {q}
          </button>
        ))}
      </div>
    );
  }

  return (
    <div className="flex flex-wrap gap-2">
      {questions.map((q) => (
        <button
          key={q}
          onClick={() => onSelect(q)}
          className="px-3.5 py-2 rounded-full border border-soft-blue bg-white hover:border-primary hover:bg-baby-blue/50 transition-colors text-xs font-medium text-deep-navy"
        >
          {q}
        </button>
      ))}
    </div>
  );
}
