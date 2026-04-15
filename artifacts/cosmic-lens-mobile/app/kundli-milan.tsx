import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useState } from "react";
import {
  ActivityIndicator, KeyboardAvoidingView, Platform,
  Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

// ── Data Tables ───────────────────────────────────────────────────────────────
const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];
const RASHIS = ["Mesh","Vrishabh","Mithun","Kark","Simha","Kanya","Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen"];
const ENGLISH_TO_RASHI: Record<string,string> = {
  "Aries":"Mesh","Taurus":"Vrishabh","Gemini":"Mithun","Cancer":"Kark",
  "Leo":"Simha","Virgo":"Kanya","Libra":"Tula","Scorpio":"Vrishchik",
  "Sagittarius":"Dhanu","Capricorn":"Makar","Aquarius":"Kumbh","Pisces":"Meen",
};
const NADI      = [0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2];
const NADI_NAMES= ["Vata (Adi)","Pitta (Madhya)","Kapha (Antya)"];
const GANA      = [0,1,2,1,0,1,0,0,2,2,1,1,0,2,0,2,0,2,2,1,1,0,1,2,1,1,0];
const GANA_NAMES= ["Dev","Manushya","Raksha"];
const VARNA     = [1,2,3,0,1,2,3,0,1,2,3,0];
const YONI      = [0,1,2,3,4,5,6,7,8,9,10,2,11,12,13,14,14,13,5,12,11,10,3,7,4,9,0];
const YONI_ENEMIES:[number,number][] = [[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,0]];
const RASHI_LORD= [2,5,3,1,0,3,5,2,4,6,6,4];
const PLN_FRIEND: number[][] = [
  [1,2,2,1,2,0,0],[2,1,0,1,2,2,0],[2,0,1,1,2,0,2],
  [2,0,2,1,0,2,0],[2,1,2,1,1,0,0],[2,2,0,2,1,1,0],[0,0,2,2,2,0,1],
];

function isYoniEnemy(a:number,b:number){return YONI_ENEMIES.some(([x,y])=>(a===x&&b===y)||(a===y&&b===x));}
function getGrahaMaitri(r1:number,r2:number):number{
  const l1=RASHI_LORD[r1]??0,l2=RASHI_LORD[r2]??0;
  if(l1>=PLN_FRIEND.length||l2>=PLN_FRIEND.length)return 3;
  const ab=PLN_FRIEND[l1]?.[l2]??1,ba=PLN_FRIEND[l2]?.[l1]??1,t=ab+ba;
  return t>=4?5:t===3?4:t===2?3:0;
}
function getTara(n1:number,n2:number):number{
  const fwd=((n2-n1+27)%27)+1,rev=((n1-n2+27)%27)+1,bad=[3,5,7];
  return(!bad.includes(fwd%9||9)&&!bad.includes(rev%9||9))?3:(!bad.includes(fwd%9||9)||!bad.includes(rev%9||9))?1.5:0;
}
function getBhakut(r1:number,r2:number):number{
  const diff=Math.abs(r1-r2);
  return [[1,11],[4,8],[5,7]].some(([a,b])=>diff===a||diff===b)?0:7;
}
function getVasya(r1:number,r2:number):number{
  if(r1===r2)return 2;
  const groups=[[0,3,4],[1,6,7,9],[2,8],[5,10,11]];
  return groups.findIndex(g=>g.includes(r1))===groups.findIndex(g=>g.includes(r2))?2:1;
}

interface KootItem { score:number; max:number; label:string; detail:string; bad:boolean; }
interface AshtakootResult {
  nadi:KootItem; gana:KootItem; bhakut:KootItem; maitri:KootItem;
  yoni:KootItem; tara:KootItem; vasya:KootItem; varna:KootItem;
  total:number; manglikDosha:boolean;
}

