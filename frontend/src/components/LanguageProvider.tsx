"use client";

import React, { createContext, useContext, useState, useEffect } from "react";

export type LanguageMode = "en" | "ta";

interface LanguageContextType {
  language: LanguageMode;
  setLanguage: (lang: LanguageMode) => void;
  isTamil: boolean;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
  const [language, setLanguageState] = useState<LanguageMode>("en");

  useEffect(() => {
    const saved = localStorage.getItem("personaforge_language") as LanguageMode;
    if (saved === "en" || saved === "ta") {
      setLanguageState(saved);
    }
  }, []);

  const setLanguage = (lang: LanguageMode) => {
    setLanguageState(lang);
    localStorage.setItem("personaforge_language", lang);
  };

  return (
    <LanguageContext.Provider
      value={{
        language,
        setLanguage,
        isTamil: language === "ta",
      }}
    >
      {children}
    </LanguageContext.Provider>
  );
}

export function useLanguage() {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error("useLanguage must be used within a LanguageProvider");
  }
  return context;
}
