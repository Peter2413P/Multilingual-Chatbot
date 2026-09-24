import { transliterateWord, transliterateTamilText } from './src/lib/tamilTransliterator.ts';

const testCases = [
  // Basic
  { input: "tamil", expected: "தமிழ்" },
  { input: "vanakkam", expected: "வணக்கம்" },
  { input: "amma", expected: "அம்மா" },
  { input: "appa", expected: "அப்பா" },
  { input: "naan", expected: "நான்" },
  { input: "nee", expected: "நீ" },

  // Words
  { input: "thamizh", expected: "தமிழ்" },
  { input: "thamizhar", expected: "தமிழர்" },
  { input: "kavingar", expected: "கவிஞர்" },
  { input: "kelvi", expected: "கேள்வி" },
  { input: "puthagam", expected: "புத்தகம்" },

  // Questions
  { input: "enna", expected: "என்ன" },
  { input: "eppadi", expected: "எப்படி" },
  { input: "yaar", expected: "யார்" },
  { input: "eththanai", expected: "எத்தனை" },
  { input: "enge", expected: "எங்கே" },

  // Project-related Tamil
  { input: "agananuru", expected: "அகநானூறு" },
  { input: "thoguppu", expected: "தொகுப்பு" },
  { input: "kavingargal", expected: "கவிஞர்கள்" },
  { input: "pathil", expected: "பதில்" },

  // Sentence
  {
    input: "agananuru thoguppirkku eththanai kavingargal",
    expected: "அகநானூறு தொகுப்பிற்கு எத்தனை கவிஞர்கள்"
  }
];

let allPassed = true;
console.log("=== TRANSLITERATION TEST SUITE ===");
for (const tc of testCases) {
  const actual = transliterateTamilText(tc.input);
  const pass = actual === tc.expected;
  if (!pass) allPassed = false;
  console.log(`${pass ? "✓ PASS" : "✗ FAIL"}: "${tc.input}" -> "${actual}" (Expected: "${tc.expected}")`);
}

if (allPassed) {
  console.log("\n>>> ALL TEST CASES PASSED SUCCESSFULLY! <<<");
} else {
  console.log("\n>>> SOME TEST CASES FAILED! <<<");
}
