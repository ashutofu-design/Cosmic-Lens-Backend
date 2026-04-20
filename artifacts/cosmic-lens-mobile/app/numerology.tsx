import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import * as Linking from "expo-linking";
import { router } from "expo-router";
import React, { useEffect, useMemo, useState } from "react";
import { API_BASE } from "@/lib/apiConfig";
import {
  Platform, Pressable, ScrollView, StyleSheet,
  Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { useC } from "@/context/ThemeContext";
import { useUser, type ProfileEntry } from "@/context/UserContext";
import { useT } from "@/hooks/useT";

// ── Calculation helpers ───────────────────────────────────────────────────────
const PYTH: Record<string, number> = {
  a:1,b:2,c:3,d:4,e:5,f:6,g:7,h:8,i:9,
  j:1,k:2,l:3,m:4,n:5,o:6,p:7,q:8,r:9,
  s:1,t:2,u:3,v:4,w:5,x:6,y:7,z:8,
};
const VOWELS = new Set(["a","e","i","o","u"]);

function reduce(n: number): number {
  while (n > 9 && n !== 11 && n !== 22 && n !== 33) {
    n = String(n).split("").reduce((a, c) => a + parseInt(c, 10), 0);
  }
  return n;
}
function digitSum(x: number): number {
  return String(Math.abs(x)).split("").reduce((a, c) => a + parseInt(c, 10), 0);
}
function letterSum(name: string, vowelsOnly?: boolean, consonantsOnly?: boolean): number {
  const chars = name.toLowerCase().replace(/[^a-z]/g, "").split("");
  const filtered = chars.filter(c =>
    vowelsOnly    ? VOWELS.has(c) :
    consonantsOnly ? !VOWELS.has(c) : true
  );
  return filtered.reduce((a, c) => a + (PYTH[c] ?? 0), 0);
}

function calcLifePath(day: number, month: number, year: number) {
  return reduce(reduce(digitSum(day)) + reduce(digitSum(month)) + reduce(digitSum(year)));
}
function calcDestiny(name: string) { return reduce(letterSum(name)); }
function calcSoulUrge(name: string) { return reduce(letterSum(name, true)); }
function calcPersonality(name: string) { return reduce(letterSum(name, false, true)); }
function calcMaturity(lp: number, dest: number) { return reduce(lp + dest); }
function calcPersonalYear(day: number, month: number) {
  const y = new Date().getFullYear();
  return reduce(digitSum(day) + digitSum(month) + digitSum(y));
}
function calcPersonalMonth(day: number, month: number) {
  const py  = calcPersonalYear(day, month);
  const now = new Date().getMonth() + 1;
  return reduce(py + now);
}

// ── Number interpretation data ────────────────────────────────────────────────
interface NumInfo {
  title: string; titleHindi: string;
  planet: string; planetEmoji: string;
  color: string;
  luckyNums: string; luckyColor: string; luckyColorHex: string;
  traits: string[]; traitsHindi: string[];
  desc: string;
  career: string;
  love: string;
  strength: string;
  weakness: string;
  remedy: string;
}

const NUM: Record<number, NumInfo> = {
  1: { title:"Leadership", titleHindi:"नेतृत्व", planet:"Surya", planetEmoji:"☀️",
       color:"#f59e0b", luckyNums:"1, 10, 19, 28", luckyColor:"Gold / Orange", luckyColorHex:"#f59e0b",
       traits:["Ambitious","Independent","Pioneering","Creative"],
       traitsHindi:["महत्त्वाकांक्षी","स्वतंत्र","अग्रणी","रचनात्मक"],
       desc:"You are a natural-born leader with iron willpower. Originality and independence define your path — you were born to blaze new trails.",
       career:"Politics, Management, Entrepreneurship, Military",
       love:"You need a partner who respects your independence and admires your drive.",
       strength:"Determination, Confidence", weakness:"Ego, Stubbornness",
       remedy:"Offer water to the rising Sun each morning. Donate wheat on Sundays." },
  2: { title:"Partnership", titleHindi:"सहयोग", planet:"Chandra", planetEmoji:"🌙",
       color:"#94a3b8", luckyNums:"2, 11, 20, 29", luckyColor:"White / Silver", luckyColorHex:"#e2e8f0",
       traits:["Sensitive","Cooperative","Diplomatic","Intuitive"],
       traitsHindi:["संवेदनशील","सहयोगी","कूटनीतिज्ञ","अंतर्ज्ञानी"],
       desc:"You are a peacemaker gifted with deep emotional intelligence. You thrive in partnerships and bring harmony to every relationship you touch.",
       career:"Counseling, Arts, Music, Nursing, Diplomacy",
       love:"You are a deeply romantic and devoted partner who values emotional safety.",
       strength:"Empathy, Patience", weakness:"Over-sensitivity, Indecisiveness",
       remedy:"Fast on Mondays and donate white cloth or rice to a temple." },
  3: { title:"Creativity", titleHindi:"सृजनात्मकता", planet:"Guru", planetEmoji:"🪐",
       color:"#facc15", luckyNums:"3, 12, 21, 30", luckyColor:"Yellow / Purple", luckyColorHex:"#facc15",
       traits:["Joyful","Expressive","Optimistic","Social"],
       traitsHindi:["आनंदमय","अभिव्यक्तिशील","आशावादी","सामाजिक"],
       desc:"You radiate joy and creativity. Gifted with communication and charisma, you inspire and uplift everyone around you.",
       career:"Writing, Entertainment, Teaching, Arts, Comedy",
       love:"You are a playful, fun-loving partner who never lets the spark fade.",
       strength:"Optimism, Creativity", weakness:"Scattered focus, Over-indulgence",
       remedy:"Worship Lord Vishnu on Thursdays. Donate yellow sweets or turmeric." },
  4: { title:"Foundation", titleHindi:"स्थिरता", planet:"Rahu", planetEmoji:"🌑",
       color:"#8b5cf6", luckyNums:"4, 13, 22, 31", luckyColor:"Electric Blue / Grey", luckyColorHex:"#8b5cf6",
       traits:["Disciplined","Hardworking","Systematic","Reliable"],
       traitsHindi:["अनुशासित","मेहनती","व्यवस्थित","विश्वसनीय"],
       desc:"You are the builder — patient, dependable, and devoted to creating lasting structures through hard work and discipline.",
       career:"Engineering, Architecture, Finance, Defense",
       love:"You are a loyal and stable partner who values commitment above all else.",
       strength:"Discipline, Reliability", weakness:"Rigidity, Resistance to change",
       remedy:"Donate blue clothes on Saturdays. Chant the Rahu Beej mantra." },
  5: { title:"Freedom", titleHindi:"स्वतंत्रता", planet:"Budha", planetEmoji:"☿️",
       color:"#10b981", luckyNums:"5, 14, 23", luckyColor:"Green / Light Blue", luckyColorHex:"#10b981",
       traits:["Adventurous","Versatile","Quick-witted","Energetic"],
       traitsHindi:["साहसी","बहुमुखी","तीक्ष्ण","ऊर्जावान"],
       desc:"You are a free spirit — curious, adaptable, and always seeking the next horizon. You thrive on change and new experiences.",
       career:"Journalism, Travel, Sales, Technology, Media",
       love:"You need an adventurous partner who can match your restless energy.",
       strength:"Adaptability, Intelligence", weakness:"Restlessness, Inconsistency",
       remedy:"Worship Lord Ganesha on Wednesdays. Donate green vegetables to the needy." },
  6: { title:"Love & Nurturing", titleHindi:"प्रेम और देखभाल", planet:"Shukra", planetEmoji:"♀️",
       color:"#f43f5e", luckyNums:"6, 15, 24", luckyColor:"Pink / Light Blue", luckyColorHex:"#f43f5e",
       traits:["Loving","Responsible","Artistic","Nurturing"],
       traitsHindi:["प्रेमपूर्ण","जिम्मेदार","कलात्मक","देखभाल करने वाला"],
       desc:"You are a caretaker with a boundless heart. Harmony, family, beauty, and service define your soul's mission in this lifetime.",
       career:"Medicine, Teaching, Art, Interior Design, Social Work",
       love:"You are a devoted, family-first partner with a deeply romantic soul.",
       strength:"Compassion, Responsibility", weakness:"Over-sacrifice, Jealousy",
       remedy:"Worship Goddess Lakshmi on Fridays. Donate sweets and white flowers." },
  7: { title:"Wisdom & Mysticism", titleHindi:"ज्ञान और रहस्य", planet:"Ketu", planetEmoji:"🌠",
       color:"#06b6d4", luckyNums:"7, 16, 25", luckyColor:"Violet / Indigo", luckyColorHex:"#8b5cf6",
       traits:["Analytical","Spiritual","Introspective","Mysterious"],
       traitsHindi:["विश्लेषणात्मक","आध्यात्मिक","अंतर्मुखी","रहस्यमय"],
       desc:"You are the seeker — drawn to hidden truths, deeper knowledge, and the mysteries of the cosmos. Solitude and reflection fuel your wisdom.",
       career:"Research, Philosophy, Science, Spiritual work, Psychology",
       love:"You seek a deep intellectual and spiritual bond with your partner.",
       strength:"Insight, Wisdom", weakness:"Aloofness, Over-analysis",
       remedy:"Worship Lord Shiva on Mondays. Donate black sesame seeds on Saturdays." },
  8: { title:"Power & Abundance", titleHindi:"शक्ति और समृद्धि", planet:"Shani", planetEmoji:"🪐",
       color:"#6366f1", luckyNums:"8, 17, 26", luckyColor:"Dark Blue / Black", luckyColorHex:"#6366f1",
       traits:["Powerful","Ambitious","Strategic","Enduring"],
       traitsHindi:["शक्तिशाली","महत्त्वाकांक्षी","रणनीतिक","धैर्यवान"],
       desc:"You carry Saturn's immense power. Obstacles only make you stronger. Great material success and authority await your perseverance.",
       career:"Business, Banking, Politics, Administration, Law",
       love:"You are an intense, protective partner — loyalty is your non-negotiable.",
       strength:"Determination, Resilience", weakness:"Materialism, Control issues",
       remedy:"Light a mustard-oil lamp on Saturdays. Donate black sesame to Lord Shani." },
  9: { title:"Compassion & Service", titleHindi:"करुणा और सेवा", planet:"Mangal", planetEmoji:"♂️",
       color:"#ef4444", luckyNums:"9, 18, 27", luckyColor:"Red / Crimson", luckyColorHex:"#ef4444",
       traits:["Courageous","Humanitarian","Passionate","Idealistic"],
       traitsHindi:["साहसी","मानवतावादी","जोशीला","आदर्शवादी"],
       desc:"You are the warrior with a golden heart — courageous in battle, compassionate in service. You fight fearlessly for truth and justice.",
       career:"Medicine, Law, Military, Social Service, Spiritual Leadership",
       love:"You love with fierce intensity and devotion. Your partner feels truly protected.",
       strength:"Courage, Generosity", weakness:"Impulsiveness, Short temper",
       remedy:"Worship Lord Hanuman on Tuesdays. Donate red lentils and jaggery." },
  11: { title:"Illumination", titleHindi:"प्रकाश", planet:"Chandra + Surya", planetEmoji:"✨",
        color:"#fbbf24", luckyNums:"11, 29, 2", luckyColor:"Silver / Gold", luckyColorHex:"#fbbf24",
        traits:["Intuitive","Inspirational","Visionary","Highly Sensitive"],
        traitsHindi:["अंतर्ज्ञानी","प्रेरणादायक","दूरदर्शी","संवेदनशील"],
        desc:"You carry the Master Number 11 — a vibration of divine illumination. You are a spiritual messenger born to uplift and inspire all of humanity.",
        career:"Spiritual Leadership, Art, Healing, Counseling, Visionary Work",
        love:"You seek a soul-level connection — deep, spiritual, and transformative.",
        strength:"Intuition, Inspiration", weakness:"Anxiety, Over-idealism",
        remedy:"Meditate at sunrise every day. Chant 'Om Namah Shivaya' 108 times." },
  22: { title:"Master Builder", titleHindi:"महान निर्माता", planet:"Shani + Surya", planetEmoji:"🌍",
        color:"#a78bfa", luckyNums:"22, 4", luckyColor:"Deep Blue / Gold", luckyColorHex:"#a78bfa",
        traits:["Visionary","Disciplined","Powerful","Practical"],
        traitsHindi:["दूरदर्शी","अनुशासित","शक्तिशाली","व्यावहारिक"],
        desc:"You carry Master Number 22 — the most powerful of all numbers. You can bridge the spiritual and material to manifest extraordinary realities.",
        career:"Architecture, Global Business, Politics, Large-scale Philanthropy",
        love:"You are a dedicated, visionary partner building a lasting legacy together.",
        strength:"Vision, Execution", weakness:"Perfectionism, Overwhelm",
        remedy:"Practice deep meditation daily. Donate to orphanages on Saturdays." },
  33: { title:"Master Teacher", titleHindi:"महान गुरु", planet:"Guru + Shukra", planetEmoji:"💫",
        color:"#34d399", luckyNums:"33, 6", luckyColor:"Gold / Pink", luckyColorHex:"#34d399",
        traits:["Selfless","Nurturing","Creative","Enlightened"],
        traitsHindi:["निस्वार्थ","पालन-पोषण करने वाला","रचनात्मक","प्रबुद्ध"],
        desc:"You carry Master Number 33 — the purest vibration of divine love and healing. You are a rare teacher destined to uplift all of humanity.",
        career:"Healing Arts, Spiritual Teaching, Creative Leadership, Service",
        love:"You love unconditionally, serving your partner and family with pure devotion.",
        strength:"Unconditional Love, Wisdom", weakness:"Martyrdom, Self-neglect",
        remedy:"Serve the underprivileged selflessly every week. Light a ghee lamp daily." },
};

const PY_THEME: Record<number, string> = {
  1:"New beginnings — a 9-year cycle begins. Plant the seeds of your dreams.",
  2:"Partnerships and patience. Let relationships deepen and blossom.",
  3:"Creativity, joy, and expression — let your inner light shine brightly.",
  4:"Hard work and foundation-building. Discipline is your greatest asset.",
  5:"Change, freedom, and travel. Embrace the unexpected with open arms.",
  6:"Family, love, and responsibility. Nurture yourself and those around you.",
  7:"Reflection, spirituality, and inner work. Seek deeper truth within.",
  8:"Power, ambition, and finance. Your efforts will finally be rewarded.",
  9:"Completion and release. Close old chapters; a new cycle approaches.",
  11:"Spiritual awakening. Divine guidance is speaking — are you listening?",
  22:"Master year of manifestation. Think big. Build something legendary.",
  33:"Year of deep love and teaching. Serve humanity with your full heart.",
};

function getInfo(n: number): NumInfo {
  return NUM[n] ?? NUM[9];
}

// ── Number badge component ─────────────────────────────────────────────────────
function NumberBadge({ num, color, size = 68 }: { num: number; color: string; size?: number }) {
  return (
    <View style={[nb.wrap, { width: size, height: size, borderRadius: size / 2,
      backgroundColor: `${color}18`, borderColor: `${color}45`, borderWidth: 2 }]}>
      <Text style={[nb.num, { color, fontSize: size * (num > 9 ? 0.30 : 0.40) }]}>{num}</Text>
    </View>
  );
}
const nb = StyleSheet.create({
  wrap: { alignItems:"center", justifyContent:"center", flexShrink:0 },
  num:  { fontWeight:"900" },
});

// ── Free numerology card ───────────────────────────────────────────────────────
function NumCard({
  label, labelHindi, num, expanded, onToggle,
}: { label: string; labelHindi: string; num: number; expanded: boolean; onToggle: () => void }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(num);

  return (
    <Pressable
      onPress={onToggle}
      style={[nc.card, { backgroundColor: C.bgCard, borderColor: `${info.color}35` }]}
    >
      {/* Top row */}
      <View style={nc.topRow}>
        <NumberBadge num={num} color={info.color} />
        <View style={{ flex:1 }}>
          <Text style={[nc.tag, { color: C.textDim }]}>{label}</Text>
          <Text style={[nc.tagHindi, { color: C.textMuted }]}>{labelHindi}</Text>
          <Text style={[nc.titleTxt, { color: info.color }]}>{info.title}</Text>
          <View style={nc.planetRow}>
            <Text style={{ fontSize:12 }}>{info.planetEmoji}</Text>
            <Text style={[nc.planetTxt, { color: C.textMuted }]}>{info.planet}</Text>
          </View>
        </View>
        <Feather name={expanded ? "chevron-up" : "chevron-down"} size={16} color={C.textMuted} />
      </View>

      {/* Traits */}
      <View style={nc.traits}>
        {info.traits.map((t, i) => (
          <View key={t} style={[nc.chip, { backgroundColor:`${info.color}12`, borderColor:`${info.color}28` }]}>
            <Text style={[nc.chipTxt, { color:info.color }]}>{t}</Text>
            <Text style={[nc.chipHindi, { color:info.color }]}> · {info.traitsHindi[i]}</Text>
          </View>
        ))}
      </View>

      {/* Description always visible */}
      <Text style={[nc.desc, { color: C.textMuted }]}>{info.desc}</Text>

      {/* Expanded detail */}
      {expanded && (
        <View style={{ gap:10, marginTop:4 }}>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numCareer}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{info.career}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numLove}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{info.love}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numStrength}</Text>
            <Text style={[nc.detailVal, { color: "#22c55e" }]}>{info.strength}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border }]}>
            <Text style={[nc.detailLabel, { color: C.textDim }]}>{t.numWeakness}</Text>
            <Text style={[nc.detailVal, { color: "#f87171" }]}>{info.weakness}</Text>
          </View>
          <View style={[nc.detailBlock, { borderColor: C.border, backgroundColor:`${info.color}06` }]}>
            <Text style={[nc.detailLabel, { color: info.color }]}>{t.numRemedy}</Text>
            <Text style={[nc.detailVal, { color: C.textMid }]}>{info.remedy}</Text>
          </View>
          <View style={nc.luckyRow}>
            <View style={[nc.luckyPill, { backgroundColor:`${info.color}12` }]}>
              <Text style={[nc.luckyLabel, { color: C.textDim }]}>{t.numLuckyNumbers}</Text>
              <Text style={[nc.luckyVal, { color: info.color }]}>{info.luckyNums}</Text>
            </View>
            <View style={[nc.luckyPill, { backgroundColor:`${info.luckyColorHex}12` }]}>
              <View style={[nc.colorDot, { backgroundColor: info.luckyColorHex }]} />
              <View>
                <Text style={[nc.luckyLabel, { color: C.textDim }]}>{t.numLuckyColor}</Text>
                <Text style={[nc.luckyVal, { color: info.color }]}>{info.luckyColor}</Text>
              </View>
            </View>
          </View>
        </View>
      )}
    </Pressable>
  );
}
const nc = StyleSheet.create({
  card:       { borderRadius:16, borderWidth:1.5, padding:16, gap:10 },
  topRow:     { flexDirection:"row", alignItems:"flex-start", gap:12 },
  tag:        { fontSize:9, fontWeight:"800", letterSpacing:1.8, marginBottom:1 },
  tagHindi:   { fontSize:9, marginBottom:3 },
  titleTxt:   { fontSize:15, fontWeight:"800", marginBottom:2 },
  planetRow:  { flexDirection:"row", alignItems:"center", gap:4 },
  planetTxt:  { fontSize:11 },
  traits:     { flexDirection:"row", flexWrap:"wrap", gap:6 },
  chip:       { flexDirection:"row", paddingHorizontal:8, paddingVertical:4, borderRadius:8, borderWidth:1 },
  chipTxt:    { fontSize:10, fontWeight:"700" },
  chipHindi:  { fontSize:10 },
  desc:       { fontSize:12, lineHeight:19 },
  detailBlock:{ borderTopWidth:1, paddingTop:8, gap:2 },
  detailLabel:{ fontSize:9, fontWeight:"800", letterSpacing:1.2 },
  detailVal:  { fontSize:12, lineHeight:19 },
  luckyRow:   { flexDirection:"row", gap:10 },
  luckyPill:  { flex:1, flexDirection:"row", alignItems:"center", gap:8, padding:10, borderRadius:12 },
  colorDot:   { width:14, height:14, borderRadius:7 },
  luckyLabel: { fontSize:9, fontWeight:"700", letterSpacing:0.8 },
  luckyVal:   { fontSize:12, fontWeight:"700", marginTop:1 },
});