function computeAshtakoot(n1:number,r1:number,mars1:boolean,n2:number,r2:number,mars2:boolean):AshtakootResult{
  const nad1=NADI[n1]??0,nad2=NADI[n2]??0,nadiScore=nad1!==nad2?8:0;
  const g1=GANA[n1]??0,g2=GANA[n2]??0;
  let ganaScore=6;
  if((g1===0&&g2===2)||(g1===2&&g2===0))ganaScore=1;
  else if((g1===1&&g2===2)||(g1===2&&g2===1))ganaScore=0;
  const bhakutScore=getBhakut(r1,r2),rashiDiff=((r2-r1+12)%12)+1;
  const maitriScore=getGrahaMaitri(r1,r2);
  const y1=YONI[n1]??0,y2=YONI[n2]??0,enemy=isYoniEnemy(y1,y2);
  const yoniScore=y1===y2?4:enemy?0:2;
  const taraScore=getTara(n1,n2);
  const vasya=getVasya(r1,r2);
  const v1=VARNA[r1]??0,v2=VARNA[r2]??0,varnaScore=v1<=v2?1:0;
  const total=nadiScore+ganaScore+bhakutScore+maitriScore+yoniScore+taraScore+vasya+varnaScore;
  return {
    nadi:  {score:nadiScore,  max:8,label:"Nadi",         detail:nadiScore===8?`${NADI_NAMES[nad1]} ≠ ${NADI_NAMES[nad2]}`:`Dono ${NADI_NAMES[nad1]}`, bad:nadiScore===0},
    gana:  {score:ganaScore,  max:6,label:"Gana",         detail:`${GANA_NAMES[g1]} + ${GANA_NAMES[g2]}`, bad:ganaScore===0},
    bhakut:{score:bhakutScore,max:7,label:"Bhakut",       detail:bhakutScore===7?`${rashiDiff}–${13-rashiDiff} Shubh`:`${rashiDiff}–${13-rashiDiff} Dosh`, bad:bhakutScore===0},
    maitri:{score:maitriScore,max:5,label:"Graha Maitri", detail:maitriScore>=4?"Graha Mitra":maitriScore>=3?"Sam":"Graha Shatru", bad:maitriScore<3},
    yoni:  {score:yoniScore,  max:4,label:"Yoni",         detail:yoniScore===4?"Sama Yoni":yoniScore===2?"Madhyam Yoni":"Vipat Yoni", bad:yoniScore===0},
    tara:  {score:taraScore,  max:3,label:"Tara",         detail:taraScore===3?"Shubh Tara":taraScore>0?"Madhyam Tara":"Vipat Tara", bad:taraScore===0},
    vasya: {score:vasya,      max:2,label:"Vasya",        detail:vasya===2?"Vasya Shubh":"Vasya Madhyam", bad:false},
    varna: {score:varnaScore, max:1,label:"Varna",        detail:varnaScore?"Varna Sahi":"Varna Anmatch", bad:varnaScore===0},
    total, manglikDosha:mars1!==mars2,
  };
}

function getGrade(total:number){
  if(total>=32)return{label:"Excellent",    emoji:"✨",colors:["#16a34a","#22c55e"] as const};
  if(total>=27)return{label:"Very Good",    emoji:"💚",colors:["#15803d","#4ade80"] as const};
  if(total>=21)return{label:"Average",      emoji:"💛",colors:["#b45309","#fbbf24"] as const};
  if(total>=18)return{label:"Below Average",emoji:"🟠",colors:["#c2410c","#f97316"] as const};
  return            {label:"Not Compatible",emoji:"🔴",colors:["#b91c1c","#ef4444"] as const};
}

const KOOT_ORDER = ["nadi","gana","bhakut","maitri","yoni","tara","vasya","varna"] as const;

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({total,color}:{total:number;color:string}){
  const R=68,circ=2*Math.PI*R,pct=total/36;
  return(
    <View style={{width:160,height:160,alignItems:"center",justifyContent:"center"}}>
      <Svg width={160} height={160} style={{position:"absolute"} as any}>
        <Circle cx={80} cy={80} r={R} fill="none" stroke="rgba(255,255,255,0.07)" strokeWidth={10}/>
        <Circle cx={80} cy={80} r={R} fill="none" stroke={color} strokeWidth={10}
          strokeLinecap="round"
          strokeDasharray={`${circ*pct} ${circ}`}
          rotation={-90} originX={80} originY={80}/>
      </Svg>
      <Text style={{fontSize:44,fontFamily:"Nunito_700Bold",color,lineHeight:50}}>{total}</Text>
      <Text style={{fontSize:13,color:"rgba(255,255,255,0.5)",fontFamily:"Nunito_500Medium"}}>out of 36</Text>
    </View>
  );
}

