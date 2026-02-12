from __future__ import annotations

from src.enrichment.apify_client import ApifyMapsClient


def test_apify_scoring_detail_builder_sets_expected_flags():
    client = ApifyMapsClient(api_token="dummy")
    item = {
        "title": "Clinique Lumiere",
        "address": "123 Rue Test, Montreal, QC",
        "description": "Prise de rendez-vous rapide, appelez-nous, nouveau service.",
        "phone": None,
        "openingHours": None,
        "questionsAndAnswers": [],
        "website": "https://example.com",
    }
    website_probe = {
        "website_has_faq": False,
        "website_has_contact_form": True,
        "website_has_social_links": True,
        "website_no_fold_cta": True,
        "website_mobile_signals_bad": True,
        "website_has_map_or_directions": False,
    }

    details = client._build_scoring_details(item, website_probe)
    assert details["location_priority"] is True
    assert details["vague_booking"] is True
    assert details["no_faq"] is True
    assert details["missing_essentials"] is True
    assert details["low_mobile_score"] is True
    assert details["no_fold_cta"] is True
    assert details["weak_contact_page"] is True
    assert details["has_contact_form"] is True
    assert details["active_social"] is True

