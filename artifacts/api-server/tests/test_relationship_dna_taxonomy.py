"""Tests for relationship_dna_taxonomy — love-domain bucket taxonomy."""
from __future__ import annotations

import unittest

from relationship_dna_taxonomy import (
    LOVE_RELATIONSHIP_BUCKETS,
    LOVE_BUCKET_SOFT_DEFAULT,
    LOVE_BUCKET_LABELS,
    normalize_love_bucket,
    map_love_bucket_to_mr,
)


class RelationshipTaxonomyTests(unittest.TestCase):
    def test_bucket_count(self):
        self.assertEqual(len(LOVE_RELATIONSHIP_BUCKETS), 23)

    def test_every_bucket_has_label_and_mr_map(self):
        from relationship_dna_taxonomy import LOVE_BUCKET_TO_MR_ARCHETYPE

        for b in LOVE_RELATIONSHIP_BUCKETS:
            self.assertIn(b, LOVE_BUCKET_LABELS, b)
            self.assertIn(b, LOVE_BUCKET_TO_MR_ARCHETYPE, b)

    def test_default_is_valid(self):
        self.assertIn(LOVE_BUCKET_SOFT_DEFAULT, LOVE_RELATIONSHIP_BUCKETS)

    def test_normalize_aliases(self):
        self.assertEqual(normalize_love_bucket("loyalty_trust"), "trust_loyalty")
        self.assertEqual(normalize_love_bucket("secret_relationship"), "third_person_infidelity")
        self.assertEqual(normalize_love_bucket("second_marriage"), "reconciliation_ex")
        self.assertEqual(normalize_love_bucket("one_sided_love"), "commitment")

    def test_normalize_unknown_empty(self):
        self.assertEqual(normalize_love_bucket("bogus"), "")
        self.assertEqual(normalize_love_bucket(""), "")

    def test_mr_mapping(self):
        self.assertEqual(map_love_bucket_to_mr("relationship_promise"), "loyalty_trust")
        self.assertEqual(map_love_bucket_to_mr("third_person_infidelity"), "secret_relationship")
        self.assertEqual(map_love_bucket_to_mr("compatibility"), "compatibility")
        self.assertEqual(map_love_bucket_to_mr("commitment"), "commitment")
        self.assertEqual(map_love_bucket_to_mr("communication"), "communication")
        self.assertEqual(map_love_bucket_to_mr("relationship_future"), "relationship_future")
        self.assertEqual(map_love_bucket_to_mr("relationship_decisions"), "relationship_decisions")
        self.assertEqual(map_love_bucket_to_mr("toxicity_red_flags"), "toxicity")
        self.assertEqual(map_love_bucket_to_mr("relationship_remedies"), "relationship_remedies")
        self.assertEqual(map_love_bucket_to_mr("unknown_relationship_intent"), "general_mr")

    def test_bucket_match_confidence(self):
        from relationship_dna_taxonomy import derive_bucket_match, LOVE_BUCKET_UNKNOWN

        score, label = derive_bucket_match(0.95, domain="love", bucket="trust_loyalty",
                                           bucket_coerced=False, coercions=0)
        self.assertEqual(label, "high")
        self.assertGreaterEqual(score, 0.85)

        score, label = derive_bucket_match(0.95, domain="love", bucket=LOVE_BUCKET_UNKNOWN,
                                           bucket_coerced=True, coercions=1)
        self.assertEqual(label, "low")
        self.assertLess(score, 0.70)


if __name__ == "__main__":
    unittest.main()
