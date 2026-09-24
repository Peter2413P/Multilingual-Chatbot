export interface KeyDefinition {
  pcKey: string;           // Small English/Latin physical key reference (e.g. "Q", "A", "1")
  tamil: string;           // Normal unshifted Tamil character
  tamilShift?: string;     // Shifted Tamil character
  isSpecial?: boolean;     // Tab, Caps, Shift, Backspace, Enter, Space, etc.
  width?: string;          // Tailwind width class (e.g., "flex-1", "w-14", "w-20")
  action?: "backspace" | "enter" | "tab" | "caps" | "shift" | "space" | "clear" | "arrow-left" | "arrow-right" | "insert";
}

export const TAMIL_KEYBOARD_ROWS: KeyDefinition[][] = [
  // Row 1: Number row (~, 1-0, -, =, Backspace)
  [
    { pcKey: "`", tamil: "ஃ", tamilShift: "~" },
    { pcKey: "1", tamil: "1", tamilShift: "௧" },
    { pcKey: "2", tamil: "2", tamilShift: "௨" },
    { pcKey: "3", tamil: "3", tamilShift: "௩" },
    { pcKey: "4", tamil: "4", tamilShift: "௪" },
    { pcKey: "5", tamil: "5", tamilShift: "௫" },
    { pcKey: "6", tamil: "6", tamilShift: "௬" },
    { pcKey: "7", tamil: "7", tamilShift: "௭" },
    { pcKey: "8", tamil: "8", tamilShift: "௮" },
    { pcKey: "9", tamil: "9", tamilShift: "௯" },
    { pcKey: "0", tamil: "0", tamilShift: "௰" },
    { pcKey: "-", tamil: "-", tamilShift: "_" },
    { pcKey: "=", tamil: "ஸ்ரீ", tamilShift: "+" },
    { pcKey: "⌫", tamil: "Backspace", isSpecial: true, width: "w-14 sm:w-20", action: "backspace" },
  ],

  // Row 2: Top row (Tab, Q-P, [, ], \)
  [
    { pcKey: "Tab", tamil: "Tab", isSpecial: true, width: "w-12 sm:w-16", action: "tab" },
    { pcKey: "Q", tamil: "ஆ", tamilShift: "ஔ" },
    { pcKey: "W", tamil: "ஈ", tamilShift: "ஐ" },
    { pcKey: "E", tamil: "ஊ", tamilShift: "ஏ" },
    { pcKey: "R", tamil: "ஐ", tamilShift: "ஶ" },
    { pcKey: "T", tamil: "ஏ", tamilShift: "ஓ" },
    { pcKey: "Y", tamil: "ள", tamilShift: "ழ" },
    { pcKey: "U", tamil: "ற", tamilShift: "ன" },
    { pcKey: "I", tamil: "ந", tamilShift: "ண" },
    { pcKey: "O", tamil: "ட", tamilShift: "ண" },
    { pcKey: "P", tamil: "ப", tamilShift: "ம" },
    { pcKey: "[", tamil: "வ", tamilShift: "{" },
    { pcKey: "]", tamil: "ங", tamilShift: "}" },
    { pcKey: "\\", tamil: "ௐ", tamilShift: "|" },
  ],

  // Row 3: Home row (Caps, A-L, ;, ', Enter)
  [
    { pcKey: "Caps", tamil: "Caps", isSpecial: true, width: "w-14 sm:w-20", action: "caps" },
    { pcKey: "A", tamil: "அ", tamilShift: "ா" },
    { pcKey: "S", tamil: "இ", tamilShift: "ீ" },
    { pcKey: "D", tamil: "உ", tamilShift: "ூ" },
    { pcKey: "F", tamil: "எ", tamilShift: "ெ" },
    { pcKey: "G", tamil: "ஒ", tamilShift: "ே" },
    { pcKey: "H", tamil: "க", tamilShift: "க்ஷ" },
    { pcKey: "J", tamil: "த", tamilShift: "ஞ" },
    { pcKey: "K", tamil: "ச", tamilShift: "ஜ" },
    { pcKey: "L", tamil: "ட", tamilShift: "ஹ" },
    { pcKey: ";", tamil: "ம", tamilShift: "ஷ" },
    { pcKey: "'", tamil: "்", tamilShift: "ஸ" }, // Pulli (virama) & Sa
    { pcKey: "Enter ↵", tamil: "Enter", isSpecial: true, width: "w-14 sm:w-20", action: "enter" },
  ],

  // Row 4: Bottom row (Shift, Z-M, ,, ., /, Shift)
  [
    { pcKey: "Shift ⇧", tamil: "Shift", isSpecial: true, width: "w-16 sm:w-24", action: "shift" },
    { pcKey: "Z", tamil: "ய", tamilShift: "ஃ" },
    { pcKey: "X", tamil: "ர", tamilShift: "ஸ" },
    { pcKey: "C", tamil: "ல", tamilShift: "க்ஷ" },
    { pcKey: "V", tamil: "ா", tamilShift: "ை" },
    { pcKey: "B", tamil: "ி", tamilShift: "ீ" },
    { pcKey: "N", tamil: "ு", tamilShift: "ூ" },
    { pcKey: "M", tamil: "ெ", tamilShift: "ே" },
    { pcKey: ",", tamil: "ொ", tamilShift: "ோ" },
    { pcKey: ".", tamil: "ை", tamilShift: "ௌ" },
    { pcKey: "/", tamil: "?", tamilShift: "/" },
    { pcKey: "Shift ⇧", tamil: "Shift", isSpecial: true, width: "w-16 sm:w-24", action: "shift" },
  ],

];

// Precomputed mapping for direct physical keyboard keypresses
const DIRECT_KEY_MAP: Record<string, { normal: string; shift?: string }> = {};

for (const row of TAMIL_KEYBOARD_ROWS) {
  for (const k of row) {
    if (!k.isSpecial && k.pcKey && k.pcKey.length === 1) {
      DIRECT_KEY_MAP[k.pcKey.toLowerCase()] = {
        normal: k.tamil,
        shift: k.tamilShift || k.tamil,
      };
    }
  }
}

const SHIFT_NUM_MAP: Record<string, string> = {
  "!": "1",
  "@": "2",
  "#": "3",
  "$": "4",
  "%": "5",
  "^": "6",
  "&": "7",
  "*": "8",
  "(": "9",
  ")": "0",
  "_": "-",
  "+": "=",
  "{": "[",
  "}": "]",
  "|": "\\",
  ":": ";",
  "\"": "'",
  "<": ",",
  ">": ".",
  "?": "/",
  "~": "`",
};

/**
 * Returns the exact Tamil character mapped to the physical PC keyboard key.
 */
export function getDirectTamilKey(key: string, isShift: boolean): string | null {
  if (key === " ") return " ";
  
  // If key is a shift-symbol (like !, @, ?, etc.), detect it
  if (SHIFT_NUM_MAP[key]) {
    const baseKey = SHIFT_NUM_MAP[key];
    const entry = DIRECT_KEY_MAP[baseKey];
    if (entry) return entry.shift || entry.normal;
  }

  const lookupKey = key.toLowerCase();
  const entry = DIRECT_KEY_MAP[lookupKey];
  if (!entry) return null;
  
  const effectiveShift = isShift || (key.length === 1 && key !== lookupKey && key.toUpperCase() === key);
  return effectiveShift && entry.shift ? entry.shift : entry.normal;
}

