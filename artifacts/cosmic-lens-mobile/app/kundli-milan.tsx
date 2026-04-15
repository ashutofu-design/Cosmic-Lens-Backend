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

// ── Ashtakoot Data ────────────────────────────────────────────────────────────
const NAKSHATRAS = [
  "Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya",
  "Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati",
  "Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana",
  "Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati",
];
const RASHIS = ["Mesh","Vrishabh","Mithun","Kark","Simha","Kanya","Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen"];
const EN2R: Record<string,string> = {
  Aries:"Mesh",Taurus:"Vrishabh",Gemini:"Mithun",Cancer:"Kark",
  Leo:"Simha",Virgo:"Kanya",Libra:"Tula",Scorpio:"Vrishchik",
  Sagittarius:"Dhanu",Capricorn:"Makar",Aquarius:"Kumbh",Pisces:"Meen",
};
const NADI=[0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2,2,1,0,0,1,2];
const NADI_N=["Vata (Adi)","Pitta (Madhya)","Kapha (Antya)"];
const GANA=[0,1,2,1,0,1,0,0,2,2,1,1,0,2,0,2,0,2,2,1,1,0,1,2,1,1,0];
const GANA_N=["Dev","Manushya","Raksha"];
const VARNA=[1,2,3,0,1,2,3,0,1,2,3,0];
const YONI=[0,1,2,3,4,5,6,7,8,9,10,2,11,12,13,14,14,13,5,12,11,10,3,7,4,9,0];
const YONI_E:[number,number][]=[[0,1],[2,3],[4,5],[6,7],[8,9],[10,11],[12,13],[14,0]];
const RLORD=[2,5,3,1,0,3,5,2,4,6,6,4];
const PLN:number[][]=[
  [1,2,2,1,2,0,0],[2,1,0,1,2,2,0],[2,0,1,1,2,0,2],
  [2,0,2,1,0,2,0],[2,1,2,1,1,0,0],[2,2,0,2,1,1,0],[0,0,2,2,2,0,1],
];
function yoniEnemy(a:number,b:number){return YONI_E.some(([x,y])=>(a===x&&b===y)||(a===y&&b===x));}
function maitri(r1:number,r2:number):number{
  const l1=RLORD[r1]??0,l2=RLORD[r2]??0;
  if(l1>=PLN.length||l2>=PLN.length)return 3;
  const t=(PLN[l1]?.[l2]??1)+(PLN[l2]?.[l1]??1);
  return t>=4?5:t===3?4:t===2?3:0;
}
function tara(n1:number,n2:number):number{
  const fwd=((n2-n1+27)%27)+1,rev=((n1-n2+27)%27)+1,bad=[3,5,7];
  return !bad.includes(fwd%9||9)&&!bad.includes(rev%9||9)?3:!bad.includes(fwd%9||9)||!bad.includes(rev%9||9)?1.5:0;
}
function bhakut(r1:number,r2:number):number{
  const d=Math.abs(r1-r2);
  return [[1,11],[4,8],[5,7]].some(([a,b])=>d===a||d===b)?0:7;
}
function vasya(r1:number,r2:number):number{
  if(r1===r2)return 2;
  const g=[[0,3,4],[1,6,7,9],[2,8],[5,10,11]];
  return g.findIndex(x=>x.includes(r1))===g.findIndex(x=>x.includes(r2))?2:1;
}

interface KootItem{score:number;max:number;label:string;detail:string;bad:boolean;}
interface Result{
  nadi:KootItem;gana:KootItem;bhakut:KootItem;maitri:KootItem;
  yoni:KootItem;tara:KootItem;vasya:KootItem;varna:KootItem;
  total:number;manglik:boolean;
}
interface PersonData{name:string;nakshatra:string;moonSign:string;manglik:boolean;}

