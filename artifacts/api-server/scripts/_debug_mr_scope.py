import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ask_marriage_relationship_slice import is_marriage_relationship_static_question, _TIMING_RX, _MR_DOMAIN_RX

qs = [
 "kya multiple relationships honge?",
 "friend se lover ban sakta hai kya?",
 "meri emotional needs poori hongi?",
 "love marriage hogi ya arranged?",
 "communication strong hogi kya?",
 "hamari chemistry kaisi hogi?",
 "private life kaisi rahegi?",
 "kya yeh soulmate hai?",
 "mother in law nature kaisi hogi?",
 "Kab shaadi hogi?",
]
for q in qs:
 t = bool(_TIMING_RX.search(q))
 d = bool(_MR_DOMAIN_RX.search(q))
 print(q[:45], "timing=", t, "domain=", d, "in_mr=", is_marriage_relationship_static_question(q))
