import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useEffect, useMemo, useState } from "react";
import {
  Modal, Platform, Pressable, ScrollView,
  StatusBar, StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { useT } from "@/hooks/useT";
import { vedicLang, NAKSHATRA, RASHI, RASHI_KEYS, pick, type VLang } from "@/lib/i18nVedic";
import { getMonthsShort, getTaraData, getKarakaDefs } from "@/lib/i18nContent";
import { pName } from "@/lib/proInsightEngine";
import type { KundliData, PlanetInfo } from "@/types";

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";
import { fetchKundliFromAPI } from "@/lib/kundliAPI";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

// Module-level fallback (English short months); per-language months come from getMonthsShort(lang).
const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];
const NAK_LORDS = [
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
  "Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury",
];
const DASHA_SEQ = ["Ketu","Venus","Sun","Moon","Mars","Rahu","Jupiter","Saturn","Mercury"];
const DASHA_YRS: Record<string,number> = {
  Ketu:7, Venus:20, Sun:6, Moon:10, Mars:7, Rahu:18, Jupiter:16, Saturn:19, Mercury:17,
};
const RASHIS_HI = [
  "Mesh","Vrishabh","Mithun","Kark","Simha","Kanya",
  "Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen",
];
const PLANET_HUE: Record<string,string> = {
  Sun:"#f59e0b", Moon:"#94a3b8", Mars:"#ef4444", Mercury:"#10b981",
  Jupiter:"#facc15", Venus:"#ec4899", Saturn:"#a78bfa",
  Rahu:"#f59e0b", Ketu:"#fb923c",
};
const hue = (p: string) => PLANET_HUE[p] ?? "#f59e0b";
const oa = (isDark: boolean, hexAlpha: string): string => {
  if (isDark) return hexAlpha;
  const n = parseInt(hexAlpha, 16);
  return Math.min(255, Math.round(n * 2.2)).toString(16).padStart(2, '0');
};

// ── i18n labels (full 25-lang via i18n) ─────────────────────────────────────────
function getKundliLabels(t: ReturnType<typeof useT>) {
  return {
    mahadasha:        t.ku_mahadasha,
    antardasha:       t.ku_antardasha,
    pratyantardasha:  t.ku_pratyantardasha,
    mahaTimeline:     t.ku_mahaTimeline,
    activeNow:        t.ku_activeNow,
    active:           t.ku_active,
    yearsSuffix:      t.ku_yearsSuffix,
    whatNavatara:     t.ku_whatNavatara,
    navataraDesc:     t.ku_navataraDesc,
    chandraNakBase:   t.ku_chandraNakBase,
    whatJaimini:      t.ku_whatJaimini,
    jaiminiDesc:      t.ku_jaiminiDesc,
    atmakaraka:       t.ku_atmakaraka,
    jaiminiLagna:     t.ku_jaiminiLagna,
    jaiminiLagnaDesc: t.ku_jaiminiLagnaDesc,
    liveChandraTransit: t.ku_liveChandraTransit,
    natalConj:        t.ku_natalConj,
    whatKP:           t.ku_whatKP,
    kpSignificators:  t.ku_kpSignificators,
    birthChartSnap:   t.ku_birthChartSnap,
    planetPosition:   t.ku_planetPosition,
    planetPositionSub: t.ku_planetPositionSub,
    dailyAlerts:      t.ku_dailyAlertsLink,
    dailyAlertsSub:   t.ku_dailyAlertsLinkSub,
    house:            t.ku_house,
    nakshatraLabel:   t.ku_nakshatraLabel,
    btnKundli:        t.ku_btnKundli,
    btnAshtak:        t.ku_btnAshtak,
    btnNavatara:      t.ku_btnNavatara,
    btnJaimini:       t.ku_btnJaimini,
    btnTransit:       t.ku_btnTransit,
    btnKP:            t.ku_btnKP,
    secDashaTimeline:    t.ku_secDashaTimeline,
    secAshtakavarga:     t.ku_secAshtakavarga,
    secNavatara9Tara:    t.ku_secNavatara9Tara,
    secJaiminiKarakas:   t.ku_secJaiminiKarakas,
    secGrahaTransit:     t.ku_secGrahaTransit,
    secKpPaddhati:       t.ku_secKpPaddhati,
    snapAscendant:       t.ku_snapAscendant,
    snapMoonSign:        t.ku_snapMoonSign,
    snapNakshatra:       t.ku_snapNakshatra,
    snapNakshatraLord:   t.ku_snapNakshatraLord,
    snapDashaBalance:    t.ku_snapDashaBalance,
    snapLiveMoonTransit: t.ku_snapLiveMoonTransit,
    snapLiveJupiterTransit: t.ku_snapLiveJupiterTransit ?? "LIVE JUPITER TRANSIT",
    snapLiveSaturnTransit:  t.ku_snapLiveSaturnTransit  ?? "LIVE SANI TRANSIT",
    padaLabel:           t.ku_padaLabel,
    jaiminiDegPre:       t.ku_jaiminiDegPre,
    jaiminiDegSuf:       t.ku_jaiminiDegSuf,
    kpDesc:              t.ku_kpDesc,
    kpFooter:            t.ku_kpFooter,
    kpStar:              t.ku_kpStar,
    kpSub:               t.ku_kpSub,
    kpSubSub:            t.ku_kpSubSub,
    kpAsc:               t.ku_kpAsc,
    savHeading:          t.ku_savHeading,
  };
}

function formatDate(d: Date | string, lang?: string) {
  const dt = new Date(d);
  const months = lang ? getMonthsShort(lang) : MONTHS;
  return `${dt.getDate()} ${months[dt.getMonth()]} ${dt.getFullYear()}`;
}
const tsOf = (d: Date | string) => +new Date(d);
const isNow = (s: Date | string, e: Date | string) => { const n=Date.now(); return tsOf(s)<=n&&n<tsOf(e); };
function progress(s: Date | string, e: Date | string) {
  const n=Date.now(), sv=tsOf(s), ev=tsOf(e);
  if(n<=sv) return 0; if(n>=ev) return 100;
  return Math.round(((n-sv)/(ev-sv))*100);
}

function calcPratyantar(antar: any): any[] {
  if (antar.subDashas?.length > 0) return antar.subDashas;
  const si = DASHA_SEQ.indexOf(antar.planet);
  const out: any[] = [];
  let cur = new Date(tsOf(antar.startDate));
  for (let j=0; j<9; j++) {
    const planet = DASHA_SEQ[(si+j)%9];
    const yrs    = (DASHA_YRS[planet]/120) * antar.years;
    const end    = new Date(cur.getTime() + yrs*365.25*86400*1000);
    out.push({ planet, startDate:new Date(cur), endDate:end, years:yrs });
    cur = end;
  }
  return out;
}

function SectionHeader({ title, icon, C }: { title: string; icon?: string; C: any }) {
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v: string) => oa(C.isDark, v);
  return (
    <View style={{ flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 2 }}>
      {icon && (
        <View style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: `${ac}${o("12")}`, alignItems: "center", justifyContent: "center" }}>
          <Feather name={icon as any} size={13} color={ac} />
        </View>
      )}
      <Text style={{ color: ac, fontSize: 12, fontFamily: F.bold, letterSpacing: 2, flex: 1 }}>{title}</Text>
      <View style={{ flex: 1, height: 1, backgroundColor: `${ac}${o("20")}`, marginLeft: 8 }} />
    </View>
  );
}

function ProgBar({ pct, color }: { pct:number; color:string }) {
  const C = useC();
  return (
    <View style={{ height: 6, borderRadius: 3, backgroundColor: C.bgCard2, overflow: "hidden" }}>
      <View style={{ height: "100%", borderRadius: 3, width: `${pct}%` as any, backgroundColor: color }} />
    </View>
  );
}

type Level = "Mahadasha"|"Antardasha"|"Pratyantardasha";

function NavArrow({ dir, enabled, onPress, C }: { dir: "left"|"right"; enabled: boolean; onPress: ()=>void; C: any }) {
  return (
    <Pressable
      onPress={() => { if (enabled) { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); onPress(); } }}
      style={{ width: 32, height: 32, borderRadius: 10, backgroundColor: C.bgCard2, borderWidth: 1, borderColor: C.border, alignItems: "center", justifyContent: "center", opacity: enabled ? 1 : 0.25 }}>
      <Feather name={dir === "left" ? "chevron-left" : "chevron-right"} size={14} color={C.text} />
    </Pressable>
  );
}

function MahadashaCard({ planet, startDate, endDate, active, onPrev, onNext, hasPrev, hasNext }: {
  planet:string; startDate:any; endDate:any; active:boolean;
  onPrev:()=>void; onNext:()=>void; hasPrev:boolean; hasNext:boolean;
}) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const color = hue(planet);
  const pct = progress(startDate, endDate);
  const yrs = ((tsOf(endDate) - tsOf(startDate)) / (365.25 * 86400 * 1000)).toFixed(0);
  const o = (vv: string) => oa(C.isDark, vv);
  return (
    <View style={{
      borderRadius: 18, borderWidth: 1.5, overflow: "hidden",
      backgroundColor: active ? `${color}${o("08")}` : C.bgCard,
      borderColor: active ? `${color}${o("50")}` : C.border,
      boxShadow: active ? `0 6px 24px ${color}${o("20")}` : C.cardShadow,
    } as any}>
      <View style={{ backgroundColor: `${color}${o("12")}`, paddingVertical: 9, paddingHorizontal: 16, flexDirection: "row", alignItems: "center", justifyContent: "space-between", borderBottomWidth: 1, borderBottomColor: `${color}${o("18")}` }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
          <Feather name="sun" size={13} color={color} />
          <Text style={{ color, fontSize: 11, fontFamily: F.bold, letterSpacing: 1.5 }}>{L.mahadasha}</Text>
        </View>
        <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.bold }}>{yrs} {L.yearsSuffix}</Text>
      </View>
      <View style={{ borderLeftWidth: 4, borderLeftColor: color, padding: 18, gap: 10 }}>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <NavArrow dir="left" enabled={hasPrev} onPress={onPrev} C={C} />
          <View style={{ alignItems: "center", flex: 1, gap: 4 }}>
            <View style={{ width: 52, height: 52, borderRadius: 16, backgroundColor: `${color}${o("15")}`, alignItems: "center", justifyContent: "center", borderWidth: 1.5, borderColor: `${color}${o("35")}` }}>
              <Text style={{ color, fontSize: 20, fontFamily: F.bold }}>{planet.slice(0, 2)}</Text>
            </View>
            <Text style={{ color: C.text, fontSize: 22, fontFamily: F.bold }}>{pName(planet)}</Text>
            <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.semibold }}>{formatDate(startDate, language)} – {formatDate(endDate, language)}</Text>
            {active && (
              <View style={{ backgroundColor: `${color}${o("18")}`, paddingVertical: 3, paddingHorizontal: 14, borderRadius: 20, borderWidth: 1, borderColor: `${color}${o("35")}`, marginTop: 2 }}>
                <Text style={{ color, fontSize: 10, fontFamily: F.bold, letterSpacing: 1 }}>{L.activeNow}</Text>
              </View>
            )}
          </View>
          <NavArrow dir="right" enabled={hasNext} onPress={onNext} C={C} />
        </View>
        {pct > 0 && (
          <View style={{ gap: 5, marginTop: 4 }}>
            <ProgBar pct={pct} color={color} />
            <View style={{ flexDirection: "row", justifyContent: "space-between", alignItems: "center" }}>
              <Text style={{ color: C.textDim, fontSize: 10, fontFamily: F.semibold }}>{formatDate(startDate, language)}</Text>
              <View style={{ backgroundColor: `${color}${o("15")}`, paddingHorizontal: 10, paddingVertical: 3, borderRadius: 8 }}>
                <Text style={{ color, fontSize: 12, fontFamily: F.bold }}>{pct}%</Text>
              </View>
              <Text style={{ color: C.textDim, fontSize: 10, fontFamily: F.semibold }}>{formatDate(endDate, language)}</Text>
            </View>
          </View>
        )}
      </View>
    </View>
  );
}

