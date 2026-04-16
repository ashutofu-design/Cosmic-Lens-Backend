import { Feather } from "@expo/vector-icons";
import * as Haptics from "expo-haptics";
import { LinearGradient } from "expo-linear-gradient";
import { router } from "expo-router";
import React, { useEffect, useRef, useState } from "react";
import {
  ActivityIndicator, Animated, Easing, KeyboardAvoidingView, Platform,
  Pressable, ScrollView, StyleSheet, Text, TextInput, View,
} from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import Svg, { Circle } from "react-native-svg";
import { useC } from "@/context/ThemeContext";
import { useUser } from "@/context/UserContext";
import { API_BASE, apiFetch } from "@/lib/apiConfig";

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
        <Text style={{color:C.text,fontSize:14,fontFamily:"Nunito_600SemiBold"}}>{isSelf?"Add Your Kundli":"Add Partner Kundli"}</Text>
        <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular"}}>{isSelf?"Birth details required":"Partner's birth details"}</Text>
      </View>
    </Pressable>
  );
}

// ── Inline Form ───────────────────────────────────────────────────────────────
interface FormProps{title:string;onDone(d:PersonData):void;onCancel():void;}
function AddKundliForm({title,onDone,onCancel}:FormProps){
  const C=useC();
  const [name,setName]=useState(""); const [dob,setDob]=useState("");
  const [time,setTime]=useState(""); const [place,setPlace]=useState("");
  const [err,setErr]=useState(""); const [loading,setLoading]=useState(false);
  async function submit(){
    if(!dob||!time||!place){setErr("Sab fields zaroori hain.");return;}
    setErr(""); setLoading(true);
    try{
      const[day,month,year]=dob.split("/").map(Number);
      const[hm,ap]=time.trim().split(" ");
      const[h,m]=(hm??"").split(":").map(Number);
      if(!day||!month||!year||!h)throw new Error("Format: DD/MM/YYYY & HH:MM AM");
      const res=await apiFetch(`${API_BASE}/api/kundli`,{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({name:name||"Person",day,month,year,hour:h,minute:m??0,ampm:ap??"AM",place})});
      const json=await res.json();
      const marsH=(json.planets as any[])?.find((p:any)=>p.name==="Mars")?.house??0;
      onDone({name:name||"Person",nakshatra:json.nakshatra,moonSign:json.moonSign,manglik:[1,4,7,8,12].includes(marsH)});
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
    }catch(e:any){setErr(e?.message??"Error. Try again.");}
    finally{setLoading(false);}
  }
  const fields=[
    {label:"Name", value:name, set:setName, ph:"Full name",           kb:"default"},
    {label:"Date", value:dob,  set:setDob,  ph:"DD/MM/YYYY",          kb:"numeric"},
    {label:"Time", value:time, set:setTime, ph:"HH:MM  AM / PM",      kb:"default"},
    {label:"Place",value:place,set:setPlace,ph:"E.g. Delhi, India",    kb:"default"},
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
  if(!type)return null;
  type BadgeSpec={bg:string;bdr:string;txtD:string;txtL:string;lbl:string};
  const M:{[k:string]:BadgeSpec}={
    most:    {bg:"rgba(244,63,94,0.15)",  bdr:"rgba(244,63,94,0.45)",   txtD:"#fb7185",txtL:"#be123c",lbl:"MOST IMPORTANT"},
    critical:{bg:"rgba(239,68,68,0.13)",  bdr:"rgba(239,68,68,0.40)",   txtD:"#f87171",txtL:"#dc2626",lbl:"CRITICAL CHECK"},
    decision:{bg:"rgba(249,115,22,0.13)", bdr:"rgba(249,115,22,0.40)",  txtD:"#fb923c",txtL:"#ea580c",lbl:"DECISION CARD"},
    premium: {bg:"rgba(109,93,246,0.12)", bdr:"rgba(109,93,246,0.38)",  txtD:"#c4b5fd",txtL:"#6D5DF6",lbl:"PREMIUM"},
    secret:  {bg:"rgba(147,51,234,0.12)", bdr:"rgba(147,51,234,0.38)",  txtD:"#e879f9",txtL:"#9333ea",lbl:"SECRET"},
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
                  <Text style={{color:C.isDark?"#a78bfa":"#5B21B6",fontSize:9,fontFamily:"Nunito_700Bold"}}>Unlock to reveal hidden truths</Text>
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
            <Text style={{color:C.isDark?col:col,fontSize:8,fontFamily:"Nunito_700Bold"}}>ON CALCULATE</Text>
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
      <Animated.View style={av(1)}><SectionHead label="TOP INSIGHTS" icon="🔥"/></Animated.View>

      {/* ══ 2-4 ══ THREE BIG CARDS ════════════════════════════════════════════ */}
      <BigCard idx={2} icon="❤️" col="#f43f5e" badge="most"
        title="Core Compatibility"
        desc="Are your hearts, minds & souls truly aligned for a lifetime together?"/>
      <BigCard idx={3} icon="⚠️" col="#ef4444" badge="critical"
        title="Risk Scan"
        desc="This insight may change your decision — hidden risks revealed"/>

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
      <Animated.View style={av(6)}><SectionHead label="DEEP INSIGHTS" icon="🧠"/></Animated.View>
      <SmallCard idx={7}  icon="🧠" col="#34d399" badge="premium"
        title="Personality Match"
        desc="This insight may change your decision — see if you truly understand each other"/>
      <SmallCard idx={8}  icon="🌙" col="#a78bfa" locked
        title="Soul & Karma"
        desc="Are you destined? Or is this just timing? Real-time analysis based on your birth chart"/>
      <SmallCard idx={9}  icon="🔥" col="#f97316" badge="premium"
        title="Intimacy Score"
        desc="Physical & emotional bonding — the truth most couples never discover"/>

      {/* ══ 10 ══ SECTION: ADVANCED ANALYSIS ════════════════════════════════ */}
      <Animated.View style={av(10)}><SectionHead label="ADVANCED ANALYSIS" icon="🔯"/></Animated.View>
      <SmallCard idx={11} icon="🔯" col="#fbbf24" badge="critical"
        title="Dosha Engine"
        desc="Mangal, Nadi & Bhakoot — conflicts that silently destroy marriages"/>
      <SmallCard idx={12} icon="🌑" col="#6366f1" locked
        title="Negative Energy"
        desc="Hidden doshas even your astrologer may have missed — don't ignore this"/>
      <SmallCard idx={13} icon="⚖️" col="#22c55e" badge="premium"
        title="Strengths & Challenges"
        desc="What will keep you together — and what may quietly pull you apart"/>
      <SmallCard idx={14} icon="🌿" col="#10b981" badge="premium"
        title="Remedies & Advice"
        desc="Exact pujas, stones & mantras to remove obstacles before they grow"/>

      {/* ══ 15 ══ SECTION: FUTURE INSIGHTS ══════════════════════════════════ */}
      <Animated.View style={av(15)}><SectionHead label="FUTURE INSIGHTS" icon="📅"/></Animated.View>
      <View style={{flexDirection:"row",flexWrap:"wrap",gap:10}}>
        <FutureCard idx={16} icon="💍" label="Marriage Timing"     col="#a78bfa"/>
        <FutureCard idx={16} icon="👶" label="Child Planning"      col="#34d399"/>
        <FutureCard idx={16} icon="💰" label="Financial Compat"    col="#fbbf24"/>
        <FutureCard idx={16} icon="🏠" label="Life Stability"      col="#818cf8"/>
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
              Rare insights even astrologers don't reveal
            </Text>
            <PipBadge type="secret"/>
          </View>
          <Text style={{color:C.isDark?C.textMuted:"#5B21B6",fontSize:10,fontFamily:"Nunito_500Medium",lineHeight:15}}>
            These 4 insights are hidden from most — unlocked only in Pro with your birth data
          </Text>
        </LinearGradient>
      </Animated.View>
      <View style={{flexDirection:"row",flexWrap:"wrap",gap:10}}>
        <HiddenCard idx={18} icon="🔮" title="Karmic Relationship Check" desc="Are you meant to meet in this lifetime?"/>
        <HiddenCard idx={19} icon="🌀" title="Past Life Connection"       desc="Spiritual bond from a previous birth"/>
        <HiddenCard idx={20} icon="💔" title="Divorce / Separation Risk"  desc="Probability based on planetary conflict"/>
        <HiddenCard idx={21} icon="🤝" title="Loyalty & Trust Index"      desc="Chances of betrayal or long-term loyalty"/>
      </View>


    </View>
  );
}

// ── Pro Result Report — 12 sections ──────────────────────────────────────────
function ProResultReport({result,g,C}:{result:Result;g:{label:string;col:string;grad:[string,string]};C:any}){
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
  const riskLevel  = result.total>=27?"Low":result.total>=21?"Moderate":"High";
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
        <Text style={{color:col,fontSize:10,fontFamily:"Nunito_700Bold"}}>{ok?"✓ Clear":warn?"~ Mild":"✗ Present"}</Text>
      </View>
    );
  }

  return(
    <View style={{gap:12}}>

      {/* ── 1. Relationship Risk Scan ── */}
      <Animated.View style={s[0]}>
        <GlowCard accent={riskCol} C={C} style={{padding:14}}>
          <SectionLabel text="1 · RELATIONSHIP RISK SCAN" col={riskCol}/>
          <View style={{flexDirection:"row",alignItems:"center",justifyContent:"space-between",marginBottom:14}}>
            <View>
              <Text style={{color:C.text,fontSize:22,fontFamily:"Nunito_700Bold"}}>Risk Level</Text>
              <Text style={{color:riskCol,fontSize:16,fontFamily:"Nunito_700Bold",marginTop:2}}>{riskLevel}</Text>
            </View>
            <View style={{width:64,height:64,borderRadius:32,borderWidth:2,borderColor:riskCol,
              backgroundColor:`${riskCol}15`,alignItems:"center",justifyContent:"center"}}>
              <Text style={{fontSize:24}}>{result.total>=27?"🛡️":result.total>=21?"⚡":"⚠️"}</Text>
            </View>
          </View>
          {[
            {label:"Compatibility Mismatch",ok:result.total>=21,warn:result.total>=18},
            {label:"Dosha Conflict",        ok:!result.manglik&&result.nadi.score>0&&result.bhakut.score>0,warn:result.manglik},
            {label:"Long-term Stability",   ok:result.total>=27,warn:result.total>=21},
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
          <SectionLabel text="2 · CORE COMPATIBILITY" col="#f9a8d4"/>
          <BarRow label="Emotional Bond"    pct={emotional}  col="#f43f5e" icon="❤️"/>
          <BarRow label="Mental Connection" pct={mental}     col="#818cf8" icon="🧠"/>
          <BarRow label="Intimacy Harmony"  pct={intimacy}   col="#f97316" icon="🔥"/>
          <BarRow label="Communication"     pct={comm}       col="#34d399" icon="💬"/>
        </GlowCard>
      </Animated.View>

      {/* ── 3. Dosha Engine ── */}
      <Animated.View style={s[2]}>
        <GlowCard accent="#fbbf24" C={C} style={{padding:14}}>
          <SectionLabel text="3 · DOSHA ENGINE" col="#fde68a"/>
          {[
            {icon:"♂️", label:"Manglik Dosh",   ok:!result.manglik,         warn:result.manglik,    desc:result.manglik?"One partner is Manglik":"No Manglik conflict"},
            {icon:"🌊", label:"Nadi Dosh",       ok:!result.nadi.bad,        warn:false,             desc:result.nadi.detail},
            {icon:"🌙", label:"Bhakoot Dosh",    ok:!result.bhakut.bad,      warn:false,             desc:result.bhakut.detail},
            {icon:"☯️", label:"Gana Dosh",       ok:!result.gana.bad,        warn:result.gana.score===1,desc:result.gana.detail},
            {icon:"✨", label:"Graha Maitri",    ok:result.maitri.score>=3,  warn:result.maitri.score===3,desc:result.maitri.detail},
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
          <SectionLabel text="4 · FUTURE TIMELINE" col="#c7d2fe"/>
          {[
            {icon:"💍",label:"Marriage Timing",
             val:result.bhakut.score===7&&result.total>=24?"2025–2026 auspicious":result.total>=21?"2026–2027 moderate":"Delay advised — seek guidance",
             col:result.bhakut.score===7?"#22c55e":"#fbbf24"},
            {icon:"👶",label:"Child Planning",
             val:result.yoni.score===4?"Natural timing expected":result.yoni.score>0?"Slight patience recommended":"Medical/expert consultation advised",
             col:result.yoni.score===4?"#22c55e":result.yoni.score>0?"#fbbf24":"#f97316"},
            {icon:"💰",label:"Financial Harmony",
             val:result.vasya.score===2?"Strong financial alignment":"Moderate — budget planning helps",
             col:result.vasya.score===2?"#22c55e":"#fbbf24"},
            {icon:"🏡",label:"Family Acceptance",
             val:result.gana.score>=4?"Highly likely":"May need time and effort",
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
          <SectionLabel text="5 · SOUL & KARMA ANALYSIS" col="#c4b5fd"/>
          <View style={{flexDirection:"row",justifyContent:"space-around",marginBottom:14}}>
            <View style={{alignItems:"center",gap:6}}>
              <MiniArc pct={soulBond/100} col="#a78bfa" size={64}/>
              <Text style={{color:"#a78bfa",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Soul Bond</Text>
              <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular",textAlign:"center",maxWidth:70}}>
                {soulBond>=75?"Deep karmic tie":"Growing connection"}
              </Text>
            </View>
            <View style={{width:1,backgroundColor:"rgba(255,255,255,0.07)"}}/>
            <View style={{alignItems:"center",gap:6}}>
              <MiniArc pct={karmaLink/100} col="#34d399" size={64}/>
              <Text style={{color:"#34d399",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Karma Link</Text>
              <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular",textAlign:"center",maxWidth:70}}>
                {karmaLink>=75?"Positive past life":"Neutral karma"}
              </Text>
            </View>
          </View>
          <View style={{backgroundColor:"rgba(167,139,250,0.08)",borderRadius:10,padding:10,gap:4}}>
            <Text style={{color:"#c4b5fd",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Nadi Nakshatra Bond</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",lineHeight:16}}>
              {result.nadi.score===8
                ?"Alag nadi — auspicious for healthy progeny and long life together."
                :"Sama nadi — strong emotional mirroring, some health caution advised."}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 6. Personality Match ── */}
      <Animated.View style={s[5]}>
        <GlowCard accent="#34d399" C={C} style={{padding:14}}>
          <SectionLabel text="6 · PERSONALITY MATCH" col="#6ee7b7"/>
          <BarRow label="Nature & Temperament" pct={personality} col="#34d399" icon="☯️"/>
          <BarRow label="Social Alignment"      pct={pct(result.vasya.score,2)} col="#a78bfa" icon="🤝"/>
          <BarRow label="Lifestyle Harmony"     pct={pct(result.varna.score,1)*100>0?80:45} col="#fbbf24" icon="🌿"/>
          <View style={{backgroundColor:"rgba(52,211,153,0.08)",borderRadius:10,padding:10,marginTop:4}}>
            <Text style={{color:"#6ee7b7",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Gana Compatibility</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",marginTop:3,lineHeight:16}}>
              {result.gana.score===6?"Excellent — both share similar life approach and values."
               :result.gana.score>0?"Moderate — differences exist but can be harmonised with effort."
               :"Challenging — temperament differences need active work."}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 7. Intimacy Compatibility ── */}
      <Animated.View style={s[6]}>
        <GlowCard accent="#f97316" C={C} style={{padding:14}}>
          <SectionLabel text="7 · INTIMACY COMPATIBILITY" col="#fdba74"/>
          <BarRow label="Physical Harmony"     pct={pct(result.yoni.score,4)} col="#f97316" icon="🌺"/>
          <BarRow label="Energetic Attraction" pct={pct(result.maitri.score,5)} col="#f43f5e" icon="⚡"/>
          <View style={{backgroundColor:"rgba(249,115,22,0.08)",borderRadius:10,padding:10,marginTop:4}}>
            <Text style={{color:"#fdba74",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Yoni Analysis</Text>
            <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",marginTop:3,lineHeight:16}}>
              {result.yoni.score===4?"Same Yoni — exceptional physical and energetic alignment."
               :result.yoni.score>0?"Complementary energies — good compatibility with some adjustments."
               :"Different energies — patience and understanding will strengthen this bond."}
            </Text>
          </View>
        </GlowCard>
      </Animated.View>

      {/* ── 8. Negative Energy Check ── */}
      <Animated.View style={s[7]}>
        <GlowCard accent={badCount>=3?"#ef4444":"#fbbf24"} C={C} style={{padding:14}}>
          <SectionLabel text="8 · NEGATIVE ENERGY CHECK" col={badCount>=3?"#fca5a5":"#fde68a"}/>
          <View style={{flexDirection:"row",alignItems:"center",gap:14,marginBottom:12}}>
            <View style={{width:52,height:52,borderRadius:26,
              backgroundColor:badCount===0?"rgba(34,197,94,0.15)":badCount<=2?"rgba(251,191,36,0.15)":"rgba(239,68,68,0.15)",
              borderWidth:1,borderColor:badCount===0?"rgba(34,197,94,0.4)":badCount<=2?"rgba(251,191,36,0.4)":"rgba(239,68,68,0.4)",
              alignItems:"center",justifyContent:"center"}}>
              <Text style={{fontSize:22}}>{badCount===0?"🌟":badCount<=2?"⚡":"🔴"}</Text>
            </View>
            <View>
              <Text style={{color:C.text,fontSize:15,fontFamily:"Nunito_700Bold"}}>{badCount} Concern{badCount!==1?"s":""} Found</Text>
              <Text style={{color:C.textMuted,fontSize:11,fontFamily:"Nunito_400Regular",marginTop:2}}>
                {badCount===0?"Excellent — no major negative patterns."
                 :badCount<=2?"Minor concerns — manageable with awareness."
                 :"Multiple concerns — remedies strongly advised."}
              </Text>
            </View>
          </View>
          {[result.nadi,result.bhakut,result.gana,result.yoni].filter(k=>k.bad).map(k=>(
            <View key={k.label} style={{flexDirection:"row",alignItems:"center",gap:8,paddingVertical:7,
              borderTopWidth:1,borderTopColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{fontSize:14}}>⚠️</Text>
              <Text style={{color:"#fca5a5",fontSize:12,fontFamily:"Nunito_600SemiBold",flex:1}}>{k.label} Dosh Detected</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>{k.detail}</Text>
            </View>
          ))}
          {badCount===0&&(
            <View style={{flexDirection:"row",alignItems:"center",gap:8,paddingVertical:7,
              borderTopWidth:1,borderTopColor:"rgba(255,255,255,0.05)"}}>
              <Text style={{fontSize:14}}>✅</Text>
              <Text style={{color:"#22c55e",fontSize:12,fontFamily:"Nunito_600SemiBold"}}>No major negative patterns found</Text>
            </View>
          )}
        </GlowCard>
      </Animated.View>

      {/* ── 9. Strengths & Challenges ── */}
      <Animated.View style={[{flexDirection:"row",gap:10},s[8]]}>
        <GlowCard accent="#22c55e" C={C} style={{flex:1,padding:12}}>
          <Text style={{color:"#86efac",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.2,marginBottom:8}}>STRENGTHS 💚</Text>
          {[
            result.nadi.score===8?"Nadi alag — auspicious progeny":"Nadi matched — deep empathy",
            result.maitri.score>=4?"Planetary friendship is strong":"Shared planetary energies",
            result.tara.score>0?"Tara nakshatra is favourable":"Moderate tara destiny",
            result.bhakut.score===7?"Bhakoot shubh — no rashi conflict":"Rashi energies align",
          ].slice(0,result.total>=27?4:2).map((s,i)=>(
            <View key={i} style={{flexDirection:"row",gap:5,marginBottom:5}}>
              <Text style={{color:"#22c55e",fontSize:11,marginTop:1}}>•</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular",flex:1,lineHeight:15}}>{s}</Text>
            </View>
          ))}
        </GlowCard>
        <GlowCard accent="#f97316" C={C} style={{flex:1,padding:12}}>
          <Text style={{color:"#fdba74",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.2,marginBottom:8}}>CHALLENGES ⚡</Text>
          {[
            result.nadi.bad?"Nadi dosh — health awareness needed":"Minor temperament differences",
            result.gana.bad?"Gana clash — nature divergence":"Communication practice needed",
            result.bhakut.bad?"Bhakoot dosh — timing caution":"Some patience during conflicts",
            result.yoni.bad?"Yoni mismatch — energy adjustment":"Regular quality time needed",
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
          <SectionLabel text="10 · REMEDIES & ADVICE" col="#c4b5fd"/>
          {[
            ...(result.manglik?[{icon:"🔴",text:"Kumbh Vivah or Mangal puja recommended before marriage."}]:[]),
            ...(result.nadi.bad?[{icon:"🌊",text:"Fast on Ekadashi — avoid Nadi imbalance with Shiva puja."}]:[]),
            ...(result.bhakut.bad?[{icon:"🌙",text:"Chant Chandra mantra — Om Chandraya Namah 108 times."}]:[]),
            ...(result.gana.bad?[{icon:"☯️",text:"Perform Rudrabhishek together before marriage."}]:[]),
            {icon:"💎",text:"Both should wear compatible gemstones — consult a Jyotishi."},
            {icon:"🙏",text:"Joint puja and regular reading of Sunderkand will strengthen bond."},
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
            <Text style={{color:"#fff",fontSize:16,fontFamily:"Nunito_700Bold",textAlign:"center"}}>Final Verdict</Text>
            <View style={{backgroundColor:"rgba(255,255,255,0.12)",borderRadius:12,paddingHorizontal:20,paddingVertical:8,borderWidth:1,borderColor:"rgba(255,255,255,0.2)"}}>
              <Text style={{color:"#fff",fontSize:18,fontFamily:"Nunito_700Bold",textAlign:"center"}}>{g.label}</Text>
            </View>
            <Text style={{color:"rgba(255,255,255,0.75)",fontSize:12,fontFamily:"Nunito_400Regular",textAlign:"center",lineHeight:19,maxWidth:260}}>
              {result.total>=32?"Exceptional match. Stars align strongly in your favour. A joyful and fulfilling union is indicated."
               :result.total>=27?"Very positive match. With mutual respect and love, this relationship has great potential."
               :result.total>=21?"Moderate match. Awareness, effort, and expert guidance will help this bond flourish."
               :"Challenging match. Remedies, patience, and consulting a Jyotishi are strongly advised before proceeding."}
            </Text>
            <Text style={{color:"rgba(255,255,255,0.5)",fontSize:10,fontFamily:"Nunito_400Regular",textAlign:"center"}}>
              Ashtakoot Score: {result.total}/36 · {badCount} concern{badCount!==1?"s":""} detected
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
              <Text style={{color:"#a78bfa",fontSize:9,fontFamily:"Nunito_700Bold",letterSpacing:1.5}}>12 · HIDDEN INSIGHTS</Text>
            </View>
            {[
              ["🔮","Past Life Connection Score"],
              ["🧬","Ancestral Karma Patterns"],
              ["🌌","Nakshatra Dream Compatibility"],
              ["💠","Advanced Dosha Reversal Plan"],
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
              <Text style={{color:"#c4b5fd",fontSize:13,fontFamily:"Nunito_700Bold"}}>+ 12 Hidden Deep Insights</Text>
              <Text style={{color:C.textMuted,fontSize:10,fontFamily:"Nunito_400Regular"}}>Tap below to unlock everything</Text>
            </View>
          </LinearGradient>
        </View>
      </Animated.View>

      {/* Unlock CTA */}
      <ShineButton colors={["#6366F1","#8B5CF6","#a855f7"]}
        disabled={false} loading={false}
        text="Unlock Complete Report"
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
export default function KundliMilanScreen(){
  const insets=useSafeAreaInsets();
  const C=useC();
  const topPad=Platform.OS==="web"?67:insets.top;
  const botPad=Platform.OS==="web"?34:insets.bottom;
  const {kundli:primaryKundli,profiles,primaryProfileId}=useUser();
  const p1Profile=profiles.find(p=>p.id===primaryProfileId);

  const [plan,setPlan]=useState<"basic"|"pro">("basic");
  const [showUnlock,setShowUnlock]=useState(false);
  const [addingFor,setAddingFor]=useState<"self"|"partner"|null>(null);
  const [p1,setP1]=useState<PersonData|null>(null);
  const [p2,setP2]=useState<PersonData|null>(null);
  const [result,setResult]=useState<Result|null>(null);
  const [calcLoading,setCalcLoading]=useState(false);

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
    name:p1Profile?.name??"Aap",
    nakshatra:primaryKundli.nakshatra,
    moonSign:primaryKundli.moonSign,
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
    if(!isPro){
      router.push({
        pathname: "/kundli-milan-result" as any,
        params: {
          p1Name: person1.name, p1Nak: person1.nakshatra, p1Moon: person1.moonSign, p1Mang: String(person1.manglik),
          p2Name: p2.name, p2Nak: p2.nakshatra, p2Moon: p2.moonSign, p2Mang: String(p2.manglik),
        },
      });
      return;
    }
    setCalcLoading(true);
    await new Promise(r=>setTimeout(r,700));
    setResult(compute(person1,p2));
    setCalcLoading(false);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
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
              <Feather name="arrow-left" size={20} color={C.isDark?"#c4b5fd":C.text}/>
            </Pressable>
            <View style={{flex:1}}>
              <Text style={{color:C.isDark?"#f3e8ff":C.text,fontSize:18,fontFamily:"Nunito_700Bold"}}>Kundli Milan</Text>
              <Text style={{color:"#7c3aed",fontSize:10,fontFamily:"Nunito_400Regular"}}>अष्टकूट गुण मिलान</Text>
            </View>
            <Pressable
              onPress={()=>{setShowUnlock(v=>!v);Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);}}
              style={({pressed})=>({opacity:pressed?0.8:1,overflow:"hidden",borderRadius:10})}>
              <LinearGradient colors={["#f59e0b","#ea580c"]} start={{x:0,y:0}} end={{x:1,y:0}}
                style={{paddingHorizontal:10,paddingVertical:6,borderRadius:10}}>
                <Text style={{color:"#fff",fontSize:9,fontFamily:"Nunito_800ExtraBold",letterSpacing:0.5}}>{showUnlock?"✕ Hide":"🔓 Unlock"}</Text>
              </LinearGradient>
            </Pressable>
          </View>

          {/* ── Segmented Basic / Pro Toggle ── */}
          <View style={{alignItems:"center",paddingTop:12,paddingBottom:4}}>
            <View style={[ms.segWrap,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.05)"}]}>
              <Pressable
                onPress={()=>{setPlan("basic");Haptics.selectionAsync();}}
                style={[ms.segBtn,
                  plan==="basic"&&{backgroundColor:C.isDark?"#1e2744":"#4f46e5"}
                ]}>
                <Text style={[ms.segTxt,{color:plan==="basic"?"#fff":C.isDark?"rgba(255,255,255,0.4)":"rgba(0,0,0,0.4)"}]}>Basic</Text>
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

          {/* ── Pro Badge ── */}
          {isPro&&(
            <Animated.View style={[ms.proBanner,{opacity:glowAnim,transform:[{scale:scaleAnim}]}]}>
              <LinearGradient colors={["#4c1d95","#6d28d9","#7c3aed"]} start={{x:0,y:0}} end={{x:1,y:0}} style={ms.proBannerGrad}>
                <View style={ms.proBannerInner}>
                  <Text style={{fontSize:16}}>✨</Text>
                  <Text style={{color:"#fff",fontSize:13,fontFamily:"Nunito_700Bold",flex:1}}>PRO INSIGHTS UNLOCKED</Text>
                  <View style={ms.proLiveDot}/>
                  <Text style={{color:"rgba(255,255,255,0.7)",fontSize:10,fontFamily:"Nunito_500Medium"}}>LIVE</Text>
                </View>
              </LinearGradient>
            </Animated.View>
          )}

          {/* ── BASIC MODE: Premium conversion screen ── */}
          {!isPro&&!result&&showUnlock&&(
            <View style={{gap:16}}>

              {/* ── Unified Unlock Section ── */}
              <View style={{borderRadius:20,overflow:"hidden",
                borderWidth:1,borderColor:"rgba(245,158,11,0.35)"}}>
                <LinearGradient colors={["#1a0d04","#111827"]}
                  style={{padding:16,gap:14}}>

                  {/* Header */}
                  <View style={{gap:4}}>
                    <View style={{flexDirection:"row",alignItems:"center",gap:7}}>
                      <Text style={{color:"#fbbf24",fontSize:15,fontFamily:"Nunito_800ExtraBold",flex:1}}>
                        Unlock Your Full Relationship Report 🔒
                      </Text>
                      <View style={{backgroundColor:"#b45309",paddingHorizontal:8,paddingVertical:3,borderRadius:8}}>
                        <Text style={{color:"#fff",fontSize:8,fontFamily:"Nunito_700Bold"}}>PRO</Text>
                      </View>
                    </View>
                    <Text style={{color:"rgba(251,191,36,0.7)",fontSize:10,fontFamily:"Nunito_500Medium"}}>
                      See what you're missing about your relationship
                    </Text>
                  </View>

                  {/* Hook */}
                  <View style={{alignItems:"center",paddingVertical:8,
                    backgroundColor:"rgba(124,58,237,0.1)",borderRadius:14,
                    borderWidth:1,borderColor:"rgba(139,92,246,0.15)"}}>
                    <View style={{flexDirection:"row",alignItems:"center",gap:6}}>
                      <Text style={{fontSize:13}}>✦</Text>
                      <Text style={{color:"#e9d5ff",fontSize:15,fontFamily:"Nunito_800ExtraBold"}}>
                        Will This Relationship Work?
                      </Text>
                    </View>
                    <Text style={{color:"#fff",fontSize:10,fontFamily:"Nunito_700Bold",marginTop:2}}>
                      Ancient Vedic wisdom meets modern insights
                    </Text>
                  </View>

                  {/* What You'll Discover */}
                  <View style={{gap:8}}>
                    <View style={{flexDirection:"row",alignItems:"center",justifyContent:"center",gap:8}}>
                      <View style={{height:1,flex:1,backgroundColor:"rgba(245,158,11,0.15)"}}/>
                      <Text style={{color:"#fbbf24",fontSize:9,fontFamily:"Nunito_700Bold",
                        textTransform:"uppercase",letterSpacing:1.5}}>
                        What You'll Discover
                      </Text>
                      <View style={{height:1,flex:1,backgroundColor:"rgba(245,158,11,0.15)"}}/>
                    </View>

                    <View style={{flexDirection:"row",flexWrap:"wrap",gap:6,justifyContent:"center"}}>
                      {([
                        {icon:"🔮",label:"Soul Sync",color:"#f59e0b"},
                        {icon:"🧲",label:"Attraction",color:"#ef4444"},
                        {icon:"⭐",label:"Destiny",color:"#8b5cf6"},
                        {icon:"🔥",label:"Intimacy",color:"#ec4899"},
                        {icon:"🤝",label:"Emotional",color:"#3b82f6"},
                        {icon:"⚡",label:"Personality",color:"#6366f1"},
                        {icon:"🌙",label:"Alignment",color:"#14b8a6"},
                        {icon:"💫",label:"Energy",color:"#a855f7"},
                      ] as const).map((item,i)=>(
                        <View key={i} style={{width:"22%",
                          backgroundColor:"rgba(255,255,255,0.04)",
                          borderRadius:10,paddingVertical:8,paddingHorizontal:3,alignItems:"center",gap:3,
                          borderWidth:1,borderColor:"rgba(255,255,255,0.06)"}}>
                          <View style={{width:24,height:24,borderRadius:12,alignItems:"center",justifyContent:"center",
                            backgroundColor:`${item.color}20`}}>
                            <Text style={{fontSize:11}}>{item.icon}</Text>
                          </View>
                          <Text style={{color:"#E5E7EB",fontSize:7,fontFamily:"Nunito_700Bold",textAlign:"center"}}>{item.label}</Text>
                        </View>
                      ))}
                    </View>
                  </View>

                  {/* Feature List */}
                  <View style={{gap:5}}>
                    {([
                      "Your true emotional & physical compatibility score",
                      "Where this relationship is truly heading",
                      "Strengths that will keep your relationship strong",
                      "Marriage stability & separation risk analysis",
                      "Hidden patterns affecting your bond",
                      "Karmic & past life connection between you",
                      "Final relationship decision (Yes / Wait / Rethink)",
                      "Energy blocks impacting your connection",
                      "Personalized remedies to improve your relationship",
                    ]).map((txt,i)=>(
                      <View key={i} style={{flexDirection:"row",alignItems:"center",gap:8,
                        backgroundColor:"rgba(245,158,11,0.08)",
                        borderRadius:10,paddingHorizontal:10,paddingVertical:7,
                        borderWidth:0.5,borderColor:"rgba(245,158,11,0.18)"}}>
                        <Feather name="lock" size={10} color="#f59e0b"/>
                        <Text style={{color:"#E5E7EB",fontSize:11,fontFamily:"Nunito_500Medium",flex:1}}>{txt}</Text>
                      </View>
                    ))}
                  </View>

                  {/* Unlock Button */}
                  <Pressable onPress={()=>{setPlan("pro");Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);}}
                    style={({pressed})=>({opacity:pressed?0.85:1,marginTop:4})}>
                    <LinearGradient colors={["#ea580c","#f59e0b","#eab308"]} start={{x:0,y:0}} end={{x:1,y:0}}
                      style={{paddingVertical:15,borderRadius:16,alignItems:"center",
                        shadowColor:"#f59e0b",shadowOffset:{width:0,height:5},shadowOpacity:0.5,shadowRadius:14}}>
                      <View style={{flexDirection:"row",alignItems:"center",gap:8}}>
                        <Feather name="unlock" size={16} color="#451a03"/>
                        <Text style={{color:"#451a03",fontSize:15,fontFamily:"Nunito_800ExtraBold",letterSpacing:0.3}}>Unlock Full Report</Text>
                        <Text style={{fontSize:15}}>✨</Text>
                      </View>
                    </LinearGradient>
                  </Pressable>
                </LinearGradient>
              </View>


            </View>
          )}


          {/* ── PRO Preview Insights ── */}
          {isPro&&!result&&<ProInsightsPanel/>}


          {/* ── PRO CTA Buttons ── */}
          {isPro&&!result&&(
            <ShineButton
              colors={["#6366F1","#8B5CF6","#a855f7"]}
              disabled={!canCalculate} loading={calcLoading}
              text={canCalculate?"Unlock Deep Match Analysis":!person1&&!p2?"Add Both Kundlis First":!person1?"Add Your Kundli":"Add Partner Kundli"}
              onPress={handleCalculate}/>
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
                      <Text style={{color:"#ef4444",fontSize:11,fontFamily:"Nunito_600SemiBold"}}>Manglik Dosh</Text>
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
                <Text style={{color:C.textMuted,fontSize:12,fontFamily:"Nunito_500Medium"}}>Recalculate / Change Details</Text>
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
