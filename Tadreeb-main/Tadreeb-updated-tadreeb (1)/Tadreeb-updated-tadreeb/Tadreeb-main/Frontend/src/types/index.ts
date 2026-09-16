export type SourceType = "official" | "government" | "document" | "community";
export type Language = "ar" | "en";
export type LocalizedText = Record<Language, string>;
export type ProgramLevel = "beginner" | "intermediate" | "advanced";

export interface Source {
  id: string;
  title: LocalizedText;
  url: string;
  organization: LocalizedText;
  type: SourceType;
  description?: LocalizedText;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[];
  suggestedQuestions?: string[];
  createdAt: string;
  liked?: boolean | null; // true = like, false = dislike, null/undefined = none
  isError?: boolean;
}

export interface Conversation {
  id: string;
  title: string;
  messages: ChatMessage[];
  createdAt: string;
  updatedAt: string;
}

export interface Organization {
  id: string;
  name: LocalizedText;
  shortName: string;
  description: LocalizedText;
  categories: LocalizedText[];
  color: string;
}

export interface Program {
  id: string;
  name: LocalizedText;
  organization: string; // Organization id
  track: string;
  level: ProgramLevel;
  description: LocalizedText;
  skills?: string[];
}

export interface Track {
  id: string;
  name: LocalizedText;
  description: LocalizedText;
}

export type ChatApiResponse = {
  answer: string;
  sources: Source[];
  suggested_questions: string[];
};
