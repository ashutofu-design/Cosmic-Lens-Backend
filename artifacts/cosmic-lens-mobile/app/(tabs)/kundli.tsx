import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { router } from "expo-router";
import React, { useEffect, useMemo, useState } from "react";
import {
  Platform, Pressable, ScrollView,
  StyleSheet, Text, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { CosmicBg } from "@/components/CosmicBg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { getT } from "@/lib/i18n";
import { pName } from "@/lib/proInsightEngine";
import type { KundliData, PlanetInfo } from "@/types";

import { API_BASE as BASE_URL, apiFetch } from "@/lib/apiConfig";

const F = {
  regular:  "Nunito_400Regular",
  medium:   "Nunito_500Medium",
  semibold: "Nunito_600SemiBold",
  bold:     "Nunito_700Bold",
};

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
function formatDate(d: Date | string) {
  const dt = new Date(d);
  return `${dt.getDate()} ${MONTHS[dt.getMonth()]} ${dt.getFullYear()}`;
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

function ProgBar({ pct, color }: { pct:number; color:string }) {
  const C = useC();
  return (
    <View style={[s.progBg, { backgroundColor: C.bgCard2 }]}>
      <View style={[s.progFill, { width:`${pct}%` as any, backgroundColor:color }]} />
    </View>
  );
}

type Level = "Mahadasha"|"Antardasha"|"Pratyantardasha";
const LEVEL_LABEL: Record<Level,string> = { Mahadasha:"MAHADASHA", Antardasha:"ANTARDASHA", Pratyantardasha:"PRATYANTAR" };

function DashaCard({ level, planet, startDate, endDate, active, onPrev, onNext, hasPrev, hasNext, showNextBtn=true }: {
  level:Level; planet:string; startDate:any; endDate:any; active:boolean;
  onPrev:()=>void; onNext:()=>void; hasPrev:boolean; hasNext:boolean; showNextBtn?:boolean;
}) {
  const C = useC();
  const color = hue(planet);
  const pct   = progress(startDate, endDate);
  return (
    <View>
      <View style={s.navRow}>
        <Pressable onPress={() => { if(hasPrev){Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);onPrev();} }}
          style={[s.navBtn,!hasPrev&&{opacity:0.3},{ backgroundColor: C.bgCard2, borderColor: C.border, borderWidth: 1 }]}>
          <Text style={[s.navBtnText,{ color: C.text }]}>← Prev</Text>
        </Pressable>
        <Text style={[s.levelLabel,{color}]}>{LEVEL_LABEL[level]}</Text>
        {showNextBtn ? (
          <Pressable onPress={() => { if(hasNext){Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);onNext();} }}
            style={[s.navBtn,!hasNext&&{opacity:0.3},{ backgroundColor: C.bgCard2, borderColor: C.border, borderWidth: 1 }]}>
            <Text style={[s.navBtnText,{ color: C.text }]}>Next →</Text>
          </Pressable>
        ) : <View style={{width:60}} />}
      </View>
      <View style={[s.dashaCard,{backgroundColor:active?`${color}0d`:C.bgCard,borderColor:active?color:C.border,boxShadow:C.cardShadow} as any]}>
        <View style={s.dashaHeader}>
          <Text style={[s.dashaPlanetName,{ color: C.text }]}>{pName(planet)}</Text>
          {active && <View style={[s.activeBadge,{backgroundColor:`${color}22`}]}>
            <Text style={[s.activeBadgeText,{color}]}>Active</Text>
          </View>}
        </View>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.medium }}>{formatDate(startDate)} – {formatDate(endDate)}</Text>
        {pct>0 && <View style={{gap:4}}>
          <ProgBar pct={pct} color={color}/>
          <Text style={{color, fontSize: 11, fontFamily: F.semibold}}>{pct}% complete</Text>
        </View>}
      </View>
    </View>
  );
}

