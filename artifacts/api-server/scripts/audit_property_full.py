#!/usr/bin/env python3
"""Full non-timing property/real-estate audit — routing, scope, D4 evidence alignment."""
from __future__ import annotations

import os
import re
import sys
from dataclasses import dataclass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ask_property import run_property_static_engine
from ask_property.classifier import classify_property_archetype, is_property_static_question
from ask_property.property_registry import (
    detect_property_archetype,
    is_property_money_only_question,
)
from ask_finance.classifier import is_finance_static_question

_SIGN_LON = {
    "Aries": 15.0,
    "Taurus": 45.0,
    "Gemini": 75.0,
    "Cancer": 105.0,
    "Leo": 135.0,
    "Virgo": 165.0,
    "Libra": 195.0,
    "Scorpio": 225.0,
    "Sagittarius": 255.0,
    "Capricorn": 285.0,
    "Aquarius": 315.0,
    "Pisces": 345.0,
}

K = {
    "ascendant": "Sagittarius",
    "ascendantDeg": 255.0,
    "planets": [
        {"name": "Moon", "sign": "Gemini", "house": 7, "longitude": 75.0},
        {"name": "Saturn", "sign": "Virgo", "house": 10, "longitude": 165.0},
        {"name": "Mars", "sign": "Cancer", "house": 8, "longitude": 105.0},
        {"name": "Venus", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Mercury", "sign": "Aries", "house": 5, "longitude": 15.0},
        {"name": "Jupiter", "sign": "Pisces", "house": 4, "longitude": 345.0},
        {"name": "Rahu", "sign": "Aquarius", "house": 3, "longitude": 315.0},
        {"name": "Ketu", "sign": "Leo", "house": 9, "longitude": 135.0},
        {"name": "Sun", "sign": "Capricorn", "house": 2, "longitude": 285.0},
    ],
}

_D4_RX = r"D4|Chaturthamsa|4th|4H|Mars|Moon|property"


@dataclass
class Case:
    q: str
    domain: str  # property | finance | timing | off
    engine: str
    focus_rx: str
    min_evidence: int = 6


def C(q: str, eng: str, rx: str = _D4_RX, min_e: int = 6) -> Case:
    return Case(q, "property", eng, rx, min_e)


def FIN(q: str) -> Case:
    return Case(q, "finance", "", "")


def TIMING(q: str) -> Case:
    return Case(q, "timing", "", "")


def OFF(q: str) -> Case:
    return Case(q, "off", "", "")


CASES: list[Case] = [
    # ── property_yog ──
    C("Property yog hai kya?", "property_yog", r"yog|4th|4H|Jupiter|D4|Chaturthamsa"),
    C("Ghar yog strong hai?", "property_yog", r"yog|4th|4H|Jupiter|D4"),
    C("Kya mujhe ghar milega?", "property_yog", r"yog|4th|4H|milega|D4"),
    C("Apna ghar possible hai?", "property_yog", r"yog|4th|4H|apna|D4"),
    C("Will I own a home?", "property_yog", r"yog|4th|4H|home|D4"),
    C("Dream home milega kya?", "property_yog", r"yog|4th|4H|dream|D4"),
    C("First home yog chart me?", "property_yog", r"yog|4th|4H|first|D4"),
    C("Khud ka ghar hoga?", "property_yog", r"yog|4th|4H|khud|D4"),
    C("Makaan milega kya?", "property_yog", r"yog|4th|4H|milega|D4"),
    C("Real estate yog chart me?", "property_yog", r"yog|4th|4H|estate|D4"),
    C("Ghar hoga ya nahi?", "property_yog", r"yog|4th|4H|ghar|D4"),
    C("Home possible hai chart se?", "property_yog", r"yog|4th|4H|possible|D4"),
    C("Property strong hai kya?", "property_yog", r"yog|4th|4H|strong|D4"),
    C("Yog kaisa hai ghar ka?", "property_yog", r"yog|4th|4H|kaisa|D4"),
    C("Own home possible chart se?", "property_yog", r"yog|4th|4H|own|D4"),
    C("Property milegi kya?", "property_yog", r"yog|4th|4H|milegi|D4"),
    C("Ghar mil sakta hai?", "property_yog", r"yog|4th|4H|mil|D4"),
    C("First property yog strong?", "property_yog", r"yog|4th|4H|first|D4"),
    # ── property_capacity ──
    C("Property capacity kaisi hai?", "property_capacity", r"capacity|4th|2nd|11th|D4"),
    C("Ghar lene ki capacity chart me?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Buying capacity chart property?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Ghar khareed sakta hoon capacity se?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Wealth for property chart?", "property_capacity", r"capacity|wealth|2nd|4th|D4"),
    C("Capacity chart property kaisi?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Ready for home chart?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Property buying power chart?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Lene ki capacity kaisi?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Ghar ke liye capacity?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Property readiness capacity?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Home capacity analysis chart?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Ghar lene ki capacity strong?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Property capacity strong hai?", "property_capacity", r"capacity|4th|2nd|D4"),
    C("Afford home chart capacity se?", "property_capacity", r"capacity|4th|2nd|D4"),
    # ── property_risk ──
    C("Property risk kaisa hai?", "property_risk", r"risk|4th|6th|8th|D4"),
    C("Ghar risk chart se?", "property_risk", r"risk|4th|6th|8th|D4"),
    C("Legal risk property chart?", "property_risk", r"risk|legal|4th|D4"),
    C("Title clear issue chart property?", "property_risk", r"risk|title|4th|D4"),
    C("Property safe hai chart se?", "property_risk", r"risk|safe|4th|D4"),
    C("Ghar safe hai kya?", "property_risk", r"risk|safe|4th|D4"),
    C("Documentation risk property?", "property_risk", r"risk|documentation|4th|D4"),
    C("Nuksan property chart?", "property_risk", r"risk|nuksan|4th|D4"),
    C("Risk in property chart?", "property_risk", r"risk|4th|6th|8th|D4"),
    C("Property problem chart?", "property_risk", r"risk|problem|4th|D4"),
    C("Ghar me dikkat property?", "property_risk", r"risk|dikkat|4th|D4"),
    C("Dispute risk chart property?", "property_risk", r"risk|dispute|4th|D4"),
    C("Legal issue property chart?", "property_risk", r"risk|legal|4th|D4"),
    C("Property nuksan ho sakta?", "property_risk", r"risk|nuksan|4th|D4"),
    C("Ghar risk tone chart?", "property_risk", r"risk|4th|6th|8th|D4"),
    # ── property_type_fit (D4 size/style emphasis) ──
    C("Plot ya flat kaun sa better?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Which property type suits me?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa"),
    C("Kis tarah ka ghar hoga?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Ghar kaisa hoga chart se?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Chota ya bada ghar?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|spacious|compact"),
    C("Bada ghar ya chota?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|spacious|compact"),
    C("Small or big home chart?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|spacious|compact"),
    C("2BHK ya 3BHK better?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Villa ya flat kaun sa?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Luxury home suits me?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|luxury|comfort"),
    C("Kis type ka makaan hoga?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Property style chart se?", "property_type_fit", r"D4|Type fit|style|Venus|Chaturthamsa"),
    C("Spacious home chart fit?", "property_type_fit", r"D4|Type fit|size|spacious|Venus|Chaturthamsa"),
    C("Compact home better chart?", "property_type_fit", r"D4|Type fit|size|compact|Venus|Chaturthamsa"),
    C("Independent house ya flat?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|style"),
    C("Duplex suits me chart?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|style"),
    C("Penthouse chart fit?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|style"),
    C("Kothi ya flat better?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|style"),
    C("Property kaisi hogi?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("Mera ghar kaisa hoga?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    C("New home ya plot type?", "property_type_fit", r"D4|Type fit|Mars|Venus|Chaturthamsa"),
    C("Commercial property type fit?", "property_type_fit", r"D4|Type fit|Venus|Chaturthamsa|style"),
    C("Land ya flat better chart?", "property_type_fit", r"D4|Type fit|Mars|Venus|Chaturthamsa"),
    C("Big home style chart se?", "property_type_fit", r"D4|Type fit|size|spacious|Venus|Chaturthamsa"),
    C("4BHK ya 3BHK chart fit?", "property_type_fit", r"D4|Type fit|size|Venus|Chaturthamsa|style"),
    # ── property_inherit ──
    C("Paitrik property milegi kya?", "property_inherit", r"inherit|ancestral|Moon|8th|9th|D4"),
    C("Ancestral home chart me?", "property_inherit", r"inherit|ancestral|Moon|8th|9th|D4"),
    C("Virasat me ghar milega?", "property_inherit", r"inherit|virasat|Moon|8th|9th|D4"),
    C("Family property share chart?", "property_inherit", r"inherit|family|Moon|8th|9th|D4"),
    C("Father property chart se?", "property_inherit", r"inherit|father|Moon|8th|9th|D4"),
    C("Mother property chart se?", "property_inherit", r"inherit|mother|Moon|8th|9th|D4"),
    C("Paitrik sampatti yog?", "property_inherit", r"inherit|paitrik|Moon|8th|9th|D4"),
    C("Parental property chart?", "property_inherit", r"inherit|parental|Moon|8th|9th|D4"),
    C("Hissa property me milega?", "property_inherit", r"inherit|hissa|Moon|8th|9th|D4"),
    C("Pitri dhan property?", "property_inherit", r"inherit|pitri|Moon|8th|9th|D4"),
    C("Virasat me zameen?", "property_inherit", r"inherit|virasat|Moon|8th|9th|D4"),
    C("Family home inherit chart?", "property_inherit", r"inherit|family|Moon|8th|9th|D4"),
    C("Ancestral land chart?", "property_inherit", r"inherit|ancestral|Moon|8th|9th|D4"),
    C("Paitric ghar chart se?", "property_inherit", r"inherit|paitric|Moon|8th|9th|D4"),
    C("Inheritance property theme?", "property_inherit", r"inherit|inheritance|Moon|8th|9th|D4"),
    # ── property_dispute ──
    C("Property dispute case hai?", "property_dispute", r"dispute|Mars|Rahu|6th|8th|D4"),
    C("Ghar ka vivad court me?", "property_dispute", r"dispute|vivad|Mars|Rahu|D4"),
    C("Land dispute chart?", "property_dispute", r"dispute|land|Mars|Rahu|D4"),
    C("Plot dispute case chart?", "property_dispute", r"dispute|plot|Mars|Rahu|D4"),
    C("Property court case chart?", "property_dispute", r"dispute|court|Mars|Rahu|D4"),
    C("Legal case property ghar?", "property_dispute", r"dispute|legal|Mars|Rahu|D4"),
    C("Hissa vivad property?", "property_dispute", r"dispute|vivad|hissa|Mars|Rahu|D4"),
    C("Family dispute property ghar?", "property_dispute", r"dispute|family|Mars|Rahu|D4"),
    C("Property fight chart?", "property_dispute", r"dispute|fight|Mars|Rahu|D4"),
    C("Ghar dispute chart se?", "property_dispute", r"dispute|ghar|Mars|Rahu|D4"),
    C("Zameen vivad court?", "property_dispute", r"dispute|vivad|zameen|Mars|Rahu|D4"),
    C("Property litigation chart?", "property_dispute", r"dispute|litigation|Mars|Rahu|D4"),
    C("Court case ghar property?", "property_dispute", r"dispute|court|Mars|Rahu|D4"),
    C("Property case chart tone?", "property_dispute", r"dispute|case|Mars|Rahu|D4"),
    C("Vivad property chart me?", "property_dispute", r"dispute|vivad|Mars|Rahu|D4"),
    # ── property_rent ──
    C("Rent income property se?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Ghar rent pe dena sahi?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Rental property chart?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Ghar kiraya income?", "property_rent", r"rent|kiraya|Saturn|11th|D4"),
    C("Tenant property chart?", "property_rent", r"rent|tenant|Saturn|11th|D4"),
    C("Lease property chart?", "property_rent", r"rent|lease|Saturn|11th|D4"),
    C("Property se rent milega?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Rent pe ghar dena chart?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Rental yield chart property?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Kiraye se income property?", "property_rent", r"rent|kiraya|Saturn|11th|D4"),
    C("Rent out home chart?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Ghar rental income theme?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Property rent income strong?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Home rent chart se?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    C("Rental property yog?", "property_rent", r"rent|rental|Saturn|11th|D4"),
    # ── property_build ──
    C("Ghar banwana sahi rahega?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Home construction chart?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Ghar banwane ka yog?", "property_build", r"build|construction|Mars|4th|D4"),
    C("House build chart se?", "property_build", r"build|construction|Mars|4th|D4"),
    C("New construction home chart?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Makaan banwana chart?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Property construction theme?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Ghar banane ka plan chart?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Build home chart support?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Construction property chart?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Ghar naya banwana?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Home build yog?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Banwane ka samay nahi timing?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Property construction chart se?", "property_build", r"build|construction|Mars|4th|D4"),
    C("Ghar construction sahi?", "property_build", r"build|construction|Mars|4th|D4"),
    # ── property_sell ──
    C("Property sell kar sakta hoon?", "property_sell", r"sell|disposal|4th|11th|D4"),
    C("Ghar bech sakta hoon?", "property_sell", r"sell|bech|4th|11th|D4"),
    C("Sell flat chart se?", "property_sell", r"sell|flat|4th|11th|D4"),
    C("Plot sell possible chart?", "property_sell", r"sell|plot|4th|11th|D4"),
    C("Land sell chart?", "property_sell", r"sell|land|4th|11th|D4"),
    C("Property disposal chart?", "property_sell", r"sell|disposal|4th|11th|D4"),
    C("Ghar beche chart support?", "property_sell", r"sell|bech|4th|11th|D4"),
    C("Sell home chart theme?", "property_sell", r"sell|home|4th|11th|D4"),
    C("Property sell yog?", "property_sell", r"sell|4th|11th|D4"),
    C("House sell chart?", "property_sell", r"sell|house|4th|11th|D4"),
    C("Flat bech sakta hoon?", "property_sell", r"sell|bech|flat|4th|D4"),
    C("Dispose property chart?", "property_sell", r"sell|dispose|4th|11th|D4"),
    C("Ghar sell karna chart?", "property_sell", r"sell|4th|11th|D4"),
    C("Property bechna chart se?", "property_sell", r"sell|bech|4th|11th|D4"),
    C("Sell land chart support?", "property_sell", r"sell|land|4th|11th|D4"),
    # ── property_buy ──
    C("Ghar kharid sakta hoon?", "property_buy", r"buy|purchase|4th|2nd|D4"),
    C("Buy flat possible hai?", "property_buy", r"buy|flat|4th|2nd|D4"),
    C("Property kharid paunga?", "property_buy", r"buy|purchase|4th|2nd|D4"),
    C("Plot lena sahi chart?", "property_land", r"buy|plot|land|Mars|D4"),
    C("Land purchase chart?", "property_buy", r"buy|purchase|4th|2nd|D4"),
    C("Invest in property chart?", "property_buy", r"buy|invest|4th|2nd|D4"),
    C("Real estate investment chart?", "property_buy", r"buy|invest|estate|4th|D4"),
    C("Ghar lena chart se?", "property_buy", r"buy|lena|4th|2nd|D4"),
    C("Property purchase yog?", "property_buy", r"buy|purchase|4th|2nd|D4"),
    C("Flat kharid sakta hoon?", "property_buy", r"buy|kharid|flat|4th|D4"),
    C("Home purchase chart?", "property_buy", r"buy|purchase|4th|2nd|D4"),
    C("Plot kharid chart se?", "property_buy", r"buy|kharid|plot|4th|D4"),
    C("Property lena chart?", "property_buy", r"buy|lena|4th|2nd|D4"),
    C("Buy home chart support?", "property_buy", r"buy|home|4th|2nd|D4"),
    C("Ghar khareedna chart?", "property_buy", r"buy|khareed|4th|2nd|D4"),
    # ── property_loan ──
    C("Home loan EMI chart se?", "property_loan", r"loan|emi|Saturn|4th|D4"),
    C("Property loan ke liye chart?", "property_loan", r"loan|property|Saturn|4th|D4"),
    C("Griha rin chart?", "property_loan", r"loan|griha|Saturn|4th|D4"),
    C("House loan chart support?", "property_loan", r"loan|house|Saturn|4th|D4"),
    C("Mortgage chart property?", "property_loan", r"loan|mortgage|Saturn|4th|D4"),
    C("EMI home loan chart?", "property_loan", r"loan|emi|Saturn|4th|D4"),
    C("Ghar loan chart se?", "property_loan", r"loan|ghar|Saturn|4th|D4"),
    C("Property EMI chart?", "property_loan", r"loan|emi|Saturn|4th|D4"),
    C("Home loan for property chart?", "property_loan", r"loan|home|Saturn|4th|D4"),
    C("Loan for home chart?", "property_loan", r"loan|home|Saturn|4th|D4"),
    C("Property loan EMI theme?", "property_loan", r"loan|emi|Saturn|4th|D4"),
    C("Griha loan chart support?", "property_loan", r"loan|griha|Saturn|4th|D4"),
    C("House loan EMI chart se?", "property_loan", r"loan|emi|Saturn|4th|D4"),
    C("Property mortgage chart?", "property_loan", r"loan|mortgage|Saturn|4th|D4"),
    C("Home loan chart reading?", "property_loan", r"loan|home|Saturn|4th|D4"),
    # ── property_land ──
    C("Plot lena sahi rahega?", "property_land", r"plot|land|Mars|zameen|D4"),
    C("Zameen khareedne ka yog?", "property_land", r"plot|zameen|Mars|land|D4"),
    C("Land purchase yog chart?", "property_land", r"land|plot|Mars|D4"),
    C("Agricultural land chart?", "property_land", r"land|agricultural|Mars|D4"),
    C("Farm land chart property?", "property_land", r"land|farm|Mars|D4"),
    C("Jameen lena chart?", "property_land", r"zameen|jameen|Mars|land|D4"),
    C("Zamin khareed sakta hoon?", "property_land", r"zamin|zameen|Mars|land|D4"),
    C("Plot yog chart se?", "property_land", r"plot|land|Mars|D4"),
    C("Farmhouse land chart?", "property_land", r"farmhouse|land|Mars|D4"),
    C("Zameen chart reading?", "property_land", r"zameen|land|Mars|D4"),
    C("Plot buy yog nahi timing?", "property_buy", r"buy|plot|4th|Mars|D4"),
    C("Land yog chart me?", "property_land", r"land|plot|Mars|D4"),
    C("Jamin lena sahi?", "property_land", r"jamin|land|Mars|D4"),
    C("Agricultural plot chart?", "property_land", r"agricultural|plot|Mars|D4"),
    C("Zameen property chart?", "property_land", r"zameen|property|Mars|D4"),
    # ── general_property ──
    C("Meri property overall kaisi?", "general_property", r"property|4th|overall|D4|Chaturthamsa"),
    C("Real estate chart reading?", "general_property", r"property|estate|4th|D4|Chaturthamsa"),
    C("Ghar topic chart analysis?", "general_property", r"property|ghar|4th|D4|Chaturthamsa"),
    C("Property overall strong?", "general_property", r"property|4th|overall|D4|Chaturthamsa"),
    C("Home axis chart reading?", "general_property", r"property|4th|home|D4|Chaturthamsa"),
    C("Makaan chart se kya kehta?", "general_property", r"property|makaan|4th|D4|Chaturthamsa"),
    C("4th house property reading?", "general_property", r"4th|4H|property|D4|Chaturthamsa"),
    C("Property theme chart me?", "general_property", r"property|4th|theme|D4|Chaturthamsa"),
    C("Real estate overall chart?", "general_property", r"property|estate|4th|D4|Chaturthamsa"),
    C("Ghar sampatti chart?", "general_property", r"property|sampatti|4th|D4|Chaturthamsa"),
    C("Property chart summary?", "general_property", r"property|4th|summary|D4|Chaturthamsa"),
    C("Home property overall?", "general_property", r"property|home|4th|D4|Chaturthamsa"),
    C("Vastu ke saath property chart?", "general_property", r"property|vastu|4th|D4|Chaturthamsa"),
    C("Sampada ghar chart?", "general_property", r"property|sampada|4th|D4|Chaturthamsa"),
    C("Property reading overall chart?", "general_property", r"property|4th|overall|D4|Chaturthamsa"),
    # ── negative: timing ──
    TIMING("Ghar kab milega?"),
    TIMING("Property kab khareed paunga?"),
    TIMING("Plot kab lena chahiye?"),
    TIMING("Home kab banega muhurat?"),
    TIMING("Registry kab hogi?"),
    TIMING("Ghar ka shubh muhurat?"),
    TIMING("When will I buy a house?"),
    TIMING("Property purchase timing dasha?"),
    TIMING("Ghar lene ka sahi samay?"),
    TIMING("Land kab milegi?"),
    TIMING("Flat kab lena best?"),
    TIMING("Construction start kab kare?"),
    # ── negative: finance money-only ──
    FIN("Ghar khareedne ke liye paisa banega kya?"),
    FIN("Property ke liye kitna paisa jama hoga?"),
    FIN("Home loan afford kar paunga paisa se?"),
    FIN("EMI afford hogi budget se?"),
    FIN("Down payment ke liye paisa?"),
    FIN("Property money chart finance?"),
    FIN("Ghar ke liye savings enough paisa?"),
    FIN("Funds for home purchase money?"),
    FIN("Paisa banega ghar khareedne ke liye?"),
    FIN("Home loan readiness paisa budget?"),
    FIN("Property cost afford paisa se?"),
    FIN("Money for house saving chart?"),
    # ── negative: off-topic ──
    OFF("Bachcha hoga kya?"),
    OFF("Love marriage hogi?"),
    OFF("Job promotion milegi?"),
    OFF("Health theek rahegi?"),
    OFF("Business profit hoga?"),
    OFF("Foreign travel possible?"),
    OFF("Partner loyal hai?"),
    OFF("Exam pass ho jayega?"),
    OFF("Salary kitni hogi?"),
    OFF("Court case job related?"),
]


def _hit(text: str, rx: str) -> bool:
    if not rx:
        return True
    blob = (text or "").lower()
    return bool(re.search(rx, blob, re.I))


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    gaps: list[str] = []
    total = len(CASES)
    scope_ok = route_ok = engine_ok = ev_ok = 0

    print(f"PROPERTY FULL AUDIT — {total} cases (D4 evidence required)\n" + "=" * 72)

    for c in CASES:
        q = c.q
        is_prop = is_property_static_question(q)
        is_money = is_property_money_only_question(q)
        is_fin = is_finance_static_question(q)
        arch = classify_property_archetype(q)
        detected = detect_property_archetype(q)

        if c.domain == "property":
            scope_hit = is_prop and not is_money
            route_hit = arch == c.engine and (detected == c.engine or arch == c.engine)
            if scope_hit:
                scope_ok += 1
            if route_hit:
                route_ok += 1

            try:
                res = run_property_static_engine(K, q, archetype=arch)
                eng_hit = res.archetype == c.engine
                if eng_hit:
                    engine_ok += 1
                ev_blob = " ".join(res.evidence or []) + " " + (res.verdict or "")
                ev_hit = len(res.evidence or []) >= c.min_evidence and _hit(ev_blob, c.focus_rx)
                if ev_hit:
                    ev_ok += 1
            except Exception as exc:
                eng_hit = ev_hit = False
                gaps.append(f"ENGINE_ERR | {q} | {exc}")

            ok = scope_hit and route_hit and eng_hit and ev_hit
            if not ok:
                gaps.append(
                    f"{c.engine} | {q[:55]} | scope={is_prop} money={is_money} "
                    f"arch={arch} det={detected} exp={c.engine} ev={ev_hit}"
                )
            tag = "OK" if ok else "GAP"
            print(f"  [{tag}] {q[:52]:<52} -> {arch}")

        elif c.domain == "timing":
            ok = not is_prop
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"TIMING | {q} | should NOT be property static")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} prop={is_prop}")

        elif c.domain == "finance":
            ok = not is_prop and (is_money or is_fin)
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(
                    f"FINANCE | {q} | prop={is_prop} money={is_money} fin={is_fin}"
                )
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} prop={is_prop} fin={is_fin}")

        else:  # off
            ok = not is_prop
            if ok:
                scope_ok += 1
                route_ok += 1
                engine_ok += 1
                ev_ok += 1
            else:
                gaps.append(f"OFF | {q} | prop={is_prop} arch={arch}")
            print(f"  [{'OK' if ok else 'GAP'}] {q[:52]:<52} prop={is_prop}")

    print("\n" + "=" * 72)
    print(
        f"TOTAL={total} SCOPE={scope_ok}/{total} ROUTE={route_ok}/{total} "
        f"ENGINE={engine_ok}/{total} EVIDENCE={ev_ok}/{total} GAPS={len(gaps)}"
    )
    for g in gaps[:80]:
        print(f"  GAP: {g}")
    if len(gaps) > 80:
        print(f"  ... and {len(gaps) - 80} more")
    return 1 if gaps else 0


if __name__ == "__main__":
    raise SystemExit(main())