function AntardashaCard({ planet, startDate, endDate, active, onPrev, onNext, hasPrev, hasNext }: {
  planet:string; startDate:any; endDate:any; active:boolean;
  onPrev:()=>void; onNext:()=>void; hasPrev:boolean; hasNext:boolean;
}) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const color = hue(planet);
  const pct = progress(startDate, endDate);
  const o = (vv: string) => oa(C.isDark, vv);
  return (
    <View style={{
      borderRadius: 14, borderWidth: 1, overflow: "hidden",
      backgroundColor: active ? `${color}${o("06")}` : C.bgCard,
      borderColor: active ? `${color}${o("40")}` : C.border,
      marginLeft: 12,
    }}>
      <View style={{ borderLeftWidth: 3, borderLeftColor: color, padding: 14, gap: 8 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 2 }}>
          <Feather name="moon" size={11} color={color} />
          <Text style={{ color, fontSize: 10, fontFamily: F.bold, letterSpacing: 1.2 }}>{L.antardasha}</Text>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <NavArrow dir="left" enabled={hasPrev} onPress={onPrev} C={C} />
          <View style={{ flexDirection: "row", alignItems: "center", gap: 10, flex: 1, marginHorizontal: 10 }}>
            <View style={{ width: 38, height: 38, borderRadius: 11, backgroundColor: `${color}${o("15")}`, alignItems: "center", justifyContent: "center", borderWidth: 1, borderColor: `${color}${o("30")}` }}>
              <Text style={{ color, fontSize: 14, fontFamily: F.bold }}>{planet.slice(0, 2)}</Text>
            </View>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                <Text style={{ color: C.text, fontSize: 16, fontFamily: F.bold }}>{pName(planet)}</Text>
                {active && (
                  <View style={{ backgroundColor: `${color}${o("18")}`, paddingVertical: 2, paddingHorizontal: 8, borderRadius: 10 }}>
                    <Text style={{ color, fontSize: 9, fontFamily: F.bold }}>{L.active}</Text>
                  </View>
                )}
              </View>
              <Text style={{ color: C.textMuted, fontSize: 11, fontFamily: F.semibold, marginTop: 2 }}>{formatDate(startDate, language)} – {formatDate(endDate, language)}</Text>
            </View>
          </View>
          <NavArrow dir="right" enabled={hasNext} onPress={onNext} C={C} />
        </View>
        {pct > 0 && (
          <View style={{ gap: 3, marginTop: 2 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 8 }}>
              <View style={{ flex: 1 }}>
                <ProgBar pct={pct} color={color} />
              </View>
              <Text style={{ color, fontSize: 11, fontFamily: F.bold, minWidth: 30, textAlign: "right" }}>{pct}%</Text>
            </View>
          </View>
        )}
      </View>
    </View>
  );
}

function PratyantarCard({ planet, startDate, endDate, active, onPrev, onNext, hasPrev, hasNext }: {
  planet:string; startDate:any; endDate:any; active:boolean;
  onPrev:()=>void; onNext:()=>void; hasPrev:boolean; hasNext:boolean;
}) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const color = hue(planet);
  const pct = progress(startDate, endDate);
  const o = (vv: string) => oa(C.isDark, vv);
  return (
    <View style={{
      borderRadius: 12, borderWidth: 1, overflow: "hidden",
      backgroundColor: active ? `${color}${o("06")}` : C.bgCard,
      borderColor: active ? `${color}${o("30")}` : C.border,
      marginLeft: 28,
    }}>
      <View style={{ borderLeftWidth: 2, borderLeftColor: color, paddingVertical: 10, paddingHorizontal: 12, gap: 6 }}>
        <View style={{ flexDirection: "row", alignItems: "center", gap: 4, marginBottom: 1 }}>
          <Feather name="star" size={10} color={color} />
          <Text style={{ color, fontSize: 9, fontFamily: F.bold, letterSpacing: 1 }}>{L.pratyantardasha}</Text>
        </View>
        <View style={{ flexDirection: "row", alignItems: "center", justifyContent: "space-between" }}>
          <Pressable
            onPress={() => { if (hasPrev) { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); onPrev(); } }}
            style={{ opacity: hasPrev ? 1 : 0.2, padding: 2 }}>
            <Feather name="chevron-left" size={14} color={C.textMuted} />
          </Pressable>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 8, flex: 1, justifyContent: "center" }}>
            <View style={{ width: 28, height: 28, borderRadius: 8, backgroundColor: `${color}${o("12")}`, alignItems: "center", justifyContent: "center" }}>
              <Text style={{ color, fontSize: 11, fontFamily: F.bold }}>{planet.slice(0, 2)}</Text>
            </View>
            <Text style={{ color: C.text, fontSize: 14, fontFamily: F.bold }}>{pName(planet)}</Text>
            {active && <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: color }} />}
          </View>
          <Pressable
            onPress={() => { if (hasNext) { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); onNext(); } }}
            style={{ opacity: hasNext ? 1 : 0.2, padding: 2 }}>
            <Feather name="chevron-right" size={14} color={C.textMuted} />
          </Pressable>
        </View>
        <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.semibold, textAlign: "center" }}>{formatDate(startDate, language)} – {formatDate(endDate, language)}</Text>
        {pct > 0 && (
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <View style={{ flex: 1 }}>
              <ProgBar pct={pct} color={color} />
            </View>
            <Text style={{ color, fontSize: 10, fontFamily: F.bold }}>{pct}%</Text>
          </View>
        )}
      </View>
    </View>
  );
}

function TimelineStrip({ dashas, selected, onSelect }: { dashas:any[];selected:number;onSelect:(i:number)=>void }) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  return (
    <View style={{ gap: 8 }}>
      <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 }}>{L.mahaTimeline}</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={{ flexDirection: "row", gap: 8, paddingBottom: 4 }}>
          {dashas.map((d,i) => {
            const active=isNow(d.startDate,d.endDate), sel=i===selected, color=hue(d.planet);
            return (
              <Pressable key={i} onPress={() => {Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);onSelect(i);}}
                style={{
                  minWidth: 50, paddingVertical: 10, paddingHorizontal: 10, borderRadius: 14,
                  borderWidth: sel ? 2 : 1.5, alignItems: "center", gap: 3,
                  backgroundColor: sel ? `${color}${oa(C.isDark,"18")}` : C.bgCard,
                  borderColor: sel ? color : C.border,
                }}>
                <Text style={{ color: sel ? color : C.textMuted, fontSize: 13, fontFamily: F.bold }}>{d.planet.slice(0,2)}</Text>
                <Text style={{ color: sel ? color : C.textMid, fontSize: 9, fontFamily: F.semibold }}>{new Date(d.startDate).getFullYear()}</Text>
                {active && <View style={{ width: 6, height: 6, borderRadius: 3, backgroundColor: color }} />}
              </Pressable>
            );
          })}
        </View>
      </ScrollView>
    </View>
  );
}

function DashaTab({ kundli, mahaIdx, setMahaIdx, antarIdx, setAntarIdx, pratIdx, setPratIdx }: {
  kundli:KundliData; mahaIdx:number; setMahaIdx:(i:number)=>void;
  antarIdx:number; setAntarIdx:(i:number)=>void;
  pratIdx:number; setPratIdx:(i:number)=>void;
}) {
  function changeMaha(i:number) {
    setMahaIdx(i);
    const now=Date.now();
    const subs=kundli.dashas[i]?.subDashas??[];
    const ai=subs.findIndex((s2:any)=>tsOf(s2.startDate)<=now&&tsOf(s2.endDate)>now);
    setAntarIdx(ai>=0?ai:0);
  }
  const maha=kundli.dashas[mahaIdx];
  const subDashas=maha?.subDashas??[];
  const antar=subDashas[antarIdx];
  const pratyantars=antar?calcPratyantar(antar):[];
  const pratyantar=pratyantars[pratIdx]??pratyantars[0];
  return (
    <View style={{gap:14}}>
      {maha && <MahadashaCard planet={maha.planet} startDate={maha.startDate} endDate={maha.endDate}
        active={isNow(maha.startDate,maha.endDate)}
        onPrev={()=>changeMaha(mahaIdx-1)} onNext={()=>changeMaha(mahaIdx+1)}
        hasPrev={mahaIdx>0} hasNext={mahaIdx<kundli.dashas.length-1} />}
      {antar && <AntardashaCard planet={antar.planet} startDate={antar.startDate} endDate={antar.endDate}
        active={isNow(antar.startDate,antar.endDate)}
        onPrev={()=>setAntarIdx(antarIdx-1)} onNext={()=>setAntarIdx(antarIdx+1)}
        hasPrev={antarIdx>0} hasNext={antarIdx<subDashas.length-1} />}
      {pratyantar && <PratyantarCard planet={pratyantar.planet} startDate={pratyantar.startDate} endDate={pratyantar.endDate}
        active={isNow(pratyantar.startDate,pratyantar.endDate)}
        onPrev={()=>setPratIdx(pratIdx-1)} onNext={()=>setPratIdx(pratIdx+1)}
        hasPrev={pratIdx>0} hasNext={pratIdx<pratyantars.length-1} />}
      <TimelineStrip dashas={kundli.dashas} selected={mahaIdx} onSelect={changeMaha} />
    </View>
  );
}

