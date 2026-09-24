/**
 * Standard Tamil Anjal / Phonetic Transliteration Engine
 * Complete, stateful, and linguistically accurate for conversational & literary Tamil.
 */

// Independent Vowels (உயிர் எழுத்துக்கள்)
const UYIR_MAP: Record<string, string> = {
  "aa": "ஆ", "A": "ஆ",
  "a": "அ",
  "ii": "ஈ", "I": "ஈ", "ee": "ஈ",
  "i": "இ",
  "uu": "ஊ", "U": "ஊ", "oo": "ஊ",
  "u": "உ",
  "ae": "ஏ", "ea": "ஏ", "E": "ஏ",
  "e": "எ",
  "ai": "ஐ",
  "oa": "ஓ", "O": "ஓ",
  "o": "ஒ",
  "au": "ஔ", "ou": "ஔ",
  "q": "ஃ", "akh": "ஃ"
};

// Vowel Signs (உயிர்மெய் குறியீடுகள்)
const VOWEL_SIGNS: Record<string, string> = {
  "aa": "ா", "A": "ா",
  "a": "", // removes pulli
  "ii": "ீ", "I": "ீ", "ee": "ீ",
  "i": "ி",
  "uu": "ூ", "U": "ூ", "oo": "ூ",
  "u": "ு",
  "ae": "ே", "ea": "ே", "E": "ே",
  "e": "ெ",
  "ai": "ை",
  "oa": "ோ", "O": "ோ",
  "o": "ொ",
  "au": "ௌ", "ou": "ௌ"
};

// Consonant Definitions
interface ConsonantEntry {
  base: string;
  pulli: string;
}

const CONSONANT_MAP: Record<string, ConsonantEntry> = {
  // Triple / Double Clusters
  "thth": { base: "த்த", pulli: "த்த்" },
  "chch": { base: "ச்ச", pulli: "ச்ச்" },
  "rkk": { base: "ற்க", pulli: "ற்க்" },
  "ndr": { base: "ன்ற", pulli: "ன்ற்" },
  "nth": { base: "ந்த", pulli: "ந்த்" },
  "nd": { base: "ந்த", pulli: "ந்த்" },
  "nj": { base: "ஞ", pulli: "ஞ்" },
  "ny": { base: "ஞ", pulli: "ஞ்" },
  "gn": { base: "ஞ", pulli: "ஞ்" },
  "ksh": { base: "க்ஷ", pulli: "க்ஷ்" },
  "sh": { base: "ஷ", pulli: "ஷ்" },
  "ch": { base: "ச", pulli: "ச்" },
  "th": { base: "த", pulli: "த்" },
  "dh": { base: "த", pulli: "த்" },
  "zh": { base: "ழ", pulli: "ழ்" },
  "kh": { base: "க", pulli: "க்" },
  "gh": { base: "க", pulli: "க்" },
  "nh": { base: "ந", pulli: "ந்" },
  "nnn": { base: "ன", pulli: "ன்" },
  "n-": { base: "ன", pulli: "ன்" },
  "nn": { base: "ன்ன", pulli: "ன்" },
  "ll": { base: "ள்ள", pulli: "ள்" },
  "rr": { base: "ற்ற", pulli: "ற்" },
  "ss": { base: "ஸ்", pulli: "ஸ்" },
  "kk": { base: "க்க", pulli: "க்" },
  "pp": { base: "ப்ப", pulli: "ப்" },
  "tt": { base: "ட்ட", pulli: "ட்" },
  "mm": { base: "ம்ம", pulli: "ம்" },
  "yy": { base: "ய்ய", pulli: "ய்" },
  "ng": { base: "ங்க", pulli: "ங்" }, // in Tamil ng is almost always ங்க / ங்

  // Single Consonants
  "k": { base: "க", pulli: "க்" },
  "g": { base: "க", pulli: "க்" },
  "c": { base: "ச", pulli: "ச்" },
  "s": { base: "ச", pulli: "ச்" },
  "j": { base: "ஜ", pulli: "ஜ்" },
  "t": { base: "த", pulli: "த்" }, // Contextual: at start/before vowel 'த', in clusters 'ட'
  "d": { base: "ட", pulli: "ட்" },
  "N": { base: "ண", pulli: "ண்" },
  "n": { base: "ந", pulli: "ன்" },
  "p": { base: "ப", pulli: "ப்" },
  "b": { base: "ப", pulli: "ப்" },
  "m": { base: "ம", pulli: "ம்" },
  "y": { base: "ய", pulli: "ய்" },
  "r": { base: "ர", pulli: "ர்" },
  "R": { base: "ற", pulli: "ற்" },
  "l": { base: "ல", pulli: "ல்" },
  "L": { base: "ள", pulli: "ள்" },
  "v": { base: "வ", pulli: "வ்" },
  "w": { base: "வ", pulli: "வ்" },
  "z": { base: "ழ", pulli: "ழ்" },
  "S": { base: "ஸ", pulli: "ஸ்" },
  "h": { base: "ஹ", pulli: "ஹ்" },
};