function compute(p1:PersonData,p2:PersonData):Result{
  const n1=NAKSHATRAS.indexOf(p1.nakshatra),n2=NAKSHATRAS.indexOf(p2.nakshatra);
  const r1=RASHIS.indexOf(EN2R[p1.moonSign]??p1.moonSign),r2=RASHIS.indexOf(EN2R[p2.moonSign]??p2.moonSign);
  const nad1=NADI[n1]??0,nad2=NADI[n2]??0,nadiSc=nad1!==nad2?8:0;
  const g1=GANA[n1]??0,g2=GANA[n2]??0;
  let ganaSc=6;
  if((g1===0&&g2===2)||(g1===2&&g2===0))ganaSc=1;
  else if((g1===1&&g2===2)||(g1===2&&g2===1))ganaSc=0;
  const bhakutSc=bhakut(r1,r2),rdiff=((r2-r1+12)%12)+1;
  const maitriSc=maitri(r1,r2);
  const y1=YONI[n1]??0,y2=YONI[n2]??0;
  const yoniSc=y1===y2?4:yoniEnemy(y1,y2)?0:2;
  const taraSc=tara(n1,n2);
  const vasyaSc=vasya(r1,r2);
  const v1=VARNA[r1]??0,v2=VARNA[r2]??0,varnaSc=v1<=v2?1:0;
  return{
    nadi:  {score:nadiSc, max:8,label:"Nadi",         detail:nadiSc===8?`${NADI_N[nad1]} × ${NADI_N[nad2]}`:`Dono ${NADI_N[nad1]}`,  bad:nadiSc===0},
    gana:  {score:ganaSc, max:6,label:"Gana",         detail:`${GANA_N[g1]} + ${GANA_N[g2]}`,                                         bad:ganaSc===0},
    bhakut:{score:bhakutSc,max:7,label:"Bhakut",      detail:bhakutSc===7?`${rdiff}–${13-rdiff} Shubh`:`${rdiff}–${13-rdiff} Dosh`,  bad:bhakutSc===0},
    maitri:{score:maitriSc,max:5,label:"Graha Maitri",detail:maitriSc>=4?"Graha Mitra":maitriSc>=3?"Sama":"Graha Shatru",             bad:maitriSc<3},
    yoni:  {score:yoniSc, max:4,label:"Yoni",         detail:yoniSc===4?"Sama Yoni":yoniSc===2?"Madhyam":"Vipat Yoni",                bad:yoniSc===0},
    tara:  {score:taraSc, max:3,label:"Tara",         detail:taraSc===3?"Shubh":taraSc>0?"Madhyam":"Vipat Tara",                      bad:taraSc===0},
    vasya: {score:vasyaSc,max:2,label:"Vasya",        detail:vasyaSc===2?"Shubh":"Madhyam",                                           bad:false},
    varna: {score:varnaSc,max:1,label:"Varna",        detail:varnaSc?"Sahi":"Anmatch",                                                bad:varnaSc===0},
    total:nadiSc+ganaSc+bhakutSc+maitriSc+yoniSc+taraSc+vasyaSc+varnaSc,
    manglik:p1.manglik!==p2.manglik,
  };
}

function grade(total:number){
  if(total>=32)return{label:"Excellent",   short:"Strong",  col:"#22c55e",grad:["#16a34a","#22c55e"] as const};
  if(total>=27)return{label:"Very Good",   short:"Good",    col:"#4ade80",grad:["#15803d","#4ade80"] as const};
  if(total>=21)return{label:"Average",     short:"Average", col:"#fbbf24",grad:["#b45309","#fbbf24"] as const};
  if(total>=18)return{label:"Below Avg",   short:"Weak",    col:"#f97316",grad:["#c2410c","#f97316"] as const};
  return            {label:"Low Match",    short:"Low",     col:"#ef4444",grad:["#b91c1c","#ef4444"] as const};
}

const KOOTS = ["nadi","gana","bhakut","maitri","yoni","tara","vasya","varna"] as const;

const PRO_LOCKED = [
  {icon:"🔮",title:"Detailed Koot Analysis",   desc:"All 8 gunas with deep interpretations"},
  {icon:"🔴",title:"Dosha Check",               desc:"Mangal, Nadi, Bhakoot & 6 more doshas"},
  {icon:"💍",title:"Marriage Timing",            desc:"Best muhurat & auspicious years"},
  {icon:"👶",title:"Child Planning",             desc:"Early or delayed — nakshatra prediction"},
  {icon:"🌿",title:"Remedies & Upay",            desc:"Personalised puja, gemstone & mantras"},
];