const BAV: Record<string,Record<string,number[]>> = {
  Sun: {
    Sun:[1,2,4,7,8,9,10,11], Moon:[3,6,10,11], Mars:[1,2,4,7,8,9,10,11],
    Mercury:[3,5,6,9,10,11,12], Jupiter:[5,6,9,11], Venus:[6,7,12],
    Saturn:[1,2,4,7,8,9,10,11], Asc:[1,2,4,7,8,9,10,11],
  },
  Moon: {
    Sun:[3,6,7,8,10,11], Moon:[1,3,6,7,10,11], Mars:[2,3,5,6,9,10,11],
    Mercury:[1,3,4,5,7,8,10,11], Jupiter:[1,4,7,8,10,11,12], Venus:[3,4,5,7,9,10,11],
    Saturn:[3,5,6,11], Asc:[3,6,10,11],
  },
  Mars: {
    Sun:[3,5,6,10,11], Moon:[3,6,11], Mars:[1,2,4,7,8,10,11],
    Mercury:[3,5,6,11], Jupiter:[6,10,11,12], Venus:[6,8,11,12],
    Saturn:[1,4,7,8,9,10,11], Asc:[1,2,4,7,8,10,11],
  },
  Mercury: {
    Sun:[5,6,9,11,12], Moon:[2,4,6,8,10,11], Mars:[1,2,4,7,8,9,10,11],
    Mercury:[1,3,5,6,9,10,11,12], Jupiter:[6,8,11,12], Venus:[1,2,3,4,5,8,9,11],
    Saturn:[1,2,4,7,8,9,10,11], Asc:[1,2,4,6,8,10,11],
  },
  Jupiter: {
    Sun:[1,2,3,4,7,8,9,10,11], Moon:[2,5,7,9,11], Mars:[1,2,4,7,8,10,11],
    Mercury:[1,2,4,5,6,9,10,11], Jupiter:[1,2,3,4,7,8,10,11], Venus:[2,5,6,9,10,11],
    Saturn:[3,5,6,12], Asc:[1,2,4,7,8,10,11],
  },
  Venus: {
    Sun:[8,11,12], Moon:[1,2,3,4,5,8,9,11,12], Mars:[3,4,6,9,11,12],
    Mercury:[3,5,6,9,11], Jupiter:[5,8,9,10,11], Venus:[1,2,3,4,5,8,9,10,11],
    Saturn:[3,4,5,8,9,10,11], Asc:[1,2,3,4,5,8,9,11],
  },
  Saturn: {
    Sun:[1,2,4,7,8,10,11], Moon:[3,6,11], Mars:[3,5,6,10,11,12],
    Mercury:[6,8,9,10,11,12], Jupiter:[5,6,11,12], Venus:[6,11,12],
    Saturn:[3,5,6,11], Asc:[1,3,4,6,10,11],
  },
};

function computeBAV(kundli: KundliData) {
  const ascRashi = Math.floor((kundli.ascendantDeg ?? 0) / 30) % 12;
  const getR = (name:string) => {
    if (name === "Asc") return ascRashi;
    const p = kundli.planets.find(pl => pl.name === name);
    if (!p) return -1;
    return Math.floor(p.longitude / 30) % 12;
  };
  const SAV = Array(12).fill(0);
  const BAVS: Record<string, number[]> = {};
  const PLANETS = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  for (const planet of PLANETS) {
    const sigs = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Asc"];
    const bav = Array(12).fill(0);
    for (const sig of sigs) {
      const sR = getR(sig);
      if (sR < 0) continue;
      const positions = BAV[planet]?.[sig] ?? [];
      for (const pos of positions) {
        const targetR = (sR + pos - 1) % 12;
        bav[targetR] += 1;
      }
    }
    BAVS[planet] = bav;
    for (let r=0; r<12; r++) SAV[r] += bav[r];
  }
  return { BAVS, SAV };
}

function AshtakavargaTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const t = useT();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v2: string) => oa(C.isDark, v2);
  const { BAVS, SAV } = useMemo(() => computeBAV(kundli), [kundli]);
  const [selPlanet, setSelPlanet] = useState("SAV");
  const PLANETS = ["SAV","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  const scores = selPlanet === "SAV" ? SAV : (BAVS[selPlanet] ?? Array(12).fill(0));
  const maxScore = selPlanet === "SAV" ? 56 : 8;
  const total = scores.reduce((a:number,b:number)=>a+b,0);

  return (
    <View style={{gap:16}}>
      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.border, backgroundColor: C.bgCard, padding: 0, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: ac, padding: 14, gap: 4 }}>
          <Text style={{ color: ac, fontSize: 14, fontFamily: F.bold }}>
            {t.ku_ashtakWhat}
          </Text>
          <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, lineHeight: 19 }}>
            {t.ku_ashtakWhatBody}
          </Text>
        </View>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={{flexDirection:"row",gap:8}}>
          {PLANETS.map(p => {
            const sel = p===selPlanet;
            const color = p==="SAV" ? ac : hue(p);
            return (
              <Pressable key={p} onPress={()=>{setSelPlanet(p);Haptics.selectionAsync();}}
                style={{
                  paddingVertical: 10, paddingHorizontal: 16, borderRadius: 12, borderWidth: sel ? 2 : 1,
                  backgroundColor: sel ? `${color}${o("18")}` : C.bgCard,
                  borderColor: sel ? `${color}${o("60")}` : C.border,
                }}>
                <Text style={{color:sel?color:C.textMuted, fontSize: 12, fontFamily: F.bold}}>{p==="SAV"?"SAV":p.slice(0,3)}</Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      <View style={{
        flexDirection:"row", alignItems:"center", justifyContent:"space-between",
        backgroundColor: `${ac}${o("10")}`, borderRadius: 10, paddingVertical: 9, paddingHorizontal: 14,
        borderWidth: 1, borderColor: `${ac}${o("20")}`,
      }}>
        <Text style={{color:C.text,fontSize:16,fontFamily:F.bold}}>
          {selPlanet === "SAV" ? t.ku_savHeading : `${selPlanet} BAV`}
        </Text>
        <View style={{ backgroundColor: `${ac}${o("18")}`, paddingVertical: 4, paddingHorizontal: 12, borderRadius: 8 }}>
          <Text style={{color:ac,fontSize:13,fontFamily:F.bold}}>{total}/{selPlanet==="SAV"?336:56}</Text>
        </View>
      </View>

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 8 }}>
        {RASHI_KEYS.map((rk, i) => {
          const rashi = pick(v, RASHI[rk]);
          const score = scores[i] ?? 0;
          const pct   = score / maxScore;
          const color = pct >= 0.7 ? "#22c55e" : pct >= 0.5 ? "#fbbf24" : pct >= 0.3 ? "#f97316" : "#ef4444";
          return (
            <View key={i} style={{
              width: "23%" as any, borderRadius: 12, borderWidth: 1, padding: 10, gap: 5,
              alignItems: "center", backgroundColor: C.bgCard, borderColor: C.border,
            }}>
              <Text style={{color: C.textMid, fontSize: 10, fontFamily: F.bold, textAlign: "center"}}>{rashi}</Text>
              <Text style={{color, fontSize: 22, fontFamily: F.bold}}>{score}</Text>
              <View style={{ width: "100%", height: 5, borderRadius: 3, backgroundColor: C.bgCard2, overflow: "hidden" }}>
                <View style={{ height: 5, borderRadius: 3, width: `${Math.round(pct*100)}%` as any, backgroundColor: color }} />
              </View>
              <View style={{ backgroundColor: `${color}${o("18")}`, paddingHorizontal: 7, paddingVertical: 2, borderRadius: 6 }}>
                <Text style={{color, fontSize: 9, fontFamily: F.bold}}>
                  {pct>=0.7?t.ku_bavStrong:pct>=0.5?t.ku_bavGood:pct>=0.3?t.ku_bavAverage:t.ku_bavWeak}
                </Text>
              </View>
            </View>
          );
        })}
      </View>

      <View style={{ flexDirection: "row", flexWrap: "wrap", gap: 12, justifyContent: "center" }}>
        {([["#22c55e",t.ku_bavLegStrong],["#fbbf24",t.ku_bavLegGood],["#f97316",t.ku_bavLegAverage],["#ef4444",t.ku_bavLegWeak]] as const).map(([c,l])=>(
          <View key={l} style={{flexDirection:"row",alignItems:"center",gap:5}}>
            <View style={{width:10,height:10,borderRadius:5,backgroundColor:c as string}}/>
            <Text style={{color:C.textMid,fontSize:11,fontFamily:F.semibold}}>{l}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

// Static type+color metadata (language-independent). Names + descriptions come from getTaraData(lang).
const TARA_TYPES: { type: "neutral"|"good"|"bad"|"great"; color: string }[] = [
  { type:"neutral", color:"#94a3b8" },
  { type:"good",    color:"#22c55e" },
  { type:"bad",     color:"#ef4444" },
  { type:"good",    color:"#4ade80" },
  { type:"bad",     color:"#f97316" },
  { type:"good",    color:"#34d399" },
  { type:"bad",     color:"#dc2626" },
  { type:"good",    color:"#60a5fa" },
  { type:"great",   color:"#a78bfa" },
];

function makeTaraData(lang: string) {
  const items = getTaraData(lang);
  return items.map((it, i) => ({ name: it.name, desc: it.desc, ...TARA_TYPES[i] }));
}

function computeNavatara(kundli: KundliData, lang: string) {
  const moonNakIdx = NAKSHATRAS.indexOf(kundli.nakshatra ?? "");
  if (moonNakIdx < 0) return [];
  const taraData = makeTaraData(lang);
  const coreplanets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];
  return coreplanets.map(name => {
    const p = kundli.planets.find(pl => pl.name === name);
    const lon = p?.longitude ?? 0;
    const pNakIdx = Math.floor(lon / (360/27)) % 27;
    const count   = ((pNakIdx - moonNakIdx + 27) % 27);
    const taraNum = (count % 9);
    const tara    = taraData[taraNum];
    return { planet: name, nakIdx: pNakIdx, nakName: NAKSHATRAS[pNakIdx], taraNum: taraNum + 1, tara };
  });
}

function NavataraTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (vv: string) => oa(C.isDark, vv);
  const data = useMemo(() => computeNavatara(kundli, t.lang), [kundli, t.lang]);
  const taraData = useMemo(() => makeTaraData(t.lang), [t.lang]);
  const moonNak = kundli.nakshatra ?? "?";

  return (
    <View style={{gap:16}}>
      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.border, backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: ac, padding: 14, gap: 4 }}>
          <Text style={{ color: ac, fontSize: 14, fontFamily: F.bold }}>{L.whatNavatara}</Text>
          <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, lineHeight: 19 }}>
            {L.navataraDesc}
          </Text>
        </View>
      </View>

      <View style={{
        flexDirection: "row", alignItems: "center", gap: 10,
        backgroundColor: `${ac}${o("10")}`, borderRadius: 14, padding: 14,
        borderWidth: 1, borderColor: `${ac}${o("25")}`,
      }}>
        <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: `${ac}${o("18")}`, alignItems: "center", justifyContent: "center" }}>
          <Text style={{ fontSize: 20 }}>🌙</Text>
        </View>
        <View style={{ flex: 1 }}>
          <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 }}>{L.chandraNakBase}</Text>
          <Text style={{ color: C.text, fontSize: 16, fontFamily: F.bold, marginTop: 2 }}>{moonNak}</Text>
        </View>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={{flexDirection:"row",gap:6}}>
          {taraData.map((t2,i) => (
            <View key={i} style={{ borderWidth: 1, borderRadius: 10, paddingHorizontal: 10, paddingVertical: 6, alignItems: "center", gap: 2, borderColor: `${t2.color}${o("35")}`, backgroundColor: `${t2.color}${o("10")}` }}>
              <Text style={{ fontSize: 11, fontFamily: F.bold, color: t2.color }}>{i+1}</Text>
              <Text style={{ fontSize: 10, fontFamily: F.bold, color: t2.color }}>{t2.name.slice(0,6)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      <View style={{gap:10}}>
        {data.map(({ planet, nakName, taraNum, tara }) => (
          <View key={planet} style={{
            flexDirection: "row", alignItems: "flex-start", gap: 12, borderWidth: 1, borderRadius: 14, padding: 14, overflow: "hidden",
            borderColor: `${tara.color}${o("25")}`, backgroundColor: C.bgCard,
          }}>
            <View style={{ borderLeftWidth: 3, borderLeftColor: tara.color, position: "absolute", left: 0, top: 0, bottom: 0 }} />
            <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: `${hue(planet)}${o("15")}`, alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
              <Text style={{ color: hue(planet), fontSize: 14, fontFamily: F.bold }}>{planet.slice(0,2)}</Text>
            </View>
            <View style={{flex:1}}>
              <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
                <Text style={{color:C.text,fontSize:14,fontFamily:F.bold}}>{pName(planet)}</Text>
                <View style={{ backgroundColor: `${tara.color}${o("18")}`, borderRadius: 8, paddingHorizontal: 8, paddingVertical: 3, borderWidth: 1, borderColor: `${tara.color}${o("30")}` }}>
                  <Text style={{color:tara.color,fontSize:10,fontFamily:F.bold}}>{taraNum}. {tara.name}</Text>
                </View>
              </View>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.semibold,marginTop:3}}>
                {L.nakshatraLabel}: {nakName}
              </Text>
              <Text style={{color:tara.color,fontSize:11,fontFamily:F.semibold,marginTop:2}}>{tara.desc}</Text>
            </View>
            <Text style={{fontSize:18}}>
              {tara.type==="great"?"⭐":tara.type==="good"?"✅":tara.type==="bad"?"⚠️":"🔵"}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

function computeChara(kundli: KundliData, lang: string) {
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  const KARAKA_DEFS = getKarakaDefs(lang);
  const vals = CORE.map(name => {
    const p = kundli.planets.find(pl => pl.name === name);
    if (!p) return { name, deg: 0 };
    let deg = p.longitude % 30;
    if (name === "Rahu") deg = 30 - deg;
    return { name, deg };
  });
  const sorted = [...vals].sort((a,b) => b.deg - a.deg);
  return sorted.map((v, i) => ({ ...v, karaka: KARAKA_DEFS[i] }));
}

function JaiminiTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (vv: string) => oa(C.isDark, vv);
  const data = useMemo(() => computeChara(kundli, t.lang), [kundli, t.lang]);
  const ak   = data[0];

  return (
    <View style={{gap:16}}>
      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.border, backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: ac, padding: 14, gap: 4 }}>
          <Text style={{ color: ac, fontSize: 14, fontFamily: F.bold }}>{L.whatJaimini}</Text>
          <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, lineHeight: 19 }}>
            {L.jaiminiDesc}
          </Text>
        </View>
      </View>

      {ak && (
        <View style={{
          borderRadius: 16, borderWidth: 1.5, padding: 0, overflow: "hidden",
          backgroundColor: C.bgCard, borderColor: `${hue(ak.name)}${o("45")}`,
          boxShadow: `0 4px 20px ${hue(ak.name)}${o("18")}`,
        } as any}>
          <View style={{ borderLeftWidth: 4, borderLeftColor: hue(ak.name), padding: 16, gap: 10 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 14 }}>
              <View style={{
                width: 56, height: 56, borderRadius: 16, alignItems: "center", justifyContent: "center",
                borderWidth: 1.5, flexShrink: 0,
                backgroundColor: `${hue(ak.name)}${o("15")}`, borderColor: `${hue(ak.name)}${o("35")}`,
              }}>
                <Text style={{ color: hue(ak.name), fontSize: 22, fontFamily: F.bold }}>{ak.name.slice(0,2)}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
                  <Feather name="award" size={13} color={hue(ak.name)} />
                  <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 }}>{L.atmakaraka}</Text>
                </View>
                <Text style={{ color: C.text, fontSize: 20, fontFamily: F.bold, marginTop: 2 }}>{pName(ak.name)}</Text>
                <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.semibold, marginTop: 3 }}>{ak.karaka?.desc}</Text>
              </View>
            </View>
            <View style={{ backgroundColor: `${hue(ak.name)}${o("10")}`, borderRadius: 8, paddingVertical: 6, paddingHorizontal: 10, borderWidth: 1, borderColor: `${hue(ak.name)}${o("18")}` }}>
              <Text style={{ color: C.textMid, fontSize: 12, fontFamily: F.semibold }}>
                {L.jaiminiDegPre} <Text style={{ color: hue(ak.name), fontFamily: F.bold }}>{ak.deg.toFixed(2)}°</Text> — {L.jaiminiDegSuf}
              </Text>
            </View>
          </View>
        </View>
      )}

      <View style={{gap:10}}>
        {data.map(({ name, deg, karaka }, idx) => {
          if (!karaka) return null;
          const color = karaka.color;
          return (
            <View key={name} style={{
              flexDirection: "row", alignItems: "flex-start", gap: 12, borderRadius: 14,
              borderWidth: 1, padding: 14, overflow: "hidden",
              backgroundColor: C.bgCard, borderColor: `${color}${o("25")}`,
            }}>
              <View style={{ borderLeftWidth: 3, borderLeftColor: color, position: "absolute", left: 0, top: 0, bottom: 0 }} />
              <View style={{
                width: 44, height: 44, borderRadius: 12, alignItems: "center", justifyContent: "center",
                flexShrink: 0, backgroundColor: `${color}${o("15")}`,
              }}>
                <Text style={{ color, fontSize: 13, fontFamily: F.bold }}>{karaka.key}</Text>
              </View>
              <View style={{flex:1}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:14,fontFamily:F.bold}}>{pName(name)}</Text>
                  <View style={{ backgroundColor: `${color}${o("12")}`, borderRadius: 6, paddingHorizontal: 6, paddingVertical: 2, borderWidth: 1, borderColor: `${color}${o("18")}` }}>
                    <Text style={{color:C.textMid,fontSize:10,fontFamily:F.semibold}}>{deg.toFixed(1)}°</Text>
                  </View>
                </View>
                <Text style={{color,fontSize:12,fontFamily:F.bold,marginTop:2}}>{karaka.name}</Text>
                <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.semibold,marginTop:2}}>{karaka.desc}</Text>
              </View>
            </View>
          );
        })}
      </View>

      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.isDark ? "rgba(167,139,250,0.2)" : "rgba(167,139,250,0.35)", backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: "#a78bfa", padding: 14, gap: 4 }}>
          <Text style={{color:"#a78bfa",fontSize:13,fontFamily:F.bold}}>{L.jaiminiLagna}</Text>
          <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.medium,lineHeight:19}}>
            {L.jaiminiLagnaDesc}
          </Text>
        </View>
      </View>
    </View>
  );
}

function approxTransit(referenceDate: Date = new Date()): Record<string,number> {
  const J2000_LON: Record<string,number> = {
    Sun:280.46, Moon:218.32, Mars:355.43, Mercury:280.47,
    Jupiter:34.35, Venus:181.97, Saturn:49.94,
    Rahu:125.04, Ketu:305.04,
  };
  const DAILY_MOT: Record<string,number> = {
    Sun:0.9856, Moon:13.1764, Mars:0.5240, Mercury:1.3833,
    Jupiter:0.0831, Venus:1.6021, Saturn:0.0335,
    Rahu:-0.0529, Ketu:-0.0529,
  };
  const J2000 = new Date("2000-01-01T12:00:00Z");
  const daysSince = (referenceDate.getTime() - J2000.getTime()) / 86400000;
  const result: Record<string,number> = {};
  for (const p of Object.keys(J2000_LON)) {
    result[p] = ((J2000_LON[p] + DAILY_MOT[p] * daysSince) % 360 + 360) % 360;
  }
  return result;
}

