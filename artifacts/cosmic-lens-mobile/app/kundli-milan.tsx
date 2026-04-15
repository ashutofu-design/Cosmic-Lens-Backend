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

// ── Pro Preview Insights ──────────────────────────────────────────────────────
function ProPreview(){
  const C=useC();
  const items=[
    {icon:"❤️",label:"Emotional Match",val:"82%",col:"#f43f5e",barPct:0.82},
    {icon:"🔥",label:"Attraction",      val:"76%",col:"#f97316",barPct:0.76},
    {icon:"⚠️",label:"Risk Areas",      val:"2",  col:"#fbbf24",barPct:0.25},
  ];
  return(
    <View style={[pv.wrap,{backgroundColor:C.isDark?"rgba(109,40,217,0.08)":"rgba(99,102,241,0.05)",borderColor:"rgba(139,92,246,0.25)"}]}>
      <View style={{flexDirection:"row",alignItems:"center",gap:8,marginBottom:12}}>
        <View style={pv.dot}/>
        <Text style={{color:"#a78bfa",fontSize:11,fontFamily:"Nunito_700Bold",letterSpacing:1}}>SAMPLE PREVIEW</Text>
      </View>
      {items.map(({icon,label,val,col,barPct})=>(
        <View key={label} style={pv.row}>
          <Text style={{fontSize:16,width:24}}>{icon}</Text>
          <View style={{flex:1}}>
            <View style={{flexDirection:"row",justifyContent:"space-between",marginBottom:5}}>
              <Text style={{color:C.text,fontSize:12,fontFamily:"Nunito_600SemiBold"}}>{label}</Text>
              <Text style={{color:col,fontSize:13,fontFamily:"Nunito_700Bold"}}>{val}</Text>
            </View>
            <View style={[pv.bar,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.06)"}]}>
              <View style={[pv.fill,{width:`${Math.round(barPct*100)}%` as any,backgroundColor:col}]}/>
            </View>
          </View>
        </View>
      ))}
    </View>
  );
}

// ── Locked Blur Card ──────────────────────────────────────────────────────────
function LockedCard({C}:{C:any}){
  return(
    <View style={[lk.wrap,{backgroundColor:C.bgCard,borderColor:"rgba(139,92,246,0.2)"}]}>
      {/* Fake blurred rows */}
      {[0.9,0.6,0.4].map((op,i)=>(
        <View key={i} style={[lk.fakeRow,{opacity:op}]}>
          <View style={[lk.fakeLabel,{backgroundColor:C.isDark?"rgba(255,255,255,0.08)":"rgba(0,0,0,0.06)"}]}/>
          <View style={[lk.fakeBar,{backgroundColor:C.isDark?"rgba(139,92,246,0.25)":"rgba(99,102,241,0.15)",width:`${70-i*15}%` as any}]}/>
        </View>
      ))}
      {/* Overlay */}
      <View style={lk.overlay}>
        <LinearGradient
          colors={C.isDark?["transparent","rgba(11,15,25,0.92)","#0B0F19"]:["transparent","rgba(248,250,252,0.92)","#F8FAFC"]}
          style={{...StyleSheet.absoluteFillObject}}/>
        <View style={lk.lockContent}>
          <View style={lk.lockCircle}>
            <Feather name="lock" size={20} color="#a78bfa"/>
          </View>
          <Text style={{color:"#fff",fontSize:14,fontFamily:"Nunito_700Bold",textAlign:"center",marginTop:10}}>
            Unlock Full Compatibility Report
          </Text>
          <Text style={{color:"rgba(255,255,255,0.55)",fontSize:11,fontFamily:"Nunito_400Regular",textAlign:"center",marginTop:4}}>
            Detailed Koot · Dosha · Timing · Remedies
          </Text>
        </View>
      </View>
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

  function handleDone(who:"self"|"partner",data:PersonData){
    if(who==="self")setP1(data); else setP2(data);
    setAddingFor(null); setResult(null);
  }
  async function handleCalculate(){
    if(!person1||!p2)return;
    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
    setCalcLoading(true);
    await new Promise(r=>setTimeout(r,700));
    setResult(compute(person1,p2));
    setCalcLoading(false);
    Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
  }

  const g=result?grade(result.total):null;
  const isPro=plan==="pro";

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
            :["#ede9fe","#F8FAFC"]}
          style={[ms.header,{paddingTop:topPad+4}]}>
          <View style={{flexDirection:"row",alignItems:"center",gap:10}}>
            <Pressable onPress={()=>router.back()} style={ms.backBtn}>
              <Feather name="arrow-left" size={20} color={C.isDark?"#c4b5fd":C.text}/>
            </Pressable>
            <View style={{flex:1}}>
              <Text style={{color:C.isDark?"#f3e8ff":C.text,fontSize:18,fontFamily:"Nunito_700Bold"}}>Kundli Milan</Text>
              <Text style={{color:"#7c3aed",fontSize:10,fontFamily:"Nunito_400Regular"}}>अष्टकूट गुण मिलान</Text>
            </View>
            {/* Basic / Pro Toggle */}
            <View style={[ms.toggleWrap,{backgroundColor:C.isDark?"rgba(255,255,255,0.07)":"rgba(0,0,0,0.05)"}]}>
              {(["basic","pro"] as const).map(t=>(
                <Pressable key={t}
                  onPress={()=>{setPlan(t);Haptics.selectionAsync();}}
                  style={[ms.toggleBtn,
                    plan===t&&(t==="pro"
                      ?{backgroundColor:"#6d28d9"}
                      :{backgroundColor:C.isDark?"#4f46e5":"#4f46e5"})
                  ]}>
                  {plan===t&&t==="pro"?(
                    <LinearGradient colors={["#6366F1","#8B5CF6"]} start={{x:0,y:0}} end={{x:1,y:0}}
                      style={[StyleSheet.absoluteFillObject,{borderRadius:14}]}/>
                  ):null}
                  <Text style={[ms.toggleTxt,{color:plan===t?"#fff":C.textMuted}]}>
                    {t==="pro"?"✨ Pro":"Basic"}
                  </Text>
                </Pressable>
              ))}
            </View>
          </View>
        </LinearGradient>

        <ScrollView
          contentContainerStyle={[ms.scroll,{paddingBottom:botPad+40}]}
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

          {/* ── Kundli Slots ── */}
          <Animated.View style={{gap:8,transform:[{scale:scaleAnim}]}}>
            {autoP1?(
              <KundliSlot who="self" locked isPro={isPro} filled={autoP1} onAdd={()=>{}}/>
            ):(
              <>
                <KundliSlot who="self" isPro={isPro} filled={p1}
                  onAdd={()=>{setAddingFor("self");setResult(null);}}
                  onClear={()=>{setP1(null);setResult(null);}}/>
                {addingFor==="self"&&(
                  <AddKundliForm title="YOUR BIRTH DETAILS"
                    onDone={d=>handleDone("self",d)} onCancel={()=>setAddingFor(null)}/>
                )}
              </>
            )}

            <View style={{alignItems:"center",marginVertical:-2,zIndex:1}}>
              <LinearGradient colors={isPro?["#7c3aed","#ec4899"]:["#ec4899","#f43f5e"]} style={ms.heart}>
                <Text style={{fontSize:14}}>♥</Text>
              </LinearGradient>
            </View>

            <KundliSlot who="partner" isPro={isPro} filled={p2}
              onAdd={()=>{setAddingFor("partner");setResult(null);}}
              onClear={()=>{setP2(null);setResult(null);}}/>
            {addingFor==="partner"&&(
              <AddKundliForm title="PARTNER'S BIRTH DETAILS"
                onDone={d=>handleDone("partner",d)} onCancel={()=>setAddingFor(null)}/>
            )}
          </Animated.View>

          {/* ── PRO Preview Insights ── */}
          {isPro&&!result&&<ProPreview/>}

          {/* ── What You'll Get (Basic only, no result) ── */}
          {!isPro&&!result&&(
            <>
              <Text style={[ms.secLabel,{color:C.textMuted}]}>WHAT YOU'LL GET</Text>
              <View style={ms.previewGrid}>
                {[
                  {icon:"❤️",title:"Emotional Compatibility",desc:"Heart & feelings"},
                  {icon:"🧠",title:"Mental Connection",      desc:"Thought sync"},
                  {icon:"🔥",title:"Attraction Level",       desc:"Physical pull"},
                  {icon:"⚖️",title:"Match Score",            desc:"Out of 36 pts"},
                ].map(({icon,title,desc})=>(
                  <View key={title} style={[ms.previewCard,{backgroundColor:C.bgCard,borderColor:C.border}]}>
                    <Text style={{fontSize:20,marginBottom:4}}>{icon}</Text>
                    <Text style={{color:C.text,fontSize:11,fontFamily:"Nunito_700Bold"}}>{title}</Text>
                    <Text style={{color:C.textMuted,fontSize:9,fontFamily:"Nunito_400Regular",textAlign:"center",marginTop:2}}>{desc}</Text>
                  </View>
                ))}
              </View>
            </>
          )}

          {/* ── CTA Buttons ── */}
          {!result&&(isPro?(
            <ShineButton
              colors={["#6366F1","#8B5CF6","#a855f7"]}
              disabled={!canCalculate} loading={calcLoading}
              text={canCalculate?"Unlock Deep Match Analysis":!person1&&!p2?"Add Both Kundlis First":!person1?"Add Your Kundli":"Add Partner Kundli"}
              onPress={handleCalculate}/>
          ):(
            <Pressable onPress={handleCalculate} disabled={!canCalculate||calcLoading}
              style={({pressed})=>({opacity:pressed||!canCalculate||calcLoading?0.45:1})}>
              <LinearGradient colors={["#4f46e5","#7c3aed"]} start={{x:0,y:0}} end={{x:1,y:0}} style={ms.basicBtn}>
                {calcLoading?<ActivityIndicator color="#fff" size="small"/>:(
                  <Text style={ms.basicBtnTxt}>
                    {canCalculate?"Check Compatibility":!person1&&!p2?"Add Both Kundlis":!person1?"Add Your Kundli":"Add Partner Kundli"}
                  </Text>
                )}
              </LinearGradient>
            </Pressable>
          ))}

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

              {/* Pro locked section */}
              {isPro&&<LockedCard C={C}/>}

              {/* Pro CTA */}
              {isPro&&(
                <ShineButton colors={["#6366F1","#8B5CF6","#a855f7"]}
                  disabled={false} loading={false}
                  text="Unlock Full Compatibility Report"
                  onPress={()=>Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Heavy)}/>
              )}

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

          {/* How it works */}
          {!result&&(
            <View style={[ms.howCard,{backgroundColor:C.bgCard,borderColor:C.isDark?"rgba(167,139,250,0.1)":C.border}]}>
              <Text style={{color:C.isDark?"#c4b5fd":"#4f46e5",fontSize:13,fontFamily:"Nunito_700Bold",marginBottom:10}}>Ashtakoot Milan Scoring</Text>
              {[["32+ / 36","Excellent"],["27–31","Very Good"],["21–26","Average"],["≤20","Below Avg"]].map(([pts,lbl])=>(
                <View key={pts} style={{flexDirection:"row",justifyContent:"space-between",paddingVertical:7,borderBottomWidth:1,borderBottomColor:C.border}}>
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

const pv=StyleSheet.create({
  wrap:{borderRadius:16,borderWidth:1,padding:16,gap:12},
  dot: {width:6,height:6,borderRadius:3,backgroundColor:"#a78bfa"},
  row: {flexDirection:"row",alignItems:"center",gap:12},
  bar: {height:5,borderRadius:3,overflow:"hidden"},
  fill:{height:5,borderRadius:3},
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