// ── Personal year mini card ───────────────────────────────────────────────────
function PersonalYearCard({ py, pm }: { py: number; pm: number }) {
  const C    = useC();
  const t    = useT();
  const info = getInfo(py);
  const pmInfo = getInfo(pm);
  const year = new Date().getFullYear();
  const month = new Date().toLocaleString("default", { month:"long" });

  return (
    <View style={[pyc.card, { backgroundColor: C.bgCard, borderColor: `${info.color}30` }]}>
      <Text style={[pyc.title, { color: C.textDim }]}>{t.numPersonalYM}</Text>
      <View style={pyc.row}>
        <View style={[pyc.box, { borderColor:`${info.color}30`, backgroundColor:`${info.color}08` }]}>
          <Text style={[pyc.bigNum, { color: info.color }]}>{py}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{t.numYearPrefix} {year}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{PY_THEME[py] ?? ""}</Text>
        </View>
        <View style={[pyc.box, { borderColor:`${pmInfo.color}30`, backgroundColor:`${pmInfo.color}08` }]}>
          <Text style={[pyc.bigNum, { color: pmInfo.color }]}>{pm}</Text>
          <Text style={[pyc.label, { color: C.textMuted }]}>{month}</Text>
          <Text style={[pyc.theme, { color: C.textMuted }]}>{PY_THEME[pm] ?? ""}</Text>
        </View>
      </View>
    </View>
  );
}
const pyc = StyleSheet.create({
  card:   { borderRadius:16, borderWidth:1, padding:16, gap:10 },
  title:  { fontSize:9, fontWeight:"800", letterSpacing:1.8 },
  row:    { flexDirection:"row", gap:10 },
  box:    { flex:1, borderRadius:12, borderWidth:1, padding:12, gap:4, alignItems:"center" },
  bigNum: { fontSize:36, fontWeight:"900" },
  label:  { fontSize:10, fontWeight:"700" },
  theme:  { fontSize:11, lineHeight:16, textAlign:"center" },
});