function TimelineStrip({ dashas, selected, onSelect }: { dashas:any[];selected:number;onSelect:(i:number)=>void }) {
  const C = useC();
  return (
    <View>
      <Text style={{ color: C.textDim, fontSize: 9, fontFamily: F.bold, letterSpacing: 1.5 }}>MAHADASHA TIMELINE</Text>
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginTop:8}}>
        <View style={s.timelineRow}>
          {dashas.map((d,i) => {
            const active=isNow(d.startDate,d.endDate), sel=i===selected, color=hue(d.planet);
            return (
              <Pressable key={i} onPress={() => {Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);onSelect(i);}}
                style={[s.timelineChip,{backgroundColor:sel?`${color}1a`:C.bgCard,borderColor:sel?color:C.border}]}>
                <Text style={{color:sel?color:C.textMuted, fontSize: 12, fontFamily: F.bold}}>{d.planet.slice(0,2)}</Text>
                {active && <View style={[s.timelineDot,{backgroundColor:color}]}/>}
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
    const ai=subs.findIndex((s:any)=>tsOf(s.startDate)<=now&&tsOf(s.endDate)>now);
    setAntarIdx(ai>=0?ai:0);
  }
  const maha=kundli.dashas[mahaIdx];
  const subDashas=maha?.subDashas??[];
  const antar=subDashas[antarIdx];
  const pratyantars=antar?calcPratyantar(antar):[];
  const pratyantar=pratyantars[pratIdx]??pratyantars[0];
  return (
    <View style={{gap:16}}>
      {maha && <DashaCard level="Mahadasha" planet={maha.planet} startDate={maha.startDate} endDate={maha.endDate}
        active={isNow(maha.startDate,maha.endDate)}
        onPrev={()=>changeMaha(mahaIdx-1)} onNext={()=>changeMaha(mahaIdx+1)}
        hasPrev={mahaIdx>0} hasNext={mahaIdx<kundli.dashas.length-1} />}
      {antar && <DashaCard level="Antardasha" planet={antar.planet} startDate={antar.startDate} endDate={antar.endDate}
        active={isNow(antar.startDate,antar.endDate)}
        onPrev={()=>setAntarIdx(antarIdx-1)} onNext={()=>setAntarIdx(antarIdx+1)}
        hasPrev={antarIdx>0} hasNext={antarIdx<subDashas.length-1} />}
      {pratyantar && <DashaCard level="Pratyantardasha" planet={pratyantar.planet} startDate={pratyantar.startDate} endDate={pratyantar.endDate}
        active={isNow(pratyantar.startDate,pratyantar.endDate)}
        onPrev={()=>setPratIdx(pratIdx-1)} onNext={()=>setPratIdx(pratIdx+1)}
        hasPrev={pratIdx>0} hasNext={pratIdx<pratyantars.length-1} showNextBtn={false} />}
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
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const { BAVS, SAV } = useMemo(() => computeBAV(kundli), [kundli]);
  const [selPlanet, setSelPlanet] = useState("SAV");
  const PLANETS = ["SAV","Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
  const scores = selPlanet === "SAV" ? SAV : (BAVS[selPlanet] ?? Array(12).fill(0));
  const maxScore = selPlanet === "SAV" ? 56 : 8;
  const total = scores.reduce((a:number,b:number)=>a+b,0);

  return (
    <View style={{gap:14}}>
      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ color: ac, fontSize: 12, fontFamily: F.bold }}>Ashtakavarga kya hai?</Text>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.regular, lineHeight: 19 }}>
          Har grah 8 sthanon (swayam + 7 graha) se 12 rashiyon ko benefic/malefic points deta hai.
          SAV (Sarvashtakavarga) = sabhi 7 grahas ka total. Zyada points = stronger rashi.
        </Text>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={{flexDirection:"row",gap:6}}>
          {PLANETS.map(p => {
            const sel = p===selPlanet;
            const color = p==="SAV" ? ac : hue(p);
            return (
              <Pressable key={p} onPress={()=>{setSelPlanet(p);Haptics.selectionAsync();}}
                style={[tb.planetBtn,{ backgroundColor: C.bgCard, borderColor: C.border }, sel && {backgroundColor:`${color}15`,borderColor:`${color}40`}]}>
                <Text style={{color:sel?color:C.textMuted, fontSize: 11, fontFamily: F.bold}}>{p==="SAV"?"SAV":p.slice(0,3)}</Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      <View style={{flexDirection:"row",alignItems:"center",justifyContent:"space-between"}}>
        <Text style={{color:C.text,fontSize:14,fontFamily:F.bold}}>
          {selPlanet === "SAV" ? "Sarvashtakavarga" : `${selPlanet} BAV`}
        </Text>
        <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.medium}}>Total: {total}/{selPlanet==="SAV"?336:56}</Text>
      </View>

      <View style={tb.rashiGrid}>
        {RASHIS_HI.map((rashi,i) => {
          const score = scores[i] ?? 0;
          const pct   = score / maxScore;
          const color = pct >= 0.7 ? "#22c55e" : pct >= 0.5 ? "#fbbf24" : pct >= 0.3 ? "#f97316" : "#ef4444";
          return (
            <View key={i} style={[tb.rashiCell,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
              <Text style={{color: C.textMuted, fontSize: 9, fontFamily: F.bold, textAlign: "center"}}>{rashi}</Text>
              <Text style={{color, fontSize: 18, fontFamily: F.bold}}>{score}</Text>
              <View style={[tb.rashiBar,{ backgroundColor: C.bgCard2 }]}>
                <View style={[tb.rashiBarFill,{width:`${Math.round(pct*100)}%` as any,backgroundColor:color}]}/>
              </View>
              <Text style={{color, fontSize: 8, fontFamily: F.bold, letterSpacing: 0.5}}>
                {pct>=0.7?"Uchh":pct>=0.5?"Shubh":pct>=0.3?"Madhyam":"Neech"}
              </Text>
            </View>
          );
        })}
      </View>

      <View style={tb.legend}>
        {[["#22c55e","7-8 (Uchh)"],["#fbbf24","5-6 (Shubh)"],["#f97316","3-4 (Madhyam)"],["#ef4444","0-2 (Neech)"]].map(([c,l])=>(
          <View key={l} style={{flexDirection:"row",alignItems:"center",gap:5}}>
            <View style={{width:8,height:8,borderRadius:4,backgroundColor:c as string}}/>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:F.medium}}>{l}</Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const TARA_DATA = [
  { name:"Janma",       nameHindi:"जन्म",       type:"neutral", color:"#94a3b8", desc:"Karmic identity — the foundation of the birth chart" },
  { name:"Sampat",      nameHindi:"सम्पत",       type:"good",    color:"#22c55e", desc:"Wealth, prosperity, and happiness" },
  { name:"Vipat",       nameHindi:"विपत",        type:"bad",     color:"#ef4444", desc:"Obstacles, disruptions, difficulties" },
  { name:"Kshema",      nameHindi:"क्षेम",       type:"good",    color:"#4ade80", desc:"Health, security, and well-being" },
  { name:"Pratyak",     nameHindi:"प्रत्यक",     type:"bad",     color:"#f97316", desc:"Opposition, blockages, resistance" },
  { name:"Sadhana",     nameHindi:"साधना",       type:"good",    color:"#34d399", desc:"Efforts bear fruit, discipline rewarded" },
  { name:"Naidhana",    nameHindi:"नैधन",        type:"bad",     color:"#dc2626", desc:"Highly harmful — proceed with caution" },
  { name:"Mitra",       nameHindi:"मित्र",       type:"good",    color:"#60a5fa", desc:"Friendship, cooperation, support received" },
  { name:"Paramamitra", nameHindi:"परममित्र",    type:"great",   color:"#a78bfa", desc:"Highly auspicious — supreme well-wisher" },
];

function computeNavatara(kundli: KundliData) {
  const moonNakIdx = NAKSHATRAS.indexOf(kundli.nakshatra ?? "");
  if (moonNakIdx < 0) return [];
  const coreplanets = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];
  return coreplanets.map(name => {
    const p = kundli.planets.find(pl => pl.name === name);
    const lon = p?.longitude ?? 0;
    const pNakIdx = Math.floor(lon / (360/27)) % 27;
    const count   = ((pNakIdx - moonNakIdx + 27) % 27);
    const taraNum = (count % 9);
    const tara    = TARA_DATA[taraNum];
    return { planet: name, nakIdx: pNakIdx, nakName: NAKSHATRAS[pNakIdx], taraNum: taraNum + 1, tara };
  });
}

function NavataraTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const data = useMemo(() => computeNavatara(kundli), [kundli]);
  const moonNak = kundli.nakshatra ?? "?";

  return (
    <View style={{gap:14}}>
      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ color: ac, fontSize: 12, fontFamily: F.bold }}>What is Navatara?</Text>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.regular, lineHeight: 19 }}>
          Starting from the Moon's nakshatra, all 27 nakshatras are grouped into 9-star cycles called Tara.
          Janma, Sampat, Kshema, Sadhana, Mitra, Paramamitra — auspicious; Vipat, Pratyak, Naidhana — inauspicious.
        </Text>
      </View>

      <View style={{flexDirection:"row",alignItems:"center",gap:8,
        backgroundColor:`${ac}0a`,borderRadius:10,padding:10,
        borderWidth:1,borderColor:`${ac}22`}}>
        <Text style={{fontSize:16}}>🌙</Text>
        <View>
          <Text style={{color:C.textDim,fontSize:9,fontFamily:F.bold,letterSpacing:1.5}}>CHANDRA NAKSHATRA (BASE)</Text>
          <Text style={{color:C.text,fontSize:14,fontFamily:F.bold,marginTop:2}}>{moonNak}</Text>
        </View>
      </View>

      <ScrollView horizontal showsHorizontalScrollIndicator={false}>
        <View style={{flexDirection:"row",gap:6}}>
          {TARA_DATA.map((t2,i) => (
            <View key={i} style={[tb.taraChip,{borderColor:`${t2.color}30`,backgroundColor:`${t2.color}08`}]}>
              <Text style={{fontSize:9,fontFamily:F.bold,color:t2.color}}>{i+1}</Text>
              <Text style={{fontSize:9,fontFamily:F.medium,color:t2.color}}>{t2.name.slice(0,6)}</Text>
            </View>
          ))}
        </View>
      </ScrollView>

      <View style={{gap:10}}>
        {data.map(({ planet, nakName, taraNum, tara }) => (
          <View key={planet} style={[tb.taraCard,{borderColor:`${tara.color}25`,backgroundColor:`${tara.color}06`}]}>
            <View style={[tb.taraIcon,{backgroundColor:`${hue(planet)}15`}]}>
              <Text style={{color:hue(planet),fontSize:12,fontFamily:F.bold}}>{planet.slice(0,2)}</Text>
            </View>
            <View style={{flex:1}}>
              <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
                <Text style={{color:C.text,fontSize:13,fontFamily:F.bold}}>{pName(planet)}</Text>
                <View style={[tb.taraBadge,{backgroundColor:`${tara.color}15`}]}>
                  <Text style={{color:tara.color,fontSize:9,fontFamily:F.bold}}>{taraNum}. {tara.name}</Text>
                </View>
              </View>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium,marginTop:2}}>
                Nakshatra: {nakName}
              </Text>
              <Text style={{color:tara.color,fontSize:11,fontFamily:F.medium,marginTop:2}}>{tara.desc}</Text>
            </View>
            <Text style={{fontSize:16}}>
              {tara.type==="great"?"⭐":tara.type==="good"?"✅":tara.type==="bad"?"⚠️":"🔵"}
            </Text>
          </View>
        ))}
      </View>
    </View>
  );
}