const CONSONANT_KEYS = Object.keys(CONSONANT_MAP).sort((a, b) => b.length - a.length);
const VOWEL_KEYS = Object.keys(UYIR_MAP).sort((a, b) => b.length - a.length);

// Lexical dictionary for well-known vocabulary & classical literature words
const LEXICAL_WORDS: Record<string, string> = {
  // Basic & Greetings
  "tamil": "தமிழ்",
  "thamizh": "தமிழ்",
  "tamizh": "தமிழ்",
  "vanakkam": "வணக்கம்",
  "vanakam": "வணக்கம்",
  "amma": "அம்மா",
  "appa": "அப்பா",
  "anna": "அண்ணா",
  "akka": "அக்கா",
  "ayya": "ஐயா",
  "naan": "நான்",
  "nan": "நான்",
  "nee": "நீ",
  "ni": "நீ",
  "nalla": "நல்ல",
  "nandri": "நன்றி",
  "nanri": "நன்றி",

  // Words
  "thamizhar": "தமிழர்",
  "thamilar": "தமிழர்",
  "kavingar": "கவிஞர்",
  "kavignar": "கவிஞர்",
  "kavinjar": "கவிஞர்",
  "kavingargal": "கவிஞர்கள்",
  "kavignargal": "கவிஞர்கள்",
  "kavinjargal": "கவிஞர்கள்",
  "kavithai": "கவிதை",
  "kavidhai": "கவிதை",
  "kelvi": "கேள்வி",
  "kelvigal": "கேள்விகள்",
  "pathil": "பதில்",
  "vidai": "விடை",
  "puthagam": "புத்தகம்",
  "puththagam": "புத்தகம்",
  "nool": "நூல்",
  "noolgal": "நூல்கள்",

  // Question words
  "enna": "என்ன",
  "eppadi": "எப்படி" ,
  "yaar": "யார்",
  "yar": "யார்",
  "eththanai": "எத்தனை",
  "ethanai": "எத்தனை",
  "enge": "எங்கே",
  "enga": "எங்கே",
  "eppodhu": "எப்போது",
  "eppo": "எப்போது",
  "edhu": "எது",
  "ethu": "எது",
  "endraal": "என்றால்",
  "endral": "என்றால்",
  "ezhudhiyavar": "எழுதியவர்",
  "ezhudhiya": "எழுதிய",

  // Sangam Literature & Project-related Tamil
  "agananuru": "அகநானூறு",
  "agananooru": "அகநானூறு",
  "akananooru": "அகநானூறு",
  "purananuru": "புறநானூறு",
  "purananooru": "புறநானூறு",
  "thirukkural": "திருக்குறள்",
  "tirukkural": "திருக்குறள்",
  "silappathikaram": "சிலப்பதிகாரம்",
  "manimekalai": "மணிமேகலை",
  "thoguppu": "தொகுப்பு",
  "thoguppirkku": "தொகுப்பிற்கு",
  "thoguppirku": "தொகுப்பிற்கு",
  "padikkiren": "படிக்கிறேன்",
  "sri": "ஸ்ரீ",
  "shree": "ஸ்ரீ",
  "om": "ௐ",
  "ohm": "ௐ"
};

/**
 * Transliterates a single English word token into Tamil Unicode.
 */
