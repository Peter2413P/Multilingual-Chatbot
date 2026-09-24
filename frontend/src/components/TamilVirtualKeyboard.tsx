"use client";

import React, { useState } from "react";
import { TAMIL_KEYBOARD_ROWS, KeyDefinition } from "@/lib/tamilKeyboardLayout";
import { Keyboard, ChevronDown, ChevronUp, Delete, CornerDownLeft, Space } from "lucide-react";

interface TamilVirtualKeyboardProps {
  onInsertChar: (char: string) => void;
  onBackspace: () => void;
  onEnter: () => void;
  onSpace: () => void;
  onClear?: () => void;
  onArrowLeft?: () => void;
  onArrowRight?: () => void;
  isOpen: boolean;
  onToggle: () => void;
  isTransliteration?: boolean;
  onToggleTransliteration?: () => void;
}

export function TamilVirtualKeyboard({
  onInsertChar,
  onBackspace,
  onEnter,
  onSpace,
  onClear,
  onArrowLeft,
  onArrowRight,
  isOpen,
  onToggle,
  isTransliteration,
  onToggleTransliteration,
}: TamilVirtualKeyboardProps) {
  const [isShift, setIsShift] = useState(false);
  const [isCaps, setIsCaps] = useState(false);

  const isShifted = isShift || isCaps;

  const handleKeyClick = (keyDef: KeyDefinition) => {
    if (keyDef.isSpecial) {
      switch (keyDef.action) {
        case "backspace":
          onBackspace();
          break;
        case "enter":
          onEnter();
          break;
        case "space":
          onSpace();
          break;
        case "tab":
          onInsertChar("\t");
          break;
        case "caps":
          setIsCaps(!isCaps);
          break;
        case "shift":
          setIsShift(!isShift);
          break;
        case "clear":
          if (onClear) onClear();
          break;
        case "arrow-left":
          if (onArrowLeft) onArrowLeft();
          break;
        case "arrow-right":
          if (onArrowRight) onArrowRight();
          break;
        default:
          break;
      }
      return;
    }

    // Normal character insertion
    const charToInsert = isShifted && keyDef.tamilShift ? keyDef.tamilShift : keyDef.tamil;
    onInsertChar(charToInsert);

    // Auto-release Shift after one character (like standard physical Shift)
    if (isShift && !isCaps) {
      setIsShift(false);
    }
  };

  return (
    <div className="w-full max-w-3xl mx-auto select-none mt-1">
      {/* Keyboard Header / Toggle Bar */}
      <div className="flex flex-wrap items-center justify-between px-2 py-1 mb-1 gap-2">
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onToggle}
            className="flex items-center gap-2 text-xs font-medium text-amber-400 hover:text-amber-300 bg-amber-950/30 hover:bg-amber-950/50 border border-amber-800/40 px-2.5 py-1 rounded-lg transition-colors shadow-sm"
          >
            <Keyboard className="w-3.5 h-3.5" />
            <span>தமிழ் விசைப்பலகை (Tamil Keyboard)</span>
            {isOpen ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronUp className="w-3.5 h-3.5" />}
          </button>

          {/* Transliteration quick toggle */}
          {onToggleTransliteration && (
            <button
              type="button"
              onClick={onToggleTransliteration}
              className={`flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-lg border transition-all ${
                isTransliteration
                  ? "bg-amber-500/20 text-amber-300 border-amber-500/50 font-medium"
                  : "bg-zinc-900/90 text-zinc-400 border-zinc-800 hover:text-zinc-200"
              }`}
              title="Toggle English phonetic transliteration for typing (e.g. vanakkam → வணக்கம்)"
            >
              <span>🗣️ ஒலிபெயர்ப்பு (Transliteration):</span>
              <span className={`font-mono text-[11px] font-bold ${isTransliteration ? "text-amber-300" : "text-zinc-500"}`}>
                {isTransliteration ? "ON" : "OFF"}
              </span>
            </button>
          )}
        </div>

        {isOpen && (
          <div className="flex items-center gap-1.5 text-[11px] text-zinc-400">
            <span className={`px-2 py-0.5 rounded border text-[10px] font-mono transition-colors ${isCaps ? "bg-amber-500/20 text-amber-300 border-amber-500/50" : "bg-zinc-900 border-zinc-800 text-zinc-500"}`}>
              CAPS {isCaps ? "ON" : "OFF"}
            </span>
            <span className={`px-2 py-0.5 rounded border text-[10px] font-mono transition-colors ${isShift ? "bg-amber-500/20 text-amber-300 border-amber-500/50" : "bg-zinc-900 border-zinc-800 text-zinc-500"}`}>
              SHIFT {isShift ? "ON" : "OFF"}
            </span>
          </div>
        )}
      </div>

      {/* Keyboard Layout Body */}
      {isOpen && (
        <div className="bg-zinc-950/95 border border-zinc-800/90 rounded-2xl p-2 sm:p-2.5 shadow-2xl backdrop-blur-md space-y-1.5 animate-in fade-in slide-in-from-bottom-2 duration-200">
          {TAMIL_KEYBOARD_ROWS.map((row, rowIdx) => (
            <div key={rowIdx} className="flex gap-1 sm:gap-1.5 justify-center w-full">
              {row.map((keyDef, keyIdx) => {
                const charDisplay = isShifted && keyDef.tamilShift ? keyDef.tamilShift : keyDef.tamil;
                const isSpecial = keyDef.isSpecial;
                const isShiftKey = keyDef.action === "shift";
                const isCapsKey = keyDef.action === "caps";
                const isActiveModifier = (isShiftKey && isShift) || (isCapsKey && isCaps);

                return (
                  <button
                    key={`${rowIdx}-${keyIdx}-${keyDef.pcKey}`}
                    type="button"
                    onMouseDown={(e) => e.preventDefault()} // Prevents textarea blur
                    onClick={() => handleKeyClick(keyDef)}
                    className={`
                      relative flex flex-col items-center justify-between
                      rounded-lg transition-all active:scale-[0.96] shadow-sm
                      border font-sans
                      ${keyDef.width ? keyDef.width : "flex-1 min-w-[24px] sm:min-w-[34px]"}
                      ${
                        isActiveModifier
                          ? "bg-amber-600/30 text-amber-200 border-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.2)]"
                          : isSpecial
                          ? "bg-zinc-900/90 text-zinc-300 border-zinc-800 hover:bg-zinc-800 hover:text-white hover:border-zinc-700"
                          : "bg-zinc-900/70 text-zinc-100 border-zinc-800/90 hover:bg-zinc-800 hover:border-zinc-700/90 hover:text-white"
                      }
                      h-10 sm:h-12 py-1 px-1 sm:px-1.5
                    `}
                  >
                    {/* Small PC key reference label at top */}
                    <span className="text-[9px] sm:text-[10px] text-zinc-500 font-mono leading-none tracking-tight">
                      {keyDef.pcKey}
                    </span>

                    {/* Large primary Tamil character */}
                    <span
                      className={`
                        font-bold leading-none select-none my-auto
                        ${
                          isSpecial
                            ? "text-[10px] sm:text-xs font-medium text-zinc-400"
                            : "text-sm sm:text-base text-zinc-100 tracking-wide font-tamil"
                        }
                      `}
                    >
                      {charDisplay}
                    </span>
                  </button>
                );
              })}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
