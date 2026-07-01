"""Shared spiritual topic detection — static, timing, and gap yield rules."""

from __future__ import annotations

import re

# Broad spiritual anchor — any match should route to spiritual engines (static or timing).
SPIRITUAL_TOPIC_RX = re.compile(
    r"(?ix)\b("
    r"spiritual|spirituality|adhyatm|adhyatmik|dharma|dharam|moksha|mukti|"
    r"soul|atma|aatma|parmatma|paramatma|"
    r"guru|guruji|satguru|deeksha|diksha|initiation|awakening|awaken|"
    r"sadhana|tapasya|sanyas|vairagya|ashram|jagran|jagruti|enlighten|"
    r"purva\s+punya|punya|pichle\s+janam|past\s+life|reincarnation|"
    r"life\s+purpose|soul\s+mission|atmakaraka|amatyakaraka|"
    r"mantra|siddhi|janeu|nishtha|rishi|saint|siddh|siddha|"
    r"meditation|dhyan|dhyana|samadhi|inner\s+peace|mansik\s+shanti|"
    r"mental\s+restlessness|restlessness|bechaini|overthinking|"
    r"sukoon|shanti|peace\s+of\s+mind|vipassana|maun|silent\s+retreat|"
    r"pranayam|enlightenment|santushti|contentment|yoga|shant|"
    r"atma-bal|willpower|third\s+eye|ajna|chakra|aura|kundalini|"
    r"naastik|atheis|vishwas|faith|bhakti|"
    r"kuldevi|kuldevta|ishta\s+dev|ishta\s+devta|bhagwan|divine|"
    r"shiv|shiva|krishna|hanuman|darshan|sanket|"
    r"mandir|temple|dharmik|devi|devta|"
    r"occult|mystic|secret\s+knowledge|hidden\s+knowledge|paravidi|"
    r"astrology|astro\s*logy|jyotish|tarot|palmistry|numerology|"
    r"reiki|pranic|lal\s+kitab|nadi|prediction|astrologer|"
    r"intuition|intuitive|purnanumaan|psychic|empath|paranormal|"
    r"tantra|energetic\s+healing|sound\s+healing|8th\s+house|9th\s+house|12th\s+house|"
    r"vedic\s+astro|hastarekha|face\s+reading|ketu|"
    r"karma|karmic|pitra|pitru|ancestor|purvajan|"
    r"teerth|tirth|pilgrim|yatra|char\s+dham|dham|kailash|mansarovar|"
    r"vaishno|amarnath|kedarnath|jagannath|kashi|rameswaram|"
    r"shakti\s+peeth|bodh\s+gaya|kumbh|pavitra\s+sthal|"
    r"religious\s+travel|religious\s+tourism|"
    r"anxiety|trauma|emotional\s+trauma|saade\s+sati|dhaiya|"
    r"negative\s+energy|buri\s+nazar|divine\s+protection|"
    r"gupta\s+spiritual|kriya\s+yoga|naam\s+jap|japa"
    r")\b|(?:आध्यात्म|धर्म|गुरु|मोक्ष|भक्ति|ध्यान|कर्म|अतींद्रिय|मुक्ति)"
)

# Parents mentioned in a spiritual ask — route to spiritual engine, not parents gap.
_PARENT_WORD_RX = re.compile(
    r"(?ix)\b(parents?|mata|pita|maa|mummy|mom|mother|father|dad|papa|mata\s*pita)\b"
)


def is_spiritual_topic(question: str) -> bool:
    q = (question or "").strip()
    return bool(q and SPIRITUAL_TOPIC_RX.search(q))


def spiritual_overrides_parents_gap(question: str) -> bool:
    """True when parents words appear inside a spiritual question."""
    q = (question or "").strip()
    if not q or not is_spiritual_topic(q):
        return False
    return _PARENT_WORD_RX.search(q) is not None