function TransitTab({ kundli, moonRashi }: { kundli: KundliData; moonRashi: any }) {
  const C = useC();
  const t = useT();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const L = getKundliLabels(t);
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v2: string) => oa(C.isDark, v2);
  const transits = useMemo(() => approxTransit(), []);
  const ascRashi = Math.floor((kundli.ascendantDeg ?? 0) / 30) % 12;
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];

  return (
    <View style={{gap:16}}>
      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.warningBorder, backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: C.warningBorder, padding: 14, gap: 4 }}>
          <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
            <Feather name="alert-triangle" size={13} color={C.warningText} />
            <Text style={{ color: C.warningText, fontSize: 13, fontFamily: F.bold }}>
              {t.ku_approxTransit}
            </Text>
          </View>
          <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, lineHeight: 19 }}>
            {t.ku_transitDisclaimer}
          </Text>
        </View>
      </View>

      {moonRashi && (
        <View style={{
          borderRadius: 14, borderWidth: 1, borderColor: `${ac}${o("35")}`, backgroundColor: C.bgCard, overflow: "hidden",
        }}>
          <View style={{ borderLeftWidth: 3, borderLeftColor: ac, padding: 14, gap: 4 }}>
            <View style={{ flexDirection: "row", alignItems: "center", gap: 6 }}>
              <View style={{ width: 8, height: 8, borderRadius: 4, backgroundColor: "#22c55e" }} />
              <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.bold, letterSpacing: 1.5 }}>{L.liveChandraTransit}</Text>
            </View>
            <Text style={{color:C.text,fontSize:16,fontFamily:F.bold,marginTop:2}}>
              {typeof moonRashi.index === "number" ? pick(v, RASHI[RASHI_KEYS[moonRashi.index]]) : moonRashi.name} · {L.house} {((moonRashi.index - ascRashi + 12)%12)+1}
            </Text>
            <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.semibold}}>
              {L.nakshatraLabel}: {(() => {
                const idx = NAKSHATRA.findIndex(n => n.en === moonRashi.nakshatra);
                return idx >= 0 ? pick(v, NAKSHATRA[idx]) : moonRashi.nakshatra;
              })()}
            </Text>
          </View>
        </View>
      )}

      <View style={{gap:10}}>
        {CORE.map(name => {
          const lon     = transits[name] ?? 0;
          const rashi   = Math.floor(lon / 30) % 12;
          const deg     = (lon % 30).toFixed(1);
          const house   = ((rashi - ascRashi + 12) % 12) + 1;
          const nIdx    = Math.floor(lon / (360/27)) % 27;
          const nakName = pick(v, NAKSHATRA[nIdx]);
          const pHue    = hue(name);

          const natal   = kundli.planets.find(p => p.name === name);
          const natalR  = natal ? Math.floor(natal.longitude/30)%12 : -1;
          const isConj  = natalR === rashi && natalR >= 0;

          return (
            <View key={name} style={{
              flexDirection: "row", alignItems: "center", gap: 12,
              borderRadius: 14, borderWidth: 1, padding: 14, overflow: "hidden",
              backgroundColor: isConj ? `${pHue}${o("06")}` : C.bgCard,
              borderColor: isConj ? `${pHue}${o("45")}` : C.border,
            }}>
              <View style={{ borderLeftWidth: 3, borderLeftColor: pHue, position: "absolute", left: 0, top: 0, bottom: 0 }} />
              <View style={{ width: 38, height: 38, borderRadius: 12, backgroundColor: `${pHue}${o("15")}`, alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Text style={{color:pHue,fontSize:13,fontFamily:F.bold}}>{name.slice(0,2)}</Text>
              </View>
              <View style={{flex:1}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:14,fontFamily:F.bold}}>{pName(name)}</Text>
                  {isConj && (
                    <View style={{backgroundColor:`${pHue}${o("20")}`,borderRadius:6,paddingHorizontal:6,paddingVertical:2,borderWidth:1,borderColor:`${pHue}${o("35")}`}}>
                      <Text style={{color:pHue,fontSize:9,fontFamily:F.bold}}>{L.natalConj}</Text>
                    </View>
                  )}
                </View>
                <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.semibold,marginTop:3}}>
                  {pick(v, RASHI[RASHI_KEYS[rashi]])} · {t.ku_houseLabel} {house} · {nakName}
                </Text>
              </View>
              <View style={{ alignItems: "flex-end" }}>
                <Text style={{color:pHue,fontSize:14,fontFamily:F.bold}}>{deg}°</Text>
                <Text style={{color:C.textMid,fontSize:10,fontFamily:F.semibold}}>H{house}</Text>
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}

function getKPLords(longitude: number): { nakIdx:number; nakName:string; starLord:string; subLord:string; subSubLord:string } {
  const NAK_SPAN = 360 / 27;
  const nakIdx   = Math.floor(longitude / NAK_SPAN) % 27;
  const nakStart = nakIdx * NAK_SPAN;
  const posInNak = longitude - nakStart;
  const starLord = NAK_LORDS[nakIdx];
  const startIdx = DASHA_SEQ.indexOf(starLord);
  let pos = 0;
  let subLord    = starLord;
  let subSubLord = starLord;
  for (let i = 0; i < 9; i++) {
    const planet = DASHA_SEQ[(startIdx + i) % 9];
    const span   = (DASHA_YRS[planet] / 120) * NAK_SPAN;
    if (posInNak < pos + span) {
      subLord = planet;
      const posInSub  = posInNak - pos;
      const subIdx    = DASHA_SEQ.indexOf(planet);
      let pos2 = 0;
      for (let j = 0; j < 9; j++) {
        const p2    = DASHA_SEQ[(subIdx + j) % 9];
        const span2 = (DASHA_YRS[p2] / 120) * span;
        if (posInSub < pos2 + span2) { subSubLord = p2; break; }
        pos2 += span2;
      }
      break;
    }
    pos += span;
  }
  return { nakIdx, nakName:NAKSHATRAS[nakIdx], starLord, subLord, subSubLord };
}

// ── Cusps Table (Astrosage-style: House | Degree | SL | NL | SB | SS) ─────
const ABBR_LORD: Record<string,string> = { Sun:"Su",Moon:"Mo",Mars:"Ma",Mercury:"Me",Jupiter:"Ju",Venus:"Ve",Saturn:"Sa",Rahu:"Ra",Ketu:"Ke" };
function fmtCuspDeg(lon: number): string {
  const within = lon % 30;
  const d = Math.floor(within);
  const mFloat = (within - d) * 60;
  const m = Math.floor(mFloat);
  const s = Math.round((mFloat - m) * 60);
  return `${String(d).padStart(2,"0")}°${String(m).padStart(2,"0")}'${String(s).padStart(2,"0")}"`;
}
const SIGN_ABBR = ["Ar","Ta","Ge","Cn","Le","Vi","Li","Sc","Sg","Cp","Aq","Pi"];
function CuspsTable({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v: string) => oa(C.isDark, v);
  const cusps = kundli.kp?.cusps;
  if (!cusps || cusps.length !== 12) return null;
  const ab = (lord: string) => ABBR_LORD[lord] ?? lord.slice(0,2);
  return (
    <View style={{ borderRadius: 18, borderWidth: 1, overflow: "hidden", backgroundColor: C.bgCard, borderColor: C.border }}>
      <View style={{ backgroundColor: `${ac}${o("12")}`, paddingVertical: 10, paddingHorizontal: 16, borderBottomWidth: 1, borderBottomColor: C.border, flexDirection: "row", alignItems: "center", gap: 8 }}>
        <Feather name="grid" size={13} color={ac} />
        <Text style={{ color: ac, fontSize: 11, fontFamily: F.bold, letterSpacing: 1 }}>CUSPS</Text>
      </View>
      <View style={{ flexDirection: "row", paddingVertical: 8, paddingHorizontal: 10, borderBottomWidth: 1, borderBottomColor: C.border }}>
        <Text style={{ width: 26, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5 }}>H</Text>
        <Text style={{ flex: 1.6, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5 }}>DEGREE</Text>
        <Text style={{ flex: 0.7, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5, textAlign: "center" }}>SL</Text>
        <Text style={{ flex: 0.7, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5, textAlign: "center" }}>NL</Text>
        <Text style={{ flex: 0.7, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5, textAlign: "center" }}>SB</Text>
        <Text style={{ flex: 0.7, color: C.textMid, fontSize: 9, fontFamily: F.bold, letterSpacing: 0.5, textAlign: "center" }}>SS</Text>
      </View>
      {cusps.map((c, idx) => {
        const signIdx = Math.floor((c.longitude % 360) / 30) % 12;
        return (
          <View key={c.house} style={{
            flexDirection: "row", alignItems: "center", paddingVertical: 8, paddingHorizontal: 10,
            backgroundColor: idx % 2 === 0 ? "transparent" : `${ac}${o("05")}`,
            borderBottomWidth: idx < cusps.length - 1 ? 1 : 0, borderBottomColor: C.border,
          }}>
            <Text style={{ width: 26, color: C.text, fontSize: 11, fontFamily: F.bold }}>{c.house}</Text>
            <View style={{ flex: 1.6, flexDirection: "row", alignItems: "baseline", gap: 4 }}>
              <Text style={{ color: C.text, fontSize: 10, fontFamily: F.semibold }} numberOfLines={1}>{fmtCuspDeg(c.longitude)}</Text>
              <Text style={{ color: C.textMuted, fontSize: 9, fontFamily: F.medium }}>{SIGN_ABBR[signIdx]}</Text>
            </View>
            <Text style={{ flex: 0.7, color: hue(c.sl), fontSize: 11, fontFamily: F.bold, textAlign: "center" }}>{ab(c.sl)}</Text>
            <Text style={{ flex: 0.7, color: hue(c.nl), fontSize: 11, fontFamily: F.bold, textAlign: "center" }}>{ab(c.nl)}</Text>
            <Text style={{ flex: 0.7, color: hue(c.sb), fontSize: 11, fontFamily: F.bold, textAlign: "center" }}>{ab(c.sb)}</Text>
            <Text style={{ flex: 0.7, color: hue(c.ss), fontSize: 11, fontFamily: F.bold, textAlign: "center" }}>{ab(c.ss)}</Text>
          </View>
        );
      })}
    </View>
  );
}

function KPTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const { language } = useUser();
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v2: string) => oa(C.isDark, v2);
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];
  const ascLon = kundli.ascendantDeg ?? 0;
  const kpData = useMemo(() => {
    // Prefer server's KP-Krishnamurti computed planets (longitudes + NL/SB/SS).
    // Fallback to client-side getKPLords() over Lahiri longitudes only when
    // the server payload doesn't include the kp block.
    const rows: Array<{name:string;lon:number;kp:{nakIdx:number;nakName:string;starLord:string;subLord:string;subSubLord:string}}> = [];
    const sp = kundli.kp?.planets || [];
    const findSp = (n: string) => sp.find(x => x.name === n);

    // Ascendant — prefer server's KP cusp[0] (Krishnamurti). Falls back to
    // client compute over Lahiri ascendantDeg only if server payload missing.
    const c0 = kundli.kp?.cusps?.[0];
    if (c0) {
      const lon = c0.longitude % 360;
      const nakSize = 360 / 27;
      const nakIdx = Math.floor(lon / nakSize) % 27;
      rows.push({
        name: "Ascendant",
        lon,
        kp: { nakIdx, nakName: "", starLord: c0.nl, subLord: c0.sb, subSubLord: c0.ss },
      });
    } else {
      rows.push({ name:"Ascendant", lon:ascLon, kp:getKPLords(ascLon) });
    }

    for (const name of CORE) {
      const s = findSp(name);
      if (s) {
        const lon = s.longitude % 360;
        const nakSize = 360 / 27;
        const nakIdx = Math.floor(lon / nakSize) % 27;
        rows.push({
          name,
          lon,
          kp: {
            nakIdx,
            nakName: NAKSHATRA[nakIdx]?.en ?? "",
            starLord: s.nl,
            subLord: s.sb,
            subSubLord: s.ss,
          },
        });
      } else {
        const p = kundli.planets.find(pl => pl.name === name);
        if (p) rows.push({ name, lon:p.longitude, kp:getKPLords(p.longitude) });
      }
    }
    return rows;
  }, [kundli]);

  return (
    <View style={{gap:16}}>
      <CuspsTable kundli={kundli} />

      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.border, backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: ac, padding: 14, gap: 4 }}>
          <Text style={{ color: ac, fontSize: 14, fontFamily: F.bold }}>{L.whatKP}</Text>
          <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium, lineHeight: 19 }}>
            {L.kpDesc}
          </Text>
        </View>
      </View>

      <KPSummaryCard kundli={kundli} />

      <View style={{gap:10}}>
        {kpData.map(({ name, lon, kp }) => {
          const isAsc = name === "Ascendant";
          const pHue  = isAsc ? ac : hue(name);
          return (
            <View key={name} style={{
              flexDirection: "row", alignItems: "flex-start", gap: 12,
              borderRadius: 14, borderWidth: 1, padding: 14, overflow: "hidden",
              backgroundColor: C.bgCard, borderColor: `${pHue}${o("25")}`,
            }}>
              <View style={{ borderLeftWidth: 3, borderLeftColor: pHue, position: "absolute", left: 0, top: 0, bottom: 0 }} />
              <View style={{ width: 40, height: 40, borderRadius: 12, backgroundColor: `${pHue}${o("15")}`, alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Text style={{color:pHue,fontSize:12,fontFamily:F.bold}}>
                  {isAsc?L.kpAsc:name.slice(0,2)}
                </Text>
              </View>
              <View style={{flex:1,gap:6}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:14,fontFamily:F.bold}}>
                    {isAsc?L.snapAscendant:pName(name)}
                  </Text>
                  <View style={{ backgroundColor: `${pHue}${o("12")}`, borderRadius: 6, paddingHorizontal: 7, paddingVertical: 3, borderWidth: 1, borderColor: `${pHue}${o("18")}` }}>
                    <Text style={{color:C.textMid,fontSize:10,fontFamily:F.semibold}}>{(lon%30).toFixed(2)}° {pick(v, NAKSHATRA[kp.nakIdx])}</Text>
                  </View>
                </View>
                <View style={{flexDirection:"row",gap:6,flexWrap:"wrap"}}>
                  <KPLordChip label={L.kpStar} lord={kp.starLord}/>
                  <KPLordChip label={L.kpSub} lord={kp.subLord}/>
                  <KPLordChip label={L.kpSubSub} lord={kp.subSubLord}/>
                </View>
              </View>
            </View>
          );
        })}
      </View>

      <View style={{ borderRadius: 14, borderWidth: 1, borderColor: C.isDark ? "rgba(167,139,250,0.2)" : "rgba(167,139,250,0.35)", backgroundColor: C.bgCard, overflow: "hidden" }}>
        <View style={{ borderLeftWidth: 3, borderLeftColor: "#a78bfa", padding: 14, gap: 4 }}>
          <Text style={{color:"#a78bfa",fontSize:13,fontFamily:F.bold}}>{L.kpSignificators}</Text>
          <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.medium,lineHeight:19}}>
            {L.kpFooter}
          </Text>
        </View>
      </View>
    </View>
  );
}