const KARAKA_DEFS = [
  { key:"AK",  name:"Atmakaraka",    nameHindi:"आत्मकारक",   desc:"Aatma, soul, jeevana ka uddeshya",    color:"#f59e0b" },
  { key:"AmK", name:"Amatyakaraka",  nameHindi:"अमात्यकारक", desc:"Career, mind, mantri, authority",     color:"#22c55e" },
  { key:"BK",  name:"Bhratrukaraka", nameHindi:"भ्रातृकारक", desc:"Bhai-behan, courage, mentors",        color:"#ef4444" },
  { key:"MK",  name:"Matrakaraka",   nameHindi:"मातृकारक",   desc:"Mata, griha sukh, emotions",          color:"#94a3b8" },
  { key:"PK",  name:"Putrakaraka",   nameHindi:"पुत्रकारक",  desc:"Santaan, creativity, intelligence",   color:"#ec4899" },
  { key:"GK",  name:"Gnatikaraka",   nameHindi:"ज्ञातिकारक", desc:"Karyasthali, shatru, competition",    color:"#a78bfa" },
  { key:"DK",  name:"Darakaraka",    nameHindi:"दारकारक",    desc:"Life partner, vivah, relationships",  color:"#f59e0b" },
];

function computeChara(kundli: KundliData) {
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn"];
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
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const data = useMemo(() => computeChara(kundli), [kundli]);
  const ak   = data[0];

  return (
    <View style={{gap:14}}>
      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ color: ac, fontSize: 12, fontFamily: F.bold }}>Jaimini Chara Karakas kya hain?</Text>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.regular, lineHeight: 19 }}>
          Jaimini Jyotish mein 7 grahas ko unke rashi-degree ke anusaar karak roles milte hain.
          Sabse zyada degree wala graha Atmakaraka (soul indicator) hota hai.
          Rahu ki degree ulti ginee jaati hai (30 - deg).
        </Text>
      </View>

      {ak && (
        <View style={[tb.akCard,{ backgroundColor: C.bgCard, borderColor:`${hue(ak.name)}40`}]}>
          <View style={{flexDirection:"row",alignItems:"center",gap:12}}>
            <View style={[tb.akPlanet,{backgroundColor:`${hue(ak.name)}15`,borderColor:`${hue(ak.name)}30`}]}>
              <Text style={{color:hue(ak.name),fontSize:20,fontFamily:F.bold}}>{ak.name.slice(0,2)}</Text>
            </View>
            <View>
              <Text style={{color:C.textDim,fontSize:10,fontFamily:F.bold,letterSpacing:1.5}}>ATMAKARAKA</Text>
              <Text style={{color:C.text,fontSize:18,fontFamily:F.bold,marginTop:2}}>{pName(ak.name)}</Text>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium,marginTop:3}}>{ak.karaka?.desc}</Text>
            </View>
          </View>
          <Text style={{color:C.textDim,fontSize:11,fontFamily:F.medium,marginTop:8}}>
            Degree within sign: {ak.deg.toFixed(2)}° — highest in chart
          </Text>
        </View>
      )}

      <View style={{gap:8}}>
        {data.map(({ name, deg, karaka }) => {
          if (!karaka) return null;
          const color = karaka.color;
          return (
            <View key={name} style={[tb.karakaRow,{ backgroundColor: C.bgCard, borderColor:`${color}20`}]}>
              <View style={[tb.karakaRank,{backgroundColor:`${color}15`}]}>
                <Text style={{color,fontSize:11,fontFamily:F.bold}}>{karaka.key}</Text>
              </View>
              <View style={{flex:1}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:13,fontFamily:F.bold}}>{pName(name)}</Text>
                  <Text style={{color:C.textDim,fontSize:10,fontFamily:F.medium}}>({deg.toFixed(1)}°)</Text>
                </View>
                <Text style={{color,fontSize:11,fontFamily:F.semibold}}>{karaka.name} · {karaka.nameHindi}</Text>
                <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium,marginTop:1}}>{karaka.desc}</Text>
              </View>
            </View>
          );
        })}
      </View>

      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor:"rgba(167,139,250,0.2)"}]}>
        <Text style={{color:"#a78bfa",fontSize:12,fontFamily:F.bold,marginBottom:4}}>Jaimini Lagna</Text>
        <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.regular,lineHeight:19}}>
          Atmakaraka ki rashi se special Jaimini Lagna banta hai. AK ki navamsha position
          jeeva ka spiritual path dikhati hai. Full analysis ke liye jyotishi se milein.
        </Text>
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
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const transits = useMemo(() => approxTransit(), []);
  const ascRashi = Math.floor((kundli.ascendantDeg ?? 0) / 30) % 12;
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];

  return (
    <View style={{gap:14}}>
      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor: C.warningBorder }]}>
        <Text style={{color: C.warningText, fontSize:11, fontFamily: F.bold, marginBottom:3}}>⚠️ Approximate Transit</Text>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.regular, lineHeight: 19 }}>
          Yeh transits mean orbital motion se computed hain — broad guidance ke liye useful.
          Exact transits ke liye Ephemeris ya jyotishi se confirm karein.
        </Text>
      </View>

      {moonRashi && (
        <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor:`${ac}30`}]}>
          <Text style={{color:C.textDim,fontSize:9,fontFamily:F.bold,letterSpacing:1.5}}>LIVE — CHANDRA TRANSIT (API)</Text>
          <Text style={{color:C.text,fontSize:14,fontFamily:F.bold,marginTop:4}}>
            {moonRashi.name} · Bhav {((moonRashi.index - ascRashi + 12)%12)+1}
          </Text>
          <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium,marginTop:2}}>Nakshatra: {moonRashi.nakshatra}</Text>
        </View>
      )}

      <Text style={{color:ac,fontSize:10,fontFamily:F.bold,letterSpacing:2.5}}>GRAHA TRANSIT (AAJKAL)</Text>
      <View style={{gap:8}}>
        {CORE.map(name => {
          const lon     = transits[name] ?? 0;
          const rashi   = Math.floor(lon / 30) % 12;
          const deg     = (lon % 30).toFixed(1);
          const house   = ((rashi - ascRashi + 12) % 12) + 1;
          const nIdx    = Math.floor(lon / (360/27)) % 27;
          const nakName = NAKSHATRAS[nIdx];
          const pHue    = hue(name);

          const natal   = kundli.planets.find(p => p.name === name);
          const natalR  = natal ? Math.floor(natal.longitude/30)%12 : -1;
          const isConj  = natalR === rashi && natalR >= 0;

          return (
            <View key={name} style={[tb.transitRow,{ backgroundColor: C.bgCard, borderColor: C.border },isConj&&{borderColor:`${pHue}40`,backgroundColor:`${pHue}05`}]}>
              <View style={[tb.transitIcon,{backgroundColor:`${pHue}15`}]}>
                <Text style={{color:pHue,fontSize:11,fontFamily:F.bold}}>{name.slice(0,2)}</Text>
              </View>
              <View style={{flex:1}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:13,fontFamily:F.bold}}>{pName(name)}</Text>
                  {isConj && <View style={{backgroundColor:`${pHue}20`,borderRadius:6,paddingHorizontal:5,paddingVertical:1}}>
                    <Text style={{color:pHue,fontSize:8,fontFamily:F.bold}}>NATAL CONJ</Text>
                  </View>}
                </View>
                <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium,marginTop:2}}>
                  {RASHIS_HI[rashi]} · Bhav {house} · {nakName}
                </Text>
              </View>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:F.medium}}>{deg}°</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

