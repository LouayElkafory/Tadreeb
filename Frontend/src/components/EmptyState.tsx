import type { ReactNode } from "react";

interface EmptyStateProps {
  icon?: ReactNode;
  title: string;
  description?: string;
  action?: ReactNode;
}

export default function EmptyState({ icon, title, description, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center text-center py-14 px-6">
      {icon && (
        <div className="w-14 h-14 rounded-2xl bg-baby-blue text-primary flex items-center justify-center mb-4">
          {icon}
        </div>
      )}
      <h3 className="text-base font-semibold text-deep-navy mb-1.5">{title}</h3>
      {description && <p className="text-sm text-text-secondary max-w-sm mb-5">{description}</p>}
      {action}
    </div>
  );
}