// ── Locked premium card ───────────────────────────────────────────────────────
function LockedCard({ title, emoji, color }: { title: string; emoji: string; color: string }) {
  const C = useC();
  return (
    <View style={[lk.card, { backgroundColor: C.bgCard, borderColor: `${color}22` }]}>
      <View style={lk.row}>
        <View style={[lk.icon, { backgroundColor:`${color}15` }]}>
          <Text style={{ fontSize:18 }}>{emoji}</Text>
        </View>
        <View style={{ flex:1, gap:6 }}>
          <Text style={[lk.title, { color: C.text }]}>{title}</Text>
          <View style={lk.blurRow}>
            {["●●●●●●","●●●●●●●●","●●●●●"].map((b,i) => (
              <View key={i} style={[lk.blurChip, { backgroundColor:`${color}18` }]}>
                <Text style={{ color:`${color}40`, fontSize:9 }}>{b}</Text>
              </View>
            ))}
          </View>
          <Text style={[lk.preview, { color: C.textDim }]}>••••••••••••••••••••••••••••••••••</Text>
        </View>
        <View style={[lk.lockIcon, { backgroundColor:`${color}12` }]}>
          <Feather name="lock" size={14} color={color} />
        </View>
      </View>
    </View>
  );
}
const lk = StyleSheet.create({
  card:     { borderRadius:14, borderWidth:1, padding:12, opacity:0.75 },
  row:      { flexDirection:"row", alignItems:"flex-start", gap:10 },
  icon:     { width:40, height:40, borderRadius:12, alignItems:"center", justifyContent:"center", flexShrink:0 },
  title:    { fontSize:13, fontWeight:"700" },
  blurRow:  { flexDirection:"row", gap:6 },
  blurChip: { paddingHorizontal:8, paddingVertical:3, borderRadius:8 },
  preview:  { fontSize:10, letterSpacing:1 },
  lockIcon: { width:30, height:30, borderRadius:15, alignItems:"center", justifyContent:"center", flexShrink:0 },
});