function getKPLords(longitude: number): { nakName:string; starLord:string; subLord:string; subSubLord:string } {
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
  return { nakName:NAKSHATRAS[nakIdx], starLord, subLord, subSubLord };
}

function KPTab({ kundli }: { kundli: KundliData }) {
  const C = useC();
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";
  const CORE = ["Sun","Moon","Mars","Mercury","Jupiter","Venus","Saturn","Rahu","Ketu"];
  const ascLon = kundli.ascendantDeg ?? 0;
  const kpData = useMemo(() => {
    const rows: Array<{name:string;lon:number;kp:ReturnType<typeof getKPLords>}> = [];
    rows.push({ name:"Ascendant", lon:ascLon, kp:getKPLords(ascLon) });
    for (const name of CORE) {
      const p = kundli.planets.find(pl => pl.name === name);
      if (p) rows.push({ name, lon:p.longitude, kp:getKPLords(p.longitude) });
    }
    return rows;
  }, [kundli]);

  return (
    <View style={{gap:14}}>
      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor: C.border }]}>
        <Text style={{ color: ac, fontSize: 12, fontFamily: F.bold }}>What is KP Paddhati?</Text>
        <Text style={{ color: C.textMuted, fontSize: 12, fontFamily: F.regular, lineHeight: 19 }}>
          Krishnamurti Paddhati (KP) calculates the Star-lord (Nakshatra Lord) and Sub-lord for each planet and ascendant.
          It uses proportional sub-divisions of Vimshottari dasha for precision — widely regarded as highly accurate for event timing.
        </Text>
      </View>

      <Text style={{color:ac,fontSize:10,fontFamily:F.bold,letterSpacing:2.5}}>STAR-LORD · SUB-LORD · SUB-SUB-LORD</Text>

      <View style={{gap:8}}>
        {kpData.map(({ name, lon, kp }) => {
          const isAsc = name === "Ascendant";
          const pHue  = isAsc ? ac : hue(name);
          return (
            <View key={name} style={[tb.kpRow,{ backgroundColor: C.bgCard, borderColor:`${pHue}20`}]}>
              <View style={[tb.kpIcon,{backgroundColor:`${pHue}12`}]}>
                <Text style={{color:pHue,fontSize:10,fontFamily:F.bold}}>
                  {isAsc?"Asc":name.slice(0,2)}
                </Text>
              </View>
              <View style={{flex:1,gap:3}}>
                <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                  <Text style={{color:C.text,fontSize:12,fontFamily:F.bold}}>
                    {isAsc?"Ascendant":pName(name)}
                  </Text>
                  <Text style={{color:C.textDim,fontSize:10,fontFamily:F.medium}}>{(lon%30).toFixed(2)}° {kp.nakName}</Text>
                </View>
                <View style={{flexDirection:"row",gap:6,flexWrap:"wrap"}}>
                  <KPLordChip label="Star" lord={kp.starLord}/>
                  <KPLordChip label="Sub" lord={kp.subLord}/>
                  <KPLordChip label="Sub-Sub" lord={kp.subSubLord}/>
                </View>
              </View>
            </View>
          );
        })}
      </View>

      <View style={[tb.infoBox,{ backgroundColor: C.bgCard, borderColor:"rgba(167,139,250,0.2)"}]}>
        <Text style={{color:"#a78bfa",fontSize:12,fontFamily:F.bold,marginBottom:4}}>KP Significators</Text>
        <Text style={{color:C.textMuted,fontSize:12,fontFamily:F.regular,lineHeight:19}}>
          Kisi bhi ghatna ke liye dekhen: Star-lord aur Sub-lord ka relationship aur unke
          nakshatra se kaunse bhav connected hain. Agar 3 lord agree karein → event pakka.
        </Text>
      </View>
    </View>
  );
}

