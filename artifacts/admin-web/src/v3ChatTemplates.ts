/** Predefined English drafts for V3 live chat — tap inserts into composer. */
export type V3ChatTemplate = {
  id: string;
  label: string;
  text: string;
};

export const V3_CHAT_TEMPLATES: V3ChatTemplate[] = [
  {
    id: "welcome",
    label: "Welcome / Intro",
    text: "Namaste. Cosmic Intelligence is connected. Please share your full name, date of birth, exact birth time, and birth place so we can begin.",
  },
  {
    id: "confirm_details",
    label: "Confirm birth details",
    text: "Thank you. Please confirm once: name, DOB (DD/MM/YYYY), birth time (AM/PM), and birth city — so the reading stays accurate.",
  },
  {
    id: "ask_question",
    label: "Ask main question",
    text: "What is your main question for this session? Share it in one clear line — career, relationship, timing, or any specific concern.",
  },
  {
    id: "clarify",
    label: "Clarify concern",
    text: "Could you clarify a little more — what exactly worries you most right now, and what outcome are you hoping for?",
  },
  {
    id: "timeline",
    label: "Ask timeline",
    text: "Over what time period should we focus — next 3 months, 6 months, or this year? That helps me prioritise the strongest signals.",
  },
  {
    id: "career",
    label: "Career focus",
    text: "For career: are you asking about job change, promotion, business, studies, or foreign opportunities? Share your current situation in 2–3 lines.",
  },
  {
    id: "relationship",
    label: "Relationship focus",
    text: "For relationship: is this about marriage timing, partner compatibility, a current relationship issue, or reconciliation? Please share briefly.",
  },
  {
    id: "finance",
    label: "Finance focus",
    text: "For finance: are you asking about income growth, savings, property, business cash flow, or a specific investment decision?",
  },
  {
    id: "health",
    label: "Health / energy",
    text: "For health and energy: what symptoms or concerns are you noticing, and since when? This is guidance only — not a medical diagnosis.",
  },
  {
    id: "reading",
    label: "Reading chart…",
    text: "I am reading your chart signals now. Please stay with me for a moment — I will share the clearest points next.",
  },
  {
    id: "one_more",
    label: "One more question",
    text: "We still have some time. Do you have one more focused question before we close?",
  },
  {
    id: "wrapping",
    label: "Wrapping up",
    text: "We are near the end of this session. I will summarise the key takeaways and practical next steps for you now.",
  },
  {
    id: "time_low",
    label: "Time almost over",
    text: "Only a short time remains on the timer. Please share your final question so I can answer it clearly before we end.",
  },
  {
    id: "closing",
    label: "Thank you / Close",
    text: "Thank you for this session. Follow the guidance with patience and consistency. You may book another session whenever you need deeper clarity. Take care.",
  },
];