// ── Profile selector ──────────────────────────────────────────────────────────
function ProfileSelector({
  profiles, activeId, onSelect,
}: { profiles: ProfileEntry[]; activeId: string | null; onSelect: (id: string) => void }) {
  const C = useC();
  if (profiles.length <= 1) return null;
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginHorizontal:-16 }}
      contentContainerStyle={{ paddingHorizontal:16, gap:8, flexDirection:"row" }}>
      {profiles.map(p => {
        const active = p.id === activeId;
        return (
          <Pressable key={p.id} onPress={() => { onSelect(p.id); Haptics.selectionAsync(); }}
            style={[ps.chip, { borderColor: active ? C.accent : C.border,
              backgroundColor: active ? `${C.accent}12` : C.bgCard2 }]}>
            <Text style={[ps.name, { color: active ? C.accent : C.textMuted }]}>{p.name}</Text>
            {p.relation && <Text style={[ps.rel, { color: C.textDim }]}>{p.relation}</Text>}
          </Pressable>
        );
      })}
    </ScrollView>
  );
}
const ps = StyleSheet.create({
  chip: { paddingHorizontal:12, paddingVertical:7, borderRadius:12, borderWidth:1.5, gap:1 },
  name: { fontSize:12, fontWeight:"700" },
  rel:  { fontSize:9 },
});