const PREVIEW_ITEMS = [
  {icon:"❤️",title:"Emotional Compatibility",  desc:"Heart & feelings connect"},
  {icon:"🧠",title:"Mental Connection",         desc:"Thought & communication"},
  {icon:"🔥",title:"Attraction Level",          desc:"Physical & energetic pull"},
  {icon:"⚖️",title:"Match Score",              desc:"Total out of 36 points"},
];

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({total,col}:{total:number;col:string}){
  const R=56,circ=2*Math.PI*R,pct=total/36;
  return(
    <View style={{width:132,height:132,alignItems:"center",justifyContent:"center"}}>
      <Svg width={132} height={132} style={{position:"absolute"} as any}>
        <Circle cx={66} cy={66} r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={9}/>
        <Circle cx={66} cy={66} r={R} fill="none" stroke={col} strokeWidth={9}
          strokeLinecap="round" strokeDasharray={`${circ*pct} ${circ}`}
          rotation={-90} originX={66} originY={66}/>
      </Svg>
      <Text style={{fontSize:36,fontFamily:"Nunito_700Bold",color:col,lineHeight:40}}>{total}</Text>
      <Text style={{fontSize:11,color:"rgba(255,255,255,0.4)",fontFamily:"Nunito_500Medium"}}>/ 36</Text>
    </View>
  );
}