function KPLordChip({ label, lord }: { label:string; lord:string }) {
  const C = useC();
  const color = hue(lord);
  return (
    <View style={[tb.kpChip,{backgroundColor:`${color}10`,borderColor:`${color}25`}]}>
      <Text style={{color:C.textMuted,fontSize:8,fontFamily:F.medium}}>{label}: </Text>
      <Text style={{color,fontSize:9,fontFamily:F.bold}}>{lord}</Text>
    </View>
  );
}

const CHART_BTNS = [
  { label:"Kundli ✦",    tab:"Kundli",       gold:false },
  { label:"Ashtakavarga",tab:"Ashtakavarga", gold:false },
  { label:"Navatara",    tab:"Navatara",     gold:false },
  { label:"Jaimini",     tab:"Jaimini",      gold:false },
  { label:"Transit",     tab:"Transit",      gold:false },
  { label:"KP ✦",        tab:"KP",           gold:true  },
];

export default function KundliScreen() {
  const insets = useSafeAreaInsets();
  const C = useC();
  const { kundli, language } = useUser();
  const tI18n = getT(language);
  const topPad = Platform.OS === "web" ? 67 : insets.top;
  const botPad = Platform.OS === "web" ? 34 : insets.bottom;
  const ac = C.isDark ? "#f59e0b" : "#7C3AED";

  const [activeTab, setActiveTab] = useState("Kundli");
  const [mahaIdx,   setMahaIdx]   = useState(0);
  const [antarIdx,  setAntarIdx]  = useState(0);
  const [pratIdx,   setPratIdx]   = useState(0);
  const [moonRashi, setMoonRashi] = useState<any>(null);

  useEffect(() => {
    apiFetch(`${BASE_URL}/api/moon_transit`)
      .then(r => r.json())
      .then(d => {
        if (typeof d.rashiIndex === "number") {
          const nakIdx = Math.floor(d.longitude / (360/27)) % 27;
          setMoonRashi({ index:d.rashiIndex, name:d.rashiName, nakshatra:NAKSHATRAS[nakIdx], longitude:d.longitude });
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
        <View style={s.emptyWrap}>
          <View style={[s.emptyIcon, { borderColor: `${ac}40`, backgroundColor: `${ac}07` }]}>
            <Feather name="star" size={32} color={ac}/>
          </View>
          <Text style={[s.emptyTitle, { color: C.text }]}>{tI18n.noKundli}</Text>
          <Text style={[s.emptySub, { color: C.textMuted }]}>{tI18n.noKundliSub}</Text>
          <Pressable style={({pressed})=>[s.emptyBtn, { backgroundColor: C.accent },pressed&&{opacity:0.8}]}
            onPress={()=>{Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);router.push("/onboarding");}}>
            <Text style={[s.emptyBtnText, { color: "#fff" }]}>{tI18n.createKundli}</Text>
            <Feather name="arrow-right" size={15} color="#fff"/>
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
  const snapshotRows = [
    { label:"ASCENDANT (LAGNA)",  value:kundli.ascendant },
    { label:"MOON SIGN (RASHI)",  value:kundli.moonSign },
    ...(kundli.nakshatra?[{ label:"NAKSHATRA", value:`${kundli.nakshatra} (Pada ${kundli.nakshatraPada??"?"})` }]:[]),
    ...(kundli.nakshatraRuler?[{ label:"NAKSHATRA LORD", value:kundli.nakshatraRuler }]:[]),
    ...(dbText?[{ label:"DASHA BALANCE", value:dbText }]:[]),
    ...(moonTransitText?[{ label:"LIVE MOON TRANSIT", value:moonTransitText }]:[]),
  ];

  return (
    <CosmicBg>
    <ScrollView style={s.root}
      contentContainerStyle={[s.content,{paddingTop:topPad+16,paddingBottom:botPad+100}]}
      showsVerticalScrollIndicator={false}>

      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{marginBottom:16}}>
        <View style={s.chartBtnRow}>
          {CHART_BTNS.map(({ label, tab, gold }) => {
            const active = activeTab === tab;
            const goldColor = C.isDark ? "#facc15" : "#B45309";
            return (
              <Pressable key={tab}
                onPress={() => { setActiveTab(tab); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
                style={[s.chartBtn, { backgroundColor: C.bgCard, borderColor: C.border },
                  gold && { borderColor: `${goldColor}40` },
                  active && { backgroundColor:`${ac}12`, borderColor:`${ac}55` }]}>
                <Text style={[{ color: C.textDim, fontSize: 11, fontFamily: F.bold, letterSpacing: 0.5 },
                  gold && { color: goldColor },
                  active && { color: ac }]}>
                  {label}
                </Text>
              </Pressable>
            );
          })}
        </View>
      </ScrollView>

      <View style={[s.snapshotCard, { backgroundColor: C.bgCard, borderColor: C.border }]}>
        {snapshotRows.map(({ label, value }, idx) => (
          <View key={label} style={[s.snapshotRow, { borderBottomColor: C.border }, idx === snapshotRows.length - 1 && { borderBottomWidth: 0 }]}>
            <Text style={{ color: C.textDim, fontSize: 10, fontFamily: F.bold, letterSpacing: 0.8, flex: 1 }}>{label}</Text>
            <Text style={{ color: C.text, fontSize: 12, fontFamily: F.medium, flex: 1, textAlign: "right" }} numberOfLines={1}>{value}</Text>
          </View>
        ))}
      </View>

      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); router.push("/planet-position"); }}
        style={({ pressed }) => [s.linkBtn, { borderColor: C.border, backgroundColor: C.bgCard }, pressed && { opacity: 0.75, transform: [{ scale: 0.98 }] }]}
      >
        <View style={s.linkBtnLeft}>
          <View style={[s.linkBtnIcon, { backgroundColor: C.bgCard2, borderColor: C.border }]}>
            <Feather name="target" size={16} color={C.textMid} />
          </View>
          <View>
            <Text style={{ color: C.text, fontSize: 13, fontFamily: F.bold }}>Planet Position</Text>
            <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium, marginTop: 1 }}>Live graha degrees aur rashi</Text>
          </View>
        </View>
        <Feather name="chevron-right" size={16} color={C.textMuted} />
      </Pressable>

      <Pressable
        onPress={() => { Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium); router.push("/daily-alerts"); }}
        style={({ pressed }) => [s.linkBtn, { borderColor: `${ac}30`, backgroundColor: `${ac}06` }, pressed && { opacity: 0.75, transform: [{ scale: 0.98 }] }]}
      >
        <View style={s.linkBtnLeft}>
          <View style={[s.linkBtnIcon, { backgroundColor: `${ac}10`, borderColor: `${ac}20` }]}>
            <Feather name="bell" size={16} color={ac} />
          </View>
          <View>
            <Text style={{ color: ac, fontSize: 13, fontFamily: F.bold }}>Daily Alerts</Text>
            <Text style={{ color: C.textMuted, fontSize: 10, fontFamily: F.medium, marginTop: 1 }}>4-day planetary guidance · आज का संकेत</Text>
          </View>
        </View>
        <Feather name="chevron-right" size={16} color={ac} style={{ opacity: 0.7 }} />
      </Pressable>

      <Text style={{ color: ac, fontSize: 10, fontFamily: F.bold, letterSpacing: 2.5 }}>
        {activeTab==="Kundli"?"DASHA TIMELINE"
          :activeTab==="Ashtakavarga"?"ASHTAKAVARGA — BINNASHTAKAVARGA"
          :activeTab==="Navatara"?"NAVATARA — 9 TARA SYSTEM"
          :activeTab==="Jaimini"?"JAIMINI — CHARA KARAKAS"
          :activeTab==="Transit"?"GRAHA TRANSIT (AAJKAL)"
          :"KP — STAR · SUB · SUB-SUB LORD"}
      </Text>

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

const s = StyleSheet.create({
  root:    { flex:1 },
  content: { paddingHorizontal:16, gap:16 },

  emptyWrap: { flex:1, alignItems:"center", paddingHorizontal:24, gap:14, paddingTop:60 },
  emptyIcon: { width:80,height:80,borderRadius:40,borderWidth:1,alignItems:"center",justifyContent:"center" },
  emptyTitle: { fontSize:20,fontFamily:F.bold,textAlign:"center" },
  emptySub:   { fontSize:13,fontFamily:F.regular,lineHeight:20,textAlign:"center" },
  emptyBtn: { flexDirection:"row",alignItems:"center",gap:8,paddingVertical:13,paddingHorizontal:24,borderRadius:14,marginTop:4 },
  emptyBtnText: { fontFamily:F.bold,fontSize:14 },

  chartBtnRow: { flexDirection:"row",gap:8 },
  chartBtn: { paddingVertical:9,paddingHorizontal:13,borderRadius:11,borderWidth:1.5 },

  snapshotCard: { borderRadius:16,borderWidth:1,padding:14,gap:0 },
  snapshotRow:  { flexDirection:"row",justifyContent:"space-between",alignItems:"flex-start",paddingVertical:8,borderBottomWidth:1 },

  linkBtn: {
    flexDirection:"row", alignItems:"center", justifyContent:"space-between",
    borderRadius:14, borderWidth:1, paddingVertical:12, paddingHorizontal:14,
  },
  linkBtnLeft: { flexDirection:"row", alignItems:"center", gap:12 },
  linkBtnIcon: {
    width:36, height:36, borderRadius:10,
    borderWidth:1, alignItems:"center", justifyContent:"center",
  },

  navRow:  { flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:8 },
  navBtn:  { paddingVertical:6,paddingHorizontal:12,borderRadius:8 },
  navBtnText: { fontSize:11,fontFamily:F.semibold },
  levelLabel: { fontSize:10,fontFamily:F.bold,letterSpacing:1.5 },
  dashaCard: { borderRadius:16,borderWidth:1.5,padding:16,gap:6 },
  dashaHeader: { flexDirection:"row",justifyContent:"space-between",alignItems:"center" },
  dashaPlanetName: { fontSize:22,fontFamily:F.bold },
  activeBadge:     { paddingVertical:3,paddingHorizontal:10,borderRadius:20 },
  activeBadgeText: { fontSize:11,fontFamily:F.bold },
  progBg:   { height:3,borderRadius:2,overflow:"hidden" },
  progFill: { height:"100%",borderRadius:2 },
  timelineRow:   { flexDirection:"row",gap:8,paddingBottom:4 },
  timelineChip: { minWidth:44,paddingVertical:8,paddingHorizontal:8,borderRadius:12,borderWidth:1.5,alignItems:"center" },
  timelineDot: { width:6,height:6,borderRadius:3,marginTop:3 },
});

const tb = StyleSheet.create({
  infoBox: { borderRadius:12,borderWidth:1,padding:12,gap:5 },
  planetBtn: { paddingVertical:8,paddingHorizontal:12,borderRadius:10,borderWidth:1 },
  rashiGrid: { flexDirection:"row",flexWrap:"wrap",gap:8 },
  rashiCell: { width:"23%" as any,borderRadius:10,borderWidth:1,padding:8,gap:4,alignItems:"center" },
  rashiBar: { width:"100%",height:3,borderRadius:2,overflow:"hidden" },
  rashiBarFill: { height:3,borderRadius:2 },
  legend: { flexDirection:"row",flexWrap:"wrap",gap:10,justifyContent:"center" },
  taraChip: { borderWidth:1,borderRadius:8,paddingHorizontal:8,paddingVertical:5,alignItems:"center",gap:2 },
  taraCard: { flexDirection:"row",alignItems:"flex-start",gap:10,borderWidth:1,borderRadius:12,padding:12 },
  taraIcon: { width:36,height:36,borderRadius:10,alignItems:"center",justifyContent:"center",flexShrink:0 },
  taraBadge: { borderRadius:8,paddingHorizontal:7,paddingVertical:2 },
  akCard: { borderRadius:14,borderWidth:1,padding:14 },
  akPlanet: { width:52,height:52,borderRadius:14,alignItems:"center",justifyContent:"center",borderWidth:1,flexShrink:0 },
  karakaRow: { flexDirection:"row",alignItems:"flex-start",gap:10,borderRadius:12,borderWidth:1,padding:12 },
  karakaRank: { width:40,height:40,borderRadius:10,alignItems:"center",justifyContent:"center",flexShrink:0 },
  transitRow: { flexDirection:"row",alignItems:"center",gap:10,borderRadius:12,borderWidth:1,padding:11 },
  transitIcon: { width:34,height:34,borderRadius:10,alignItems:"center",justifyContent:"center",flexShrink:0 },
  kpRow:  { flexDirection:"row",alignItems:"flex-start",gap:10,borderRadius:12,borderWidth:1,padding:11 },
  kpIcon: { width:36,height:36,borderRadius:10,alignItems:"center",justifyContent:"center",flexShrink:0 },
  kpChip: { flexDirection:"row",alignItems:"center",borderWidth:1,borderRadius:6,paddingHorizontal:6,paddingVertical:3 },
});
