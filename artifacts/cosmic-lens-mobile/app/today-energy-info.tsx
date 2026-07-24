import React from "react";
import LegalScreen, { Bullet, P, Section } from "@/components/LegalScreen";
import { FadeInView, staggerDelay } from "@/components/motion/FadeInView";
import { useUser } from "@/context/UserContext";
import type { UILang } from "@/lib/i18n";

type Labels = {
  title: string;
  subtitle: string;
  whatTitle: string;
  whatP: string;
  howTitle: string;
  howP: string;
  tara: string;
  ashtaka: string;
  scoreTitle: string;
  scoreStrong: string;
  scoreModerate: string;
  scoreUnstable: string;
  scoreLow: string;
  updateTitle: string;
  updateP: string;
};

const LABELS: Partial<Record<UILang, Labels>> = {
  en: {
    title: "Today's Energy",
    subtitle: "How it works",
    whatTitle: "What is this?",
    whatP:
      "Today's Energy is a daily score (1–100) on your home screen. It shows how supportive the day's planetary transits are for you, based on your birth kundli.",
    howTitle: "How is the score calculated?",
    howP: "Your score blends two classical Vedic factors:",
    tara: "Tara chakra (55%) — compares today's Moon nakshatra with your birth nakshatra.",
    ashtaka:
      "Ashtakavarga (45%) — measures how strong the Moon's current house is in your chart.",
    scoreTitle: "What does the score mean?",
    scoreStrong: "75–100 — Strong positive energy",
    scoreModerate: "55–74 — Moderate, stay focused",
    scoreUnstable: "35–54 — Unstable, plan carefully",
    scoreLow: "Below 35 — Low energy, rest & introspect",
    updateTitle: "When does it update?",
    updateP:
      "The score refreshes when you open the app. It uses today's live Moon transit position against your saved kundli.",
  },
  hn: {
    title: "Aaj ki Energy",
    subtitle: "Yeh kaise kaam karta hai",
    whatTitle: "Yeh kya hai?",
    whatP:
      "Aaj ki Energy ek daily score (1–100) hai jo home screen par dikhta hai. Yeh batata hai ki aaj ke grah gochar aapke liye kitne supportive hain — aapki janam kundli ke hisaab se.",
    howTitle: "Score kaise nikala jata hai?",
    howP: "Aapka score do classical Vedic factors se banta hai:",
    tara: "Tara chakra (55%) — aaj ke Chandra nakshatra ko aapke janam nakshatra se compare karta hai.",
    ashtaka:
      "Ashtakavarga (45%) — Chandra ke current house ki strength aapki kundli mein measure karta hai.",
    scoreTitle: "Score ka matlab kya hai?",
    scoreStrong: "75–100 — Strong positive energy",
    scoreModerate: "55–74 — Moderate, focus rakhein",
    scoreUnstable: "35–54 — Unstable, carefully plan karein",
    scoreLow: "35 se kam — Kam energy, aaram aur introspect",
    updateTitle: "Kab update hota hai?",
    updateP:
      "Jab aap app kholte hain tab score refresh hota hai. Yeh aaj ke live Chandra gochar ko aapki saved kundli se match karta hai.",
  },
  hi: {
    title: "आज की ऊर्जा",
    subtitle: "यह कैसे काम करता है",
    whatTitle: "यह क्या है?",
    whatP:
      "आज की ऊर्जा एक दैनिक स्कोर (1–100) है जो होम स्क्रीन पर दिखता है। यह बताता है कि आज के ग्रह गोचर आपके लिए कितने अनुकूल हैं — आपकी जन्म कुंडली के आधार पर।",
    howTitle: "स्कोर कैसे निकाला जाता है?",
    howP: "आपका स्कोर दो शास्त्रीय वैदिक कारकों से बनता है:",
    tara: "तारा चक्र (55%) — आज के चंद्र नक्षत्र की तुलना आपके जन्म नक्षत्र से करता है।",
    ashtaka:
      "अष्टकवर्ग (45%) — चंद्र के वर्तमान भाव की शक्ति आपकी कुंडली में मापता है।",
    scoreTitle: "स्कोर का क्या अर्थ है?",
    scoreStrong: "75–100 — मजबूत सकारात्मक ऊर्जा",
    scoreModerate: "55–74 — मध्यम, ध्यान रखें",
    scoreUnstable: "35–54 — अस्थिर, सावधानी से योजना बनाएं",
    scoreLow: "35 से कम — कम ऊर्जा, आराम और आत्मचिंतन",
    updateTitle: "कब अपडेट होता है?",
    updateP:
      "जब आप ऐप खोलते हैं तब स्कोर रिफ्रेश होता है। यह आज के लाइव चंद्र गोचर को आपकी सहेजी कुंडली से मिलाता है।",
  },
};

function getLabels(lang: UILang): Labels {
  return LABELS[lang] ?? LABELS.en!;
}

export default function TodayEnergyInfoScreen() {
  const { language } = useUser();
  const L = getLabels(language);

  return (
    <LegalScreen title={L.title} subtitle={L.subtitle}>
      <FadeInView delay={staggerDelay(0)}>
      <Section title={L.whatTitle}>
        <P>{L.whatP}</P>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(1)}>
      <Section title={L.howTitle}>
        <P>{L.howP}</P>
        <Bullet>{L.tara}</Bullet>
        <Bullet>{L.ashtaka}</Bullet>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(2)}>
      <Section title={L.scoreTitle}>
        <Bullet>{L.scoreStrong}</Bullet>
        <Bullet>{L.scoreModerate}</Bullet>
        <Bullet>{L.scoreUnstable}</Bullet>
        <Bullet>{L.scoreLow}</Bullet>
      </Section>
      </FadeInView>

      <FadeInView delay={staggerDelay(3)}>
      <Section title={L.updateTitle}>
        <P>{L.updateP}</P>
      </Section>
      </FadeInView>
    </LegalScreen>
  );
}
