from neurothera_map import build_drug_profile


def test_build_drug_profile_caffeine():
    p = build_drug_profile("caffeine")
    assert p.name == "caffeine"
    assert len(p.interactions) >= 1
    assert "ADORA1" in p.targets()


def test_build_drug_profile_unknown_is_empty():
    p = build_drug_profile("some_unknown_compound")
    assert p.name == "some_unknown_compound"
    assert len(p.interactions) == 0
    assert p.provenance["seed_db_hit"] is False