// ── KP Summary Card (inline on Kundli main screen) ────────────────────────
// Compact 3-column table: Planet | Star Lord (with PL houses) | Sub Lord (with PL houses).
// Computes everything client-side from kundli.planets + ascendant.
const KP_SIGN_LORDS = [
  "Mars","Venus","Mercury","Moon","Sun","Mercury",
  "Venus","Mars","Jupiter","Saturn","Saturn","Jupiter",
];
function KPSummaryCard({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v: string) => oa(C.isDark, v);
  const ABBR: Record<string,string> = { Sun:"Su",Moon:"Mo",Mars:"Ma",Mercury:"Me",Jupiter:"Ju",Venus:"Ve",Saturn:"Sa",Rahu:"Ra",Ketu:"Ke" };
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];
  const lagnaSign = Math.floor((kundli.ascendantDeg ?? 0) / 30) % 12;

  // Build map: planet name -> { house, sign }
  const pmap: Record<string,{house:number; signIdx:number}> = {};
  for (const p of kundli.planets) {
    pmap[p.name] = { house: p.house, signIdx: Math.floor((p.longitude % 360) / 30) % 12 };
  }
  // Prefer server-computed significations (full classical KP inheritance for
  // Rahu/Ketu) when present in kundli.kp; fall back to local compute otherwise.
  const serverSigs = kundli.kp?.significations;
  const serverPlanets = kundli.kp?.planets;

  // Compute PL houses for any lord = occupation + owned (client fallback only)
  const plHousesOfLocal = (lord: string): number[] => {
    const occ = pmap[lord]?.house;
    const owned: number[] = [];
    for (let h = 0; h < 12; h++) {
      const signAtCusp = (lagnaSign + h) % 12;
      if (KP_SIGN_LORDS[signAtCusp] === lord) owned.push(h + 1);
    }
    const set = new Set<number>(owned);
    if (occ) set.add(occ);
    return [...set].sort((a,b)=>a-b);
  };
  const plHousesOf = (lord: string): number[] => {
    const sv = serverSigs?.[lord]?.pl;
    // PURE KP: only trust server's KP-Placidus significations. Never mix in
    // Vedic whole-sign house from kundli.planets[].house — KP and Vedic are
    // two different house systems and must not be merged. If server data is
    // missing (legacy kundli), local fallback uses KP cusp sign-lord ownership
    // only; the auto-refetch effect upstream backfills the kp block.
    return (sv && sv.length) ? [...sv].sort((a,b)=>a-b) : plHousesOfLocal(lord);
  };
  const fmt = (lord: string): string => {
    const hs = plHousesOf(lord);
    return `${ABBR[lord] ?? lord}-${hs.length ? hs.join(",") : "?"}`;
  };

  // Owned houses per planet relative to lagna (sign-lord cusps). Nodes own none.
  const NODES = new Set(["Rahu","Ketu"]);
  const ownedHousesOf = (lord: string): number[] => {
    if (NODES.has(lord)) return [];
    const out: number[] = [];
    for (let h = 0; h < 12; h++) {
      const signAtCusp = (lagnaSign + h) % 12;
      if (KP_SIGN_LORDS[signAtCusp] === lord) out.push(h + 1);
    }
    return out;
  };

  const rows = CORE.filter(n => pmap[n]).map(n => {
    const p = kundli.planets.find(pl => pl.name === n)!;
    // Prefer server's KP Placidus house + NL/SBL (matches Astrosage convention).
    // kundli.planets[].house uses whole-sign Vedic; KP table must use Placidus.
    const sp = serverPlanets?.find(x => x.name === n);
    const base = sp
      ? { name: n, house: sp.house, nl: sp.nl, sb: sp.sb }
      : (() => { const kp = getKPLords(p.longitude); return { name: n, house: p.house, nl: kp.starLord, sb: kp.subLord }; })();
    // Use full classical PL houses (server significations: occ + dispositor +
    // conjuncts + aspects for nodes). This matches the NL/SBL columns and
    // Astrosage. Falls back to occ+owned only when server sigs are missing.
    return { ...base, plHouses: plHousesOf(n), owns: ownedHousesOf(n) };
  });

  return (
    <View style={{
      borderRadius: 18, borderWidth: 1, overflow: "hidden",
      backgroundColor: C.bgCard, borderColor: C.border,
    }}>
      <View style={{
        backgroundColor: `${ac}${o("12")}`, paddingVertical: 10, paddingHorizontal: 16,
        borderBottomWidth: 1, borderBottomColor: C.border,
        flexDirection: "row", alignItems: "center", gap: 8,
      }}>
        <Feather name="crosshair" size={13} color={ac} />
        <Text style={{ color: ac, fontSize: 11, fontFamily: F.bold, letterSpacing: 1 }}>KP SUB-LORDS</Text>
      </View>
      <View style={{ flexDirection: "row", paddingVertical: 8, paddingHorizontal: 14, borderBottomWidth: 1, borderBottomColor: C.border }}>
        <Text style={{ flex: 1.7, color: C.textMid, fontSize: 10, fontFamily: F.bold, letterSpacing: 0.5 }}>PLANET</Text>
        <Text style={{ flex: 1.3, color: C.textMid, fontSize: 10, fontFamily: F.bold, letterSpacing: 0.5, paddingLeft: 6 }}>NL</Text>
        <Text style={{ flex: 1.3, color: C.textMid, fontSize: 10, fontFamily: F.bold, letterSpacing: 0.5, paddingLeft: 6 }}>SBL</Text>
      </View>
      {rows.map((r, idx) => {
        const pHue = hue(r.name);
        return (
          <View key={r.name} style={{
            flexDirection: "row", alignItems: "center", paddingVertical: 9, paddingHorizontal: 14,
            backgroundColor: idx % 2 === 0 ? "transparent" : `${ac}${o("05")}`,
            borderBottomWidth: idx < rows.length - 1 ? 1 : 0, borderBottomColor: C.border,
          }}>
            <View style={{ flex: 1.7, flexDirection: "row", alignItems: "center", gap: 6, paddingRight: 6 }}>
              <View style={{ width: 22, height: 22, borderRadius: 6, backgroundColor: `${pHue}${o("15")}`, alignItems: "center", justifyContent: "center", flexShrink: 0 }}>
                <Text style={{ color: pHue, fontSize: 9, fontFamily: F.bold }}>{ABBR[r.name]}</Text>
              </View>
              <Text style={{ flex: 1, color: C.text, fontSize: 11, fontFamily: F.semibold }} numberOfLines={1}>
                {r.name}-{r.plHouses.length ? r.plHouses.join(",") : "—"}
              </Text>
            </View>
            <Text style={{ flex: 1.3, color: C.textMid, fontSize: 10, fontFamily: F.semibold, paddingLeft: 6 }} numberOfLines={1}>{fmt(r.nl)}</Text>
            <Text style={{ flex: 1.3, color: C.textMid, fontSize: 10, fontFamily: F.semibold, paddingLeft: 6 }} numberOfLines={1}>{fmt(r.sb)}</Text>
          </View>
        );
      })}
    </View>
  );
}

