import { Feather } from "@expo/vector-icons";
import { BlurView } from "expo-blur";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router, useLocalSearchParams } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator,
  Alert,
  Animated,
  Easing,
  I18nManager,
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { useT } from "@/hooks/useT";
import { API_BASE, apiFetch } from "@/lib/apiConfig";
import { MilanResultStore } from "@/lib/milanResultStore";
import { useFeatureGate } from "@/components/FeatureGate";
import * as FileSystem from "expo-file-system/legacy";
import * as Sharing from "expo-sharing";
import { saveLocalReport } from "@/lib/localReports";

// ── Ashtakoot tables ──────────────────────────────────────────────────────────
const NAKSHATRAS=["Ashwini","Bharani","Krittika","Rohini","Mrigashira","Ardra","Punarvasu","Pushya","Ashlesha","Magha","Purva Phalguni","Uttara Phalguni","Hasta","Chitra","Swati","Vishakha","Anuradha","Jyeshtha","Mula","Purva Ashadha","Uttara Ashadha","Shravana","Dhanishtha","Shatabhisha","Purva Bhadrapada","Uttara Bhadrapada","Revati"];
const RASHIS=["Mesh","Vrishabh","Mithun","Kark","Simha","Kanya","Tula","Vrishchik","Dhanu","Makar","Kumbh","Meen"];
const EN2R:Record<string,string>={Aries:"Mesh",Taurus:"Vrishabh",Gemini:"Mithun",Cancer:"Kark",Leo:"Simha",Virgo:"Kanya",Libra:"Tula",Scorpio:"Vrishchik",Sagittarius:"Dhanu",Capricorn:"Makar",Aquarius:"Kumbh",Pisces:"Meen"};
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
interface RawBirth{day:number;month:number;year:number;hour:number;minute:number;ampm:string;place:string;}
interface PersonData{name:string;nakshatra:string;moonSign:string;manglik:boolean;_rawBirth?:RawBirth;}

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
    nadi:  {score:nadiSc, max:8,label:"Nadi",         detail:nadiSc===8?`${NADI_N[nad1]} × ${NADI_N[nad2]}`:`Dono ${NADI_N[nad1]}`,bad:nadiSc===0},
    gana:  {score:ganaSc, max:6,label:"Gana",         detail:`${GANA_N[g1]} + ${GANA_N[g2]}`,bad:ganaSc===0},
    bhakut:{score:bhakutSc,max:7,label:"Bhakut",      detail:bhakutSc===7?`${rdiff}–${13-rdiff} Shubh`:`${rdiff}–${13-rdiff} Dosh`,bad:bhakutSc===0},
    maitri:{score:maitriSc,max:5,label:"Graha Maitri",detail:maitriSc>=4?"Graha Mitra":maitriSc>=3?"Sama":"Graha Shatru",bad:maitriSc<3},
    yoni:  {score:yoniSc, max:4,label:"Yoni",         detail:yoniSc===4?"Sama Yoni":yoniSc===2?"Madhyam":"Vipat Yoni",bad:yoniSc===0},
    tara:  {score:taraSc, max:3,label:"Tara",         detail:taraSc===3?"Shubh":taraSc>0?"Madhyam":"Vipat Tara",bad:taraSc===0},
    vasya: {score:vasyaSc,max:2,label:"Vasya",        detail:vasyaSc===2?"Shubh":"Madhyam",bad:false},
    varna: {score:varnaSc,max:1,label:"Varna",        detail:varnaSc?"Sahi":"Anmatch",bad:varnaSc===0},
    total:nadiSc+ganaSc+bhakutSc+maitriSc+yoniSc+taraSc+vasyaSc+varnaSc,
    manglik:p1.manglik!==p2.manglik,
  };
}
function grade(total:number){
  if(total>=32)return{label:"Excellent",   col:"#22c55e",grad:["#16a34a","#22c55e"] as const};
  if(total>=27)return{label:"Very Good",   col:"#4ade80",grad:["#15803d","#4ade80"] as const};
  if(total>=21)return{label:"Average",     col:"#fbbf24",grad:["#b45309","#fbbf24"] as const};
  if(total>=18)return{label:"Below Avg",   col:"#f97316",grad:["#c2410c","#f97316"] as const};
  return            {label:"Low Match",    col:"#ef4444",grad:["#b91c1c","#ef4444"] as const};
}

// ── Score Ring ────────────────────────────────────────────────────────────────
function ScoreRing({total,col}:{total:number;col:string}){
  const R=52,circ=2*Math.PI*R,pct=total/36;
  return(
    <View style={{width:120,height:120,alignItems:"center",justifyContent:"center"}}>
      <Svg width={120} height={120} style={{position:"absolute"} as any}>
        <Circle cx={60} cy={60} r={R} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={9}/>
        <Circle cx={60} cy={60} r={R} fill="none" stroke={col} strokeWidth={9}
          strokeLinecap="round" strokeDasharray={`${circ*pct} ${circ}`}
          rotation={-90} originX={60} originY={60}/>
      </Svg>
      <Text style={{fontSize:32,fontFamily:"Nunito_700Bold",color:col,lineHeight:36}}>{total}</Text>
      <Text style={{fontSize:10,color:"rgba(255,255,255,0.4)",fontFamily:"Nunito_500Medium"}}>/ 36</Text>
    </View>
  );
}

// ── Kundli Slot ───────────────────────────────────────────────────────────────
interface SlotProps{who:"self"|"partner";locked?:boolean;filled?:PersonData|null;isPro:boolean;onAdd():void;onClear?():void;}
function KundliSlot({who,locked,filled,isPro,onAdd,onClear}:SlotProps){
  const t=useT();
  const C=useC();
  const isSelf=who==="self";
  const accent=isSelf?"#a78bfa":"#f9a8d4";
  const glowBorder=isPro?`${accent}60`:C.border;
  const shadow=isPro?{shadowColor:accent,shadowOffset:{width:0,height:0},shadowOpacity:0.55,shadowRadius:12,elevation:8}:{};

  if(filled){
    return(
      <View style={[sl.filled,{borderColor:glowBorder,backgroundColor:C.bgCard},...(isPro?[shadow]:[])]}>
        {isPro&&<View style={[sl.glowBar,{backgroundColor:accent}]}/>}
        <View style={[sl.avatar,{backgroundColor:`${accent}18`,borderColor:`${accent}40`}]}>
          <Text style={{fontSize:20}}>{isSelf?"♀":"♂"}</Text>
        </View>
        <View style={{flex:1,gap:2}}>
          <Text style={{color:C.text,fontSize:14,fontFamily:"Nunito_700Bold"}}>{filled.name}</Text>
          <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>
            {EN2R[filled.moonSign]??filled.moonSign} Rashi · {filled.nakshatra}
          </Text>
        </View>
        <View style={[sl.check,{backgroundColor:`${accent}18`}]}>
          <Feather name="check" size={13} color={accent}/>
        </View>
        {!locked&&onClear&&(
          <Pressable onPress={onClear} style={{padding:4}}>
            <Feather name="x" size={13} color={C.textDim}/>
          </Pressable>
        )}
      </View>
    );
  }
  return(
    <Pressable onPress={locked?undefined:onAdd} style={({pressed})=>({opacity:pressed?0.7:1})}>
      <View style={[sl.empty,{backgroundColor:C.bgCard,borderColor:glowBorder,borderStyle:"dashed"},...(isPro?[shadow]:[])]}>
        <View style={[sl.addIcon,{backgroundColor:`${accent}12`,borderColor:`${accent}30`}]}>
          <Feather name="plus" size={16} color={accent}/>
        </View>
        <Text style={{color:C.text,fontSize:14,fontFamily:"Nunito_600SemiBold"}}>{isSelf?t.km_addYourKundli:t.km_addPartnerKundli}</Text>
        <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular"}}>{isSelf?t.km_birthDetailsReq:t.km_partnerBirth}</Text>
      </View>
    </Pressable>
  );
}

