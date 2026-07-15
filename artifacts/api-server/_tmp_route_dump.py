from ask_answer_mode import resolve_answer_mode, infer_answer_mode
from ask_routing_policy import should_bypass_static_engines_for_direct_llm, matches_dedicated_static_engine
from ask_master_router import resolve_ask_route

cases = [
    "6th house me deblited planet acha he ya exalted",
    "6th house me debilitated planet accha hai ya exalted",
    "Meri career kaisi rahegi",
    "D10 chart mein meri career kaisi rahegi",
    "Mere 10th house mein kaun se graha hain",
    "manglik kya hota hai matlab",
]
for q in cases:
    print("---", q)
    print(" mode", resolve_answer_mode(q))
    print(" bypass", should_bypass_static_engines_for_direct_llm(q))
    print(" match_eng", matches_dedicated_static_engine(q))
    print(" route", resolve_ask_route(q).path, resolve_ask_route(q).reason)
