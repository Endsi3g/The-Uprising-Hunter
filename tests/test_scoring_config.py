from __future__ import annotations

from copy import deepcopy

import pytest
import yaml

from src.core.models import Company, Lead
from src.scoring.config_schema import load_scoring_config
from src.scoring.engine import ScoringEngine


def _make_lead() -> Lead:
    return Lead(
        id="lead-1",
        first_name="Jean",
        last_name="Dupont",
        email="jean.dupont@example.com",
        company=Company(
            name="Clinique Test",
            industry="medical",
            size_range="2-5",
            description="rendez-vous appelez",
        ),
        details={"low_mobile_score": True, "intent": {"intent_level": "high", "surge_score": 50, "topic_count": 2}},
    )


def test_load_scoring_config_rejects_missing_sections(tmp_path):
    config_path = tmp_path / "broken.yaml"
    config_path.write_text("icp_weights: {}\n", encoding="utf-8")

    with pytest.raises(ValueError):
        load_scoring_config(str(config_path))


def test_scoring_engine_respects_yaml_tier_cutoffs(tmp_path):
    base = load_scoring_config()
    custom = deepcopy(base)
    custom["tier_cutoffs"]["tier_a"] = 5
    custom["tier_cutoffs"]["tier_b"] = 3
    custom["tier_cutoffs"]["tier_c"] = 1
    custom["thresholds"]["qualification_min_score"] = 2

    config_path = tmp_path / "scoring.yaml"
    config_path.write_text(yaml.safe_dump(custom, sort_keys=False), encoding="utf-8")

    engine = ScoringEngine(config_path=str(config_path))
    scored = engine.score_lead(_make_lead())

    assert engine.qualification_threshold == 2
    assert "Tier A" in scored.tags
    assert scored.score.icp_score > 0
    assert scored.score.heat_score > 0


def test_advanced_feature_flags_drive_breakdown():
    engine = ScoringEngine()
    lead = Lead(
        id="lead-advanced",
        first_name="Sophie",
        last_name="Martin",
        email="sophie@clinic.ca",
        company=Company(
            name="Clinique Soleil",
            industry="Dental clinic",
            size_range="2-5",
            location="Montreal, QC",
            description="Prise de rendez-vous difficile, appelez-nous, sans rendez-vous.",
        ),
        details={
            "admin_present": True,
            "no_faq": True,
            "missing_essentials": True,
            "low_mobile_score": True,
            "no_fold_cta": True,
            "weak_contact_page": True,
        },
    )

    scored = engine.score_lead(lead)
    icp = scored.score.icp_breakdown

    assert icp["fit_size_match"] > 0
    assert icp["fit_location_priority"] > 0
    assert icp["pain_no_faq"] > 0
    assert icp["pain_missing_essentials"] > 0
    assert icp["digital_no_fold_cta"] > 0
    assert scored.score.tier in {"Tier A", "Tier B", "Tier C"}


def test_heat_status_and_action_are_set():
    engine = ScoringEngine()
    lead = Lead(
        id="lead-hot",
        first_name="Alex",
        last_name="Roy",
        email="alex@clinic.ca",
        company=Company(name="Clinique Flux", industry="Medical", size_range="2-5"),
        details={
            "intent": {"intent_level": "high", "surge_score": 90, "topic_count": 5},
            "site_events": [
                {"page": "pricing", "return_within_hours": 12, "multi_page": True},
                {"page": "offre", "return_within_hours": 24},
            ],
        },
    )

    scored = engine.score_lead(lead)
    assert scored.score.heat_status in {"Warm", "Hot"}
    assert scored.score.next_best_action is not None
    assert "next_best_action" in scored.details
