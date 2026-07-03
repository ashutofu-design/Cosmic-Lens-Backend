import importlib
import sys

sys.path.insert(0, ".")

q = "D10 mein Sun Makar rashi mein hai (5th house se kya hota hai"
probes = [
    ("mr", "ask_marriage_relationship_slice", "is_marriage_relationship_static_question"),
    ("career", "ask_career.classifier", "is_career_static_question"),
    ("children", "ask_children.children_registry", "is_children_static_question"),
    ("health", "ask_health.classifier", "is_health_static_question"),
    ("finance", "ask_finance.finance_registry", "is_finance_static_question"),
    ("education", "ask_education.education_registry", "is_education_static_question"),
    ("property", "ask_property.property_registry", "is_property_static_question"),
    ("vehicle", "ask_vehicle.vehicle_registry", "is_vehicle_static_question"),
    ("travel", "ask_travel.travel_registry", "is_travel_static_question"),
    ("litigation", "ask_litigation.litigation_registry", "is_litigation_static_question"),
    ("luck", "ask_luck.luck_registry", "is_luck_static_question"),
    ("network", "ask_network.network_registry", "is_network_static_question"),
]
for name, mod, fn in probes:
    f = getattr(importlib.import_module(mod), fn)
    r = f(q)
    print(f"{name}: {r}")

from ask_gap_dispatch import detect_gap_static_key
print("gap:", detect_gap_static_key(q))

from ask_routing_policy import matches_dedicated_static_engine, should_bypass_static_engines_for_direct_llm
print("matches_dedicated:", matches_dedicated_static_engine(q))
print("bypass:", should_bypass_static_engines_for_direct_llm(q))