function KPLordChip({ label, lord }: { label:string; lord:string }) {
  const C = useC();
  const color = hue(lord);
  const o = (v: string) => oa(C.isDark, v);
  return (
    <View style={{
      flexDirection: "row", alignItems: "center", borderWidth: 1, borderRadius: 8,
      paddingHorizontal: 8, paddingVertical: 4, gap: 3,
      backgroundColor: `${color}${o("12")}`, borderColor: `${color}${o("30")}`,
    }}>
      <Text style={{color:C.textMid,fontSize:9,fontFamily:F.semibold}}>{label}:</Text>
      <Text style={{color,fontSize:10,fontFamily:F.bold}}>{lord}</Text>
    </View>
  );
}

const CHART_BTNS = [
  { tab:"Kundli",       icon:"star" },
  { tab:"KP",           icon:"crosshair" },
  { tab:"Ashtakavarga", icon:"grid" },
  { tab:"Navatara",     icon:"compass" },
  { tab:"Jaimini",      icon:"award" },
  { tab:"Transit",      icon:"navigation" },
] as const;

function chartBtnLabel(tab: string, L: ReturnType<typeof getKundliLabels>): string {
  switch (tab) {
    case "Kundli":       return L.btnKundli;
    case "Ashtakavarga": return L.btnAshtak;
    case "Navatara":     return L.btnNavatara;
    case "Jaimini":      return L.btnJaimini;
    case "Transit":      return L.btnTransit;
    case "KP":           return L.btnKP;
    default:             return tab;
  }
}

function sectionTitleFor(tab: string, L: ReturnType<typeof getKundliLabels>): string {
  switch (tab) {
    case "Kundli":       return L.secDashaTimeline;
    case "Ashtakavarga": return L.secAshtakavarga;
    case "Navatara":     return L.secNavatara9Tara;
    case "Jaimini":      return L.secJaiminiKarakas;
    case "Transit":      return L.secGrahaTransit;
    case "KP":           return L.secKpPaddhati;
    default:             return tab;
  }
}