// ── PRO Report Panel ──────────────────────────────────────────────────────────
function ProReportPanel({ profile }: { profile: ProfileEntry }) {
  const C = useC();
  const [opening, setOpening] = useState(false);

  const bd = profile.birthData;

  const openPdf = async () => {
    if (!bd) return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setOpening(true);
    try {
      const dob =
        `${bd.year}-${String(bd.month).padStart(2, "0")}-${String(bd.day).padStart(2, "0")}`;
      const tob =
        bd.hour != null && bd.minute != null
          ? `${String(bd.hour).padStart(2, "0")}:${String(bd.minute).padStart(2, "0")}`
          : "12:00";
      const params = new URLSearchParams({
        name: bd.name,
        dob,
        tob,
        gender: (profile.gender || "male").toLowerCase(),
      });
      const url = `${API_BASE}/api/numerology/pdf?${params.toString()}`;
      await Linking.openURL(url);
    } catch (e) {
      // best-effort: silent failure on browser launch
    } finally {
      setOpening(false);
    }
  };

  const sections = [
    { icon: "🎯", title: "Core Numbers",       sub: "Driver, Conductor, Name + planet rulers + compatibility" },
    { icon: "🔢", title: "Lo Shu Grid (3×3)",  sub: "Your magic-square: missing & repeated numbers + meaning" },
    { icon: "🌟", title: "Identity Numbers",   sub: "Life-Path, Soul-Urge, Personality, Expression + Master + Karmic" },
    { icon: "📜", title: "Cheiro Compound",    sub: "Classical occult meaning of your DOB + Name compound" },
    { icon: "📅", title: "Personal Cycles",    sub: "Personal Year, Month, Day with themes (live timing)" },
    { icon: "⛰️", title: "Pinnacles & Challenges", sub: "Life's 4 phases — energies + karmic lessons" },
    { icon: "💼", title: "Career & Lucky",     sub: "Suitable fields + lucky colors, gems, day, mantra, ishta" },
  ];

  return (
    <View style={{ gap: 12 }}>
      {/* Hero card */}
      <View style={[pp.hero, { backgroundColor: C.bgCard, borderColor: "rgba(245,158,11,0.35)" }]}>
        <View style={pp.heroRow}>
          <View style={[pp.heroIcon, { backgroundColor: "rgba(245,158,11,0.15)" }]}>
            <Text style={{ fontSize: 28 }}>📄</Text>
          </View>
          <View style={{ flex: 1 }}>
            <View style={pp.tagRow}>
              <View style={[pp.tag, { backgroundColor: "#f59e0b" }]}>
                <Text style={pp.tagTxt}>PRO REPORT</Text>
              </View>
              <View style={[pp.tag, { backgroundColor: "rgba(34,197,94,0.18)" }]}>
                <Text style={[pp.tagTxt, { color: "#16a34a" }]}>FREE</Text>
              </View>
            </View>
            <Text style={[pp.heroTitle, { color: C.text }]}>
              Numerology PRO PDF
            </Text>
            <Text style={[pp.heroSub, { color: C.textMuted }]}>
              8-page detailed report — instant download
            </Text>
          </View>
        </View>
      </View>

      {/* What's inside */}
      <Text style={[pp.sectionLabel, { color: C.textDim }]}>WHAT'S INSIDE</Text>
      {sections.map((sec, i) => (
        <View key={i} style={[pp.row, { backgroundColor: C.bgCard, borderColor: C.border }]}>
          <Text style={{ fontSize: 22 }}>{sec.icon}</Text>
          <View style={{ flex: 1 }}>
            <Text style={[pp.rowTitle, { color: C.text }]}>{sec.title}</Text>
            <Text style={[pp.rowSub, { color: C.textMuted }]}>{sec.sub}</Text>
          </View>
          <Feather name="check" size={16} color="#22c55e" />
        </View>
      ))}

      {/* Generate button */}
      <Pressable
        onPress={openPdf}
        disabled={opening}
        style={[pp.cta, opening && { opacity: 0.6 }]}
      >
        <View style={pp.ctaInner}>
          <Feather name={opening ? "loader" : "download"} size={18} color="#fff" />
          <Text style={pp.ctaTxt}>{opening ? "Opening report…" : "Generate PRO Report"}</Text>
        </View>
      </Pressable>

      {/* Foot note */}
      <View style={[pp.note, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Feather name="info" size={12} color={C.textMuted} />
        <Text style={[pp.noteTxt, { color: C.textMuted }]}>
          Report opens in your browser. PDF can be saved or shared from there.
          All numbers are deterministic — recomputable any time.
        </Text>
      </View>
    </View>
  );
}
const pp = StyleSheet.create({
  hero:        { borderRadius: 16, borderWidth: 1.5, padding: 16 },
  heroRow:     { flexDirection: "row", alignItems: "center", gap: 14 },
  heroIcon:    { width: 56, height: 56, borderRadius: 16, alignItems: "center", justifyContent: "center" },
  tagRow:      { flexDirection: "row", gap: 6, marginBottom: 4 },
  tag:         { paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 },
  tagTxt:      { fontSize: 9, fontWeight: "900", color: "#fff", letterSpacing: 1 },
  heroTitle:   { fontSize: 16, fontWeight: "800" },
  heroSub:     { fontSize: 11, marginTop: 2 },
  sectionLabel:{ fontSize: 9, fontWeight: "800", letterSpacing: 2, marginTop: 4, marginBottom: -4 },
  row:         { flexDirection: "row", alignItems: "center", gap: 12, padding: 12, borderRadius: 12, borderWidth: 1 },
  rowTitle:    { fontSize: 13, fontWeight: "800" },
  rowSub:      { fontSize: 11, marginTop: 1, lineHeight: 15 },
  cta:         {
                 borderRadius: 16, overflow: "hidden", backgroundColor: "#f59e0b",
                 shadowColor: "#f59e0b", shadowOffset: { width: 0, height: 6 },
                 shadowOpacity: 0.4, shadowRadius: 12, elevation: 10,
               },
  ctaInner:    { flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 10, padding: 16 },
  ctaTxt:      { color: "#fff", fontSize: 15, fontWeight: "900" },
  note:        { borderRadius: 12, borderWidth: 1, padding: 12, flexDirection: "row", alignItems: "flex-start", gap: 8 },
  noteTxt:     { fontSize: 11, lineHeight: 16, flex: 1 },
});

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function NumerologyScreen() {
  const C       = useC();
  const t       = useT();
  const insets  = useSafeAreaInsets();
  const { profiles, primaryProfileId, setPrimaryProfile } = useUser();
  const topPad  = Platform.OS === "web" ? 67 : insets.top;
  const botPad  = Platform.OS === "web" ? 34 : insets.bottom;

  // Local selected profile (for this screen; defaults to primary)
  const [selectedId, setSelectedId] = useState<string | null>(primaryProfileId);
  useEffect(() => { setSelectedId(primaryProfileId); }, [primaryProfileId]);

  const profile = profiles.find(p => p.id === selectedId) ?? profiles[0] ?? null;
  const bd      = profile?.birthData ?? null;

  // Expanded cards
  const [expLP,   setExpLP]   = useState(true);
  const [expDest, setExpDest] = useState(false);
  const [expSoul, setExpSoul] = useState(false);

  // Pattern A — Free / PRO Report tab
  const [tab, setTab] = useState<"free" | "pro">("free");

  // All calculations — instant, no API call
  const nums = useMemo(() => {
    if (!bd) return null;
    const lp   = calcLifePath(bd.day, bd.month, bd.year);
    const dest = calcDestiny(bd.name);
    const soul = calcSoulUrge(bd.name);
    const pers = calcPersonality(bd.name);
    const mat  = calcMaturity(lp, dest);
    const py   = calcPersonalYear(bd.day, bd.month);
    const pm   = calcPersonalMonth(bd.day, bd.month);
    return { lp, dest, soul, pers, mat, py, pm };
  }, [bd]);

  // Format DOB for display
  const dobStr = bd
    ? `${String(bd.day).padStart(2,"0")} / ${String(bd.month).padStart(2,"0")} / ${bd.year}`
    : null;

  const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
  const dobFull = bd
    ? `${bd.day} ${MONTHS[bd.month - 1]} ${bd.year}`
    : null;

  return (
    <View style={[s.root, { backgroundColor: C.bg }]}>
      {/* Header */}
      <View style={[s.header, { paddingTop: topPad + 8, borderBottomColor: C.border }]}>
        <Pressable onPress={() => router.back()} style={s.back}>
          <Feather name="arrow-left" size={20} color={C.textMuted} />
        </Pressable>
        <View style={{ flex:1 }}>
          <Text style={[s.title, { color: C.text }]}>{t.numerologyTitle}</Text>
          <Text style={[s.sub, { color: C.textMuted }]}>{t.numSubtitle}</Text>
        </View>
        <View style={[s.badge, { backgroundColor: `${C.accent}15` }]}>
          <Text style={[s.badgeTxt, { color: C.accent }]}>{t.numFreeBadge}</Text>
        </View>
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={[s.content, { paddingBottom: botPad + 40 }]}
      >
        {/* Profile selector */}
        {profiles.length > 1 && (
          <View style={{ gap:6 }}>
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numSelectProfile}</Text>
            <ProfileSelector
              profiles={profiles} activeId={selectedId}
              onSelect={(id) => setSelectedId(id)}
            />
          </View>
        )}

        {/* No profile state */}
        {!bd && (
          <View style={[s.emptyCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <Text style={{ fontSize:40 }}>🔢</Text>
            <Text style={[s.emptyTitle, { color: C.text }]}>{t.numNoProfileTitle}</Text>
            <Text style={[s.emptyBody, { color: C.textMuted }]}>
              {t.numNoProfileBody}
            </Text>
            <Pressable
              onPress={() => router.push("/profile-edit" as any)}
              style={[s.emptyBtn, { backgroundColor: C.accent }]}
            >
              <Text style={s.emptyBtnTxt}>{t.numSetupProfile}</Text>
            </Pressable>
          </View>
        )}

        {/* Profile info card */}
        {bd && (
          <View style={[s.profileCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
            <View style={s.profileRow}>
              <View style={[s.avatar, { backgroundColor:`${C.accent}15`, borderColor:`${C.accent}30` }]}>
                <Text style={{ fontSize:20 }}>👤</Text>
              </View>
              <View style={{ flex:1 }}>
                <Text style={[s.profileName, { color: C.text }]}>{bd.name}</Text>
                <Text style={[s.profileDob, { color: C.textMuted }]}>🎂 {dobFull}</Text>
                {bd.place && <Text style={[s.profilePlace, { color: C.textDim }]}>📍 {bd.place}</Text>}
              </View>
              <View style={[s.syncBadge, { backgroundColor:`${C.accent}10` }]}>
                <Feather name="check-circle" size={11} color={C.accent} />
                <Text style={[s.syncTxt, { color: C.accent }]}>{t.numAutoSynced}</Text>
              </View>
            </View>
          </View>
        )}

        {/* Pattern A — Segmented tab toggle (Free | PRO Report) */}
        {bd && (
          <View style={[s.tabBar, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Pressable
              onPress={() => { setTab("free"); Haptics.selectionAsync(); }}
              style={[
                s.tabBtn,
                tab === "free" && { backgroundColor: C.accent },
              ]}
            >
              <Feather name="hash" size={13} color={tab === "free" ? "#fff" : C.textMuted} />
              <Text style={[
                s.tabTxt,
                { color: tab === "free" ? "#fff" : C.textMuted },
              ]}>
                Free Numerology
              </Text>
            </Pressable>
            <Pressable
              onPress={() => { setTab("pro"); Haptics.selectionAsync(); }}
              style={[
                s.tabBtn,
                tab === "pro" && { backgroundColor: "#f59e0b" },
              ]}
            >
              <Feather name="file-text" size={13} color={tab === "pro" ? "#fff" : C.textMuted} />
              <Text style={[
                s.tabTxt,
                { color: tab === "pro" ? "#fff" : C.textMuted },
              ]}>
                PRO Report
              </Text>
            </Pressable>
          </View>
        )}

        {/* PRO Report tab */}
        {bd && tab === "pro" && (
          <ProReportPanel profile={profile!} />
        )}

        {/* Free section */}
        {nums && tab === "free" && (
          <>
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numFreeSection}</Text>
            <Text style={[s.sectionSub, { color: C.textMuted }]}>{t.numTapHint}</Text>

            <NumCard
              label={t.numLifePathLbl} labelHindi={t.numLifePathHi}
              num={nums.lp} expanded={expLP}
              onToggle={() => { setExpLP(v => !v); Haptics.selectionAsync(); }}
            />
            <NumCard
              label={t.numDestinyLbl} labelHindi={t.numDestinyHi}
              num={nums.dest} expanded={expDest}
              onToggle={() => { setExpDest(v => !v); Haptics.selectionAsync(); }}
            />
            <NumCard
              label={t.numSoulUrgeLbl} labelHindi={t.numSoulUrgeHi}
              num={nums.soul} expanded={expSoul}
              onToggle={() => { setExpSoul(v => !v); Haptics.selectionAsync(); }}
            />

            {/* Personal Year / Month */}
            <PersonalYearCard py={nums.py} pm={nums.pm} />

            {/* Divider + Advanced teaser */}
            <View style={[s.divider, { borderColor: C.border }]}>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
              <View style={[s.divBadge, { backgroundColor: C.bgCard, borderColor: C.border }]}>
                <Feather name="lock" size={10} color={C.isDark ? "#f59e0b" : "#92400E"} />
                <Text style={[s.divTxt, { color: C.isDark ? "#f59e0b" : "#92400E" }]}>{t.numPremiumDivider}</Text>
              </View>
              <View style={[s.divLine, { backgroundColor: C.border }]} />
            </View>

            {/* Teaser blurb */}
            <View style={[s.teaserCard, { backgroundColor: C.bgCard, borderColor:"rgba(245,158,11,0.25)" }]}>
              <Text style={{ fontSize:32 }}>🔐</Text>
              <View style={{ flex:1, gap:4 }}>
                <Text style={[s.teaserTitle, { color: C.text }]}>{t.numUnlockTitle}</Text>
                <Text style={[s.teaserBody, { color: C.textMuted }]}>
                  {t.numUnlockBody}
                </Text>
              </View>
            </View>

            {/* Locked cards preview */}
            <Text style={[s.sectionLabel, { color: C.textDim }]}>{t.numAdvancedSection}</Text>

            <LockedCard title={t.numLockPersonality} emoji="🎭" color="#8b5cf6" />
            <LockedCard title={t.numLockMaturity} emoji="🌱" color="#10b981" />
            <LockedCard title={t.numLockCareerFin} emoji="💼" color="#f59e0b" />
            <LockedCard title={t.numLockLoveCompat} emoji="❤️" color="#f43f5e" />
            <LockedCard title={t.numLockNameCorr} emoji="✍️" color="#06b6d4" />
            <LockedCard title={t.numLockChallenges} emoji="🙏" color="#f97316" />

            {/* CTA */}
            <Pressable
              onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/subscription" as any); }}
              style={s.ctaBtn}
            >
              <View style={s.ctaInner}>
                <Text style={{ fontSize:22 }}>⭐</Text>
                <View style={{ flex:1 }}>
                  <Text style={s.ctaTitle}>{t.numCtaTitle}</Text>
                  <Text style={s.ctaSub}>{t.numCtaSub}</Text>
                </View>
                <Feather name="arrow-right" size={18} color="#fff" />
              </View>
            </Pressable>

            {/* Info footer */}
            <View style={[s.footer, { backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Feather name="info" size={12} color={C.textMuted} />
              <Text style={[s.footerTxt, { color: C.textMuted }]}>
                {t.numFooterNote}
              </Text>
            </View>
          </>
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  root:        { flex:1 },
  header:      { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:14, borderBottomWidth:1 },
  back:        { width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:       { fontSize:17, fontWeight:"800" },
  sub:         { fontSize:10, marginTop:1 },
  badge:       { paddingHorizontal:8, paddingVertical:3, borderRadius:8 },
  badgeTxt:    { fontSize:9, fontWeight:"800", letterSpacing:1 },
  content:     { paddingHorizontal:16, gap:12, paddingTop:14 },
  sectionLabel:{ fontSize:9, fontWeight:"800", letterSpacing:2, marginBottom:-4 },
  sectionSub:  { fontSize:11, marginTop:-8 },

  emptyCard:   { borderRadius:18, borderWidth:1, padding:24, alignItems:"center", gap:14 },
  emptyTitle:  { fontSize:16, fontWeight:"800", textAlign:"center" },
  emptyBody:   { fontSize:13, lineHeight:20, textAlign:"center" },
  emptyBtn:    { paddingHorizontal:24, paddingVertical:12, borderRadius:14 },
  emptyBtnTxt: { color:"#fff", fontSize:14, fontWeight:"800" },

  profileCard: { borderRadius:14, borderWidth:1, padding:14 },
  profileRow:  { flexDirection:"row", alignItems:"center", gap:12 },
  avatar:      { width:48, height:48, borderRadius:16, borderWidth:1.5, alignItems:"center", justifyContent:"center", flexShrink:0 },
  profileName: { fontSize:15, fontWeight:"800" },
  profileDob:  { fontSize:12, marginTop:2 },
  profilePlace:{ fontSize:11, marginTop:1 },
  syncBadge:   { flexDirection:"row", alignItems:"center", gap:4, paddingHorizontal:7, paddingVertical:3, borderRadius:8 },
  syncTxt:     { fontSize:9, fontWeight:"700" },

  divider:     { flexDirection:"row", alignItems:"center", gap:10, borderTopWidth:0 },
  divLine:     { flex:1, height:1 },
  divBadge:    { flexDirection:"row", alignItems:"center", gap:5, paddingHorizontal:10, paddingVertical:4, borderRadius:12, borderWidth:1 },
  divTxt:      { fontSize:9, fontWeight:"800", letterSpacing:1 },

  teaserCard:  { borderRadius:16, borderWidth:1, padding:16, flexDirection:"row", alignItems:"flex-start", gap:12 },
  teaserTitle: { fontSize:14, fontWeight:"800" },
  teaserBody:  { fontSize:12, lineHeight:18 },

  ctaBtn: {
    borderRadius:18, overflow:"hidden",
    backgroundColor:"#f59e0b",
    shadowColor:"#f59e0b", shadowOffset:{ width:0, height:6 },
    shadowOpacity:0.4, shadowRadius:12, elevation:10,
  },
  ctaInner:  { flexDirection:"row", alignItems:"center", gap:12, padding:18 },
  ctaTitle:  { color:"#fff", fontSize:15, fontWeight:"900" },
  ctaSub:    { color:"rgba(255,255,255,0.8)", fontSize:11, marginTop:2 },

  footer:    { borderRadius:12, borderWidth:1, padding:12, flexDirection:"row", alignItems:"flex-start", gap:8 },
  footerTxt: { fontSize:11, lineHeight:17, flex:1 },

  tabBar:    { flexDirection:"row", padding:4, borderRadius:14, borderWidth:1, gap:4 },
  tabBtn:    { flex:1, flexDirection:"row", alignItems:"center", justifyContent:"center",
               gap:6, paddingVertical:10, borderRadius:10 },
  tabTxt:    { fontSize:12, fontWeight:"800", letterSpacing:0.3 },
});