// ── Kundli Slot Card ──────────────────────────────────────────────────────────
interface SlotProps{
  who:"self"|"partner";
  locked?:boolean;
  filled?:PersonData|null;
  onAdd:()=>void;
  onClear?:()=>void;
}
function KundliSlot({who,locked,filled,onAdd,onClear}:SlotProps){
  const C=useC();
  const isSelf=who==="self";
  const accent=isSelf?"#a78bfa":"#f9a8d4";
  const gradDark=isSelf?["#3b0764","#1e1b4b"]:["#4a0519","#1c0614"];
  const gradLight=isSelf?["#ede9fe","#ddd6fe"]:["#fce7f3","#fbcfe8"];
  const grad=(C.isDark?gradDark:gradLight) as [string,string];

  if(filled){
    return(
      <LinearGradient colors={grad} style={[sl.slotFilled,{borderColor:`${accent}35`}]}>
        <View style={[sl.slotAvatarFilled,{backgroundColor:`${accent}20`,borderColor:`${accent}40`}]}>
          <Text style={{fontSize:20}}>{isSelf?"♀":"♂"}</Text>
        </View>
        <View style={{flex:1,gap:2}}>
          <Text style={[sl.slotName,{color:C.text}]}>{filled.name}</Text>
          <Text style={[sl.slotSub,{color:C.textMuted}]}>
            {EN2R[filled.moonSign]??filled.moonSign} Rashi · {filled.nakshatra}
          </Text>
        </View>
        <View style={[sl.slotDone,{backgroundColor:`${accent}20`}]}>
          <Feather name="check" size={13} color={accent}/>
        </View>
        {!locked&&onClear&&(
          <Pressable onPress={onClear} style={sl.slotClear}>
            <Feather name="x" size={13} color={C.textDim}/>
          </Pressable>
        )}
      </LinearGradient>
    );
  }

  return(
    <Pressable onPress={locked?undefined:onAdd}
      style={({pressed})=>({opacity:pressed?0.7:1})}
    >
      <View style={[sl.slotEmpty,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(255,255,255,0.07)":C.border,borderStyle:"dashed"}]}>
        <View style={[sl.slotAddBtn,{backgroundColor:`${accent}12`,borderColor:`${accent}30`}]}>
          <Feather name="plus" size={16} color={accent}/>
        </View>
        <Text style={[sl.slotAddText,{color:C.text}]}>
          {locked?"Kundli Ready":isSelf?"Add Your Kundli":"Add Partner Kundli"}
        </Text>
        <Text style={[sl.slotAddSub,{color:C.textMuted}]}>
          {locked?"Auto-filled from profile":isSelf?"Birth details required":"Partner's birth details"}
        </Text>
      </View>
    </Pressable>
  );
}

// ── Inline Add Form ───────────────────────────────────────────────────────────
interface FormProps{
  title:string;
  onDone:(d:PersonData)=>void;
  onCancel:()=>void;
  loading:boolean;
}
function AddKundliForm({title,onDone,onCancel,loading}:FormProps){
  const C=useC();
  const [name,setName]=useState("");
  const [dob,setDob]=useState("");
  const [time,setTime]=useState("");
  const [place,setPlace]=useState("");
  const [err,setErr]=useState("");

  async function submit(){
    if(!dob||!time||!place){setErr("Sab fields zaroori hain.");return;}
    setErr("");
    try{
      const[day,month,year]=dob.split("/").map(Number);
      const[hm,ap]=time.trim().split(" ");
      const[h,m]=(hm??"").split(":").map(Number);
      if(!day||!month||!year||!h)throw new Error("Format: DD/MM/YYYY & HH:MM AM");
      const res=await apiFetch(`${API_BASE}/api/kundli`,{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:name||"Person",day,month,year,hour:h,minute:m??0,ampm:ap??"AM",place}),
      });
      const json=await res.json();
      const marsH=(json.planets as any[])?.find((p:any)=>p.name==="Mars")?.house??0;
      onDone({name:name||"Person",nakshatra:json.nakshatra,moonSign:json.moonSign,manglik:[1,4,7,8,12].includes(marsH)});
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }catch(e:any){setErr(e?.message??"Error. Try again.");}
  }

  const fields=[
    {label:"Name",     value:name, set:setName, ph:"Full name",           kb:"default"},
    {label:"Date",     value:dob,  set:setDob,  ph:"DD/MM/YYYY",          kb:"numeric"},
    {label:"Time",     value:time, set:setTime, ph:"HH:MM  AM / PM",      kb:"default"},
    {label:"Place",    value:place,set:setPlace,ph:"E.g. Delhi, India",    kb:"default"},
  ];

  return(
    <View style={[fm.wrap,{backgroundColor:C.bgCard,borderColor:C.border}]}>
      <Text style={[fm.title,{color:C.textMuted}]}>{title}</Text>
      {fields.map(({label,value,set,ph,kb},i,arr)=>(
        <View key={label}>
          <View style={fm.row}>
            <Text style={[fm.label,{color:C.textDim}]}>{label}</Text>
            <TextInput value={value} onChangeText={set as any} placeholder={ph}
              placeholderTextColor={C.textDim} keyboardType={kb as any}
              style={[fm.input,{color:C.text}]}/>
          </View>
          {i<arr.length-1&&<View style={[fm.sep,{backgroundColor:C.border}]}/>}
        </View>
      ))}
      {!!err&&(
        <View style={fm.errRow}>
          <Feather name="alert-circle" size={11} color="#ef4444"/>
          <Text style={fm.errText}>{err}</Text>
        </View>
      )}
      <View style={fm.actions}>
        <Pressable onPress={onCancel} style={[fm.cancelBtn,{borderColor:C.border}]}>
          <Text style={{color:C.textMuted,fontSize:13,fontFamily:"Nunito_600SemiBold"}}>Cancel</Text>
        </Pressable>
        <Pressable onPress={submit} disabled={loading} style={({pressed})=>({opacity:pressed?0.7:1,flex:1})}>
          <LinearGradient colors={["#6d28d9","#a855f7"]} start={{x:0,y:0}} end={{x:1,y:0}} style={fm.addBtn}>
            {loading?<ActivityIndicator color="#fff" size="small"/>:
              <Text style={{color:"#fff",fontSize:13,fontFamily:"Nunito_700Bold"}}>Add Kundli →</Text>}
          </LinearGradient>
        </Pressable>
      </View>
    </View>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
export default function KundliMilanScreen(){
  const insets=useSafeAreaInsets();
  const C=useC();
  const topPad=Platform.OS==="web"?67:insets.top;
  const botPad=Platform.OS==="web"?34:insets.bottom;
  const {kundli:primaryKundli,profiles,primaryProfileId}=useUser();
  const p1Profile=profiles.find(p=>p.id===primaryProfileId);

  const [plan,setPlan]=useState<"basic"|"pro">("basic");
  const [addingFor,setAddingFor]=useState<"self"|"partner"|null>(null);
  const [formLoading,setFormLoading]=useState(false);
  const [p1,setP1]=useState<PersonData|null>(null);
  const [p2,setP2]=useState<PersonData|null>(null);
  const [result,setResult]=useState<Result|null>(null);
  const [calcLoading,setCalcLoading]=useState(false);

  // Auto-populate Person 1 if primary kundli exists
  const autoP1:PersonData|null = primaryKundli?{
    name: p1Profile?.name??"Aap",
    nakshatra: primaryKundli.nakshatra,
    moonSign:  primaryKundli.moonSign,
    manglik:   [1,4,7,8,12].includes(primaryKundli.planets.find(p=>p.name==="Mars")?.house??0),
  }:null;

  const person1 = autoP1 ?? p1;
  const person2 = p2;
  const canCalculate = !!person1 && !!person2;

  function handleDone(who:"self"|"partner",data:PersonData){
    if(who==="self")setP1(data);
    else setP2(data);
    setAddingFor(null);
    setResult(null);
  }

  async function handleCalculate(){
    if(!person1||!person2)return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setCalcLoading(true);
    await new Promise(r=>setTimeout(r,600));
    setResult(compute(person1,person2));
    setCalcLoading(false);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }

  const g=result?grade(result.total):null;

  return(
    <KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS==="ios"?"padding":"height"}>
      <View style={{flex:1,backgroundColor:C.bg}}>

        {/* ── Header ── */}
        <LinearGradient
          colors={C.isDark?["#1a0533","#0B0F19"]:["#ede9fe","#F8FAFC"]}
          style={[sc.header,{paddingTop:topPad+4}]}
        >
          <View style={{flexDirection:"row",alignItems:"center",gap:10}}>
            <Pressable onPress={()=>router.back()} style={sc.backBtn}>
              <Feather name="arrow-left" size={20} color={C.isDark?"#c4b5fd":C.text}/>
            </Pressable>
            <View style={{flex:1}}>
              <Text style={[sc.titleText,{color:C.isDark?"#f3e8ff":C.text}]}>Kundli Milan</Text>
              <Text style={{color:"#7c3aed",fontSize:10,fontFamily:"Nunito_400Regular"}}>अष्टकूट गुण मिलान</Text>
            </View>
            {/* Basic / Pro Toggle */}
            <View style={[sc.toggle,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.05)"}]}>
              {(["basic","pro"] as const).map(t=>(
                <Pressable key={t} onPress={()=>{setPlan(t);Haptics.selectionAsync();}}
                  style={[sc.toggleBtn,plan===t&&{backgroundColor:C.isDark?"#6d28d9":"#4f46e5"}]}>
                  <Text style={[sc.toggleTxt,{color:plan===t?"#fff":C.textMuted}]}>
                    {t==="pro"?"✨ Pro":"Basic"}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>
        </LinearGradient>

        <ScrollView
          contentContainerStyle={[sc.scroll,{paddingBottom:botPad+40}]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >

          {/* ── Kundli Slots ── */}
          <View style={{gap:8}}>
            {/* Person 1 */}
            {autoP1?(
              <KundliSlot who="self" locked filled={autoP1} onAdd={()=>{}}/>
            ):(
              <>
                <KundliSlot who="self" filled={p1}
                  onAdd={()=>{setAddingFor("self");setResult(null);}}
                  onClear={()=>{setP1(null);setResult(null);}}/>
                {addingFor==="self"&&(
                  <AddKundliForm title="YOUR BIRTH DETAILS"
                    loading={formLoading}
                    onDone={d=>handleDone("self",d)}
                    onCancel={()=>setAddingFor(null)}/>
                )}
              </>
            )}

            {/* Connector */}
            <View style={{alignItems:"center",marginVertical:-2,zIndex:1}}>
              <LinearGradient colors={["#ec4899","#f43f5e"]} style={sc.heart}>
                <Text style={{fontSize:14}}>♥</Text>
              </LinearGradient>
            </View>

            {/* Person 2 */}
            <KundliSlot who="partner" filled={person2}
              onAdd={()=>{setAddingFor("partner");setResult(null);}}
              onClear={()=>{setP2(null);setResult(null);}}/>
            {addingFor==="partner"&&(
              <AddKundliForm title="PARTNER'S BIRTH DETAILS"
                loading={formLoading}
                onDone={d=>handleDone("partner",d)}
                onCancel={()=>setAddingFor(null)}/>
            )}
          </View>

          {/* ── What You'll Get ── */}
          {!result&&(
            <>
              <Text style={[sc.secLabel,{color:C.textMuted}]}>WHAT YOU'LL GET</Text>
              <View style={sc.previewGrid}>
                {PREVIEW_ITEMS.map(({icon,title,desc})=>(
                  <View key={title} style={[sc.previewCard,{backgroundColor:C.bgCard,borderColor:C.border}]}>
                    <Text style={{fontSize:22,marginBottom:6}}>{icon}</Text>
                    <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_700Bold",marginBottom:2}}>{title}</Text>
                    <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",textAlign:"center",lineHeight:14}}>{desc}</Text>
                  </View>
                ))}
              </View>
            </>
          )}

          {/* ── CTA Button ── */}
          {!result&&(
            <Pressable onPress={handleCalculate} disabled={!canCalculate||calcLoading}
              style={({pressed})=>({opacity:pressed||(!canCalculate)||calcLoading?0.45:1})}>
              <LinearGradient
                colors={C.isDark?["#6d28d9","#a855f7"]:["#4f46e5","#7c3aed"]}
                start={{x:0,y:0}} end={{x:1,y:0}}
                style={sc.ctaBtn}>
                {calcLoading?<ActivityIndicator color="#fff" size="small"/>:(
                  <>
                    <Text style={{fontSize:18}}>✨</Text>
                    <Text style={sc.ctaTxt}>
                      {canCalculate?"Check Compatibility":
                       !person1&&!person2?"Add Both Kundlis First":
                       !person1?"Add Your Kundli First":"Add Partner Kundli First"}
                    </Text>
                  </>
                )}
              </LinearGradient>
            </Pressable>
          )}

          {/* ── FREE RESULTS ── */}
          {result&&g&&(
            <>
              {/* Score hero */}
              <LinearGradient
                colors={C.isDark?["#1a0533","#0f172a"]:["#f5f3ff","#ede9fe"]}
                style={[sc.scoreHero,{borderColor:`${g.col}30`}]}>
                <ScoreRing total={result.total} col={g.col}/>
                <View style={{alignItems:"center",gap:10}}>
                  <View style={[sc.gradeBadge,{backgroundColor:`${g.col}15`,borderColor:`${g.col}35`}]}>
                    <Text style={{color:g.col,fontSize:18,fontFamily:"Nunito_700Bold"}}>{g.label}</Text>
                  </View>
                  <Text style={{color:C.textMuted,fontSize:12,fontFamily:"Nunito_400Regular",textAlign:"center",maxWidth:200,lineHeight:18}}>
                    {result.total>=27?"Aapka milan bahut auspicious hai. Bahut achha match."
                     :result.total>=21?"Thodi precautions ki zaroorat hai. Consult Jyotishi."
                     :"Kuch doshas hain. Expert guidance lena chahiye."}
                  </Text>
                  {result.manglik&&(
                    <View style={sc.mangChip}>
                      <View style={sc.mangDot}/>
                      <Text style={sc.mangTxt}>Manglik Dosh Present</Text>
                    </View>
                  )}
                </View>
                <View style={[sc.heroBg,{backgroundColor:C.isDark?"rgba(255,255,255,0.06)":"rgba(0,0,0,0.05)"}]}>
                  <LinearGradient colors={g.grad} start={{x:0,y:0}} end={{x:1,y:0}}
                    style={[sc.heroFill,{width:`${Math.round((result.total/36)*100)}%` as any}]}/>
                </View>
              </LinearGradient>

              {/* Recalculate */}
              <Pressable onPress={()=>{setResult(null);Haptics.selectionAsync();}}
                style={[sc.recalcBtn,{borderColor:C.border,backgroundColor:C.bgCard}]}>
                <Feather name="refresh-cw" size={13} color={C.textMuted}/>
                <Text style={{color:C.textMuted,fontSize:12,fontFamily:"Nunito_500Medium"}}>Check Again / Change Details</Text>
              </Pressable>

              {/* ── PRO LOCKED SECTION ── */}
              <View style={[sc.proSection,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(167,139,250,0.2)":C.border}]}>
                <LinearGradient
                  colors={C.isDark?["rgba(109,40,217,0.15)","transparent"]:["rgba(99,102,241,0.08)","transparent"]}
                  style={sc.proGlow}/>
                <View style={{flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:14}}>
                  <View>
                    <Text style={{color:C.isDark?"#c4b5fd":"#4f46e5",fontSize:14,fontFamily:"Nunito_700Bold"}}>✨ Pro Analysis</Text>
                    <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",marginTop:2}}>Unlock deep insights</Text>
                  </View>
                  <View style={sc.proBadge}>
                    <Text style={sc.proBadgeTxt}>PRO</Text>
                  </View>
                </View>

                {PRO_LOCKED.map(({icon,title,desc})=>(
                  <View key={title} style={[sc.lockedRow,{borderColor:C.isDark?"rgba(255,255,255,0.05)":C.border}]}>
                    <View style={[sc.lockedIcon,{backgroundColor:C.isDark?"rgba(255,255,255,0.05)":"rgba(0,0,0,0.04)"}]}>
                      <Text style={{fontSize:17}}>{icon}</Text>
                    </View>
                    <View style={{flex:1}}>
                      <Text style={{color:C.text,fontSize:13,fontFamily:"Nunito_600SemiBold"}}>{title}</Text>
                      <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",marginTop:2}}>{desc}</Text>
                    </View>
                    <View style={sc.lockIcon}>
                      <Feather name="lock" size={13} color={C.isDark?"#a78bfa":"#7c3aed"}/>
                    </View>
                  </View>
                ))}

                <Pressable style={({pressed})=>({opacity:pressed?0.8:1})} onPress={()=>Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium)}>
                  <LinearGradient colors={["#6d28d9","#a855f7","#ec4899"]}
                    start={{x:0,y:0}} end={{x:1,y:0}}
                    style={sc.unlockBtn}>
                    <Text style={sc.unlockTxt}>🔓 Unlock Pro Features</Text>
                  </LinearGradient>
                </Pressable>
              </View>
            </>
          )}

          {/* ── How it works (before result) ── */}
          {!result&&(
            <View style={[sc.howCard,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(167,139,250,0.1)":C.border}]}>
              <Text style={{color:C.isDark?"#c4b5fd":"#4f46e5",fontSize:13,fontFamily:"Nunito_700Bold",marginBottom:10}}>
                Ashtakoot Milan — 8 Points System
              </Text>
              {[["32+ / 36","Excellent Match"],["27–31","Very Good"],["21–26","Average"],["≤20","Below Average"]].map(([pts,lbl])=>(
                <View key={pts} style={{flexDirection:"row",justifyContent:"space-between",paddingVertical:6,borderBottomWidth:1,borderBottomColor:C.border}}>
                  <Text style={{color:C.isDark?"#a78bfa":"#6d28d9",fontFamily:"Nunito_700Bold",fontSize:13}}>{pts}</Text>
                  <Text style={{color:C.textMuted,fontFamily:"Nunito_400Regular",fontSize:12}}>{lbl}</Text>
                </View>
              ))}
            </View>
          )}

        </ScrollView>
      </View>
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const sc = StyleSheet.create({
  header:    {paddingHorizontal:16,paddingBottom:14},
  backBtn:   {width:36,height:36,alignItems:"center",justifyContent:"center"},
  titleText: {fontSize:18,fontFamily:"Nunito_700Bold"},
  toggle:    {flexDirection:"row",borderRadius:20,padding:3,gap:2},
  toggleBtn: {paddingHorizontal:11,paddingVertical:6,borderRadius:16},
  toggleTxt: {fontSize:12,fontFamily:"Nunito_700Bold"},
  scroll:    {paddingHorizontal:16,paddingTop:16,gap:14},
  secLabel:  {fontSize:10,fontFamily:"Nunito_700Bold",letterSpacing:2},
  heart:     {width:34,height:34,borderRadius:17,alignItems:"center",justifyContent:"center"},

  previewGrid:{flexDirection:"row",flexWrap:"wrap",gap:10},
  previewCard:{width:"47%",borderRadius:14,borderWidth:1,padding:14,alignItems:"center"},

  ctaBtn:    {borderRadius:16,height:56,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:10},
  ctaTxt:    {color:"#fff",fontSize:15,fontFamily:"Nunito_700Bold"},

  scoreHero: {borderRadius:20,borderWidth:1,padding:22,alignItems:"center",gap:16},
  gradeBadge:{borderRadius:20,borderWidth:1,paddingHorizontal:20,paddingVertical:8},
  heroBg:    {width:"100%",height:6,borderRadius:3,overflow:"hidden"},
  heroFill:  {height:6,borderRadius:3},
  mangChip:  {flexDirection:"row",alignItems:"center",gap:6,backgroundColor:"rgba(239,68,68,0.1)",borderRadius:12,paddingHorizontal:12,paddingVertical:5},
  mangDot:   {width:6,height:6,borderRadius:3,backgroundColor:"#ef4444"},
  mangTxt:   {color:"#ef4444",fontSize:11,fontFamily:"Nunito_600SemiBold"},

  recalcBtn: {flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8,borderRadius:12,borderWidth:1,paddingVertical:11},

  proSection:{borderRadius:20,borderWidth:1,padding:18,gap:10,overflow:"hidden"},
  proGlow:   {position:"absolute",top:0,left:0,right:0,height:80},
  proBadge:  {backgroundColor:"rgba(109,40,217,0.15)",borderRadius:8,paddingHorizontal:10,paddingVertical:4},
  proBadgeTxt:{color:"#a78bfa",fontSize:10,fontFamily:"Nunito_700Bold",letterSpacing:1.5},
  lockedRow: {flexDirection:"row",alignItems:"center",gap:12,paddingVertical:10,borderBottomWidth:1},
  lockedIcon:{width:38,height:38,borderRadius:10,alignItems:"center",justifyContent:"center"},
  lockIcon:  {width:28,height:28,borderRadius:8,backgroundColor:"rgba(109,40,217,0.12)",alignItems:"center",justifyContent:"center"},
  unlockBtn: {borderRadius:14,height:50,alignItems:"center",justifyContent:"center",marginTop:4},
  unlockTxt: {color:"#fff",fontSize:14,fontFamily:"Nunito_700Bold"},

  howCard:   {borderRadius:16,borderWidth:1,padding:16},
});

const sl = StyleSheet.create({
  slotFilled:{flexDirection:"row",alignItems:"center",gap:12,borderRadius:16,borderWidth:1,padding:14},
  slotAvatarFilled:{width:46,height:46,borderRadius:23,borderWidth:1,alignItems:"center",justifyContent:"center"},
  slotName:  {fontSize:14,fontFamily:"Nunito_700Bold"},
  slotSub:   {fontSize:10,fontFamily:"Nunito_400Regular",marginTop:2},
  slotDone:  {width:28,height:28,borderRadius:14,alignItems:"center",justifyContent:"center"},
  slotClear: {width:24,height:24,alignItems:"center",justifyContent:"center"},
  slotEmpty: {borderRadius:16,borderWidth:1.5,padding:16,alignItems:"center",gap:6},
  slotAddBtn:{width:40,height:40,borderRadius:20,borderWidth:1,alignItems:"center",justifyContent:"center"},
  slotAddText:{fontSize:14,fontFamily:"Nunito_600SemiBold"},
  slotAddSub: {fontSize:10,fontFamily:"Nunito_400Regular"},
});

const fm = StyleSheet.create({
  wrap:    {borderRadius:16,borderWidth:1,overflow:"hidden"},
  title:   {fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:2,paddingHorizontal:16,paddingTop:14,paddingBottom:8},
  row:     {flexDirection:"row",alignItems:"center",paddingHorizontal:16,paddingVertical:13,gap:10},
  label:   {width:48,fontSize:11,fontFamily:"Nunito_500Medium"},
  input:   {flex:1,fontSize:14,fontFamily:"Nunito_400Regular"},
  sep:     {height:1,marginHorizontal:16},
  errRow:  {flexDirection:"row",alignItems:"center",gap:6,paddingHorizontal:16,paddingTop:8},
  errText: {color:"#ef4444",fontSize:11,fontFamily:"Nunito_400Regular"},
  actions: {flexDirection:"row",gap:10,padding:14},
  cancelBtn:{flex:0.6,borderRadius:12,borderWidth:1,alignItems:"center",justifyContent:"center",height:44},
  addBtn:  {borderRadius:12,height:44,alignItems:"center",justifyContent:"center"},
});
