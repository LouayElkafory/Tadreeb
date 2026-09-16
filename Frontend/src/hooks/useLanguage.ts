import { createContext, createElement, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import type { Language, LocalizedText } from "../types";

type TranslationValues = Record<string, string | number | undefined>;
type TranslationMap = Record<string, LocalizedText>;

const translations: TranslationMap = {
  "brand.name": { ar: "تدريب", en: "Tadreeb" },
  "nav.home": { ar: "الرئيسية", en: "Home" },
  "nav.sources": { ar: "المصادر", en: "Sources" },
  "nav.assistant": { ar: "المساعد الذكي", en: "AI Assistant" },
  "nav.organizations": { ar: "المؤسسات", en: "Institutions" },
  "nav.programs": { ar: "البرامج", en: "Programs" },
  "nav.login": { ar: "دخول", en: "Log in" },
  "nav.switchTo": { ar: "English", en: "العربية" },
  "nav.switchAria": { ar: "تغيير اللغة", en: "Switch language" },
  "nav.openMenu": { ar: "فتح القائمة", en: "Open menu" },
  "nav.closeMenu": { ar: "إغلاق", en: "Close" },

  "common.startChat": { ar: "ابدأ المحادثة", en: "Start chatting" },
  "common.explorePrograms": { ar: "اكتشف البرامج", en: "Explore programs" },
  "common.askAi": { ar: "اسأل AI", en: "Ask AI" },
  "common.learnMore": { ar: "اعرف أكتر", en: "Learn more" },
  "common.details": { ar: "عرض التفاصيل", en: "View details" },
  "common.clearFilters": { ar: "امسح الفلاتر", en: "Clear filters" },
  "common.clearSearch": { ar: "امسح البحث", en: "Clear search" },
  "common.filters": { ar: "فلاتر", en: "Filters" },
  "common.results": { ar: "{count} نتيجة", en: "{count} results" },
  "common.or": { ar: "أو", en: "or" },
  "common.backHome": { ar: "العودة للرئيسية", en: "Back to home" },
  "common.noData": { ar: "لا توجد بيانات متاحة حاليا.", en: "No data is currently available." },
  "common.allOrganizations": { ar: "كل المؤسسات", en: "All institutions" },
  "common.allTracks": { ar: "كل المسارات", en: "All tracks" },
  "common.allLevels": { ar: "كل المستويات", en: "All levels" },

  "level.beginner": { ar: "مبتدئ", en: "Beginner" },
  "level.intermediate": { ar: "متوسط", en: "Intermediate" },
  "level.advanced": { ar: "متقدم", en: "Advanced" },
  "source.official": { ar: "رسمي", en: "Official" },
  "source.government": { ar: "حكومي", en: "Government" },
  "source.document": { ar: "مستند", en: "Document" },
  "source.community": { ar: "مجتمعي", en: "Community" },

  "hero.trust": { ar: "إجابات مبنية على مصادر موثوقة", en: "Answers grounded in trusted sources" },
  "hero.headline": { ar: "اسأل عن التدريب. وإحنا نجيبلك الإجابة.", en: "Ask about training. We'll bring you the answer." },
  "hero.subheadline": { ar: "مساعدك الذكي لاكتشاف فرص التدريب التقني.", en: "Your AI guide to technical training opportunities." },
  "hero.body": {
    ar: "مساعد ذكي بيساعدك تعرف البرامج، شروط التقديم، التخصصات، ومدة التدريب من مصادر موثوقة.",
    en: "A smart assistant that helps you explore programs, admission requirements, tracks, and duration from trusted sources.",
  },
  "hero.placeholder": { ar: "اسأل أي حاجة عن ITI، NTI، DEPI...", en: "Ask anything about ITI, NTI, DEPI..." },
  "hero.suggestion.iti": { ar: "إيه شروط التقديم في ITI؟", en: "What are the ITI admission requirements?" },
  "hero.suggestion.business": { ar: "أنا خريج تجارة، إيه البرامج المناسبة ليا؟", en: "I studied business. Which programs fit me?" },
  "hero.suggestion.free": { ar: "هل التدريب مجاني؟", en: "Is the training free?" },
  "hero.suggestion.ai": { ar: "إيه أفضل مسار للـ AI؟", en: "What is the best AI track?" },

  "home.trustTitle": { ar: "اسأل براحتك. وإحنا نجيبلك الإجابة من المصادر.", en: "Ask freely. We answer from trusted sources." },
  "home.trustBody": { ar: "معلومات التدريب، البرامج، وشروط التقديم في مكان واحد.", en: "Training information, programs, and application requirements in one place." },
  "home.step.question": { ar: "سؤالك", en: "Your question" },
  "home.step.search": { ar: "البحث في المصادر", en: "Source search" },
  "home.step.answer": { ar: "إجابة ذكية", en: "Smart answer" },
  "home.step.sources": { ar: "المصادر", en: "Sources" },
  "home.orgEyebrow": { ar: "جهات موثوقة", en: "Trusted institutions" },
  "home.orgTitle": { ar: "المؤسسات التدريبية", en: "Training institutions" },
  "home.orgViewAll": { ar: "اعرف كل المؤسسات", en: "View all institutions" },
  "home.tracksTitle": { ar: "المسارات التقنية الأكثر طلبا", en: "In-demand technical tracks" },
  "home.tracksBody": { ar: "اختار مجال يهمك واسأل المساعد عن البرامج المناسبة ليك.", en: "Choose a field you care about and ask the assistant about suitable programs." },
  "home.askTrack": { ar: "اسأل AI عن المسار", en: "Ask AI about this track" },
  "home.askTrackPrompt": { ar: "إيه أفضل برامج {track}؟", en: "What are the best {track} programs?" },
  "home.howTitle": { ar: "إزاي بيشتغل تدريب؟", en: "How Tadreeb works" },
  "home.howBody": { ar: "أربع خطوات بسيطة لحد ما توصل لإجابتك.", en: "Four simple steps to get to your answer." },
  "home.how.1.title": { ar: "اسأل سؤالك", en: "Ask your question" },
  "home.how.1.desc": { ar: "اكتب أي سؤال عن التدريب التقني بلغتك العادية.", en: "Write any question about technical training in natural language." },
  "home.how.2.title": { ar: "المساعد يبحث في المصادر", en: "The assistant checks sources" },
  "home.how.2.desc": { ar: "بندور في قاعدة معرفة موثوقة عشان نلاقي أدق إجابة.", en: "We look through trusted knowledge sources to find the clearest answer." },
  "home.how.3.title": { ar: "تحصل على إجابة واضحة", en: "Get a clear answer" },
  "home.how.3.desc": { ar: "إجابة مبسطة ومباشرة من غير تعقيد.", en: "A simple, direct answer without unnecessary complexity." },
  "home.how.4.title": { ar: "راجع المصادر وكمل المحادثة", en: "Review sources and continue" },
  "home.how.4.desc": { ar: "شوف المصادر واسأل أي سؤال تاني يفيدك.", en: "Check the sources and ask any useful follow-up." },
  "home.finalTitle": { ar: "مش عارف تبدأ منين؟ اسأل تدريب.", en: "Not sure where to start? Ask Tadreeb." },
  "home.finalBody": { ar: "خلي المساعد يساعدك تكتشف الطريق المناسب ليك.", en: "Let the assistant help you discover the right path for you." },
  "home.programPreviewTitle": { ar: "برامج تدريبية مختارة", en: "Featured training programs" },
  "home.programPreviewBody": {
    ar: "نماذج من مسارات ITI و NTI و DEPI و MCIT، اسأل المساعد الذكي لتفاصيل أكتر.",
    en: "Examples from ITI, NTI, DEPI, and MCIT tracks. Ask the AI assistant for more details.",
  },
  "home.allPrograms": { ar: "كل البرامج", en: "All programs" },
  "home.trustStep.1.title": { ar: "اسأل براحتك", en: "Ask freely" },
  "home.trustStep.1.desc": { ar: "اكتب سؤالك بالعامية المصرية أو بأي طريقة تريحك.", en: "Write your question naturally, in the style that feels easiest." },
  "home.trustStep.2.title": { ar: "بندور في مصادر موثوقة", en: "We check trusted sources" },
  "home.trustStep.2.desc": { ar: "المساعد بيراجع معلومات ITI و NTI و DEPI و MCIT وغيرها.", en: "The assistant reviews information from ITI, NTI, DEPI, MCIT, and more." },
  "home.trustStep.3.title": { ar: "بنجهز إجابة واضحة", en: "We prepare a clear answer" },
  "home.trustStep.3.desc": { ar: "إجابة مبنية فعليا على المصادر، مش تخمين.", en: "The answer is based on available sources, not guesswork." },
  "home.trustStep.4.title": { ar: "بنوريك المصدر", en: "We show the source" },
  "home.trustStep.4.desc": { ar: "كل إجابة بتيجي معاها المصادر اللي اتبنت عليها.", en: "Every answer comes with the sources behind it." },

  "chat.welcomeTitle": { ar: "أهلا بيك في تدريب", en: "Welcome to Tadreeb" },
  "chat.welcomeBody": { ar: "اسألني عن البرامج، شروط التقديم، التخصصات، أو أي حاجة تخص التدريب التقني.", en: "Ask about programs, requirements, tracks, or anything related to technical training." },
  "chat.disclaimer": { ar: "تدريب بيقدملك معلومات إرشادية بناء على مصادر متاحة، وممكن تحتوي على أخطاء.", en: "Tadreeb provides guidance based on available sources and may contain mistakes." },
  "chat.historyTitle": { ar: "سجل المحادثات", en: "Chat history" },
  "chat.sourcesTitle": { ar: "المصادر", en: "Sources" },
  "chat.inputPlaceholder": { ar: "اكتب سؤالك عن التدريب...", en: "Type your training question..." },
  "chat.send": { ar: "إرسال", en: "Send" },
  "chat.thinking": { ar: "المساعد بيفكر...", en: "Assistant is thinking..." },
  "chat.headerTitle": { ar: "مساعد تدريب", en: "Tadreeb Assistant" },
  "chat.online": { ar: "متصل", en: "Online" },
  "chat.trust": { ar: "إجابات مبنية على مصادر موثوقة", en: "Answers grounded in trusted sources" },
  "chat.new": { ar: "محادثة جديدة", en: "New chat" },
  "chat.emptyHistoryTitle": { ar: "لسه مفيش محادثات", en: "No conversations yet" },
  "chat.emptyHistoryBody": { ar: "ابدأ محادثة جديدة عشان تشوفها هنا.", en: "Start a new chat and it will appear here." },
  "chat.deleteConversation": { ar: "حذف المحادثة", en: "Delete conversation" },
  "chat.defaultTitle": { ar: "محادثة جديدة", en: "New chat" },
  "chat.copy": { ar: "نسخ", en: "Copy" },
  "chat.copied": { ar: "تم النسخ", en: "Copied" },
  "chat.regenerate": { ar: "إعادة توليد", en: "Regenerate" },
  "chat.regenerateAria": { ar: "إعادة توليد الإجابة", en: "Regenerate answer" },
  "chat.like": { ar: "إعجاب", en: "Like" },
  "chat.dislike": { ar: "عدم إعجاب", en: "Dislike" },
  "chat.helpful": { ar: "مفيد", en: "Helpful" },
  "chat.notHelpful": { ar: "غير مفيد", en: "Not helpful" },
  "chat.errorLabel": { ar: "حدث خطأ", en: "Something went wrong" },
  "chat.apiError": { ar: "حصلت مشكلة وإحنا بنحاول نجيب الإجابة. جرب تاني.", en: "Something went wrong while getting the answer. Try again." },
  "chat.unknownError": { ar: "حصل خطأ غير متوقع. جرب تاني.", en: "An unexpected error occurred. Try again." },
  "chat.sourcesCount": { ar: "{count} مصادر", en: "{count} sources" },
  "chat.suggestion.iti": { ar: "إيه شروط التقديم في ITI؟", en: "What are the ITI admission requirements?" },
  "chat.suggestion.business": { ar: "أنا خريج تجارة، إيه المناسب ليا؟", en: "I studied business. What fits me?" },
  "chat.suggestion.ai": { ar: "إيه أفضل مسار للذكاء الاصطناعي؟", en: "What is the best AI track?" },
  "chat.suggestion.free": { ar: "هل التدريب مجاني؟", en: "Is the training free?" },

  "sources.title": { ar: "مصادر المعرفة", en: "Knowledge sources" },
  "sources.body": { ar: "اطلع على المصادر اللي بنعتمد عليها لفهم برامج التدريب.", en: "Explore the sources we use to understand training programs." },
  "sources.search": { ar: "دور في المصادر...", en: "Search sources..." },
  "sources.available": { ar: "{count} مصدر متاح", en: "{count} sources available" },
  "sources.emptyTitle": { ar: "مش لاقيين مصادر مطابقة", en: "No matching sources found" },
  "sources.panelEmptyTitle": { ar: "مفيش مصادر لسه", en: "No sources yet" },
  "sources.panelEmptyBody": { ar: "المصادر المستخدمة في الإجابة هتظهر هنا بعد ما تسأل سؤال.", en: "Sources used in an answer will appear here after you ask a question." },
  "sources.close": { ar: "إغلاق المصادر", en: "Close sources" },

  "programs.title": { ar: "اكتشف مسارك التقني", en: "Discover your technical path" },
  "programs.body": { ar: "اختار مجال يهمك واسأل المساعد عن البرامج المناسبة ليك.", en: "Choose an area and ask the assistant about programs that fit you." },
  "programs.search": { ar: "دور على برنامج أو مجال...", en: "Search for a program or field..." },
  "programs.organization": { ar: "المؤسسة", en: "Institution" },
  "programs.track": { ar: "المسار", en: "Track" },
  "programs.level": { ar: "المستوى", en: "Level" },
  "programs.emptyTitle": { ar: "مش لاقيين برامج مطابقة للبحث", en: "No matching programs found" },
  "programs.back": { ar: "رجوع للبرامج", en: "Back to programs" },
  "programs.about": { ar: "عن البرنامج", en: "About the program" },
  "programs.skills": { ar: "المهارات المستهدفة", en: "Target skills" },
  "programs.ask": { ar: "اسأل AI عن البرنامج", en: "Ask AI about this program" },
  "programs.askAssistant": { ar: "اسأل المساعد", en: "Ask the assistant" },
  "programs.askPrompt": { ar: "إيه شروط التقديم في {program}؟", en: "What are the admission requirements for {program}?" },
  "programs.cardAskPrompt": { ar: "احكيلي عن برنامج {program} وشروط التقديم عليه.", en: "Tell me about {program} and its admission requirements." },
  "programs.info": {
    ar: "لمعرفة تفاصيل زي مدة التدريب، شروط القبول الدقيقة، والمستندات المطلوبة، اسأل المساعد لمعرفة التفاصيل المتاحة من المصادر الموثوقة.",
    en: "For details such as training duration, precise admission requirements, and required documents, ask the assistant for information from trusted sources.",
  },
  "programs.related": { ar: "برامج مشابهة", en: "Similar programs" },

  "organizations.title": { ar: "اكتشف المؤسسات التدريبية", en: "Explore training institutions" },
  "organizations.body": { ar: "اعرف أكتر عن الجهات اللي بتقدم فرص تدريب تقني.", en: "Learn more about the institutions offering technical training opportunities." },
  "organizations.back": { ar: "رجوع للمؤسسات", en: "Back to institutions" },
  "organizations.ask": { ar: "اسأل AI عن المؤسسة", en: "Ask AI about this institution" },
  "organizations.askPrompt": { ar: "احكيلي عن برامج {organization} وشروط التقديم.", en: "Tell me about {organization} programs and admission requirements." },
  "organizations.availablePrograms": { ar: "برامج متاحة", en: "Available programs" },
  "organizations.noPrograms": { ar: "اسأل المساعد لمعرفة التفاصيل المتاحة من المصادر الموثوقة.", en: "Ask the assistant for details available from trusted sources." },
  "organizations.relatedTracks": { ar: "المسارات المرتبطة", en: "Related tracks" },
  "organizations.other": { ar: "مؤسسات أخرى", en: "Other institutions" },

  "assistant.title": { ar: "مساعدك الذكي لاكتشاف فرص التدريب.", en: "Your AI guide to training opportunities." },
  "assistant.body": { ar: "من أول سؤال لحد ما تعرف المسار المناسب ليك، تدريب بيساعدك تفهم اختياراتك من مصادر موثوقة.", en: "From your first question to choosing a suitable path, Tadreeb helps you understand options from trusted sources." },
  "assistant.canHelpTitle": { ar: "إيه اللي تدريب يقدر يساعدك فيه؟", en: "What can Tadreeb help with?" },
  "assistant.howTitle": { ar: "إزاي بيشتغل؟", en: "How it works" },
  "assistant.sourcesTitle": { ar: "ليه المصادر مهمة؟", en: "Why sources matter" },
  "assistant.sourcesBody": { ar: "تدريب بيجاوب بناء على المعرفة المتاحة له، وبيكون شفاف معاك لو المعلومة مش موجودة بدل ما يختلق إجابة.", en: "Tadreeb answers from available knowledge and is transparent when information is missing instead of inventing an answer." },
  "assistant.quote": { ar: "لو مش لاقيين معلومات موثوقة كفاية، هنقولك بصراحة.", en: "If we cannot find enough reliable information, we will say so clearly." },
  "assistant.try": { ar: "جرب المساعد دلوقتي", en: "Try the assistant now" },
  "assistant.help.programs": { ar: "برامج التدريب", en: "Training programs" },
  "assistant.help.admission": { ar: "شروط القبول", en: "Admission requirements" },
  "assistant.help.tracks": { ar: "المسارات التعليمية", en: "Learning tracks" },
  "assistant.help.institutions": { ar: "المؤسسات التدريبية", en: "Training institutions" },
  "assistant.help.eligibility": { ar: "أسئلة الأهلية", en: "Eligibility questions" },
  "assistant.help.duration": { ar: "مدة التدريب", en: "Training duration" },
  "assistant.help.documents": { ar: "المستندات المطلوبة", en: "Required documents" },
  "assistant.help.compare": { ar: "مقارنة المسارات", en: "Track comparison" },
  "assistant.step.ask.title": { ar: "اسأل سؤالك", en: "Ask your question" },
  "assistant.step.ask.desc": { ar: "اكتب سؤالك عن التدريب التقني بشكل طبيعي.", en: "Write your technical training question naturally." },
  "assistant.step.retrieve.title": { ar: "استرجاع المعلومات", en: "Retrieve information" },
  "assistant.step.retrieve.desc": { ar: "بندور في مصادر موثوقة عن أدق معلومة ليك.", en: "We search trusted sources for the most relevant information." },
  "assistant.step.answer.title": { ar: "توليد إجابة مبنية على مصادر", en: "Generate a sourced answer" },
  "assistant.step.answer.desc": { ar: "بنولد إجابة واضحة بناء على اللي لقيناه.", en: "We generate a clear answer based on what we found." },
  "assistant.step.sources.title": { ar: "عرض المصادر", en: "Show sources" },
  "assistant.step.sources.desc": { ar: "بنوريك المصادر اللي اعتمدنا عليها في إجابتنا.", en: "We show the sources used for the answer." },

  "footer.description": { ar: "مساعد ذكي بيساعدك تكتشف فرص التدريب التقني في مصر من مصادر موثوقة.", en: "An AI assistant that helps you discover technical training opportunities in Egypt from trusted sources." },
  "footer.explore": { ar: "استكشف", en: "Explore" },
  "footer.assistant": { ar: "المساعد", en: "Assistant" },
  "footer.aboutAssistant": { ar: "عن المساعد الذكي", en: "About the AI assistant" },
  "footer.signIn": { ar: "تسجيل الدخول", en: "Sign in" },
  "footer.about": { ar: "منصة مستقلة لإتاحة معلومات التدريب التقني في مكان واحد.", en: "An independent platform for technical training information in one place." },
  "footer.rights": { ar: "© {year} تدريب. جميع الحقوق محفوظة.", en: "© {year} Tadreeb. All rights reserved." },
  "footer.made": { ar: "صنع بعناية لدعم رحلتك التقنية.", en: "Crafted to support your technical journey." },

  "login.title": { ar: "أهلا بيك تاني", en: "Welcome back" },
  "login.body": { ar: "سجل دخولك عشان تكمل تجربتك.", en: "Sign in to continue your experience." },
  "login.notice": { ar: "دي واجهة تجريبية لتسجيل الدخول، وهتتفعل لاحقا مع الربط بالخادم.", en: "This is a demo login screen and will be enabled later with backend integration." },
  "login.email": { ar: "البريد الإلكتروني", en: "Email" },
  "login.password": { ar: "كلمة المرور", en: "Password" },
  "login.forgot": { ar: "نسيت كلمة المرور؟", en: "Forgot password?" },
  "login.submit": { ar: "تسجيل الدخول", en: "Log in" },
  "login.google": { ar: "المتابعة عبر Google", en: "Continue with Google" },
  "login.noAccount": { ar: "لسه معملتش حساب؟", en: "Do not have an account yet?" },
  "login.signup": { ar: "سجل دلوقتي", en: "Sign up now" },

  "notFound.title": { ar: "الصفحة دي مش موجودة.", en: "This page does not exist." },
  "notFound.body": { ar: "ممكن تكون الصفحة اتنقلت أو الرابط مش صحيح.", en: "The page may have moved, or the link may be incorrect." },
  "notFound.openAssistant": { ar: "افتح المساعد الذكي", en: "Open the AI assistant" },

  "mock.defaultSuggestion.docs": { ar: "طب إيه الأوراق المطلوبة؟", en: "What documents are required?" },
  "mock.defaultSuggestion.test": { ar: "هل في اختبار قبول؟", en: "Is there an admission test?" },
  "mock.defaultSuggestion.duration": { ar: "مدة التدريب كام؟", en: "How long is the training?" },
  "mock.defaultSuggestion.date": { ar: "إمتى التقديم؟", en: "When does application open?" },
  "mock.noInfo": {
    ar: "مش لاقي معلومات موثوقة كفاية في المصادر المتاحة عشان أجاوب على السؤال ده بدقة. ممكن تحاول توضح سؤالك أكتر، أو تسأل عن مؤسسة أو برنامج معين زي ITI أو NTI أو DEPI؟",
    en: "I cannot find enough reliable information in the available sources to answer that accurately. Try clarifying your question, or ask about a specific institution or program such as ITI, NTI, or DEPI.",
  },
  "mock.general": {
    ar: "شكرا لسؤالك. بناء على المصادر المتاحة، فيه معلومات عامة بتساعدك تبدأ:\n\n- في أكتر من جهة تدريب تقني موثوقة في مصر زي **ITI** و**NTI** و**DEPI** و**MCIT** و**ITIDA**\n- كل جهة بتقدم مسارات مختلفة حسب المستوى والتخصص\n- ممكن تسألني عن مؤسسة أو مسار معين عشان أديك تفاصيل أدق\n\nعايز أساعدك تختار المسار المناسب ليك؟",
    en: "Thanks for your question. Based on available sources, here are useful starting points:\n\n- Egypt has several trusted technology training institutions such as **ITI**, **NTI**, **DEPI**, **MCIT**, and **ITIDA**\n- Each institution offers different tracks depending on level and specialization\n- You can ask about a specific institution or track for more precise details\n\nWould you like help choosing a suitable path?",
  },
};

interface LanguageContextValue {
  language: Language;
  lang: Language;
  dir: "rtl" | "ltr";
  toggleLanguage: () => void;
  toggleLang: () => void;
  setLanguage: (language: Language) => void;
  setLang: (language: Language) => void;
  t: (key: string, values?: TranslationValues) => string;
  localize: (value: LocalizedText) => string;
}

const LanguageContext = createContext<LanguageContextValue | undefined>(undefined);

function getInitialLanguage(): Language {
  const stored = window.localStorage.getItem("tadreeb-lang") ?? window.localStorage.getItem("tadreeb.lang");
  return stored === "en" ? "en" : "ar";
}

function format(template: string, values?: TranslationValues) {
  if (!values) return template;
  return template.replace(/\{(\w+)\}/g, (_, key: string) => String(values[key] ?? ""));
}

export function LanguageProvider({ children }: { children: ReactNode }) {
  const [language, setLanguage] = useState<Language>(getInitialLanguage);
  const dir = language === "ar" ? "rtl" : "ltr";

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = dir;
    window.localStorage.setItem("tadreeb-lang", language);
  }, [language, dir]);

  const toggleLanguage = useCallback(() => {
    setLanguage((prev) => (prev === "ar" ? "en" : "ar"));
  }, []);

  const t = useCallback(
    (key: string, values?: TranslationValues) => {
      const entry = translations[key];
      return format(entry?.[language] ?? key, values);
    },
    [language],
  );

  const localize = useCallback((value: LocalizedText) => value[language], [language]);

  const value = useMemo(
    () => ({
      language,
      lang: language,
      dir,
      toggleLanguage,
      toggleLang: toggleLanguage,
      setLanguage,
      setLang: setLanguage,
      t,
      localize,
    }),
    [dir, language, localize, t, toggleLanguage],
  );

  return createElement(LanguageContext.Provider, { value }, children);
}

export function useLanguage() {
  const ctx = useContext(LanguageContext);
  if (!ctx) throw new Error("useLanguage must be used within a LanguageProvider");
  return ctx;
}
