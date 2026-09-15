export type SourceType = "official" | "government" | "document" | "community";
export type Language = "ar" | "en";

export interface Source {
  id: string;
  title: string;
  url: string;
  organization: string;
  type: SourceType;
  description?: string;
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
  name: string;
  shortName: string;
  description: string;
  categories: string[];
  color: string;
}

export interface Program {
  id: string;
  name: string;
  organization: string; // Organization id
  track: string;
  level: "مبتدئ" | "متوسط" | "متقدم";
  description: string;
  skills?: string[];
}

export interface Track {
  id: string;
  name: string;
  description: string;
}

export type ChatApiResponse = {
  answer: string;
  sources: Source[];
  suggested_questions: string[];
};