// ── Inline Form ───────────────────────────────────────────────────────────────
interface FormProps{title:string;onDone(d:PersonData):void;onCancel():void;}
function AddKundliForm({title,onDone,onCancel}:FormProps){
  const C=useC();
  const t=useT();
  const [name,setName]=useState(""); const [dob,setDob]=useState("");
  const [time,setTime]=useState(""); const [place,setPlace]=useState("");
  const [err,setErr]=useState(""); const [loading,setLoading]=useState(false);
  async function submit(){
    if(!name.trim()){setErr(t.km_errName);return;}
    if(!dob||!time||!place){setErr(t.km_errAllFields);return;}
    setErr(""); setLoading(true);
    try{
      const[day,month,year]=dob.split("/").map(Number);
      const[hm,ap]=time.trim().split(" ");
      const[h,m]=(hm??"").split(":").map(Number);
      if(!day||!month||!year||!h)throw new Error("Format: DD/MM/YYYY & HH:MM AM");
      const res=await apiFetch(`${API_BASE}/api/kundli`,{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:name||t.km3_personFallback,day,month,year,hour:h,minute:m??0,ampm:ap??"AM",place})});
      const json=await res.json();
      const marsH=(json.planets as any[])?.find((p:any)=>p.name==="Mars")?.house??0;
      onDone({
        name:name||t.km3_personFallback,
        nakshatra:json.nakshatra,
        moonSign:json.moonSign,
        manglik:[1,4,7,8,12].includes(marsH),
        _rawBirth:{day,month,year,hour:h,minute:m??0,ampm:ap??"AM",place},
      });
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }catch(e:any){setErr(e?.message??t.km3_errTryAgain);}
    finally{setLoading(false);}
  }
  const fields=[
    {label:t.km_lblName, value:name, set:setName, ph:t.km_phName, kb:"default"},
    {label:t.km_lblDob,  value:dob,  set:setDob,  ph:t.km_phDob,  kb:"numeric"},
    {label:t.km_lblTime, value:time, set:setTime, ph:t.km_phTime, kb:"default"},
    {label:t.km_lblPlace,value:place,set:setPlace,ph:t.km_phPlace,kb:"default"},
  ];
  return(
    <View style={[fm.wrap,{backgroundColor:C.bgCard,borderColor:C.border}]}>
      <Text style={[fm.heading,{color:C.textMuted}]}>{title}</Text>
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
      {!!err&&<View style={fm.errRow}><Feather name="alert-circle" size={11} color="#ef4444"/><Text style={fm.errText}>{err}</Text></View>}
      <View style={fm.btns}>
        <Pressable onPress={onCancel} style={[fm.cancelBtn,{borderColor:C.border}]}>
          <Text style={{color:C.textMuted,fontSize:13,fontFamily:"Nunito_600SemiBold"}}>{t.cancel}</Text>
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

// ── Animated section entrance ─────────────────────────────────────────────────
function useFadeIn(delay=0){
  const anim=useRef(new Animated.Value(0)).current;
  const slide=useRef(new Animated.Value(18)).current;
  useEffect(()=>{
    Animated.parallel([
      Animated.timing(anim,{toValue:1,duration:480,delay,useNativeDriver:true}),
      Animated.timing(slide,{toValue:0,duration:420,delay,easing:Easing.out(Easing.quad),useNativeDriver:true}),
    ]).start();
  },[]);
  return{opacity:anim,transform:[{translateY:slide}]};
}

// ── Glowing card shell ────────────────────────────────────────────────────────
function GlowCard({children,style,accent="#8B5CF6",C}:{children:React.ReactNode;style?:any;accent?:string;C:any}){
  return(
    <View style={[{borderRadius:16,borderWidth:1,borderColor:`${accent}35`,overflow:"hidden",
      backgroundColor:C.isDark?"rgba(20,10,40,0.7)":"rgba(245,240,255,0.9)",
      shadowColor:accent,shadowOffset:{width:0,height:0},shadowOpacity:0.25,shadowRadius:10,elevation:6},style]}>
      <LinearGradient colors={[`${accent}14`,"transparent"]} style={{position:"absolute",top:0,left:0,right:0,height:60}}/>
      {children}
    </View>
  );
}

// ── Mini arc for compatibility ────────────────────────────────────────────────
function MiniArc({pct,col,size=56}:{pct:number;col:string;size?:number}){
  const r=size/2-5,circ=2*Math.PI*r;
  return(
    <View style={{width:size,height:size,alignItems:"center",justifyContent:"center"}}>
      <Svg width={size} height={size} style={{position:"absolute"} as any}>
        <Circle cx={size/2} cy={size/2} r={r} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={5}/>
        <Circle cx={size/2} cy={size/2} r={r} fill="none" stroke={col} strokeWidth={5}
          strokeLinecap="round" strokeDasharray={`${circ*pct} ${circ}`}
          rotation={-90} originX={size/2} originY={size/2}/>
      </Svg>
      <Text style={{fontSize:10,fontFamily:"Nunito_700Bold",color:col}}>{Math.round(pct*100)}%</Text>
    </View>
  );
}

// ── Pro Insights Panel + Shared sub-components ───────────────────────────────
function PipBadge({type}:{type:"most"|"critical"|"premium"|"secret"|"decision"|null|undefined}){
  const C=useC();
  const t=useT();
  if(!type)return null;
  type BadgeSpec={bg:string;bdr:string;txtD:string;txtL:string;lbl:string};
  const M:{[k:string]:BadgeSpec}={
    most:    {bg:"rgba(244,63,94,0.15)",  bdr:"rgba(244,63,94,0.45)",   txtD:"#fb7185",txtL:"#be123c",lbl:t.km_badgeMostImp},
    critical:{bg:"rgba(239,68,68,0.13)",  bdr:"rgba(239,68,68,0.40)",   txtD:"#f87171",txtL:"#dc2626",lbl:t.km_badgeCritCheck},
    decision:{bg:"rgba(249,115,22,0.13)", bdr:"rgba(249,115,22,0.40)",  txtD:"#fb923c",txtL:"#ea580c",lbl:t.km_badgeDecCard},
    premium: {bg:"rgba(109,93,246,0.12)", bdr:"rgba(109,93,246,0.38)",  txtD:"#c4b5fd",txtL:"#6D5DF6",lbl:"PREMIUM"},
    secret:  {bg:"rgba(147,51,234,0.12)", bdr:"rgba(147,51,234,0.38)",  txtD:"#e879f9",txtL:"#9333ea",lbl:t.km_badgeSecret},
  };
  const b=M[type]; if(!b)return null;
  return(
    <View style={{backgroundColor:b.bg,borderRadius:6,paddingHorizontal:7,paddingVertical:3,
      borderWidth:1,borderColor:b.bdr,alignSelf:"flex-start"}}>
      <Text style={{color:C.isDark?b.txtD:b.txtL,fontSize:8,fontFamily:"Nunito_700Bold",letterSpacing:0.9}}>{b.lbl}</Text>
    </View>
  );
}

function ProInsightsPanel(){
  const C=useC();
  const t=useT();

  // ── Stagger: 23 total animated elements ──
  const TOTAL=23;
  const anims=useRef(
    Array.from({length:TOTAL},()=>({op:new Animated.Value(0),sl:new Animated.Value(18)}))
  ).current;
  useEffect(()=>{
    Animated.parallel(
      anims.flatMap((a,i)=>[
        Animated.timing(a.op,{toValue:1,duration:420,delay:i*55,useNativeDriver:true}),
        Animated.timing(a.sl,{toValue:0,duration:360,delay:i*55,easing:Easing.out(Easing.quad),useNativeDriver:true}),
      ])
    ).start();
  },[]);
  const av=(i:number)=>({opacity:anims[i]?.op,transform:[{translateY:anims[i]?.sl}]});

  // ── Helpers ──
  function SectionHead({label,icon}:{label:string;icon:string}){
    return(
      <View style={{flexDirection:"row",alignItems:"center",gap:8,marginTop:4}}>
        <Text style={{fontSize:14}}>{icon}</Text>
        <Text style={{color:C.isDark?"rgba(196,181,253,0.9)":"#3B0764",fontSize:10,
          fontFamily:"Nunito_700Bold",letterSpacing:1.5}}>{label}</Text>
        <View style={{flex:1,height:1,backgroundColor:C.isDark?"rgba(139,92,246,0.2)":"rgba(109,40,217,0.45)"}}/>
      </View>
    );
  }

  function BigCard({icon,title,desc,col,badge,idx}:{icon:string;title:string;desc:string;col:string;badge:"most"|"critical"|"decision";idx:number}){
    return(
      <Animated.View style={av(idx)}>
        <View style={{borderRadius:16,borderWidth:1.5,
          borderColor:C.isDark?`${col}35`:`${col}55`,
          padding:16,gap:10,
          backgroundColor:C.isDark?"rgba(255,255,255,0.04)":C.bgCard,
          shadowColor:col,
          shadowOffset:{width:0,height:C.isDark?0:3},
          shadowOpacity:C.isDark?0.22:0.18,shadowRadius:C.isDark?14:10,elevation:C.isDark?5:3}}>
          <PipBadge type={badge}/>
          <View style={{flexDirection:"row",alignItems:"flex-start",gap:12}}>
            <View style={{width:44,height:44,borderRadius:13,
              backgroundColor:C.isDark?`${col}18`:`${col}25`,
              alignItems:"center",justifyContent:"center",flexShrink:0,
              borderWidth:C.isDark?0:1,borderColor:`${col}40`}}>
              <Text style={{fontSize:22}}>{icon}</Text>
            </View>
            <View style={{flex:1,gap:4}}>
              <Text style={{color:C.text,fontSize:14,fontFamily:"Nunito_700Bold",lineHeight:20}}>{title}</Text>
              <Text style={{color:C.isDark?C.textMuted:"#374151",fontSize:11,fontFamily:"Nunito_500Medium",lineHeight:16}}>{desc}</Text>
            </View>
          </View>
          <View style={{height:1,backgroundColor:C.isDark?"rgba(255,255,255,0.06)":`${col}30`}}/>
          <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
            <View style={{width:6,height:6,borderRadius:3,backgroundColor:col}}/>
            <Text style={{color:C.isDark?`${col}CC`:col,fontSize:9,fontFamily:"Nunito_700Bold"}}>
              Calculated live with your kundli data
            </Text>
          </View>
        </View>
      </Animated.View>
    );
  }

  function SmallCard({icon,title,desc,col,locked,badge,idx}:{icon:string;title:string;desc:string;col:string;locked?:boolean;badge?:"premium"|"secret"|"critical";idx:number}){
    if(locked){
      return(
        <Animated.View style={av(idx)}>
          <View style={{borderRadius:14,borderWidth:1,borderStyle:"dashed" as any,
            borderColor:C.isDark?"rgba(139,92,246,0.35)":"rgba(109,40,217,0.35)",padding:13,gap:6,
            backgroundColor:C.isDark?"rgba(20,5,40,0.7)":"#FFFFFF"}}>
            <View style={{flexDirection:"row",alignItems:"center",gap:10}}>
              <View style={{width:36,height:36,borderRadius:10,backgroundColor:C.isDark?"rgba(139,92,246,0.12)":"rgba(109,40,217,0.18)",
                alignItems:"center",justifyContent:"center",opacity:C.isDark?0.6:1}}>
                <Text style={{fontSize:18}}>{icon}</Text>
              </View>
              <View style={{flex:1,gap:3}}>
                <Text style={{color:C.isDark?"rgba(196,181,253,0.65)":"#4C1D95",fontSize:12,
                  fontFamily:"Nunito_700Bold"}}>{title}</Text>
                <View style={{flexDirection:"row",alignItems:"center",gap:4}}>
                  <Feather name="lock" size={9} color={C.isDark?"#a78bfa":"#5B21B6"}/>
                  <Text style={{color:C.isDark?"#a78bfa":"#5B21B6",fontSize:9,fontFamily:"Nunito_700Bold"}}>{t.km_unlockReveal}</Text>
                </View>
              </View>
            </View>
            {/* fake blurred lines */}
            {[0.5,0.3].map((op,k)=>(
              <View key={k} style={{height:6,borderRadius:3,opacity:op,
                backgroundColor:C.isDark?"rgba(139,92,246,0.25)":"rgba(99,102,241,0.2)",
                width:`${65-k*15}%` as any}}/>
            ))}
          </View>
        </Animated.View>
      );
    }
    return(
      <Animated.View style={av(idx)}>
        <View style={{borderRadius:14,borderWidth:1.5,
          borderColor:C.isDark?`${col}28`:`${col}50`,
          padding:13,gap:6,
          backgroundColor:C.isDark?"rgba(255,255,255,0.035)":C.bgCard,
          shadowColor:col,shadowOffset:{width:0,height:C.isDark?0:2},
          shadowOpacity:C.isDark?0:0.14,shadowRadius:6,elevation:C.isDark?0:2}}>
          <View style={{flexDirection:"row",alignItems:"flex-start",gap:10}}>
            <View style={{width:36,height:36,borderRadius:10,
              backgroundColor:C.isDark?`${col}18`:`${col}25`,
              alignItems:"center",justifyContent:"center",flexShrink:0,
              borderWidth:C.isDark?0:1,borderColor:`${col}40`}}>
              <Text style={{fontSize:18}}>{icon}</Text>
            </View>
            <View style={{flex:1,gap:4}}>
              {badge&&<PipBadge type={badge}/>}
              <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_700Bold",lineHeight:17}}>{title}</Text>
              <Text style={{color:C.isDark?C.textMuted:"#374151",fontSize:10,fontFamily:"Nunito_500Medium",lineHeight:14}}>{desc}</Text>
            </View>
          </View>
        </View>
      </Animated.View>
    );
  }

  function FutureCard({icon,label,col,idx}:{icon:string;label:string;col:string;idx:number}){
    return(
      <Animated.View style={[{width:"47%"},av(idx)]}>
        <View style={{borderRadius:13,borderWidth:1.5,
          borderColor:C.isDark?`${col}28`:`${col}55`,
          padding:12,gap:5,
          backgroundColor:C.isDark?"rgba(255,255,255,0.035)":C.bgCard,
          shadowColor:col,shadowOffset:{width:0,height:C.isDark?0:2},
          shadowOpacity:C.isDark?0:0.15,shadowRadius:5,elevation:C.isDark?0:2,
          alignItems:"center"}}>
          <Text style={{fontSize:22}}>{icon}</Text>
          <Text style={{color:C.text,fontSize:11,fontFamily:"Nunito_700Bold",textAlign:"center",lineHeight:15}}>{label}</Text>
          <View style={{backgroundColor:C.isDark?`${col}18`:`${col}30`,borderRadius:8,
            paddingHorizontal:8,paddingVertical:3,
            borderWidth:1,borderColor:C.isDark?`${col}30`:`${col}70`}}>
            <Text style={{color:C.isDark?col:col,fontSize:8,fontFamily:"Nunito_700Bold"}}>{t.km_onCalculate}</Text>
          </View>
        </View>
      </Animated.View>
    );
  }

  function HiddenCard({icon,title,desc,idx}:{icon:string;title:string;desc:string;idx:number}){
    return(
      <Animated.View style={[{width:"47%"},av(idx)]}>
        <View style={{borderRadius:13,borderWidth:1.5,borderStyle:"dashed" as any,
          borderColor:C.isDark?"rgba(192,132,252,0.4)":"rgba(109,40,217,0.4)",
          padding:12,gap:5,
          backgroundColor:C.isDark?"rgba(30,5,50,0.7)":"#FFFFFF",alignItems:"center",
          shadowColor:"#7c3aed",shadowOffset:{width:0,height:C.isDark?0:2},
          shadowOpacity:C.isDark?0:0.1,shadowRadius:5,elevation:C.isDark?0:2}}>
          <View style={{width:36,height:36,borderRadius:10,
            backgroundColor:C.isDark?"rgba(192,132,252,0.12)":"rgba(109,40,217,0.1)",
            alignItems:"center",justifyContent:"center"}}>
            <Text style={{fontSize:18}}>{icon}</Text>
          </View>
          <PipBadge type="secret"/>
          <Text style={{color:C.isDark?"rgba(240,171,252,0.7)":"#3B0764",fontSize:10,
            fontFamily:"Nunito_700Bold",textAlign:"center",lineHeight:14}}>{title}</Text>
          <Text style={{color:C.isDark?C.textDim:"#5B21B6",fontSize:9,fontFamily:"Nunito_500Medium",textAlign:"center",lineHeight:13}}>{desc}</Text>
        </View>
      </Animated.View>
    );
  }

  return(
    <View style={{gap:14}}>

      {/* ══ 0 ══ HERO ══════════════════════════════════════════════════════════ */}
      <Animated.View style={av(0)}>
        <LinearGradient
          colors={C.isDark?["#1e0040","#0d001a","#0B0F19"]:["#EDE9FE","#DDD6FE","#F5F3FF"]}
          start={{x:0,y:0}} end={{x:1,y:1}}
          style={{borderRadius:18,padding:14,borderWidth:1.5,borderColor:C.isDark?"rgba(139,92,246,0.35)":"rgba(109,40,217,0.45)",
            shadowColor:"#7c3aed",shadowOffset:{width:0,height:4},shadowOpacity:C.isDark?0.25:0.18,shadowRadius:14,elevation:8}}>
          {/* Title row */}
          <View style={{flexDirection:"row",alignItems:"center",gap:8,marginBottom:6}}>
            <Text style={{fontSize:22}}>⚡</Text>
            <View style={{flex:1}}>
              <Text style={{color:C.isDark?"#f5f3ff":"#3b0764",fontSize:15,fontFamily:"Nunito_700Bold",lineHeight:22}}>
                Your Relationship Truth Revealed
              </Text>
              <Text style={{color:C.isDark?"rgba(196,181,253,0.8)":"#5b21b6",fontSize:10,
                fontFamily:"Nunito_400Regular",lineHeight:15,marginTop:2}}>
                Know if this will succeed, struggle, or break over time
              </Text>
            </View>
          </View>

          {/* Inline stats — replaces boxed grid */}
          <View style={{flexDirection:"row",alignItems:"center",justifyContent:"center",gap:6,
            paddingVertical:6,borderTopWidth:1,borderBottomWidth:1,
            borderColor:C.isDark?"rgba(139,92,246,0.15)":"rgba(109,40,217,0.4)",marginBottom:10}}>
            {[["36","Points"],["12","Insights"],["8","Checks"]].map(([n,l],i)=>(
              <View key={l} style={{flexDirection:"row",alignItems:"center",gap:i<2?6:0}}>
                <Text style={{color:C.isDark?"#a78bfa":"#4C1D95",fontSize:13,fontFamily:"Nunito_700Bold"}}>{n} </Text>
                <Text style={{color:C.isDark?C.textMuted:"#5B21B6",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{l}</Text>
                {i<2&&<Text style={{color:C.isDark?"rgba(139,92,246,0.3)":"rgba(109,40,217,0.5)",fontSize:13,marginLeft:6}}>•</Text>}
              </View>
            ))}
          </View>

          {/* Compact progress bar */}
          <View style={{gap:5}}>
            <View style={{flexDirection:"row",justifyContent:"space-between",alignItems:"center"}}>
              <Text style={{color:C.isDark?"rgba(196,181,253,0.8)":"#4C1D95",fontSize:10,fontFamily:"Nunito_700Bold"}}>
                Compatibility Score
              </Text>
              <Text style={{color:C.isDark?"#a78bfa":"#3B0764",fontSize:12,fontFamily:"Nunito_700Bold"}}>72%</Text>
            </View>
            <View style={{height:6,borderRadius:3,backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(109,40,217,0.2)",overflow:"hidden"}}>
              <LinearGradient colors={["#6366f1","#8B5CF6","#6D5DF6"]}
                start={{x:0,y:0}} end={{x:1,y:0}}
                style={{width:"72%",height:"100%",borderRadius:3}}/>
            </View>
            <Text style={{color:C.textDim,fontSize:8,fontFamily:"Nunito_400Regular"}}>
              Sample preview — real score from your kundli
            </Text>
          </View>
        </LinearGradient>
      </Animated.View>

      {/* ══ 1 ══ SECTION: TOP INSIGHTS ════════════════════════════════════════ */}
      <Animated.View style={av(1)}><SectionHead label={t.km_secTopInsights} icon="🔥"/></Animated.View>

      {/* ══ 2-4 ══ THREE BIG CARDS ════════════════════════════════════════════ */}
      <BigCard idx={2} icon="❤️" col="#f43f5e" badge="most"
        title={t.km_coreCompTitle}
        desc={t.km_coreCompDesc}/>
      <BigCard idx={3} icon="⚠️" col="#ef4444" badge="critical"
        title={t.km_riskScanTitle}
        desc={t.km_riskScanDesc}/>

      {/* ══ 4 ══ MARRIAGE DECISION CARD (replaces Final Verdict) ══════════════ */}
      <Animated.View style={av(4)}>
        <LinearGradient
          colors={C.isDark?["rgba(251,191,36,0.12)","rgba(249,115,22,0.08)"]:["#FEF3C7","#FDE68A"]}
          start={{x:0,y:0}} end={{x:1,y:1}}
          style={{borderRadius:16,borderWidth:1.5,borderColor:C.isDark?"rgba(251,191,36,0.4)":"rgba(180,83,9,0.55)",padding:16,gap:10,
            shadowColor:"#fbbf24",shadowOffset:{width:0,height:0},shadowOpacity:0.25,shadowRadius:16,elevation:6}}>
          <PipBadge type="decision"/>
          <View style={{flexDirection:"row",alignItems:"flex-start",gap:12}}>
            <View style={{width:44,height:44,borderRadius:13,backgroundColor:"rgba(251,191,36,0.18)",
              alignItems:"center",justifyContent:"center",flexShrink:0}}>
              <Text style={{fontSize:22}}>💍</Text>
            </View>
            <View style={{flex:1,gap:4}}>
              <Text style={{color:C.text,fontSize:14,fontFamily:"Nunito_700Bold",lineHeight:20}}>
                Marriage Decision
              </Text>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",lineHeight:16}}>
                Should you marry, wait, or rethink? Vedic Jyotish final answer
              </Text>
            </View>
          </View>
          {/* YES / WAIT / RISK pills */}
          <View style={{flexDirection:"row",gap:8}}>
            {[
              {l:"✅  YES",  colD:"#22c55e", colL:"#15803D", bg:"rgba(34,197,94,0.12)",  bdr:"rgba(34,197,94,0.4)"},
              {l:"⏳  WAIT", colD:"#fbbf24", colL:"#B45309", bg:"rgba(251,191,36,0.18)", bdr:"rgba(180,83,9,0.4)"},
              {l:"⚠️  RISK", colD:"#ef4444", colL:"#B91C1C", bg:"rgba(239,68,68,0.12)",  bdr:"rgba(239,68,68,0.4)"},
            ].map(({l,colD,colL,bg,bdr})=>(
              <View key={l} style={{flex:1,borderRadius:10,backgroundColor:bg,borderWidth:1,
                borderColor:bdr,paddingVertical:8,alignItems:"center"}}>
                <Text style={{color:C.isDark?colD:colL,fontSize:11,fontFamily:"Nunito_700Bold"}}>{l}</Text>
              </View>
            ))}
          </View>
          <View style={{height:1,backgroundColor:C.isDark?"rgba(255,255,255,0.06)":C.border}}/>
          <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
            <View style={{width:6,height:6,borderRadius:3,backgroundColor:C.isDark?"#fbbf24":"#D97706"}}/>
            <Text style={{color:C.isDark?"rgba(251,191,36,0.9)":"#92400E",fontSize:9,fontFamily:"Nunito_600SemiBold"}}>
              Real-time analysis based on your birth chart
            </Text>
          </View>
        </LinearGradient>
      </Animated.View>


      {/* ══ 6 ══ SECTION: DEEP INSIGHTS ══════════════════════════════════════ */}
      <Animated.View style={av(6)}><SectionHead label={t.km_secDeepInsights} icon="🧠"/></Animated.View>
      <SmallCard idx={7}  icon="🧠" col="#34d399" badge="premium"
        title={t.km_personMatchTitle}
        desc={t.km_personMatchDesc}/>
      <SmallCard idx={8}  icon="🌙" col="#a78bfa" locked
        title={t.km_soulKarmaTitle}
        desc={t.km_soulKarmaDesc}/>
      <SmallCard idx={9}  icon="🔥" col="#f97316" badge="premium"
        title={t.km_intimacyTitle}
        desc={t.km_intimacyDesc}/>

      {/* ══ 10 ══ SECTION: ADVANCED ANALYSIS ════════════════════════════════ */}
      <Animated.View style={av(10)}><SectionHead label={t.km_secAdvAnalysis} icon="🔯"/></Animated.View>
      <SmallCard idx={11} icon="🔯" col="#fbbf24" badge="critical"
        title={t.km_doshaEngTitle}
        desc={t.km_doshaEngDesc}/>
      <SmallCard idx={12} icon="🌑" col="#6366f1" locked
        title={t.km_negEnergyTitle}
        desc={t.km_negEnergyDesc}/>
      <SmallCard idx={13} icon="⚖️" col="#22c55e" badge="premium"
        title={t.km_strChalTitle}
        desc={t.km_strChalDesc}/>
      <SmallCard idx={14} icon="🌿" col="#10b981" badge="premium"
        title={t.km_remAdvTitle}
        desc={t.km_remAdvDesc}/>

      {/* ══ 15 ══ SECTION: FUTURE INSIGHTS ══════════════════════════════════ */}
      <Animated.View style={av(15)}><SectionHead label={t.km_secFutInsights} icon="📅"/></Animated.View>
      <View style={{flexDirection:"row",flexWrap:"wrap",gap:10}}>
        <FutureCard idx={16} icon="💍" label={t.km_marriageTime}  col="#a78bfa"/>
        <FutureCard idx={16} icon="👶" label={t.km_childPlan}     col="#34d399"/>
        <FutureCard idx={16} icon="💰" label={t.km_finCompat}     col="#fbbf24"/>
        <FutureCard idx={16} icon="🏠" label={t.km_lifeStab}      col="#818cf8"/>
      </View>

      {/* ══ 17 ══ SECTION: HIDDEN PREMIUM ════════════════════════════════════ */}
      <Animated.View style={av(17)}>
        <LinearGradient colors={C.isDark?["rgba(120,40,240,0.22)","rgba(79,7,120,0.14)"]:["#FFFFFF","#F5F3FF"]}
          start={{x:0,y:0}} end={{x:1,y:0}}
          style={{borderRadius:14,padding:14,borderWidth:1.5,
            borderColor:C.isDark?"rgba(192,132,252,0.4)":"rgba(109,40,217,0.4)",gap:4}}>
          <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
            <Text style={{fontSize:18}}>⚠️</Text>
            <Text style={{color:C.isDark?"#f0abfc":"#4C1D95",fontSize:12,fontFamily:"Nunito_700Bold",flex:1}}>
              {t.km_secHidPremium}
            </Text>
            <PipBadge type="secret"/>
          </View>
          <Text style={{color:C.isDark?C.textMuted:"#5B21B6",fontSize:10,fontFamily:"Nunito_500Medium",lineHeight:15}}>
            {t.km_realTimeAnalysis}
          </Text>
        </LinearGradient>
      </Animated.View>
      <View style={{flexDirection:"row",flexWrap:"wrap",gap:10}}>
        <HiddenCard idx={18} icon="🔮" title={t.km_karmRelTitle}  desc={t.km_karmRelDesc}/>
        <HiddenCard idx={19} icon="🌀" title={t.km_pastLifeTitle} desc={t.km_pastLifeDesc}/>
        <HiddenCard idx={20} icon="💔" title={t.km_divorceTitle}  desc={t.km_divorceDesc}/>
        <HiddenCard idx={21} icon="🤝" title={t.km_loyaltyTitle}  desc={t.km_loyaltyDesc}/>
      </View>


    </View>
  );
}

// ── Pro Result Report — 12 sections ──────────────────────────────────────────
function ProResultReport({result,g,C}:{result:Result;g:{label:string;col:string;grad:readonly [string,string]};C:any}){
  const t=useT();
  // Derived metrics (0-100)
  const pct=(n:number,d:number)=>Math.round(Math.min((n/d)*100,100));
  const emotional  = Math.round((pct(result.nadi.score,8)*0.45+pct(result.tara.score,3)*0.3+pct(result.maitri.score,5)*0.25));
  const mental     = pct(result.maitri.score,5);
  const intimacy   = Math.round((pct(result.yoni.score,4)*0.6+pct(result.maitri.score,5)*0.4));
  const comm       = Math.round((pct(result.gana.score,6)*0.5+pct(result.vasya.score,2)*0.5));
  const soulBond   = pct(result.nadi.score,8);
  const karmaLink  = pct(result.tara.score,3);
  const personality= pct(result.gana.score,6);
  const badCount   = [result.nadi,result.gana,result.bhakut,result.maitri,result.yoni,result.tara,result.varna].filter(k=>k.bad).length;
  const riskLevel  = result.total>=27?t.km_riskLow:result.total>=21?t.km_riskModerate:t.km_riskHigh;
  const riskCol    = result.total>=27?"#22c55e":result.total>=21?"#fbbf24":"#ef4444";

  // Staggered fade-in (12 sections) — must not call hook inside map
  const anims=useRef(
    Array.from({length:12},()=>({op:new Animated.Value(0),sl:new Animated.Value(16)}))
  ).current;
  useEffect(()=>{
    Animated.parallel(
      anims.flatMap((a,i)=>[
        Animated.timing(a.op,{toValue:1,duration:480,delay:i*70,useNativeDriver:true}),
        Animated.timing(a.sl,{toValue:0,duration:400,delay:i*70,easing:Easing.out(Easing.quad),useNativeDriver:true}),
      ])
    ).start();
  },[]);
  const s=anims.map(a=>({opacity:a.op,transform:[{translateY:a.sl}]}));

  function SectionLabel({text,col="#a78bfa"}:{text:string;col?:string}){
    return(
      <View style={{flexDirection:"row",alignItems:"center",gap:8,marginBottom:10}}>
        <View style={{width:3,height:14,borderRadius:2,backgroundColor:col}}/>
        <Text style={{color:col,fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.8}}>{text}</Text>
      </View>
    );
  }
  function BarRow({label,pct:p,col,icon}:{label:string;pct:number;col:string;icon:string}){
    return(
      <View style={{gap:5,marginBottom:10}}>
        <View style={{flexDirection:"row",justifyContent:"space-between",alignItems:"center"}}>
          <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
            <Text style={{fontSize:13}}>{icon}</Text>
            <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{label}</Text>
          </View>
          <Text style={{color:col,fontSize:13,fontFamily:"Nunito_700Bold"}}>{p}%</Text>
        </View>
        <View style={{height:6,borderRadius:3,backgroundColor:"rgba(255,255,255,0.07)",overflow:"hidden"}}>
          <LinearGradient colors={[col,col+"99"]} start={{x:0,y:0}} end={{x:1,y:0}}
            style={{height:6,width:`${p}%` as any,borderRadius:3}}/>
        </View>
      </View>
    );
  }
  function StatusChip({label,ok,warn=false}:{label:string;ok:boolean;warn?:boolean}){
    const col=ok?"#22c55e":warn?"#fbbf24":"#ef4444";
    return(
      <View style={{backgroundColor:`${col}18`,borderRadius:10,borderWidth:1,borderColor:`${col}35`,
        paddingHorizontal:10,paddingVertical:4}}>
        <Text style={{color:col,fontSize:10,fontFamily:"Nunito_700Bold"}}>{ok?`✓ ${t.km2_chipClear}`:warn?`~ ${t.km2_chipMild}`:`✗ ${t.km2_chipPresent}`}</Text>
      </View>
    );
  }

  return(
    <View style={{gap:12}}>

      {/* ── 1. Relationship Risk Scan ── */}
      <Animated.View style={s[0]}>
        <GlowCard accent={riskCol} C={C} style={{padding:14}}>
          <SectionLabel text={`1 · ${t.km2_secRiskScan}`} col={riskCol}/>
          <View style={{flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:14}}>
            <View>
              <Text style={{color:C.text,fontSize:22,fontFamily:"Nunito_700Bold"}}>{t.km_riskLevel}</Text>
              <Text style={{color:riskCol,fontSize:16,fontFamily:"Nunito_700Bold",marginTop:2}}>{riskLevel}</Text>
            </View>
            <View style={{width:64,height:64,borderRadius:32,borderWidth:2,borderColor:riskCol,
              backgroundColor:`${riskCol}15`,alignItems:"center",justifyContent:"center"}}>
              <Text style={{fontSize:24}}>{result.total>=27?"🛡️":result.total>=21?"⚡":"⚠️"}</Text>
            </View>
          </View>
          {[
            {label:t.km_compMismatch,    ok:result.total>=21,warn:result.total>=18},
            {label:t.km_doshaConflict,   ok:!result.manglik&&result.nadi.score>0&&result.bhakut.score>0,warn:result.manglik},
            {label:t.km_longTermStab,    ok:result.total>=27,warn:result.total>=21},
          ].map(({label,ok,warn})=>(
            <View key={label} style={{flexDirection:"row",alignItems:"center",justifyContent:"space-between",
              paddingVertical:8,borderBottomWidth:1,borderBottomColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_500Medium"}}>{label}</Text>
              <StatusChip label={label} ok={ok} warn={warn}/>
            </View>
          ))}
        </GlowCard>
      </Animated.View>

      {/* ── 2. Core Compatibility ── */}
      <Animated.View style={s[1]}>
        <GlowCard accent="#f43f5e" C={C} style={{padding:14}}>
          <SectionLabel text={`2 · ${t.km_coreCompTitle.toUpperCase()}`} col="#f9a8d4"/>
          <BarRow label={t.km_emotionalBond} pct={emotional}  col="#f43f5e" icon="❤️"/>
          <BarRow label={t.km_mentalConn}    pct={mental}     col="#818cf8" icon="🧠"/>
          <BarRow label={t.km_intimacyHarm}  pct={intimacy}   col="#f97316" icon="🔥"/>
          <BarRow label={t.km_communication} pct={comm}       col="#34d399" icon="💬"/>
        </GlowCard>
      </Animated.View>

      {/* ── 3. Dosha Engine ── */}
      <Animated.View style={s[2]}>
        <GlowCard accent="#fbbf24" C={C} style={{padding:14}}>
          <SectionLabel text={`3 · ${t.km_doshaEngTitle.toUpperCase()}`} col="#fde68a"/>
          {[
            {icon:"♂️", label:t.km_manglikDosh, ok:!result.manglik,         warn:result.manglik,    desc:result.manglik?t.km_onePartMang:t.km_noMangConf},
            {icon:"🌊", label:t.km_nadiDosh,    ok:!result.nadi.bad,        warn:false,             desc:result.nadi.detail},
            {icon:"🌙", label:t.km_bhakootDosh, ok:!result.bhakut.bad,      warn:false,             desc:result.bhakut.detail},
            {icon:"☯️", label:t.km_ganaDosh,    ok:!result.gana.bad,        warn:result.gana.score===1,desc:result.gana.detail},
            {icon:"✨", label:t.km_grahaMaitri, ok:result.maitri.score>=3,  warn:result.maitri.score===3,desc:result.maitri.detail},
          ].map(({icon,label,ok,warn,desc})=>(
            <View key={label} style={{flexDirection:"row",alignItems:"center",gap:10,paddingVertical:9,
              borderBottomWidth:1,borderBottomColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{fontSize:15,width:22}}>{icon}</Text>
              <View style={{flex:1}}>
                <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{label}</Text>
                <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",marginTop:2}}>{desc}</Text>
              </View>
              <StatusChip label={label} ok={ok} warn={warn}/>
            </View>
          ))}
        </GlowCard>
      </Animated.View>

      {/* ── 4. Future Timeline ── */}
      <Animated.View style={s[3]}>
        <GlowCard accent="#818cf8" C={C} style={{padding:14}}>
          <SectionLabel text={`4 · ${t.km_secFutTimeline}`} col="#c7d2fe"/>
          {[
            {icon:"💍",label:t.km_marriageTime,
             val:result.bhakut.score===7&&result.total>=24?t.km_marrAusp:result.total>=21?t.km_marrModerate:t.km_marrDelay,
             col:result.bhakut.score===7?"#22c55e":"#fbbf24"},
            {icon:"👶",label:t.km_childPlan,
             val:result.yoni.score===4?t.km_natTimingExp:result.yoni.score>0?t.km_slightPatience:t.km_medConsAdv,
             col:result.yoni.score===4?"#22c55e":result.yoni.score>0?"#fbbf24":"#f97316"},
            {icon:"💰",label:t.km_finHarmony,
             val:result.vasya.score===2?t.km_strongFinAlign:t.km_modBudgetHelp,
             col:result.vasya.score===2?"#22c55e":"#fbbf24"},
            {icon:"🏡",label:t.km_familyAccept,
             val:result.gana.score>=4?t.km_highlyLikely:t.km_mayNeedTime,
             col:result.gana.score>=4?"#22c55e":"#fbbf24"},
          ].map(({icon,label,val,col})=>(
            <View key={label} style={{flexDirection:"row",gap:12,paddingVertical:9,alignItems:"flex-start",
              borderBottomWidth:1,borderBottomColor:"rgba(255,255,255,0.05)"}}>
              <View style={{width:36,height:36,borderRadius:10,backgroundColor:`${col}18`,
                alignItems:"center",justifyContent:"center"}}>
                <Text style={{fontSize:16}}>{icon}</Text>
              </View>
              <View style={{flex:1}}>
                <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{label}</Text>
                <Text style={{color:col,fontSize:11,fontFamily:"Nunito_500Medium",marginTop:3,lineHeight:16}}>{val}</Text>
              </View>
            </View>
          ))}
        </GlowCard>
      </Animated.View>

      {/* ── 5. Soul & Karma Analysis ── */}
      <Animated.View style={s[4]}>
        <GlowCard accent="#a78bfa" C={C} style={{padding:14}}>
          <SectionLabel text={`5 · ${t.km_secSoulKarma}`} col="#c4b5fd"/>
          <View style={{flexDirection:"row",justifyContent:"space-around",marginBottom:14}}>
            <View style={{alignItems:"center",gap:6}}>
              <MiniArc pct={soulBond/100} col="#a78bfa" size={64}/>
              <Text style={{color:"#a78bfa",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_soulBond}</Text>
              <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular",textAlign:"center",maxWidth:70}}>
                {soulBond>=75?t.km_deepKarmTie:t.km_growConn}
              </Text>
            </View>
            <View style={{width:1,backgroundColor:"rgba(255,255,255,0.07)"}}/>
            <View style={{alignItems:"center",gap:6}}>
              <MiniArc pct={karmaLink/100} col="#34d399" size={64}/>
              <Text style={{color:"#34d399",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_karmaLink}</Text>
              <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular",textAlign:"center",maxWidth:70}}>
                {karmaLink>=75?t.km_posPastLife:t.km_neutralKarma}
              </Text>
            </View>
          </View>
          <View style={{backgroundColor:"rgba(167,139,250,0.08)",borderRadius:10,padding:10,gap:4}}>
            <Text style={{color:"#c4b5fd",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_nadiNakBond}</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",lineHeight:16}}>
              {result.nadi.score===8 ? t.km3_nadiAlag : t.km3_nadiSama}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 6. Personality Match ── */}
      <Animated.View style={s[5]}>
        <GlowCard accent="#34d399" C={C} style={{padding:14}}>
          <SectionLabel text={`6 · ${t.km2_secPersMatch}`} col="#6ee7b7"/>
          <BarRow label={t.km_natureTemp}    pct={personality} col="#34d399" icon="☯️"/>
          <BarRow label={t.km_socialAlign}   pct={pct(result.vasya.score,2)} col="#a78bfa" icon="🤝"/>
          <BarRow label={t.km_lifestyleHarm} pct={pct(result.varna.score,1)*100>0?80:45} col="#fbbf24" icon="🌿"/>
          <View style={{backgroundColor:"rgba(52,211,153,0.08)",borderRadius:10,padding:10,marginTop:4}}>
            <Text style={{color:"#6ee7b7",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_ganaCompat}</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",marginTop:3,lineHeight:16}}>
              {result.gana.score===6?t.km2_persExcellent
               :result.gana.score>0?t.km2_persModerate
               :t.km2_persChallenging}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 7. Intimacy Compatibility ── */}
      <Animated.View style={s[6]}>
        <GlowCard accent="#f97316" C={C} style={{padding:14}}>
          <SectionLabel text={`7 · ${t.km2_secIntimacyComp}`} col="#fdba74"/>
          <BarRow label={t.km_physicalHarm} pct={pct(result.yoni.score,4)}   col="#f97316" icon="🌺"/>
          <BarRow label={t.km_energeticAttr} pct={pct(result.maitri.score,5)} col="#f43f5e" icon="⚡"/>
          <View style={{backgroundColor:"rgba(249,115,22,0.08)",borderRadius:10,padding:10,marginTop:4}}>
            <Text style={{color:"#fdba74",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_yoniAnalysis}</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",marginTop:3,lineHeight:16}}>
              {result.yoni.score===4?t.km2_yoniExceptional
               :result.yoni.score>0?t.km2_yoniComplementary
               :t.km2_yoniDifferent}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 8. Negative Energy Check ── */}
      <Animated.View style={s[7]}>
        <GlowCard accent={badCount>=3?"#ef4444":"#fbbf24"} C={C} style={{padding:14}}>
          <SectionLabel text={`8 · ${t.km2_secNegEnergy}`} col={badCount>=3?"#fca5a5":"#fde68a"}/>
          <View style={{flexDirection:"row",alignItems:"center",gap:14,marginBottom:12}}>
            <View style={{width:52,height:52,borderRadius:26,
              backgroundColor:badCount===0?"rgba(34,197,94,0.15)":badCount<=2?"rgba(251,191,36,0.15)":"rgba(239,68,68,0.15)",
              borderWidth:1,borderColor:badCount===0?"rgba(34,197,94,0.4)":badCount<=2?"rgba(251,191,36,0.4)":"rgba(239,68,68,0.4)",
              alignItems:"center",justifyContent:"center"}}>
              <Text style={{fontSize:22}}>{badCount===0?"🌟":badCount<=2?"⚡":"🔴"}</Text>
            </View>
            <View>
              <Text style={{color:C.text,fontSize:15,fontFamily:"Nunito_700Bold"}}>{badCount} {badCount!==1?t.km2_concernPlural:t.km2_concernSing} {t.km2_concernsFound}</Text>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",marginTop:2}}>
                {badCount===0?t.km2_negPatExcell
                 :badCount<=2?t.km2_negPatMinor
                 :t.km2_negPatMulti}
              </Text>
            </View>
          </View>
          {[result.nadi,result.bhakut,result.gana,result.yoni].filter(k=>k.bad).map(k=>(
            <View key={k.label} style={{flexDirection:"row",alignItems:"center",gap:8,paddingVertical:7,
              borderTopWidth:1,borderTopColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{fontSize:14}}>⚠️</Text>
              <Text style={{color:"#fca5a5",fontSize:12,fontFamily:"Nunito_600SemiBold",flex:1}}>{k.label} {t.km2_doshDetect}</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>{k.detail}</Text>
            </View>
          ))}
          {badCount===0&&(
            <View style={{flexDirection:"row",alignItems:"center",gap:8,paddingVertical:7,
              borderTopWidth:1,borderTopColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{fontSize:14}}>✅</Text>
              <Text style={{color:"#22c55e",fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{t.km_noNegPatterns}</Text>
            </View>
          )}
        </GlowCard>
      </Animated.View>

      {/* ── 9. Strengths & Challenges ── */}
      <Animated.View style={[{flexDirection:"row",gap:10},s[8]]}>
        <GlowCard accent="#22c55e" C={C} style={{flex:1,padding:12}}>
          <Text style={{color:"#86efac",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.2,marginBottom:8}}>{t.km2_strengthsHdr}</Text>
          {[
            result.nadi.score===8?t.km2_nadiAuspProgeny:t.km2_nadiDeepEmpathy,
            result.maitri.score>=4?t.km_planFriendStrong:t.km_sharedEnergies,
            result.tara.score>0?t.km_taraFav:t.km_modTaraDest,
            result.bhakut.score===7?t.km_bhakSubh:t.km_rashiAlign,
          ].slice(0,result.total>=27?4:2).map((s,i)=>(
            <View key={i} style={{flexDirection:"row",gap:5,marginBottom:5}}>
              <Text style={{color:"#22c55e",fontSize:11,marginTop:1}}>•</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",flex:1,lineHeight:15}}>{s}</Text>
            </View>
          ))}
        </GlowCard>
        <GlowCard accent="#f97316" C={C} style={{flex:1,padding:12}}>
          <Text style={{color:"#fdba74",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.2,marginBottom:8}}>{t.km2_challengesHdr}</Text>
          {[
            result.nadi.bad?t.km_nadiHealth:t.km_minorTempDiff,
            result.gana.bad?t.km_ganaClash:t.km_commPracNeeded,
            result.bhakut.bad?t.km_bhakTimeCaut:t.km_patienceConfl,
            result.yoni.bad?t.km_yoniMismatch:t.km_qualityTimeNeeded,
          ].slice(0,badCount>=2?4:2).map((s,i)=>(
            <View key={i} style={{flexDirection:"row",gap:5,marginBottom:5}}>
              <Text style={{color:"#f97316",fontSize:11,marginTop:1}}>•</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",flex:1,lineHeight:15}}>{s}</Text>
            </View>
          ))}
        </GlowCard>
      </Animated.View>

      {/* ── 10. Remedies & Advice ── */}
      <Animated.View style={s[9]}>
        <GlowCard accent="#a78bfa" C={C} style={{padding:14}}>
          <SectionLabel text={`10 · ${t.km_remAdvTitle.toUpperCase()}`} col="#c4b5fd"/>
          {[
            ...(result.manglik?[{icon:"🔴",text:t.km2_remKumbhVivah}]:[]),
            ...(result.nadi.bad?[{icon:"🌊",text:t.km2_remEkadashi}]:[]),
            ...(result.bhakut.bad?[{icon:"🌙",text:t.km2_remChandraMantra}]:[]),
            ...(result.gana.bad?[{icon:"☯️",text:t.km2_remRudrabhishek}]:[]),
            {icon:"💎",text:t.km2_remGemstones},
            {icon:"🙏",text:t.km2_remSunderkand},
          ].slice(0,5).map(({icon,text},i)=>(
            <View key={i} style={{flexDirection:"row",gap:10,paddingVertical:9,
              borderBottomWidth:1,borderBottomColor:"rgba(255,255,255,0.05)"}}>
              <View style={{width:30,height:30,borderRadius:8,backgroundColor:"rgba(167,139,250,0.15)",
                alignItems:"center",justifyContent:"center"}}>
                <Text style={{fontSize:14}}>{icon}</Text>
              </View>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",flex:1,lineHeight:17}}>{text}</Text>
            </View>
          ))}
        </GlowCard>
      </Animated.View>

      {/* ── 11. Final Verdict ── */}
      <Animated.View style={s[10]}>
        <LinearGradient
          colors={result.total>=27?["#14532d","#166534"]:result.total>=21?["#78350f","#92400e"]:["#7f1d1d","#991b1b"]}
          style={{borderRadius:18,padding:18,borderWidth:1,borderColor:`${g.col}40`,
            shadowColor:g.col,shadowOffset:{width:0,height:0},shadowOpacity:0.3,shadowRadius:12,elevation:8}}>
          <View style={{alignItems:"center",gap:12}}>
            <Text style={{fontSize:32}}>
              {result.total>=32?"🌟":result.total>=27?"💚":result.total>=21?"💛":"❤️‍🩹"}
            </Text>
            <Text style={{color:"#fff",fontSize:16,fontFamily:"Nunito_700Bold",textAlign:"center"}}>{t.km_finalVerdict}</Text>
            <View style={{backgroundColor:"rgba(255,255,255,0.12)",borderRadius:12,paddingHorizontal:20,paddingVertical:8,borderWidth:1,borderColor:"rgba(255,255,255,0.2)"}}>
              <Text style={{color:"#fff",fontSize:18,fontFamily:"Nunito_700Bold",textAlign:"center"}}>{g.label}</Text>
            </View>
            <Text style={{color:"rgba(255,255,255,0.75)",fontSize:12,fontFamily:"Nunito_400Regular",textAlign:"center",lineHeight:19,maxWidth:260}}>
              {result.total>=32?t.km2_fvExceptional
               :result.total>=27?t.km2_fvVeryPositive
               :result.total>=21?t.km2_fvModerate
               :t.km2_fvChallenging}
            </Text>
            <Text style={{color:"rgba(255,255,255,0.5)",fontSize:10,fontFamily:"Nunito_400Regular",textAlign:"center"}}>
              {t.km2_ashtakootScoreLbl}: {result.total}/36 · {badCount} {badCount!==1?t.km2_concernPlural:t.km2_concernSing} {t.km2_concernDetSuffix}
            </Text>
          </View>
        </LinearGradient>
      </Animated.View>

      {/* ── 12. Hidden Insights (Locked) ── */}
      <Animated.View style={s[11]}>
        <View style={{borderRadius:16,overflow:"hidden"}}>
          <View style={{backgroundColor:C.isDark?"rgba(20,10,40,0.85)":"rgba(240,235,255,0.9)",
            borderWidth:1,borderColor:"rgba(139,92,246,0.25)",padding:14,gap:8}}>
            <View style={{flexDirection:"row",alignItems:"center",gap:8,marginBottom:4}}>
              <View style={{width:4,height:4,borderRadius:2,backgroundColor:"#a78bfa"}}/>
              <Text style={{color:"#a78bfa",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.5}}>12 · {t.km_secHidPremium}</Text>
            </View>
            {[
              ["🔮",t.km_pastLifeScore],
              ["🧬",t.km_ancestKarma],
              ["🌌",t.km_nakDream],
              ["💠",t.km_advDoshaRev],
            ].map(([ic,lb],i)=>(
              <View key={i} style={{flexDirection:"row",gap:10,alignItems:"center",
                opacity:0.7-i*0.15,paddingVertical:5}}>
                <View style={{width:32,height:32,borderRadius:8,backgroundColor:"rgba(139,92,246,0.12)"}}/>
                <View style={{height:9,flex:0.7,borderRadius:4,backgroundColor:"rgba(139,92,246,0.18)"}}/>
                <View style={{height:9,flex:0.25,borderRadius:4,backgroundColor:"rgba(139,92,246,0.12)"}}/>
              </View>
            ))}
          </View>
          <LinearGradient
            colors={C.isDark?["transparent","rgba(11,15,25,0.9)","#0B0F19"]:["transparent","rgba(248,250,252,0.92)","#F8FAFC"]}
            style={{position:"absolute",top:0,left:0,right:0,bottom:0,alignItems:"center",justifyContent:"flex-end",paddingBottom:16}}>
            <View style={{alignItems:"center",gap:6}}>
              <View style={{width:44,height:44,borderRadius:22,backgroundColor:"rgba(109,40,217,0.2)",
                borderWidth:1,borderColor:"rgba(139,92,246,0.4)",alignItems:"center",justifyContent:"center"}}>
                <Feather name="lock" size={18} color="#a78bfa"/>
              </View>
              <Text style={{color:"#c4b5fd",fontSize:13,fontFamily:"Nunito_700Bold"}}>+ 12 {t.km_secHidPremium}</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>{t.km_tapUnlock}</Text>
            </View>
          </LinearGradient>
        </View>
      </Animated.View>

      {/* Unlock CTA */}
      <ShineButton colors={["#6366F1","#8B5CF6","#a855f7"]}
        disabled={false} loading={false}
        text={t.km_unlockComplete}
        onPress={()=>Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy)}/>

    </View>
  );
}

// ── Shine Button ──────────────────────────────────────────────────────────────
function ShineButton({onPress,disabled,loading,text,colors}:{onPress():void;disabled:boolean;loading:boolean;text:string;colors:[string,string,string]}){
  const shineX=useRef(new Animated.Value(-200)).current;
  useEffect(()=>{
    const anim=Animated.loop(
      Animated.sequence([
        Animated.timing(shineX,{toValue:400,duration:2000,easing:Easing.linear,useNativeDriver:true}),
        Animated.timing(shineX,{toValue:-200,duration:0,useNativeDriver:true}),
        Animated.delay(1200),
      ])
    );
    anim.start();
    return ()=>anim.stop();
  },[]);
  return(
    <Pressable onPress={onPress} disabled={disabled||loading}
      style={({pressed})=>({opacity:pressed||disabled||loading?0.5:1})}>
      <LinearGradient colors={colors} start={{x:0,y:0}} end={{x:1,y:0}} style={sb.btn}>
        {/* Shine sweep */}
        <Animated.View style={[sb.shine,{transform:[{translateX:shineX}]}]}>
          <LinearGradient colors={["transparent","rgba(255,255,255,0.22)","transparent"]}
            start={{x:0,y:0}} end={{x:1,y:0}} style={{width:80,height:"100%"}}/>
        </Animated.View>
        {loading?<ActivityIndicator color="#fff" size="small"/>:(
          <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
            <Text style={{fontSize:18}}>✨</Text>
            <Text style={sb.txt}>{text}</Text>
          </View>
        )}
      </LinearGradient>
    </Pressable>
  );
}

// ── Main Screen ───────────────────────────────────────────────────────────────
// ──────────────────────────────────────────────────────────────
// PRO KUNDLI SECTION — Dynamic personalized hooks (4 layers)
// ──────────────────────────────────────────────────────────────
interface ProSignals {
  karmic: boolean; emotionalGap: boolean; attraction: boolean;
  stability: boolean; conflict: boolean;
  breakup: "low"|"medium"|"high";
  marriage: "strong"|"average"|"weak";
  manglikImbalance: boolean;
  nameA: string; nameB: string;
  total: number;
}

function buildSignals(p1: PersonData, p2: PersonData): ProSignals {
  const r = compute(p1, p2);
  const manglikImbalance = p1.manglik !== p2.manglik;
  return {
    karmic: r.nadi.score === 0 || r.yoni.score === 0 || manglikImbalance || r.tara.score === 0,
    emotionalGap: r.gana.score <= 1 || r.maitri.score < 3,
    attraction: r.yoni.score >= 3 && r.maitri.score >= 4,
    stability: r.bhakut.score === 7 && r.maitri.score >= 4 && r.total >= 27,
    conflict: r.bhakut.score === 0 || r.gana.score === 0 || r.yoni.score === 0,
    breakup: r.total < 18 || (r.nadi.bad && r.bhakut.bad) ? "high" : r.total < 24 ? "medium" : "low",
    marriage: r.total >= 28 ? "strong" : r.total >= 21 ? "average" : "weak",
    manglikImbalance,
    nameA: p1.name, nameB: p2.name,
    total: r.total,
  };
}

function pickHook<T>(arr:T[], seed:number):T { return arr[seed % arr.length]!; }

interface HookItem { key:string; emoji:string; title:string; text:string; }
function buildProHooks(s: ProSignals, t: any): HookItem[] {
  const seed = (s.total * 17 + s.nameA.length * 31 + s.nameB.length * 13) >>> 0;
  const A = s.nameA, B = s.nameB;

  const emotional = s.emotionalGap && s.karmic
    ? pickHook([
        `${A} aur ${B} ke beech ek connection hai — par feelings ek hi taal par nahi chalti. Iska asli reason chhupa hai`,
        `Dono ka bond asli hai, lekin ek andekha emotional gap hai jo baar-baar dil ko kheenchta hai —`,
      ], seed)
    : s.attraction
    ? pickHook([
        `Ek gehra emotional pull hai jo ${A} ko ${B} ki taraf khinchta rahta hai — aur yeh pull kisi aam vajah se nahi`,
        `Dono ki Moon energy aapas me baat karti hai — yahan ek silent understanding hai jo words se`,
      ], seed+1)
    : s.emotionalGap
    ? pickHook([
        `Upar se sab theek lagta hai, par ek unspoken distance hai jo ${A} aur ${B} mehsoos karte hain`,
        `Ek feeling-gap chhupa hua hai — roz ke pyar me yeh nahi dikhta, lekin crucial moments me`,
      ], seed+2)
    : pickHook([
        `${A} aur ${B} ka emotional rhythm surprisingly aligned hai — iska asli raaz aapki Chandra`,
        `Dono ke feelings ek hi frequency par hain — aur iski wajah sirf pyar nahi, kuch aur`,
      ], seed+3);

  const marriageFuture = s.marriage === "strong"
    ? pickHook([
        `Shaadi ke baad ka safar unusual tareeke se smooth dikhta hai — ek specific planetary support yahan`,
        `Is jodi ka future marriage ek solid foundation par khada hai — par asli turning point kab aayega`,
      ], seed+4)
    : s.marriage === "average"
    ? pickHook([
        `Shaadi possible hai, lekin ek specific year me liya gaya decision is rishte ki direction`,
        `Marriage timing par ek important window khul rahi hai — miss kiya to wait`,
      ], seed+5)
    : pickHook([
        `Shaadi ka rasta hai par usme ek hidden delay baitha hai — yeh kab clear hoga aur kaunsa`,
        `Future marriage par ek particular dasha ka chhaya hai — agle 18 mahine critical`,
      ], seed+6);

  const risks = s.breakup === "high"
    ? pickHook([
        `Agle 6–12 mahine me ek trigger-point aa sakta hai jo rishte ko hila de — yeh kab aur kaise`,
        `Ek repeating pattern exists yahan — aur yeh random nahi, iska root ek specific planetary`,
      ], seed+7)
    : s.conflict
    ? pickHook([
        `Chhote-chhote jhagde random nahi lagte — ek cycle chal raha hai jo specific dates par`,
        `Ek friction pattern dikh raha hai jo aam couples me nahi hota — iska source aur fix`,
      ], seed+8)
    : s.breakup === "medium"
    ? pickHook([
        `Risk medium level par hai — par ek choti si chook ise badha sakti hai, aur woh`,
        `Rishte me ek gray-zone hai jahan dono partners unknowingly distance`,
      ], seed+9)
    : pickHook([
        `Breakup risk bahut kam hai, par ek specific phase aata hai jab dono ko`,
        `Natural risks minimal hain — sirf ek external influence se bachna hoga, aur woh`,
      ], seed+10);

  const karmicBond = s.karmic
    ? pickHook([
        `Yeh connection normal nahi hai — ek purva-janma ka karmic thread yahan active hai jo`,
        `${A} aur ${B} ek karmic loan lekar mile hain — iska poora matlab aur resolution`,
      ], seed+11)
    : s.manglikImbalance
    ? pickHook([
        `Mangal ki energy ek partner me strong hai doosre me nahi — yeh imbalance exactly kaise`,
        `Ek Mangal-based karmic pattern hai jo sirf married life me surface karta hai —`,
      ], seed+12)
    : pickHook([
        `Karmic weight halka hai — par ek sookshm dhaaga dono ko jodta hai jiska source`,
        `Past-life bond subtle hai, fir bhi certain moments me aap dono ko ek strange familiarity`,
      ], seed+13);

  const strengths = s.stability
    ? pickHook([
        `Is rishte me ek silent force hai jo ise tootne nahi deti — chahe kitne fights ho, ek`,
        `Aap dono ki combined kundli me ek rare yoga ban raha hai jo long-term loyalty`,
      ], seed+14)
    : s.attraction
    ? pickHook([
        `Aap dono ki biggest taaqat physical ya emotional nahi — yeh kuch aur hai jo aapne`,
        `Ek unexpected strength is bond me chhupi hai — zyadatar couples ise late realize`,
      ], seed+15)
    : pickHook([
        `Challenges ke bawajood ek hidden anchor hai jo is rishte ko stable rakhta hai —`,
        `Aapke chart me ek subtle planetary shield hai jo is bond ko crises me`,
      ], seed+16);

  const conflictTriggers = s.conflict
    ? pickHook([
        `Repeated fights ka trigger ek specific planet hai — aur woh kis ghar me baitha hai`,
        `Jhagde ka pattern same ghoomta hai — iska precise root aur shaant karne ka tareeka`,
      ], seed+17)
    : s.breakup === "medium"
    ? pickHook([
        `Conflict points kam hain par ek sensitive area hai jahan dono ki bolti alag hoti`,
        `Friction ka source chhupa hai — seedha dikhta nahi, par har bada decision use`,
      ], seed+18)
    : pickHook([
        `Natural clashes minimal hain — par ek specific situation me dono ki energy collide`,
        `Triggers thorey hain, lekin ek specific dasha ke dauran ye tez ho`,
      ], seed+19);

  const stability = s.stability
    ? pickHook([
        `Long-term stability strong hai, par ek subtle phase aayega jab patience`,
        `Is jodi ki tikau shakti impressive hai — par ek external factor jo aap na socho`,
      ], seed+20)
    : s.marriage === "weak"
    ? pickHook([
        `Natural stability kam hai — par ek specific remedy ise dramatically badal sakti`,
        `Bond tikau banane ke liye ek precise jyotish upaay available hai jo`,
      ], seed+21)
    : pickHook([
        `Stability average hai — ek specific saal ke baad rishta settle hota hai, par us`,
        `Tikau kitna hoga, yeh ek chhoti si decision par tik ja raha hai jo aap`,
      ], seed+22);

  const finalOutcome = s.marriage === "strong" && !s.conflict
    ? pickHook([
        `Long-term outcome bright hai, par ek specific choice jo 2 saal ke andar lenge`,
        `Is rishte ka destiny positive hai — sirf ek hidden warning point hai jise`,
      ], seed+23)
    : s.breakup === "high"
    ? pickHook([
        `Current path par rishta critical hai — ek specific remedy direction`,
        `Bina intervention ke trajectory risky hai — par ek mantra-based fix hai jo`,
      ], seed+24)
    : s.marriage === "average"
    ? pickHook([
        `Outcome aapke haath me hai — ek specific year me liya gaya decision 20 saal`,
        `Middle-path hai — but 3 key actions jo agle 6 mahine me hain woh poori`,
      ], seed+25)
    : pickHook([
        `Rishta ek crossroad par hai — ek choti si guidance se poori taraf badal sakta`,
        `Final picture mixed hai — par ek specific jyotish remedy ise sharply positive`,
      ], seed+26);

  return [
    { key:"emotional",  emoji:"❤️",  title:t.km3_insEmotional, text:emotional },
    { key:"marriage",   emoji:"💍", title:t.km3_insMarriage,  text:marriageFuture },
    { key:"risks",      emoji:"⚠️",  title:t.km3_insRisks,     text:risks },
    { key:"karmic",     emoji:"🕉️", title:t.km3_insKarmic,    text:karmicBond },
    { key:"strengths",  emoji:"✨", title:t.km3_insStrength,  text:strengths },
    { key:"triggers",   emoji:"⚡", title:t.km3_insTriggers,  text:conflictTriggers },
    { key:"stability",  emoji:"🛡️", title:t.km3_insStability, text:stability },
    { key:"final",      emoji:"🔮", title:t.km3_insFinal,     text:finalOutcome },
  ];
}

function LockedHook({ item, isDark }:{ item:HookItem; isDark:boolean }) {
  const cut = Math.min(item.text.length, Math.max(40, Math.floor(item.text.length * 0.62)));
  const visible = item.text.slice(0, cut);
  const hidden = item.text.slice(cut) + " Poori detail aur remedy Pro report me dikhegi.";
  return (
    <View style={{
      backgroundColor: isDark ? "rgba(245,158,11,0.06)" : "rgba(124,58,237,0.05)",
      borderColor: isDark ? "rgba(245,158,11,0.28)" : "rgba(124,58,237,0.22)",
      borderWidth: 1, borderRadius: 14, padding: 12, gap: 8, overflow: "hidden",
    }}>
      <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
        <Text style={{fontSize:15}}>{item.emoji}</Text>
        <Text style={{color:isDark?"#fcd34d":"#6d28d9",fontSize:13,fontFamily:"Nunito_800ExtraBold",flex:1}}>
          {item.title}
        </Text>
        <View style={{
          flexDirection:"row",alignItems:"center",gap:3,
          paddingHorizontal:6,paddingVertical:2,borderRadius:8,borderWidth:1,
          backgroundColor:isDark?"rgba(245,158,11,0.15)":"rgba(124,58,237,0.12)",
          borderColor:isDark?"rgba(245,158,11,0.4)":"rgba(124,58,237,0.3)",
        }}>
          <Feather name="lock" size={8} color={isDark?"#f59e0b":"#7C3AED"}/>
          <Text style={{color:isDark?"#f59e0b":"#7C3AED",fontSize:8,fontFamily:"Nunito_800ExtraBold",letterSpacing:0.6}}>PRO</Text>
        </View>
      </View>
      <Text style={{color:isDark?"rgba(226,232,240,0.88)":"#1e293b",fontSize:12,fontFamily:"Nunito_400Regular",lineHeight:19}}>
        {visible}
      </Text>
      <View style={{position:"relative",borderRadius:8,overflow:"hidden",minHeight:42,justifyContent:"center"}}>
        <Text style={{color:isDark?"rgba(226,232,240,0.88)":"#1e293b",fontSize:12,fontFamily:"Nunito_400Regular",lineHeight:19,paddingHorizontal:2}} numberOfLines={3}>
          {hidden}
        </Text>
        <BlurView intensity={Platform.OS==="ios"?22:18} tint={isDark?"dark":"light"} style={StyleSheet.absoluteFillObject}/>
        <LinearGradient
          colors={isDark?["rgba(8,14,30,0)","rgba(8,14,30,0.55)"]:["rgba(255,255,255,0)","rgba(255,255,255,0.6)"]}
          style={StyleSheet.absoluteFillObject} pointerEvents="none"/>
        <View style={{...StyleSheet.absoluteFillObject,alignItems:"center",justifyContent:"center"}} pointerEvents="none">
          <Text style={{fontSize:16}}>🔒</Text>
        </View>
      </View>
    </View>
  );
}

type DeepSection = { title: string; tease: string };
function getDeepSections(lang: string): DeepSection[] {
  const code = (lang || "en").toLowerCase();
  if (code === "hi") return [
    { title: "भावनात्मक तालमेल",  tease: "एक साथी सब कुछ चुपचाप महसूस करता है, दूसरा पूछे जाने का इंतज़ार करता है — दोनों ख़ुद को सब्र वाला मानते हैं —" },
    { title: "विश्वास और वफ़ादारी", tease: "इस रिश्ते में भरोसे की असली परीक्षा एक ख़ास पड़ाव पर आती है — और वो पड़ाव है —" },
    { title: "टकराव का स्वरूप",     tease: "आपके झगड़े वो नहीं होते जो ऊपर से दिखते हैं — असली ट्रिगर एक ख़ास जगह बैठा है —" },
    { title: "विवाह की स्थिरता",    tease: "यह रिश्ता दीर्घकाल स्थिर बन सकता है — बस एक ख़ास बदलाव के बाद, जिसका दोनों पहले विरोध करेंगे।" },
    { title: "प्रतिबद्धता की गहराई", tease: "एक का जुड़ाव गहरा है, दूसरे का इरादा पक्का — पर एक चीज़ है जो अभी दिख नहीं रही —" },
    { title: "आगे की दिशा",         tease: "यह रिश्ता दोनों को इस तरह बदलता है जो किसी ने सोचा भी नहीं था — असली नतीजा एक चुप-से फ़ैसले पर टिका है।" },
  ];
  if (code === "hn") return [
    { title: "Emotional Alignment", tease: "Ek partner sab kuch chuppi mein feel karta hai, doosra poochhe jaane ka wait karta hai — dono khud ko patient maante hain —" },
    { title: "Trust & Loyalty",     tease: "Is rishte mein bharose ka asli imtihaan ek specific phase pe aata hai — aur woh phase hai —" },
    { title: "Conflict Patterns",   tease: "Aapke fights woh nahi hote jo upar se dikhte hain — asli trigger ek specific jagah baitha hai —" },
    { title: "Marriage Stability",  tease: "Yeh rishta long-term stable ban sakta hai — bas ek specific adjustment ke baad, jise dono pehle resist karenge." },
    { title: "Commitment Strength", tease: "Ek ka attachment gehra hai, doosre ka iraada pakka — par ek cheez hai jo abhi dikh nahi rahi —" },
    { title: "Future Direction",    tease: "Yeh rishta dono ko us tarah badalta hai jo dono ne socha bhi nahi tha — asli outcome ek chuppi-bhare faisle pe tika hai." },
  ];
  return [
    { title: "Emotional Alignment", tease: "One of you feels everything in silence. The other waits to be asked. Both think they're the patient one —" },
    { title: "Trust & Loyalty",     tease: "Trust faces its real test at one specific phase in this bond — and that phase is —" },
    { title: "Conflict Patterns",   tease: "Your fights aren't really about what they look like. The real trigger sits in one specific area of —" },
    { title: "Marriage Stability",  tease: "This bond can become stable long-term — but only after one specific adjustment that both of you will resist at first." },
    { title: "Commitment Strength", tease: "One of you is deeply attached, the other quietly committed — but one thing isn't visible yet —" },
    { title: "Future Direction",    tease: "This relationship changes both of you in ways neither expected — the real outcome depends on one quiet choice." },
  ];
}

function ProKundliSection({ p1, p2, isDark, t }:{ p1:PersonData|null; p2:PersonData|null; isDark:boolean; t:any }) {
  const canBuild = !!p1 && !!p2;
  const hooks: HookItem[] = canBuild ? buildProHooks(buildSignals(p1!, p2!), t) : [];
  const deepSections = getDeepSections(t.lang);

  return (
    <View style={{gap:14}}>
      {/* LAYER 1 — TOP MESSAGE */}
      <View style={{
        backgroundColor:isDark?"rgba(124,58,237,0.10)":"rgba(124,58,237,0.05)",
        borderWidth:1,borderColor:isDark?"rgba(167,139,250,0.28)":"rgba(124,58,237,0.20)",
        borderRadius:16,padding:14,gap:8,
      }}>
        <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
          <Text style={{fontSize:16}}>🪔</Text>
          <Text style={{color:isDark?"#e9d5ff":"#5b21b6",fontSize:13,fontFamily:"Nunito_800ExtraBold",letterSpacing:0.2}}>
            {t.km3_yourPersAnalysis}
          </Text>
        </View>
        <Text style={{color:isDark?"rgba(226,232,240,0.85)":"#334155",fontSize:12.5,fontFamily:"Nunito_400Regular",lineHeight:19}}>
          {t.km3_kundliBased}
          {"\n\n"}{t.km3_truthsBelow}
          {"\n"}{t.km3_unlockToSee}
        </Text>
      </View>

      {/* LAYER 2 — WHAT YOU WILL UNLOCK */}
      <View style={{
        backgroundColor:isDark?"rgba(255,255,255,0.03)":"rgba(0,0,0,0.02)",
        borderWidth:1,borderColor:isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)",
        borderRadius:16,padding:14,gap:10,
      }}>
        <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
          <Feather name="unlock" size={14} color={isDark?"#f59e0b":"#7C3AED"}/>
          <Text style={{color:isDark?"#f59e0b":"#7C3AED",fontSize:12,fontFamily:"Nunito_800ExtraBold",letterSpacing:1.5}}>
            {t.km3_whatYouUnlock}
          </Text>
        </View>
        <View style={{gap:11}}>
          {deepSections.map((sec,i)=>(
            <View key={i} style={{gap:3}}>
              <View style={{flexDirection:"row",alignItems:"center",gap:7}}>
                <Text style={{color:isDark?"#f59e0b":"#7C3AED",fontSize:11,fontFamily:"Nunito_800ExtraBold",marginTop:0}}>✓</Text>
                <Text style={{color:isDark?"#f5e6c8":"#1e293b",fontSize:12.5,fontFamily:"Nunito_800ExtraBold",letterSpacing:0.15,flex:1}}>
                  {sec.title}
                </Text>
              </View>
              <View style={{flexDirection:"row",alignItems:"flex-start",gap:7,paddingLeft:18}}>
                <Text style={{color:isDark?"rgba(245,158,11,0.7)":"rgba(124,58,237,0.65)",fontSize:11,fontFamily:"Nunito_700Bold",marginTop:1}}>→</Text>
                <Text style={{color:isDark?"rgba(226,232,240,0.72)":"#475569",fontSize:11.5,fontFamily:"Nunito_400Regular",flex:1,lineHeight:17,fontStyle:"italic"}}>
                  {sec.tease}
                </Text>
              </View>
            </View>
          ))}
        </View>
      </View>

      {/* LAYER 3 — LOCKED DYNAMIC HOOKS */}
      {canBuild ? (
        <View style={{gap:10}}>
          <View style={{flexDirection:"row",alignItems:"center",gap:10,marginTop:2}}>
            <View style={{flex:1,height:1,backgroundColor:isDark?"rgba(245,158,11,0.3)":"rgba(124,58,237,0.2)"}}/>
            <Text style={{color:isDark?"#f59e0b":"#7C3AED",fontSize:10,fontFamily:"Nunito_800ExtraBold",letterSpacing:1.8}}>
              {t.km3_lockedPreview}
            </Text>
            <View style={{flex:1,height:1,backgroundColor:isDark?"rgba(245,158,11,0.3)":"rgba(124,58,237,0.2)"}}/>
          </View>
          {hooks.map(h => <LockedHook key={h.key} item={h} isDark={isDark}/>)}
        </View>
      ) : (
        <View style={{
          backgroundColor:isDark?"rgba(245,158,11,0.08)":"rgba(124,58,237,0.06)",
          borderWidth:1,borderStyle:"dashed" as any,
          borderColor:isDark?"rgba(245,158,11,0.35)":"rgba(124,58,237,0.3)",
          borderRadius:14,padding:14,alignItems:"center",gap:6,
        }}>
          <Text style={{fontSize:22}}>💑</Text>
          <Text style={{color:isDark?"#fcd34d":"#6d28d9",fontSize:13,fontFamily:"Nunito_800ExtraBold"}}>
            {t.km3_addBothToUnlock}
          </Text>
          <Text style={{color:isDark?"rgba(255,255,255,0.6)":"rgba(0,0,0,0.55)",fontSize:11,fontFamily:"Nunito_500Medium",textAlign:"center"}}>
            {t.km3_addBothSubtext}
          </Text>
        </View>
      )}
    </View>
  );
}

export default function KundliMilanScreen(){
  const insets=useSafeAreaInsets();
  const C=useC();
  const { LockOverlay } = useFeatureGate("kundli_milan");
  const t=useT();
  const topPad=Platform.OS==="web"?67:insets.top;
  const botPad=Platform.OS==="web"?34:insets.bottom;
  const {kundli:primaryKundli,profiles,primaryProfileId}=useUser();
  const p1Profile=profiles.find(p=>p.id===primaryProfileId);
  const params=useLocalSearchParams<{partnerId?:string}>();

  const [plan,setPlan]=useState<"basic"|"pro">("basic");
  const [addingFor,setAddingFor]=useState<"self"|"partner"|null>(null);
  const [p1,setP1]=useState<PersonData|null>(null);
  const [p2,setP2]=useState<PersonData|null>(null);
  const [p2Profile,setP2Profile]=useState<any|null>(null);
  const [result,setResult]=useState<Result|null>(null);
  const [pdfLoading,setPdfLoading]=useState(false);
  const [calcLoading,setCalcLoading]=useState(false);

  // Auto-load partner from relationship page selection (URL param)
  useEffect(()=>{
    if(!params.partnerId)return;
    const prof=profiles.find(p=>p.id===params.partnerId);
    if(prof?.kundli){
      const marsH=prof.kundli.planets.find((p:any)=>p.name==="Mars")?.house??0;
      setP2({
        name:prof.name,
        nakshatra:prof.kundli.nakshatra ?? "",
        moonSign:prof.kundli.moonSign ?? "",
        manglik:[1,4,7,8,12].includes(marsH),
      });
      setP2Profile(prof);
    }
  },[params.partnerId,profiles]);

  // Pro glow animation
  const glowAnim=useRef(new Animated.Value(0)).current;
  const scaleAnim=useRef(new Animated.Value(1)).current;

  useEffect(()=>{
    if(plan==="pro"){
      Animated.parallel([
        Animated.timing(glowAnim,{toValue:1,duration:500,useNativeDriver:true}),
        Animated.sequence([
          Animated.timing(scaleAnim,{toValue:1.02,duration:150,useNativeDriver:true}),
          Animated.timing(scaleAnim,{toValue:1,duration:200,useNativeDriver:true}),
        ]),
      ]).start();
    }else{
      Animated.timing(glowAnim,{toValue:0,duration:400,useNativeDriver:true}).start();
    }
  },[plan]);

  const autoP1:PersonData|null=primaryKundli?{
    name:p1Profile?.name??t.km_aap,
    nakshatra:primaryKundli.nakshatra ?? "",
    moonSign:primaryKundli.moonSign ?? "",
    manglik:[1,4,7,8,12].includes(primaryKundli.planets.find(p=>p.name==="Mars")?.house??0),
  }:null;
  const person1=autoP1??p1;
  const canCalculate=!!person1&&!!p2;
  const isPro=plan==="pro";

  function handleDone(who:"self"|"partner",data:PersonData){
    if(who==="self")setP1(data); else setP2(data);
    setAddingFor(null);
    setResult(null);
  }
  async function handleCalculate(){
    if(!person1||!p2)return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    // Birth data resolution priority:
    //   1. Saved profile's birthData (when user picked an existing profile)
    //   2. _rawBirth attached by AddKundliForm (when user filled inline form)
    const bd1=p1Profile?.birthData ?? (person1._rawBirth ? {
      day:person1._rawBirth.day, month:person1._rawBirth.month, year:person1._rawBirth.year,
      hour:person1._rawBirth.hour, minute:person1._rawBirth.minute, ampm:person1._rawBirth.ampm,
      place:person1._rawBirth.place,
    } : undefined);
    const bd2=p2Profile?.birthData ?? (p2._rawBirth ? {
      day:p2._rawBirth.day, month:p2._rawBirth.month, year:p2._rawBirth.year,
      hour:p2._rawBirth.hour, minute:p2._rawBirth.minute, ampm:p2._rawBirth.ampm,
      place:p2._rawBirth.place,
    } : undefined);

    if(!bd1||!bd2){
      Alert.alert(
        t.km_birthMissing,
        t.km2_birthMissingBody,
        [{text:t.km_okBtn}]
      );
      return;
    }

    setCalcLoading(true);
    MilanResultStore.clear();

    try{
      const ctrl=new AbortController();
      const timer=setTimeout(()=>ctrl.abort(),18000);
      const resp=await fetch(`${API_BASE}/api/kundli-milan`,{
        method:"POST",
        headers:{"Content-Type":"application/json"},
        body:JSON.stringify({
          p1:{...bd1,name:person1.name},
          p2:{...bd2,name:p2.name},
          lang:t.lang,
        }),
        signal:ctrl.signal,
      });
      clearTimeout(timer);

      if(!resp.ok){
        const errData=await resp.json().catch(()=>({}));
        throw new Error(errData.error||`Server error ${resp.status}`);
      }

      const json=await resp.json();
      MilanResultStore.set(json);

      if(isPro){
        // Pro: transform backend result for inline ProResultReport
        const bk:Record<string,any>={};
        for(const k of json.koots) bk[k.key]=k;
        const r:Result={
          nadi:   bk.nadi   ??{score:0,max:8, label:"Nadi",         detail:"-",bad:true},
          gana:   bk.gana   ??{score:0,max:6, label:"Gana",         detail:"-",bad:true},
          bhakut: bk.bhakut ??{score:0,max:7, label:"Bhakut",       detail:"-",bad:true},
          maitri: bk.maitri ??{score:0,max:5, label:"Graha Maitri", detail:"-",bad:true},
          yoni:   bk.yoni   ??{score:0,max:4, label:"Yoni",         detail:"-",bad:true},
          tara:   bk.tara   ??{score:0,max:3, label:"Tara",         detail:"-",bad:true},
          vasya:  bk.vasya  ??{score:0,max:2, label:"Vasya",        detail:"-",bad:false},
          varna:  bk.varna  ??{score:0,max:1, label:"Varna",        detail:"-",bad:true},
          total:  json.total??0,
          manglik:json.manglik_dosh??false,
        };
        setResult(r);
        Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      }else{
        router.push("/kundli-milan-result" as any);
      }
    }catch(e:any){
      const msg=e?.name==="AbortError"
        ?t.km2_calcFailedBody
        :(e?.message??t.km2_calcFailedBody);
      Alert.alert(t.km_calcFailed,msg,[{text:t.km_okBtn}]);
    }finally{
      setCalcLoading(false);
    }
  }

  /** Generate the premium 12-page PRO PDF and share/save it.
   *  Flow: POST /api/kundli-milan (cached server-side via L1+L2) →
   *  POST /api/kundli-milan/pdf with the JSON → download bytes →
   *  save into local "My Reports" registry → open share sheet.
   *  Fact-locked engine + LLM polish (gpt-4o-mini, Phase 2.5.11.20-A
   *  cache) — never names AI; brand: "Powered by Advanced Cosmic
   *  Intelligence".
   */
  async function handleDownloadProPdf(){
    if(!person1||!p2)return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);

    const bd1=p1Profile?.birthData ?? (person1._rawBirth ? {
      day:person1._rawBirth.day, month:person1._rawBirth.month, year:person1._rawBirth.year,
      hour:person1._rawBirth.hour, minute:person1._rawBirth.minute, ampm:person1._rawBirth.ampm,
      place:person1._rawBirth.place,
    } : undefined);
    const bd2=p2Profile?.birthData ?? (p2._rawBirth ? {
      day:p2._rawBirth.day, month:p2._rawBirth.month, year:p2._rawBirth.year,
      hour:p2._rawBirth.hour, minute:p2._rawBirth.minute, ampm:p2._rawBirth.ampm,
      place:p2._rawBirth.place,
    } : undefined);
    if(!bd1||!bd2){
      Alert.alert(t.km_birthMissing,t.km2_birthMissingBody,[{text:t.km_okBtn}]);
      return;
    }

    setPdfLoading(true);

    // Stable fingerprint of (p1 + p2 + lang) — prevents stale MilanResultStore
    // cached for a previous couple from being reused for this download.
    const fp=(bd:any,nm:string)=>[
      nm||"",bd.day,bd.month,bd.year,bd.hour,bd.minute,(bd.ampm||"").toUpperCase(),
      bd.lat??"",bd.lon??bd.lng??"",bd.tz??"",
    ].join("|");
    const wantFp=`${fp(bd1,person1.name||"")}::${fp(bd2,p2.name||"")}::${t.lang}`;

    let timer1:ReturnType<typeof setTimeout>|null=null;
    let timer2:ReturnType<typeof setTimeout>|null=null;
    let tempPath:string|null=null;
    let savedToRegistry=false;

    try{
      // Step 1 — get (or reuse) the milan analysis JSON.
      let milanJson:any = null;
      const cached=MilanResultStore.get() as any;
      if(cached && cached.__cosmicFp===wantFp) milanJson=cached;

      if(!milanJson){
        const ctrl1=new AbortController();
        timer1=setTimeout(()=>ctrl1.abort(),22000);
        const r1=await fetch(`${API_BASE}/api/kundli-milan`,{
          method:"POST",
          headers:{"Content-Type":"application/json"},
          body:JSON.stringify({
            p1:{...bd1,name:person1.name},
            p2:{...bd2,name:p2.name},
            lang:t.lang,
          }),
          signal:ctrl1.signal,
        });
        if(!r1.ok){
          const e=await r1.json().catch(()=>({}));
          throw new Error(e.error||`Server error ${r1.status}`);
        }
        milanJson=await r1.json();
        try{ (milanJson as any).__cosmicFp=wantFp; }catch{/* frozen */}
        MilanResultStore.set(milanJson);
      }

      // Step 2 — POST it to the PDF renderer and write the response bytes to disk.
      const ctrl2=new AbortController();
      timer2=setTimeout(()=>ctrl2.abort(),28000);
      const safe=(s:string)=>(s||"x").replace(/[^a-zA-Z0-9_-]+/g,"_").slice(0,32)||"x";
      const fileName=`Kundli_Milan_${safe(person1.name||"p1")}_${safe(p2.name||"p2")}.pdf`;
      const dest=(FileSystem.cacheDirectory||"")+fileName;

      const r2=await fetch(`${API_BASE}/api/kundli-milan/pdf`,{
        method:"POST",
        headers:{"Content-Type":"application/json","Accept":"application/pdf"},
        body:JSON.stringify(milanJson),
        signal:ctrl2.signal,
      });
      if(!r2.ok){
        const e=await r2.json().catch(()=>({}));
        throw new Error(e.error||`PDF render failed ${r2.status}`);
      }

      // ArrayBuffer → base64 → disk. Smaller (16 KB) chunks + sub-array indexing
      // to avoid stack overflow / huge intermediate strings on PDFs >1 MB.
      const buf=await r2.arrayBuffer();
      const bytes=new Uint8Array(buf);
      const CHUNK=0x4000;
      const parts:string[]=[];
      for(let i=0;i<bytes.length;i+=CHUNK){
        const slice=bytes.subarray(i,Math.min(i+CHUNK,bytes.length));
        let s="";
        for(let j=0;j<slice.length;j++) s+=String.fromCharCode(slice[j]);
        parts.push(s);
      }
      if(typeof globalThis.btoa!=="function") throw new Error("encoding_failed");
      const b64=globalThis.btoa(parts.join(""));
      await FileSystem.writeAsStringAsync(dest,b64,{encoding:FileSystem.EncodingType.Base64});
      tempPath=dest;

      // Step 3 — register in local "My Reports" + open share sheet.
      const total=milanJson?.total ?? 0;
      const max=milanJson?.max ?? 36;
      try{
        await saveLocalReport({
          kind:"milan",
          title:`${person1.name||"Partner 1"} & ${p2.name||"Partner 2"} — Kundli Milan PRO`,
          subtitle:`${total}/${max} · ${new Date().toLocaleDateString()}`,
          sourceUri:tempPath,
        });
        savedToRegistry=true;
      }catch{/* ignore — share still works */}

      const can=await Sharing.isAvailableAsync();
      if(can){
        await Sharing.shareAsync(tempPath,{
          mimeType:"application/pdf",
          dialogTitle:fileName,
          UTI:"com.adobe.pdf",
        });
      }
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }catch(e:any){
      const msg=e?.name==="AbortError"
        ? "PDF download timeout. Internet check kar ke phir try kare."
        : (e?.message ?? "PDF download fail hua. Phir try kare.");
      Alert.alert("PDF Error",msg,[{text:t.km_okBtn||"OK"}]);
    }finally{
      // Always clear abort timers — early throws would otherwise leak them.
      if(timer1) clearTimeout(timer1);
      if(timer2) clearTimeout(timer2);
      // If write succeeded but registry-save AND share both failed mid-way,
      // best-effort delete the temp to avoid cache bloat. saveLocalReport
      // copies into documentDirectory/reports/ so this is safe when saved.
      if(tempPath && !savedToRegistry){
        try{ await FileSystem.deleteAsync(tempPath,{idempotent:true}); }catch{/* ignore */}
      }
      setPdfLoading(false);
    }
  }

  const g=result?grade(result.total):null;

  return(
    <KeyboardAvoidingView style={{flex:1}} behavior={Platform.OS==="ios"?"padding":"height"}>
      <View style={{flex:1,backgroundColor:C.bg}}>

        {/* Pro ambient glow bg */}
        <Animated.View pointerEvents="none"
          style={[ms.glowBg,{opacity:glowAnim}]}>
          <LinearGradient
            colors={["rgba(109,40,217,0.18)","rgba(67,56,202,0.10)","transparent"]}
            locations={[0,0.5,1]}
            style={{flex:1}}/>
        </Animated.View>

        {/* ── Header ── */}
        <LinearGradient
          colors={C.isDark
            ?isPro?["#240041","#0B0F19"]:["#1a0533","#0B0F19"]
            :["#EDE9FE","#F8F9FC"]}
          style={[ms.header,{paddingTop:topPad+4}]}>
          <View style={{flexDirection:"row",alignItems:"center",gap:10}}>
            <Pressable onPress={()=>router.back()} style={ms.backBtn}>
              <Feather name={I18nManager.isRTL ? "arrow-right" : "arrow-left"} size={20} color={C.isDark?"#c4b5fd":C.text}/>
            </Pressable>
            <View style={{flex:1}}>
              <Text style={{color:C.isDark?"#f3e8ff":C.text,fontSize:18,fontFamily:"Nunito_700Bold"}}>{t.kundliMilanTitle}</Text>
              <Text style={{color:"#7c3aed",fontSize:10,fontFamily:"Nunito_400Regular"}}>अष्टकूट गुण मिलान</Text>
            </View>
          </View>

          {/* ── Segmented Basic / Pro Toggle ── */}
          <View style={{alignItems:"center",paddingTop:12,paddingBottom:4}}>
            <View style={[ms.segWrap,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.05)"}]}>
              <Pressable
                onPress={()=>{setPlan("basic");Haptics.selectionAsync();}}
                style={[ms.segBtn,
                  plan==="basic"&&{backgroundColor:C.isDark?"#1e2744":"#4f46e5"}
                ]}>
                <Text style={[ms.segTxt,{color:plan==="basic"?"#fff":C.isDark?"rgba(255,255,255,0.4)":"rgba(0,0,0,0.4)"}]}>{t.km_basic}</Text>
              </Pressable>
              <Pressable
                onPress={()=>{setPlan("pro");Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);}}
                style={[ms.segBtn,{overflow:"hidden"}]}>
                <LinearGradient colors={plan==="pro"?["#7c3aed","#db2777"]:["#5b21b6","#9d174d"]} start={{x:0,y:0}} end={{x:1,y:0}}
                  style={[StyleSheet.absoluteFillObject,{borderRadius:14}]}/>
                <View style={{position:"absolute",top:-8,left:"25%",right:"25%",height:16,borderRadius:8,backgroundColor:plan==="pro"?"rgba(219,39,119,0.3)":"rgba(219,39,119,0.15)"}}/>
                <Text style={[ms.segTxt,{color:"#fff"}]}>✨ Pro</Text>
              </Pressable>
            </View>
          </View>

        </LinearGradient>

        <ScrollView
          contentContainerStyle={[ms.scroll,{paddingBottom:botPad+30}]}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled">


          {/* ── BASIC MODE: Hook + Discovery (always visible) ── */}
          {!isPro&&!result&&(
            <View style={{gap:16}}>

              {/* ── Selected Partner Pill (if loaded from relationship) ── */}
              {p2&&(
                <View style={{flexDirection:"row",alignItems:"center",gap:10,
                  backgroundColor:C.isDark?"rgba(236,72,153,0.10)":"rgba(236,72,153,0.07)",
                  borderWidth:1,borderColor:C.isDark?"rgba(236,72,153,0.28)":"rgba(236,72,153,0.20)",
                  borderRadius:14,paddingHorizontal:12,paddingVertical:10}}>
                  <View style={{width:32,height:32,borderRadius:16,
                    backgroundColor:C.isDark?"rgba(236,72,153,0.18)":"rgba(236,72,153,0.12)",
                    alignItems:"center",justifyContent:"center"}}>
                    <Text style={{fontSize:15}}>💑</Text>
                  </View>
                  <View style={{flex:1}}>
                    <Text style={{color:C.isDark?"rgba(255,255,255,0.55)":"rgba(0,0,0,0.5)",
                      fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:0.8,textTransform:"uppercase"}}>
                      {t.km2_matchingWith}
                    </Text>
                    <Text style={{color:C.text,fontSize:13,fontFamily:"Nunito_800ExtraBold"}} numberOfLines={1}>
                      {p1Profile?.name||t.km2_youPlaceholder}  ✦  {p2.name}
                    </Text>
                  </View>
                  <Pressable onPress={()=>router.back()}
                    style={({pressed})=>({opacity:pressed?0.6:1,padding:6})}>
                    <Feather name="edit-2" size={13} color={C.isDark?"#f472b6":"#db2777"}/>
                  </Pressable>
                </View>
              )}

              {/* ── No Partner Selected: CTA to Relationship page ── */}
              {!p2&&(
                <Pressable onPress={()=>{Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);router.push("/relationship" as any);}}
                  style={({pressed})=>({opacity:pressed?0.85:1,
                    backgroundColor:C.isDark?"rgba(236,72,153,0.10)":"rgba(236,72,153,0.06)",
                    borderWidth:1,borderStyle:"dashed" as any,
                    borderColor:C.isDark?"rgba(236,72,153,0.35)":"rgba(236,72,153,0.30)",
                    borderRadius:16,padding:16,gap:8})}>
                  <View style={{flexDirection:"row",alignItems:"center",gap:10}}>
                    <View style={{width:38,height:38,borderRadius:19,
                      backgroundColor:C.isDark?"rgba(236,72,153,0.18)":"rgba(236,72,153,0.12)",
                      alignItems:"center",justifyContent:"center"}}>
                      <Text style={{fontSize:18}}>💑</Text>
                    </View>
                    <View style={{flex:1}}>
                      <Text style={{color:C.text,fontSize:13,fontFamily:"Nunito_800ExtraBold"}}>
                        Partner Select Karein
                      </Text>
                      <Text style={{color:C.isDark?"rgba(255,255,255,0.55)":"rgba(0,0,0,0.55)",
                        fontSize:10.5,fontFamily:"Nunito_500Medium",marginTop:2}}>
                        Relationship page se partner chunein matching ke liye
                      </Text>
                    </View>
                    <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={16} color={C.isDark?"#f472b6":"#db2777"}/>
                  </View>
                </Pressable>
              )}

              {/* ── Top CTA: Check Now ── */}
              <View>
                <Pressable
                  onPress={()=>{handleCalculate();}}
                  disabled={!person1||!p2||calcLoading}
                  style={({pressed})=>({opacity:(!person1||!p2)?0.5:pressed?0.9:1,overflow:"hidden",borderRadius:16,
                    borderWidth:1,borderColor:"rgba(245,158,11,0.4)"})}>
                  <LinearGradient colors={["#FFD89B","#FFB347"]} start={{x:0,y:0}} end={{x:1,y:0}}
                    style={{paddingVertical:18,alignItems:"center",
                      shadowColor:"#f59e0b",shadowOffset:{width:0,height:6},shadowOpacity:0.55,shadowRadius:16}}>
                    <View style={{flexDirection:"row",alignItems:"center",gap:9}}>
                      <Feather name="zap" size={18} color="#000000"/>
                      <Text style={{color:"#000000",fontSize:18,fontWeight:"800",letterSpacing:0.5,
                        textShadowColor:"rgba(0,0,0,0.15)",textShadowOffset:{width:0,height:1},textShadowRadius:1}}>
                        Check Now
                      </Text>
                    </View>
                  </LinearGradient>
                </Pressable>
                <Text style={{color:C.isDark?"rgba(255,255,255,0.55)":"rgba(0,0,0,0.5)",
                  fontSize:11,fontFamily:"Nunito_500Medium",textAlign:"center",marginTop:8}}>
                  Get your compatibility score in seconds
                </Text>
              </View>

              {/* ── Section Title ── */}
              <View style={{alignItems:"center",gap:6,marginTop:8}}>
                <Text style={{color:C.isDark?"#fbbf24":"#b45309",fontSize:15,fontFamily:"Nunito_800ExtraBold",
                  textTransform:"uppercase",letterSpacing:2.5,
                  textShadowColor:C.isDark?"rgba(251,191,36,0.5)":"rgba(180,83,9,0.25)",
                  textShadowOffset:{width:0,height:0},textShadowRadius:10}}>
                  ✦ What You'll Discover ✦
                </Text>
                <Text style={{color:C.isDark?"rgba(255,255,255,0.6)":"rgba(0,0,0,0.55)",
                  fontSize:11,fontFamily:"Nunito_500Medium"}}>
                  Based on 36 Gun Milan (Ashtakoot matching)
                </Text>
              </View>

              {/* ── 2-Column Detailed Grid ── */}
              <View style={{flexDirection:"row",flexWrap:"wrap",gap:10}}>
                {([
                  {icon:"🔮",title:"Soul Sync",koot:"Varna",desc:"Spiritual & intellectual match",color:"#f59e0b"},
                  {icon:"🧲",title:"Attraction Power",koot:"Vashya",desc:"Mutual attraction & influence",color:"#ef4444"},
                  {icon:"⭐",title:"Destiny Link",koot:"Tara",desc:"Luck & timing alignment",color:"#8b5cf6"},
                  {icon:"🔥",title:"Intimacy Match",koot:"Yoni",desc:"Physical & emotional chemistry",color:"#ec4899"},
                  {icon:"🤝",title:"Emotional Bond",koot:"Graha Maitri",desc:"Heart-to-heart connection",color:"#3b82f6"},
                  {icon:"⚡",title:"Personality Energy",koot:"Gana",desc:"Nature & temperament match",color:"#6366f1"},
                  {icon:"🌙",title:"Life Alignment",koot:"Bhakoot",desc:"Family & life harmony",color:"#14b8a6"},
                  {icon:"💫",title:"Energy Flow",koot:"Nadi",desc:"Deep soul compatibility",color:"#a855f7"},
                ] as const).map((item,i)=>(
                  <View key={i} style={{width:"48%",
                    backgroundColor:"#111827",
                    borderRadius:14,padding:12,gap:6,
                    borderWidth:1,borderColor:"rgba(255,255,255,0.08)",
                    shadowColor:"#000",shadowOffset:{width:0,height:3},
                    shadowOpacity:0.3,shadowRadius:6,elevation:3}}>
                    <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
                      <View style={{width:32,height:32,borderRadius:10,alignItems:"center",justifyContent:"center",
                        backgroundColor:`${item.color}22`}}>
                        <Text style={{fontSize:16}}>{item.icon}</Text>
                      </View>
                      <View style={{flex:1}}>
                        <Text style={{color:"#F3F4F6",fontSize:11,fontFamily:"Nunito_800ExtraBold"}} numberOfLines={1}>
                          {item.title}
                        </Text>
                        <Text style={{color:item.color,fontSize:8,fontFamily:"Nunito_700Bold",
                          textTransform:"uppercase",letterSpacing:0.6}}>
                          {item.koot}
                        </Text>
                      </View>
                    </View>
                    <Text style={{color:"#9CA3AF",fontSize:10,fontFamily:"Nunito_500Medium",lineHeight:14}}>
                      {item.desc}
                    </Text>
                  </View>
                ))}
              </View>

              {/* ── Pro Push Line ── */}
              <Pressable onPress={()=>{setPlan("pro");Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);}}
                style={({pressed})=>({opacity:pressed?0.85:1,marginTop:2,overflow:"hidden",borderRadius:14})}>
                <LinearGradient colors={C.isDark?["rgba(124,58,237,0.18)","rgba(219,39,119,0.18)"]:["rgba(124,58,237,0.1)","rgba(219,39,119,0.1)"]}
                  start={{x:0,y:0}} end={{x:1,y:0}}
                  style={{paddingVertical:12,paddingHorizontal:14,flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8,
                    borderWidth:1,borderColor:C.isDark?"rgba(168,85,247,0.35)":"rgba(124,58,237,0.25)",borderRadius:14}}>
                  <Text style={{fontSize:14}}>✨</Text>
                  <Text style={{color:C.isDark?"#e9d5ff":"#5b21b6",fontSize:13,fontFamily:"Nunito_800ExtraBold"}}>
                    When Vedic meets Tech
                  </Text>
                  <Feather name={I18nManager.isRTL ? "arrow-left" : "arrow-right"} size={14} color={C.isDark?"#e9d5ff":"#5b21b6"}/>
                </LinearGradient>
              </Pressable>

            </View>
          )}


          {/* ── PRO SECTION: 4-Layer Personalized Hooks ── */}
          {isPro&&!result&&(
            <ProKundliSection p1={p1} p2={p2} isDark={C.isDark} t={t}/>
          )}

          {/* ── PRO CTA Buttons ── */}
          {isPro&&!result&&(
            <ShineButton
              colors={["#6366F1","#8B5CF6","#a855f7"]}
              disabled={!canCalculate||pdfLoading} loading={calcLoading||pdfLoading}
              text={pdfLoading?"PDF generate ho raha hai…":(canCalculate?t.km2_unlockFullAnal:!person1&&!p2?t.km2_addBothFirst:!person1?t.km_addYourKundli:t.km_addPartnerKundli)}
              onPress={handleDownloadProPdf}/>
          )}

          {/* ── Results ── */}
          {result&&g&&(
            <>
              {/* Score hero */}
              <LinearGradient
                colors={C.isDark
                  ?isPro?["#1a003a","#0f172a"]:["#1a0533","#0f172a"]
                  :["#f5f3ff","#ede9fe"]}
                style={[ms.scoreHero,{
                  borderColor:isPro?"rgba(139,92,246,0.4)":`${g.col}30`,
                  ...(isPro?{shadowColor:"#8B5CF6",shadowOffset:{width:0,height:0},shadowOpacity:0.4,shadowRadius:20,elevation:12}:{})
                }]}>
                <ScoreRing total={result.total} col={g.col}/>
                <View style={{alignItems:"center",gap:8}}>
                  <View style={[ms.gradeBadge,{backgroundColor:`${g.col}15`,borderColor:`${g.col}35`}]}>
                    <Text style={{color:g.col,fontSize:16,fontFamily:"Nunito_700Bold"}}>{g.label}</Text>
                  </View>
                  {result.manglik&&(
                    <View style={ms.mangChip}>
                      <View style={ms.mangDot}/>
                      <Text style={{color:"#ef4444",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>{t.km_manglikDosh}</Text>
                    </View>
                  )}
                </View>
                <View style={[ms.heroBg,{backgroundColor:"rgba(255,255,255,0.07)"}]}>
                  <LinearGradient colors={isPro?["#6366F1","#8B5CF6","#a855f7"]:g.grad}
                    start={{x:0,y:0}} end={{x:1,y:0}}
                    style={[ms.heroFill,{width:`${Math.round((result.total/36)*100)}%` as any}]}/>
                </View>
              </LinearGradient>

              {/* Pro: Full 12-section report */}
              {isPro&&g&&<ProResultReport result={result} g={g} C={C}/>}

              {/* Recalculate */}
              <Pressable onPress={()=>{setResult(null);Haptics.selectionAsync();}}
                style={[ms.recalcBtn,{borderColor:C.border,backgroundColor:C.bgCard}]}>
                <Feather name="refresh-cw" size={13} color={C.textMuted}/>
                <Text style={{color:C.textMuted,fontSize:12,fontFamily:"Nunito_500Medium"}}>{t.km_recalc}</Text>
              </Pressable>

              {!isPro&&(
                <View style={[ms.upgradeNudge,{backgroundColor:C.isDark?"rgba(109,40,217,0.12)":"rgba(99,102,241,0.06)",borderColor:"rgba(139,92,246,0.2)"}]}>
                  <Text style={{color:C.isDark?"#c4b5fd":"#4f46e5",fontSize:13,fontFamily:"Nunito_700Bold"}}>✨ Want deeper insights?</Text>
                  <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",marginTop:4,marginBottom:12}}>
                    Switch to Pro for detailed Koot analysis, Dosha check, Marriage timing & Remedies.
                  </Text>
                  <Pressable onPress={()=>{setPlan("pro");Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);}}
                    style={({pressed})=>({opacity:pressed?0.8:1})}>
                    <LinearGradient colors={["#6366F1","#8B5CF6","#a855f7"]} start={{x:0,y:0}} end={{x:1,y:0}} style={ms.switchProBtn}>
                      <Text style={{color:"#fff",fontSize:13,fontFamily:"Nunito_700Bold"}}>Switch to Pro →</Text>
                    </LinearGradient>
                  </Pressable>
                </View>
              )}
            </>
          )}


        </ScrollView>

      </View>

      {LockOverlay}
    </KeyboardAvoidingView>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const ms=StyleSheet.create({
  glowBg:    {position:"absolute",top:0,left:0,right:0,height:340,zIndex:0},
  header:    {paddingHorizontal:16,paddingBottom:14,zIndex:1},
  backBtn:   {width:36,height:36,alignItems:"center",justifyContent:"center"},
  toggleWrap:{flexDirection:"row",borderRadius:20,padding:3,gap:2},
  toggleBtn: {paddingHorizontal:11,paddingVertical:6,borderRadius:14,overflow:"hidden"},
  toggleTxt: {fontSize:12,fontFamily:"Nunito_700Bold"},
  scroll:    {paddingHorizontal:16,paddingTop:14,gap:14,zIndex:1},
  secLabel:  {fontSize:10,fontFamily:"Nunito_700Bold",letterSpacing:2},
  heart:     {width:34,height:34,borderRadius:17,alignItems:"center",justifyContent:"center"},

  proBanner: {borderRadius:14,overflow:"hidden"},
  proBannerGrad:{},
  proBannerInner:{flexDirection:"row",alignItems:"center",gap:10,padding:13},
  proLiveDot:{width:6,height:6,borderRadius:3,backgroundColor:"#86efac"},

  previewGrid:{flexDirection:"row",flexWrap:"wrap",gap:10},
  previewCard:{width:"47%",borderRadius:14,borderWidth:1,padding:14,alignItems:"center"},

  basicBtn:  {borderRadius:16,height:54,alignItems:"center",justifyContent:"center"},
  basicBtnTxt:{color:"#fff",fontSize:15,fontFamily:"Nunito_700Bold"},

  scoreHero: {borderRadius:20,borderWidth:1,padding:22,alignItems:"center",gap:14},
  gradeBadge:{borderRadius:20,borderWidth:1,paddingHorizontal:18,paddingVertical:7},
  mangChip:  {flexDirection:"row",alignItems:"center",gap:6,backgroundColor:"rgba(239,68,68,0.1)",borderRadius:12,paddingHorizontal:12,paddingVertical:5},
  mangDot:   {width:6,height:6,borderRadius:3,backgroundColor:"#ef4444"},
  heroBg:    {width:"100%",height:6,borderRadius:3,overflow:"hidden"},
  heroFill:  {height:6,borderRadius:3},

  recalcBtn: {flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8,borderRadius:12,borderWidth:1,paddingVertical:11},
  upgradeNudge:{borderRadius:16,borderWidth:1,padding:16},
  switchProBtn:{borderRadius:12,height:42,alignItems:"center",justifyContent:"center"},
  howCard:   {borderRadius:16,borderWidth:1,padding:16},
  segWrap:   {flexDirection:"row",borderRadius:18,padding:3,gap:3,width:200},
  segBtn:    {flex:1,height:36,borderRadius:14,alignItems:"center",justifyContent:"center"},
  segTxt:    {fontSize:12,fontFamily:"Nunito_800ExtraBold"},
});

const sl=StyleSheet.create({
  filled:  {flexDirection:"row",alignItems:"center",gap:12,borderRadius:16,borderWidth:1,padding:14,overflow:"hidden"},
  glowBar: {position:"absolute",top:0,left:0,width:3,bottom:0,opacity:0.8},
  avatar:  {width:46,height:46,borderRadius:23,borderWidth:1,alignItems:"center",justifyContent:"center"},
  check:   {width:28,height:28,borderRadius:14,alignItems:"center",justifyContent:"center"},
  empty:   {borderRadius:16,borderWidth:1.5,padding:16,alignItems:"center",gap:6},
  addIcon: {width:40,height:40,borderRadius:20,borderWidth:1,alignItems:"center",justifyContent:"center"},
});

const fm=StyleSheet.create({
  wrap:    {borderRadius:16,borderWidth:1,overflow:"hidden"},
  heading: {fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:2,paddingHorizontal:16,paddingTop:14,paddingBottom:8},
  row:     {flexDirection:"row",alignItems:"center",paddingHorizontal:16,paddingVertical:13,gap:10},
  label:   {width:48,fontSize:11,fontFamily:"Nunito_500Medium"},
  input:   {flex:1,fontSize:14,fontFamily:"Nunito_400Regular"},
  sep:     {height:1,marginHorizontal:16},
  errRow:  {flexDirection:"row",alignItems:"center",gap:6,paddingHorizontal:16,paddingTop:8},
  errText: {color:"#ef4444",fontSize:11,fontFamily:"Nunito_400Regular"},
  btns:    {flexDirection:"row",gap:10,padding:14},
  cancelBtn:{flex:0.6,borderRadius:12,borderWidth:1,alignItems:"center",justifyContent:"center",height:44},
  addBtn:  {borderRadius:12,height:44,alignItems:"center",justifyContent:"center"},
});

const lk=StyleSheet.create({
  wrap:    {borderRadius:16,borderWidth:1,overflow:"hidden",padding:16,gap:10,minHeight:180},
  fakeRow: {flexDirection:"row",alignItems:"center",gap:12,paddingVertical:6},
  fakeLabel:{height:10,width:90,borderRadius:5},
  fakeBar:  {height:8,borderRadius:4},
  overlay: {position:"absolute",top:0,left:0,right:0,bottom:0,alignItems:"center",justifyContent:"center"},
  lockContent:{alignItems:"center",paddingTop:60},
  lockCircle:{width:50,height:50,borderRadius:25,backgroundColor:"rgba(109,40,217,0.3)",borderWidth:1,borderColor:"rgba(139,92,246,0.5)",alignItems:"center",justifyContent:"center"},
});

const sb=StyleSheet.create({
  btn:  {borderRadius:16,height:56,alignItems:"center",justifyContent:"center",overflow:"hidden"},
  shine:{position:"absolute",top:0,bottom:0,left:0,width:80,alignItems:"center",justifyContent:"center"},
  txt:  {color:"#fff",fontSize:15,fontFamily:"Nunito_700Bold"},
});