export default function KundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, language, profiles, primaryProfileId, setPrimaryProfile, updateProfile, user } = useUser();
  const primaryProfile = profiles.find(p => p.id === primaryProfileId) ?? profiles[0] ?? null;
  const [switcherOpen, setSwitcherOpen] = useState(false);

  // Auto-refetch kundli when active profile lacks a complete KP block (older
  // profiles saved before kp_engine v12 won't have kundli.kp, or may have
  // partial cusps without sl/nl/sb/ss lord fields). Ensures KP table updates
  // correctly when switching between profiles.
  const kpBlock = primaryProfile?.kundli?.kp;
  const kpComplete = !!(
    kpBlock?.planets?.length === 9 &&
    kpBlock?.cusps?.length === 12 &&
    kpBlock?.cusps?.[0]?.sl &&
    kpBlock?.cusps?.[0]?.nl &&
    kpBlock?.cusps?.[0]?.sb &&
    kpBlock?.cusps?.[0]?.ss &&
    kpBlock?.significations &&
    Object.keys(kpBlock.significations).length >= 9
  );
  useEffect(() => {
    if (!primaryProfile?.id || !primaryProfile?.birthData) return;
    if (kpComplete) return;
    let cancelled = false;
    const auth = user?.id && user?.api_key ? { user_id: user.id, api_key: user.api_key } : null;
    fetchKundliFromAPI(primaryProfile.birthData, auth)
      .then((fresh) => {
        if (cancelled) return;
        updateProfile(primaryProfile.id, { kundli: fresh });
      })
      .catch(() => { /* silent — old data still renders via fallback */ });
    return () => { cancelled = true; };
  }, [primaryProfile?.id, kpComplete, user?.id, user?.api_key, updateProfile, primaryProfile?.birthData]);
  const tI18n = getT(language);
  const v: VLang = vedicLang(language);
  const t = useT();
  const L = getKundliLabels(t);
  const androidSB = StatusBar.currentHeight ?? 24;
  const topPad = Platform.OS === "web" ? 67 : Platform.OS === "android" ? Math.max(insets.top, androidSB) : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const o = (v: string) => oa(C.isDark, v);

  const [activeTab, setActiveTab] = useState("Kundli");
  const [mahaIdx,   setMahaIdx]   = useState(0);
  const [antarIdx,  setAntarIdx]  = useState(0);
  const [pratIdx,   setPratIdx]   = useState(0);
  const [moonRashi, setMoonRashi] = useState<any>(null);
  // Phase 2.8.59: live Jupiter + Saturn transit (real Swiss Ephemeris from
  // /api/moon_transit response, sits under Live Moon Transit in snapshot).
  const [jupiterT, setJupiterT] = useState<any>(null);
  const [saturnT,  setSaturnT]  = useState<any>(null);

  useEffect(() => {
    apiFetch(`${BASE_URL}/api/moon_transit`)
      .then(r => r.json())
      .then(d => {
        if (typeof d.rashiIndex === "number") {
          const nakIdx = Math.floor(d.longitude / (360/27)) % 27;
          setMoonRashi({ index:d.rashiIndex, name:d.rashiName, nakshatra:NAKSHATRAS[nakIdx], longitude:d.longitude });
        }
        if (d.jupiter && typeof d.jupiter.rashiIndex === "number") {
          setJupiterT({
            index:      d.jupiter.rashiIndex,
            name:       d.jupiter.rashiName,
            nakshatra:  d.jupiter.nakshatra,
            retrograde: d.jupiter.retrograde,
            degInSign:  d.jupiter.degInSign,
          });
        }
        if (d.saturn && typeof d.saturn.rashiIndex === "number") {
          setSaturnT({
            index:      d.saturn.rashiIndex,
            name:       d.saturn.rashiName,
            nakshatra:  d.saturn.nakshatra,
            retrograde: d.saturn.retrograde,
            degInSign:  d.saturn.degInSign,
          });
        }
      }).catch(()=>{});
  }, []);

  useEffect(() => {
    if (!kundli) return;
    const now=Date.now();
    const mi=kundli.dashas.findIndex((d:any)=>tsOf(d.startDate)<=now&&tsOf(d.endDate)>now);
    const mI=mi>=0?mi:0; setMahaIdx(mI);
    const subs=kundli.dashas[mI]?.subDashas??[];
    const ai=subs.findIndex((s2:any)=>tsOf(s2.startDate)<=now&&tsOf(s2.endDate)>now);
    const aI=ai>=0?ai:0; setAntarIdx(aI);
    const prats=subs[aI]?calcPratyantar(subs[aI]):[];
    const pi=prats.findIndex((p:any)=>tsOf(p.startDate)<=now&&tsOf(p.endDate)>now);
    setPratIdx(pi>=0?pi:0);
  }, [kundli]);

  if (!kundli) {
    return (
      <CosmicBg contentStyle={{paddingTop:topPad+20,paddingBottom:botPad+80}}>
        <View style={{ flex: 1, alignItems: "center", paddingHorizontal: 24, gap: 16, paddingTop: 60 }}>
          <View style={{ width: 88, height: 88, borderRadius: 44, borderWidth: 1.5, alignItems: "center", justifyContent: "center", borderColor: `${ac}${o("45")}`, backgroundColor: `${ac}${o("10")}` }}>
            <Feather name="star" size={36} color={ac}/>
          </View>
          <Text style={{ color: C.text, fontSize: 22, fontFamily: F.bold, textAlign: "center" }}>{tI18n.noKundli}</Text>
          <Text style={{ color: C.textMuted, fontSize: 14, fontFamily: F.regular, lineHeight: 22, textAlign: "center" }}>{tI18n.noKundliSub}</Text>
          <Pressable style={({pressed})=>[{
            flexDirection: "row", alignItems: "center", gap: 8, paddingVertical: 14, paddingHorizontal: 28,
            borderRadius: 16, marginTop: 4, backgroundColor: C.accent,
          },pressed&&{opacity:0.8}]}
            onPress={()=>{Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);router.push("/onboarding");}}>
            <Text style={{ color: "#fff", fontFamily: F.bold, fontSize: 15 }}>{tI18n.createKundli}</Text>
            <Feather name="arrow-right" size={16} color="#fff"/>
          </Pressable>
        </View>
      </CosmicBg>
    );
  }

  const dashaBalance = kundli.dashaBalance;
  const ruler        = kundli.nakshatraRuler ?? "?";
  const dbText = dashaBalance != null ? (() => {
    const y=Math.floor(dashaBalance);
    const mo=Math.floor((dashaBalance-y)*12);
    const d=Math.round(((dashaBalance-y)*12-mo)*30);
    return `${ruler} — ${y}y ${mo}m ${d}d`;
  })() : null;
  const lagnaSign = Math.floor((kundli.ascendantDeg??0)/30)%12;
  const moonTransitText = moonRashi
    ? (() => { const h=((moonRashi.index-lagnaSign+12)%12)+1; return `${moonRashi.name} · H${h} · ${moonRashi.nakshatra}`; })()
    : null;
  // Phase 2.8.59 — live Jupiter & Saturn transit rows under Live Moon Transit
  const jupiterTransitText = jupiterT
    ? (() => {
        const h = ((jupiterT.index - lagnaSign + 12) % 12) + 1;
        const r = jupiterT.retrograde ? " · R" : "";
        return `${jupiterT.name} · H${h} · ${jupiterT.nakshatra}${r}`;
      })()
    : null;
  const saturnTransitText = saturnT
    ? (() => {
        const h = ((saturnT.index - lagnaSign + 12) % 12) + 1;
        const r = saturnT.retrograde ? " · R" : "";
        return `${saturnT.name} · H${h} · ${saturnT.nakshatra}${r}`;
      })()
    : null;
  const snapshotRows = [
    { label:L.snapAscendant,  value:kundli.ascendant,  icon:"sunrise" },
    { label:L.snapMoonSign,   value:kundli.moonSign,   icon:"moon" },
    ...(kundli.nakshatra?[{ label:L.snapNakshatra, value:`${kundli.nakshatra} (${L.padaLabel} ${kundli.nakshatraPada??"?"})`, icon:"star" }]:[]),
    ...(kundli.nakshatraRuler?[{ label:L.snapNakshatraLord, value:kundli.nakshatraRuler, icon:"shield" }]:[]),
    ...(dbText?[{ label:L.snapDashaBalance, value:dbText, icon:"clock" }]:[]),
    ...(moonTransitText?[{ label:L.snapLiveMoonTransit, value:moonTransitText, icon:"radio" }]:[]),
    ...(jupiterTransitText?[{ label:L.snapLiveJupiterTransit, value:jupiterTransitText, icon:"trending-up" }]:[]),
    ...(saturnTransitText?[{ label:L.snapLiveSaturnTransit, value:saturnTransitText, icon:"clock" }]:[]),
  ];

  return (
    <CosmicBg>
    <ScrollView style={{ flex: 1 }}
      contentContainerStyle={{ paddingHorizontal: 16, gap: 18, paddingTop: topPad + 8, paddingBottom: botPad + 100 }}
      showsVerticalScrollIndicator={false}>

      <View style={{ flexDirection: "row", alignItems: "center", gap: 10 }}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.back(); }}
          style={{
            width: 36, height: 36, borderRadius: 11,
            alignItems: "center", justifyContent: "center",
            backgroundColor: C.bgCard, borderWidth: 1, borderColor: C.border,
          }}
        >
          <Feather name="arrow-left" size={16} color={C.text} />
        </Pressable>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); setSwitcherOpen(true); }}
          style={{ flex: 1, flexDirection: "row", alignItems: "center", gap: 6 }}
        >
          <View style={{ flex: 1 }}>
            <Text style={{ color: C.text, fontSize: 17, fontFamily: F.bold }} numberOfLines={1}>
              {primaryProfile?.name ?? t.tabKundli}
            </Text>
            {primaryProfile?.birthData && (
              <Text style={{ color: C.textMuted, fontSize: 10.5, fontFamily: F.medium }}>
                {`${primaryProfile.birthData.day}/${primaryProfile.birthData.month}/${primaryProfile.birthData.year} · ${String(primaryProfile.birthData.hour).padStart(2,"0")}:${String(primaryProfile.birthData.minute).padStart(2,"0")} ${primaryProfile.birthData.ampm}`}
              </Text>
            )}
          </View>
          {profiles.length > 1 && <Feather name="chevron-down" size={16} color={C.textMid} />}
        </Pressable>
      </View>

      <Modal visible={switcherOpen} transparent animationType="fade" onRequestClose={() => setSwitcherOpen(false)}>
        <Pressable
          onPress={() => setSwitcherOpen(false)}
          style={{ flex: 1, backgroundColor: "rgba(0,0,0,0.55)", justifyContent: "center", alignItems: "center", padding: 24 }}
        >
          <Pressable
            onPress={(e) => e.stopPropagation()}
            style={{
              width: "100%", maxWidth: 380, borderRadius: 18, borderWidth: 1,
              backgroundColor: C.bgCard, borderColor: C.border, overflow: "hidden",
            }}
          >
            <View style={{ paddingVertical: 14, paddingHorizontal: 18, borderBottomWidth: 1, borderBottomColor: C.border, flexDirection: "row", alignItems: "center", gap: 8 }}>
              <Feather name="users" size={14} color={ac} />
              <Text style={{ color: C.text, fontSize: 14, fontFamily: F.bold, flex: 1 }}>Switch Kundli</Text>
              <Pressable onPress={() => setSwitcherOpen(false)}>
                <Feather name="x" size={18} color={C.textMid} />
              </Pressable>
            </View>
            <ScrollView style={{ maxHeight: 360 }}>
              {profiles.map((p, idx) => {
                const isActive = p.id === primaryProfileId;
                return (
                  <Pressable
                    key={p.id}
                    onPress={() => {
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                      setPrimaryProfile(p.id);
                      setSwitcherOpen(false);
                    }}
                    style={{
                      flexDirection: "row", alignItems: "center", gap: 12,
                      paddingVertical: 14, paddingHorizontal: 18,
                      backgroundColor: isActive ? `${ac}${o("12")}` : "transparent",
                      borderBottomWidth: idx < profiles.length - 1 ? 1 : 0, borderBottomColor: C.border,
                    }}
                  >
                    <View style={{ width: 34, height: 34, borderRadius: 10, alignItems: "center", justifyContent: "center", backgroundColor: isActive ? `${ac}${o("20")}` : C.bgCard2, borderWidth: 1, borderColor: isActive ? `${ac}${o("50")}` : C.border }}>
                      <Feather name="user" size={14} color={isActive ? ac : C.textMid} />
                    </View>
                    <View style={{ flex: 1 }}>
                      <Text style={{ color: C.text, fontSize: 14, fontFamily: F.semibold }} numberOfLines={1}>{p.name}</Text>
                      {p.birthData && (
                        <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium, marginTop: 2 }} numberOfLines={1}>
                          {`${p.birthData.day}/${p.birthData.month}/${p.birthData.year} · ${String(p.birthData.hour).padStart(2,"0")}:${String(p.birthData.minute).padStart(2,"0")} ${p.birthData.ampm}`}
                        </Text>
                      )}
                    </View>
                    {isActive && <Feather name="check" size={16} color={ac} />}
                  </Pressable>
                );
              })}
            </ScrollView>
            <Pressable
              onPress={() => { setSwitcherOpen(false); router.push("/profile-edit" as any); }}
              style={{ flexDirection: "row", alignItems: "center", justifyContent: "center", gap: 6, paddingVertical: 14, borderTopWidth: 1, borderTopColor: C.border, backgroundColor: `${ac}${o("08")}` }}
            >
              <Feather name="plus" size={14} color={ac} />
              <Text style={{ color: ac, fontSize: 13, fontFamily: F.bold }}>Manage Profiles</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginBottom:2}}>
        <View style={{ flexDirection: "row", gap: 8 }}>
          {CHART_BTNS.map(({ tab, icon }) => {
            const active = activeTab === tab;
            return (
              <Pressable key={tab}
                onPress={() => { setActiveTab(tab); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
                style={{
                  flexDirection: "row", alignItems: "center", gap: 6,
                  paddingVertical: 10, paddingHorizontal: 16, borderRadius: 12,
                  borderWidth: active ? 2 : 1.5,
                  backgroundColor: active ? `${ac}${o("18")}` : C.bgCard,
                  borderColor: active ? `${ac}${o("60")}` : C.border,
                }}>
                <Feather name={icon as any} size={12} color={active ? ac : C.textMid} />
                <Text style={{ color: active ? ac : C.textMid, fontSize: 12, fontFamily: F.bold }}>
                  {chartBtnLabel(tab, L)}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      {activeTab === "Kundli" && (<>
      <View style={{
        borderRadius: 18, borderWidth: 1, overflow: "hidden",
        backgroundColor: C.bgCard, borderColor: C.border,
        boxShadow: C.cardShadow,
      } as any}>
        <View style={{
          backgroundColor: `${ac}${o("12")}`, paddingVertical: 10, paddingHorizontal: 16,
          borderBottomWidth: 1, borderBottomColor: C.border,
          flexDirection: "row", alignItems: "center", gap: 8,
        }}>
          <Feather name="book-open" size={13} color={ac} />
          <Text style={{ color: ac, fontSize: 11, fontFamily: F.bold, letterSpacing: 1 }}>{L.birthChartSnap}</Text>
        </View>
        <View style={{ padding: 2 }}>
          {snapshotRows.map(({ label, value, icon }, idx) => (
            <View key={label} style={{
              flexDirection: "row", alignItems: "center", paddingVertical: 10, paddingHorizontal: 14, gap: 10,
              backgroundColor: idx % 2 === 0 ? "transparent" : `${ac}${o("05")}`,
              borderBottomWidth: idx < snapshotRows.length - 1 ? 1 : 0,
              borderBottomColor: C.border,
            }}>
              <Feather name={icon as any} size={12} color={C.textMid} />
              <Text style={{ color: C.textMid, fontSize: 10, fontFamily: F.bold, letterSpacing: 0.5, flex: 1 }}>{label}</Text>
              <Text style={{ color: C.text, fontSize: 13, fontFamily: F.semibold }} numberOfLines={1}>{value}</Text>
            </View>
          ))}
        </View>
      </View>

      <View style={{ gap: 10 }}>
        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/planet-position"); }}
          style={({ pressed }) => [{
            flexDirection: "row", alignItems: "center", justifyContent: "space-between",
            borderRadius: 14, borderWidth: 1, paddingVertical: 14, paddingHorizontal: 16,
            borderColor: C.border, backgroundColor: C.bgCard,
          }, pressed && { opacity: 0.75, transform: [{ scale: 0.98 }] }]}
        >
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <View style={{ width: 38, height: 38, borderRadius: 11, borderWidth: 1, alignItems: "center", justifyContent: "center", backgroundColor: C.bgCard2, borderColor: C.border }}>
              <Feather name="target" size={16} color={C.textMid} />
            </View>
            <View>
              <Text style={{ color: C.text, fontSize: 14, fontFamily: F.bold }}>{L.planetPosition}</Text>
              <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium, marginTop: 2 }}>{L.planetPositionSub}</Text>
            </View>
          </View>
          <Feather name="chevron-right" size={16} color={C.textMuted} />
        </Pressable>

        <Pressable
          onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/daily-alerts"); }}
          style={({ pressed }) => [{
            flexDirection: "row", alignItems: "center", justifyContent: "space-between",
            borderRadius: 14, borderWidth: 1, paddingVertical: 14, paddingHorizontal: 16,
            borderColor: `${ac}${o("35")}`, backgroundColor: `${ac}${o("08")}`,
          }, pressed && { opacity: 0.75, transform: [{ scale: 0.98 }] }]}
        >
          <View style={{ flexDirection: "row", alignItems: "center", gap: 12 }}>
            <View style={{ width: 38, height: 38, borderRadius: 11, borderWidth: 1, alignItems: "center", justifyContent: "center", backgroundColor: `${ac}${o("12")}`, borderColor: `${ac}${o("30")}` }}>
              <Feather name="bell" size={16} color={ac} />
            </View>
            <View>
              <Text style={{ color: ac, fontSize: 14, fontFamily: F.bold }}>{L.dailyAlerts}</Text>
              <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium, marginTop: 2 }}>{L.dailyAlertsSub}</Text>
            </View>
          </View>
          <Feather name="chevron-right" size={16} color={ac} style={{ opacity: 0.7 }} />
        </Pressable>
      </View>

      </>)}

      <SectionHeader
        title={sectionTitleFor(activeTab, L)}
        icon={CHART_BTNS.find(b=>b.tab===activeTab)?.icon}
        C={C}
      />

      {activeTab === "Kundli" && (
        <DashaTab kundli={kundli} mahaIdx={mahaIdx} setMahaIdx={setMahaIdx}
          antarIdx={antarIdx} setAntarIdx={setAntarIdx}
          pratIdx={pratIdx} setPratIdx={setPratIdx} />
      )}
      {activeTab === "Ashtakavarga" && <AshtakavargaTab kundli={kundli} />}
      {activeTab === "Navatara"     && <NavataraTab kundli={kundli} />}
      {activeTab === "Jaimini"      && <JaiminiTab kundli={kundli} />}
      {activeTab === "Transit"      && <TransitTab kundli={kundli} moonRashi={moonRashi} />}
      {activeTab === "KP"           && <KPTab kundli={kundli} />}
    </ScrollView>
    </CosmicBg>
  );
}