export function transliterateWord(word: string): string {
  if (!word) return "";

  const lower = word.toLowerCase();
  if (lower in LEXICAL_WORDS) {
    return LEXICAL_WORDS[lower];
  }

  // Handle plural suffix -gal / -kal
  if (lower.endsWith("gal") && lower.length > 3) {
    const root = lower.substring(0, lower.length - 3);
    const rootTamil = transliterateWord(root);
    return rootTamil + "கள்";
  }
  if (lower.endsWith("kku") && lower.length > 3) {
    const root = lower.substring(0, lower.length - 3);
    const rootTamil = transliterateWord(root);
    return rootTamil + "க்கு";
  }

  let i = 0;
  let result = "";
  const len = word.length;
  let isStartOfWord = true;

  while (i < len) {
    const remaining = word.substring(i);

    // If character is not a Latin letter, append directly
    if (!/^[a-zA-Z]/.test(remaining)) {
      result += word[i];
      i++;
      isStartOfWord = true;
      continue;
    }

    // 1. Check for consonant match at current position
    let matchedConsonant = "";
    for (const cKey of CONSONANT_KEYS) {
      if (remaining.startsWith(cKey) || remaining.toLowerCase().startsWith(cKey.toLowerCase())) {
        if (cKey === "N" || cKey === "L" || cKey === "R" || cKey === "S") {
          if (remaining.startsWith(cKey)) {
            matchedConsonant = cKey;
            break;
          }
        } else if (remaining.toLowerCase().startsWith(cKey.toLowerCase())) {
          matchedConsonant = cKey;
          break;
        }
      }
    }

    if (matchedConsonant) {
      const consObj = CONSONANT_MAP[matchedConsonant];
      i += matchedConsonant.length;
      const afterConsonant = word.substring(i);

      let baseChar = consObj.base;
      let pulliChar = consObj.pulli;

      // Special contextual rules:
      // 'n' at start of word -> 'ந' (ந்)
      // 'n' medially -> 'ன்' (unless before 'th'/'d')
      if (matchedConsonant.toLowerCase() === "n") {
        if (isStartOfWord) {
          baseChar = "ந";
          pulliChar = "ந்";
        } else {
          baseChar = "ன";
          pulliChar = "ன்";
        }
      }

      // 't' medially between vowels or in clusters -> 'ட' (otherwise 'த')
      if (matchedConsonant.toLowerCase() === "t") {
        if (!isStartOfWord && !remaining.toLowerCase().startsWith("th")) {
          baseChar = "ட";
          pulliChar = "ட்";
        }
      }

      // Check if followed by a vowel
      let matchedVowel = "";
      for (const vKey of VOWEL_KEYS) {
        if (afterConsonant.startsWith(vKey) || afterConsonant.toLowerCase().startsWith(vKey.toLowerCase())) {
          if (vKey === "A" || vKey === "I" || vKey === "U" || vKey === "E" || vKey === "O") {
            if (afterConsonant.startsWith(vKey)) {
              matchedVowel = vKey;
              break;
            }
          } else if (afterConsonant.toLowerCase().startsWith(vKey.toLowerCase())) {
            matchedVowel = vKey;
            break;
          }
        }
      }

      if (matchedVowel && matchedVowel in VOWEL_SIGNS) {
        const sign = VOWEL_SIGNS[matchedVowel];
        result += baseChar + sign;
        i += matchedVowel.length;
      } else {
        result += pulliChar;
      }
      isStartOfWord = false;
    } else {
      // 2. Match independent vowel (at start of word or standalone)
      let matchedVowel = "";
      for (const vKey of VOWEL_KEYS) {
        if (remaining.startsWith(vKey) || remaining.toLowerCase().startsWith(vKey.toLowerCase())) {
          if (vKey === "A" || vKey === "I" || vKey === "U" || vKey === "E" || vKey === "O") {
            if (remaining.startsWith(vKey)) {
              matchedVowel = vKey;
              break;
            }
          } else if (remaining.toLowerCase().startsWith(vKey.toLowerCase())) {
            matchedVowel = vKey;
            break;
          }
        }
      }

      if (matchedVowel && matchedVowel in UYIR_MAP) {
        result += UYIR_MAP[matchedVowel];
        i += matchedVowel.length;
      } else {
        result += word[i];
        i++;
      }
      isStartOfWord = false;
    }
  }

  return result;
}

/**
 * Transliterates an entire text block containing words, spaces, numbers, and punctuation into Tamil Unicode.
 */
export function transliterateTamilText(text: string): string {
  if (!text) return "";

  // Split into tokens of Latin words vs non-Latin segments
  const tokens = text.split(/([a-zA-Z]+)/);

  return tokens
    .map((tok) => {
      if (!tok) return "";
      if (/^[a-zA-Z]+$/.test(tok)) {
        return transliterateWord(tok);
      }
      return tok;
    })
    .join("");
}