// ── Koot Row ──────────────────────────────────────────────────────────────────
function KootRow({k,accent}:{k:KootItem;accent:string}){
  const C=useC();
  const pct=k.max>0?k.score/k.max:0;
  const barColor=k.bad?"#ef4444":pct>=0.8?"#22c55e":pct>=0.5?"#fbbf24":"#f97316";
  return(
    <View style={[km.kootRow,{backgroundColor:C.bgCard,borderColor:k.bad?"rgba(239,68,68,0.3)":C.border}]}>
      <View style={{flexDirection:"row",justifyContent:"space-between",alignItems:"center",marginBottom:6}}>
        <View style={{flexDirection:"row",alignItems:"center",gap:7}}>
          {k.bad&&<View style={km.kootBadDot}/>}
          <Text style={[km.kootLabel,{color:C.text}]}>{k.label}</Text>
        </View>
        <Text style={[km.kootScore,{color:barColor}]}>{k.score}<Text style={{color:C.textDim,fontSize:10}}>/{k.max}</Text></Text>
      </View>
      <View style={[km.kootBarBg,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.06)"}]}>
        <View style={[km.kootBarFill,{width:`${Math.round(pct*100)}%` as any,backgroundColor:barColor}]}/>
      </View>
      <Text style={[km.kootDetail,{color:C.textMuted}]}>{k.detail}</Text>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function KundliMilanScreen(){
  const insets=useSafeAreaInsets();
  const C=useC();
  const topPad=Platform.OS==="web"?67:insets.top;
  const botPad=Platform.OS==="web"?34:insets.bottom;
  const {kundli:p1Kundli,profiles,primaryProfileId}=useUser();
  const p1Profile=profiles.find(p=>p.id===primaryProfileId);

  const [p2Name, setP2Name] =useState("");
  const [p2DOB,  setP2DOB]  =useState("");
  const [p2Time, setP2Time] =useState("");
  const [p2Place,setP2Place]=useState("");
  const [loading,setLoading]=useState(false);
  const [result, setResult] =useState<AshtakootResult|null>(null);
  const [error,  setError]  =useState("");

  const p1Nak    =NAKSHATRAS.indexOf(p1Kundli?.nakshatra??"");
  const p1RashiEn=p1Kundli?.moonSign??"";
  const p1RashiHi=ENGLISH_TO_RASHI[p1RashiEn]??"";
  const p1Rashi  =RASHIS.indexOf(p1RashiHi);
  const p1Mars   =(p1Kundli?.planets.find(p=>p.name==="Mars")?.house??0);
  const p1Manglik=[1,4,7,8,12].includes(p1Mars);

  async function handleCalculate(){
    if(!p1Kundli){setError("Please create your kundli from your profile first.");return;}
    if(!p2DOB||!p2Time||!p2Place){setError("Please fill all birth details for Person 2.");return;}
    setError("");setLoading(true);
    try{
      const[day,month,year]=p2DOB.split("/").map(Number);
      const[hourMin,ampm]=p2Time.trim().split(" ");
      const[h,m]=(hourMin??"").split(":").map(Number);
      if(!day||!month||!year||!h)throw new Error("Use format: DD/MM/YYYY  and  HH:MM AM");
      const res=await apiFetch(`${API_BASE}/api/kundli`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({name:p2Name||"Person 2",day,month,year,hour:h,minute:m,ampm:ampm??"AM",place:p2Place})});
      const json=await res.json();
      const p2Nak  =NAKSHATRAS.indexOf(json.nakshatra??"");
      const p2Rashi=RASHIS.indexOf(ENGLISH_TO_RASHI[json.moonSign??""]??"");
      const p2MarsH=(json.planets as any[]).find(p=>p.name==="Mars")?.house??0;
      const p2Manglik=[1,4,7,8,12].includes(p2MarsH);
      if(p2Nak<0||p2Rashi<0)throw new Error("Could not calculate Person 2's kundli.");
      if(p1Nak<0||p1Rashi<0)throw new Error("Could not find Person 1's nakshatra/rashi.");
      setResult(computeAshtakoot(p1Nak,p1Rashi,p1Manglik,p2Nak,p2Rashi,p2Manglik));
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }catch(e:any){
      setError(e?.message??"An error occurred. Please try again.");
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Error);
    }finally{setLoading(false);}
  }

  const grade=result?getGrade(result.total):null;
  const gradeColor=grade?grade.colors[1]:"#a855f7";

  return(
    <KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS==="ios"?"padding":"height"}>
      <View style={{flex:1,backgroundColor:C.bg}}>

        {/* ── Header ── */}
        <LinearGradient
          colors={C.isDark?["#1a0533","#0B0F19"]:["#ede9fe","#F8FAFC"]}
          style={[km.header,{paddingTop:topPad+6}]}
        >
          <Pressable onPress={()=>router.back()} style={km.backBtn}>
            <Feather name="arrow-left" size={20} color={C.isDark?"#c4b5fd":C.text}/>
          </Pressable>
          <View style={{flex:1}}>
            <Text style={[km.title,{color:C.isDark?"#f3e8ff":C.text}]}>Kundli Milan</Text>
            <Text style={[km.titleHindi,{color:C.isDark?"#7c3aed":"#7c3aed"}]}>अष्टकूट गुण मिलान • 36 Points</Text>
          </View>
        </LinearGradient>

        <ScrollView
          contentContainerStyle={[km.scroll,{paddingBottom:botPad+40}]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >

          {/* ── VS Card ── */}
          <View style={[km.vsCard,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(167,139,250,0.2)":C.border}]}>
            {/* Person 1 */}
            <View style={km.vsPerson}>
              <LinearGradient colors={C.isDark?["#4c1d95","#2e1065"]:["#ede9fe","#ddd6fe"]} style={km.vsAvatar}>
                <Text style={{fontSize:20}}>♀</Text>
              </LinearGradient>
              <Text style={[km.vsName,{color:C.text}]} numberOfLines={1}>{p1Profile?.name??"Aap"}</Text>
              {p1Kundli?(
                <Text style={[km.vsSub,{color:C.textMuted}]} numberOfLines={1}>{p1RashiHi||p1RashiEn} Rashi</Text>
              ):(
                <Pressable onPress={()=>router.push("/onboarding")}>
                  <Text style={{color:"#f97316",fontSize:9,textAlign:"center"}}>Kundli banao →</Text>
                </Pressable>
              )}
            </View>

            {/* Heart divider */}
            <View style={{alignItems:"center",gap:4}}>
              <LinearGradient colors={["#ec4899","#f43f5e"]} style={km.vsHeart}>
                <Text style={{fontSize:16}}>♥</Text>
              </LinearGradient>
              <Text style={{color:C.textDim,fontSize:9,fontFamily:"Nunito_500Medium",letterSpacing:1}}>VS</Text>
            </View>

            {/* Person 2 */}
            <View style={km.vsPerson}>
              <LinearGradient colors={C.isDark?["#7c2d12","#431407"]:["#fff7ed","#ffedd5"]} style={km.vsAvatar}>
                <Text style={{fontSize:20}}>♂</Text>
              </LinearGradient>
              <Text style={[km.vsName,{color:C.text}]} numberOfLines={1}>{p2Name||"Partner"}</Text>
              <Text style={[km.vsSub,{color:C.textMuted}]} numberOfLines={1}>
                {p2Place||"Birth place"}
              </Text>
            </View>
          </View>

          {/* ── Person 2 Form ── */}
          <View style={[km.formCard,{backgroundColor:C.bgCard,borderColor:C.border}]}>
            <Text style={[km.formTitle,{color:C.textMuted}]}>PERSON 2 — PARTNER DETAILS</Text>

            {[
              {label:"Name",        value:p2Name,  set:setP2Name,  ph:"Partner's name",    kb:"default"},
              {label:"Birth Date",  value:p2DOB,   set:setP2DOB,   ph:"DD / MM / YYYY",   kb:"numeric"},
              {label:"Birth Time",  value:p2Time,  set:setP2Time,  ph:"HH:MM  AM / PM",   kb:"default"},
              {label:"Birth Place", value:p2Place, set:setP2Place, ph:"E.g. Delhi, India", kb:"default"},
            ].map(({label,value,set,ph,kb},i,arr)=>(
              <View key={label}>
                <View style={km.inputRow}>
                  <Text style={[km.inputLabel,{color:C.textDim}]}>{label}</Text>
                  <TextInput
                    value={value}
                    onChangeText={set as any}
                    placeholder={ph}
                    placeholderTextColor={C.textDim}
                    keyboardType={kb as any}
                    style={[km.input,{color:C.text}]}
                  />
                </View>
                {i<arr.length-1&&<View style={[km.sep,{backgroundColor:C.border}]}/>}
              </View>
            ))}
          </View>

          {/* Error */}
          {!!error&&(
            <View style={km.errorRow}>
              <Feather name="alert-circle" size={12} color="#ef4444"/>
              <Text style={km.errorText}>{error}</Text>
            </View>
          )}

          {/* ── Calculate Button ── */}
          <Pressable
            onPress={()=>{Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);handleCalculate();}}
            disabled={loading}
            style={({pressed})=>({opacity:pressed||loading?0.75:1})}
          >
            <LinearGradient
              colors={C.isDark?["#6d28d9","#7c3aed","#a855f7"]:["#4f46e5","#7c3aed"]}
              start={{x:0,y:0}} end={{x:1,y:0}}
              style={km.calcBtn}
            >
              {loading?(
                <ActivityIndicator color="white" size="small"/>
              ):(
                <>
                  <Text style={{fontSize:18}}>⚡</Text>
                  <Text style={km.calcBtnText}>Calculate Compatibility</Text>
                </>
              )}
            </LinearGradient>
          </Pressable>

          {/* ── Results ── */}
          {result&&grade&&(
            <>
              {/* Score hero */}
              <LinearGradient
                colors={C.isDark?["#1a0533","#0f172a"]:["#f5f3ff","#ede9fe"]}
                style={[km.scoreHero,{borderColor:`${gradeColor}30`}]}
              >
                <ScoreRing total={result.total} color={gradeColor}/>
                <View style={km.gradeInfo}>
                  <View style={[km.gradeBadge,{backgroundColor:`${gradeColor}18`,borderColor:`${gradeColor}40`}]}>
                    <Text style={{fontSize:14}}>{grade.emoji}</Text>
                    <Text style={[km.gradeLabel,{color:gradeColor}]}>{grade.label}</Text>
                  </View>
                  {result.manglikDosha&&(
                    <View style={km.manglikChip}>
                      <View style={km.manglikDot}/>
                      <Text style={km.manglikChipText}>Manglik Dosh</Text>
                    </View>
                  )}
                </View>
                {/* Bar */}
                <View style={[km.heroBar,{backgroundColor:C.isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)"}]}>
                  <LinearGradient
                    colors={grade.colors}
                    start={{x:0,y:0}} end={{x:1,y:0}}
                    style={[km.heroBarFill,{width:`${Math.round((result.total/36)*100)}%` as any}]}
                  />
                </View>
              </LinearGradient>

              {/* Koot breakdown */}
              <Text style={[km.sectionLabel,{color:C.textMuted}]}>ASHTAKOOT BREAKDOWN</Text>
              <View style={{gap:8}}>
                {KOOT_ORDER.map(key=>(
                  <KootRow key={key} k={result[key]} accent={gradeColor}/>
                ))}
              </View>

              {/* Manglik card */}
              {result.manglikDosha&&(
                <View style={[km.manglikCard,{backgroundColor:C.bgCard,borderColor:"rgba(239,68,68,0.25)"}]}>
                  <LinearGradient colors={["rgba(239,68,68,0.15)","transparent"]} style={km.manglikCardGlow}/>
                  <Text style={{fontSize:20}}>🔴</Text>
                  <View style={{flex:1,gap:4}}>
                    <Text style={[km.manglikTitle,{color:"#ef4444"}]}>Manglik Dosh Present</Text>
                    <Text style={[km.manglikDesc,{color:C.textMuted}]}>
                      Ek vyakti Manglik hai, doosra nahi. Kumbh Vivah ya upay karein. Kisi qualified Jyotishi se zaroor milein.
                    </Text>
                  </View>
                </View>
              )}

              {/* Disclaimer */}
              <View style={[km.disclaimer,{backgroundColor:C.bgCard,borderColor:C.border}]}>
                <Feather name="info" size={11} color={C.textDim}/>
                <Text style={[km.disclaimerText,{color:C.textDim}]}>
                  Yeh Ashtakoot Milan ek anuman hai. Vivah se pehle kisi qualified Jyotishi se poori kundli analysis zaroor karwaein.
                </Text>
              </View>
            </>
          )}

          {/* How it works */}
          {!result&&(
            <View style={[km.howCard,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(167,139,250,0.15)":C.border}]}>
              <Text style={[km.howTitle,{color:C.isDark?"#c4b5fd":C.text}]}>Ashtakoot Milan kya hai?</Text>
              <View style={{gap:6,marginTop:8}}>
                {[
                  ["Nadi","8 pts","Sab se important — health & progeny"],
                  ["Bhakut","7 pts","Rashi based compatibility"],
                  ["Gana","6 pts","Nature & temperament"],
                  ["Graha Maitri","5 pts","Planetary friendship"],
                  ["Yoni","4 pts","Physical compatibility"],
                  ["Tara","3 pts","Nakshatra destiny"],
                  ["Vasya","2 pts","Mutual attraction"],
                  ["Varna","1 pt","Spiritual compatibility"],
                ].map(([name,pts,desc])=>(
                  <View key={name} style={{flexDirection:"row",alignItems:"center",gap:10}}>
                    <View style={[km.howDot,{backgroundColor:C.isDark?"rgba(167,139,250,0.3)":"rgba(99,102,241,0.15)"}]}>
                      <Text style={{color:C.isDark?"#c4b5fd":"#4f46e5",fontSize:9,fontFamily:"Nunito_700Bold"}}>{pts}</Text>
                    </View>
                    <View style={{flex:1}}>
                      <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{name}</Text>
                      <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>{desc}</Text>
                    </View>
                  </View>
                ))}
              </View>
              <View style={[km.howScores,{borderColor:C.border,marginTop:14}]}>
                {[["18+","Acceptable"],["24+","Good"],["28+","Very Good"],["32+","Excellent"]].map(([n,l])=>(
                  <View key={n} style={{alignItems:"center"}}>
                    <Text style={{color:C.isDark?"#a78bfa":"#6d28d9",fontSize:15,fontFamily:"Nunito_700Bold"}}>{n}</Text>
                    <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular"}}>{l}</Text>
                  </View>
                ))}
              </View>
            </View>
          )}

        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const km = StyleSheet.create({
  header: { flexDirection:"row", alignItems:"center", gap:12, paddingHorizontal:16, paddingBottom:16 },
  backBtn:{ width:36, height:36, alignItems:"center", justifyContent:"center" },
  title:  { fontSize:18, fontFamily:"Nunito_700Bold" },
  titleHindi:{ fontSize:11, fontFamily:"Nunito_400Regular", marginTop:2 },

  scroll: { paddingHorizontal:16, gap:14, paddingTop:18 },
  sectionLabel:{ fontSize:10, fontFamily:"Nunito_700Bold", letterSpacing:2, marginBottom:2, marginTop:4 },

  // VS card
  vsCard: { borderRadius:18, borderWidth:1, padding:18, flexDirection:"row", alignItems:"center", justifyContent:"space-between" },
  vsPerson:{ flex:1, alignItems:"center", gap:6 },
  vsAvatar:{ width:52, height:52, borderRadius:26, alignItems:"center", justifyContent:"center" },
  vsName:  { fontSize:13, fontFamily:"Nunito_700Bold", textAlign:"center" },
  vsSub:   { fontSize:10, fontFamily:"Nunito_400Regular", textAlign:"center" },
  vsHeart: { width:36, height:36, borderRadius:18, alignItems:"center", justifyContent:"center" },

  // Form
  formCard:  { borderRadius:16, borderWidth:1, overflow:"hidden" },
  formTitle: { fontSize:9, fontFamily:"Nunito_700Bold", letterSpacing:2, paddingHorizontal:16, paddingTop:14, paddingBottom:8 },
  inputRow:  { flexDirection:"row", alignItems:"center", paddingHorizontal:16, paddingVertical:13, gap:12 },
  inputLabel:{ width:80, fontSize:11, fontFamily:"Nunito_500Medium" },
  input:     { flex:1, fontSize:14, fontFamily:"Nunito_400Regular" },
  sep:       { height:1, marginHorizontal:16 },

  // Error
  errorRow:  { flexDirection:"row", alignItems:"center", gap:6 },
  errorText: { color:"#ef4444", fontSize:12, fontFamily:"Nunito_400Regular" },

  // Button
  calcBtn:   { borderRadius:16, height:54, flexDirection:"row", alignItems:"center", justifyContent:"center", gap:10 },
  calcBtnText:{ color:"#fff", fontSize:15, fontFamily:"Nunito_700Bold" },

  // Score hero
  scoreHero:     { borderRadius:20, borderWidth:1, padding:24, alignItems:"center", gap:14 },
  gradeInfo:     { alignItems:"center", gap:10 },
  gradeBadge:    { flexDirection:"row", alignItems:"center", gap:8, borderRadius:20, borderWidth:1, paddingHorizontal:14, paddingVertical:7 },
  gradeLabel:    { fontSize:15, fontFamily:"Nunito_700Bold" },
  manglikChip:   { flexDirection:"row", alignItems:"center", gap:6, backgroundColor:"rgba(239,68,68,0.1)", borderRadius:12, paddingHorizontal:12, paddingVertical:5 },
  manglikDot:    { width:6, height:6, borderRadius:3, backgroundColor:"#ef4444" },
  manglikChipText:{ color:"#ef4444", fontSize:11, fontFamily:"Nunito_600SemiBold" },
  heroBar:       { width:"100%", height:6, borderRadius:3, overflow:"hidden" },
  heroBarFill:   { height:6, borderRadius:3 },

  // Koot rows
  kootRow:    { borderRadius:14, borderWidth:1, padding:14, gap:0 },
  kootBadDot: { width:6, height:6, borderRadius:3, backgroundColor:"#ef4444" },
  kootLabel:  { fontSize:13, fontFamily:"Nunito_600SemiBold" },
  kootScore:  { fontSize:15, fontFamily:"Nunito_700Bold" },
  kootBarBg:  { height:5, borderRadius:3, overflow:"hidden", marginTop:8 },
  kootBarFill:{ height:5, borderRadius:3 },
  kootDetail: { fontSize:11, fontFamily:"Nunito_400Regular", marginTop:5 },

  // Manglik
  manglikCard:    { borderRadius:16, borderWidth:1, padding:14, flexDirection:"row", gap:12, alignItems:"flex-start", overflow:"hidden" },
  manglikCardGlow:{ position:"absolute", top:0, left:0, right:0, height:60 },
  manglikTitle:   { fontSize:13, fontFamily:"Nunito_700Bold" },
  manglikDesc:    { fontSize:11, fontFamily:"Nunito_400Regular", lineHeight:17 },

  // Disclaimer
  disclaimer:     { borderRadius:14, borderWidth:1, padding:12, flexDirection:"row", gap:8, alignItems:"flex-start" },
  disclaimerText: { flex:1, fontSize:11, fontFamily:"Nunito_400Regular", lineHeight:16 },

  // How card
  howCard:    { borderRadius:18, borderWidth:1, padding:18 },
  howTitle:   { fontSize:15, fontFamily:"Nunito_700Bold" },
  howDot:     { borderRadius:8, paddingHorizontal:6, paddingVertical:3, minWidth:40, alignItems:"center" },
  howScores:  { flexDirection:"row", justifyContent:"space-around", borderTopWidth:1, paddingTop:12 },
});
