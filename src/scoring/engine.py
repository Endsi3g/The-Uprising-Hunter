from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Tuple

from ..core.models import InteractionType, Lead, ScoringData
from .config_schema import load_scoring_config


class ScoringEngine:
    def __init__(self, config_path: str | None = None):
        self.config = load_scoring_config(config_path)
        self.icp_weights = self.config["icp_weights"]
        self.heat_weights = self.config["heat_weights"]
        self.thresholds = self.config["thresholds"]
        self.tier_cutoffs = self.config["tier_cutoffs"]
        self.caps = self.config["caps"]
        self.rules = self.config["rules"]

    @property
    def qualification_threshold(self) -> float:
        return float(self.thresholds["qualification_min_score"])

    def determine_tier(self, icp_score: float) -> str:
        if icp_score >= float(self.tier_cutoffs["tier_a"]):
            return "Tier A"
        if icp_score >= float(self.tier_cutoffs["tier_b"]):
            return "Tier B"
        if icp_score >= float(self.tier_cutoffs["tier_c"]):
            return "Tier C"
        return "Tier D"

    def determine_heat_status(self, heat_score: float) -> str:
        if heat_score >= float(self.thresholds["heat_hot_min"]):
            return "Hot"
        if heat_score >= float(self.thresholds["heat_warm_min"]):
            return "Warm"
        return "Cold"

    @staticmethod
    def _truthy(value: Any) -> bool:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)):
            return value > 0
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "y", "on"}
        return False

    @staticmethod
    def _contains_any(text: str, keywords: list[str]) -> bool:
        if not text:
            return False
        return any(keyword in text for keyword in keywords)

    @staticmethod
    def _contains_all(text: str, keywords: list[str]) -> bool:
        if not text:
            return False
        return all(keyword in text for keyword in keywords)

    @staticmethod
    def _cap(value: float, cap: float) -> float:
        return max(0.0, min(float(cap), float(value)))

    def _cap_section(self, section_name: str, section_score: float, breakdown: Dict[str, float], cap_value: float) -> float:
        capped = self._cap(section_score, cap_value)
        if capped < section_score:
            breakdown[f"{section_name}_cap_adjustment"] = round(capped - section_score, 4)
        return capped

    def _score_site_event(self, event: Dict[str, Any], breakdown_key_prefix: str) -> Tuple[float, Dict[str, float]]:
        score = 0.0
        breakdown: Dict[str, float] = {}
        w = self.heat_weights["site"]
        rules = self.rules["heat"]

        page = str(event.get(rules["site_page_key"], "")).lower()
        if self._contains_any(page, rules["pricing_page_tokens"]):
            score += float(w["pricing_page"])
            breakdown[f"{breakdown_key_prefix}_pricing_page"] = float(w["pricing_page"])

        return_hours = event.get(rules["site_return_within_hours_key"])
        try:
            return_hours_val = float(return_hours) if return_hours is not None else None
        except (TypeError, ValueError):
            return_hours_val = None

        if return_hours_val is not None and return_hours_val <= float(rules["return_visit_hours_max"]):
            score += float(w["return_visit"])
            breakdown[f"{breakdown_key_prefix}_return_visit"] = float(w["return_visit"])

        if self._truthy(event.get("multi_page")):
            score += float(w["multi_page"])
            breakdown[f"{breakdown_key_prefix}_multi_page"] = float(w["multi_page"])

        return score, breakdown

    def _resolve_automated_action(self, tier: str, heat_status: str) -> str:
        tier_actions = self.rules["actions"]["tier"]
        heat_actions = self.rules["actions"]["heat"]

        tier_key = tier.lower().replace(" ", "_")
        heat_key = heat_status.lower()

        tier_action = tier_actions.get(tier_key, "")
        heat_action = heat_actions.get(heat_key, "")
        if tier_action and heat_action:
            return f"{tier_action} | {heat_action}"
        return tier_action or heat_action or "No action"

    def calculate_icp_score(self, lead: Lead) -> Tuple[float, Dict[str, float]]:
        score = 0.0
        breakdown: Dict[str, float] = {}
        w = self.icp_weights
        rules = self.rules

        # 1) Fit (0-30)
        fit_score = 0.0
        size_range = (lead.company.size_range or "").strip()
        location = (lead.company.location or "").lower()
        industry = (lead.company.industry or "").lower()

        if size_range in rules["fit"]["small_size_ranges"]:
            p = float(w["fit"]["prac_2_5"])
            fit_score += p
            breakdown["fit_size_match"] = p
        elif size_range in rules["fit"].get("solo_size_ranges", []):
            p = float(w["fit"]["solo_penalty"])
            fit_score += p
            breakdown["fit_solo_penalty"] = p
        elif size_range in rules["fit"].get("large_size_ranges", []):
            p = float(w["fit"]["group_10_penalty"])
            fit_score += p
            breakdown["fit_large_group_penalty"] = p

        if self._contains_any(industry, rules["fit"]["medical_industry_keywords"]):
            p = float(w["fit"]["medical_industry"])
            fit_score += p
            breakdown["fit_industry_match"] = p

        location_priority_key = rules["fit"]["location_priority_detail_key"]
        if self._truthy(lead.details.get(location_priority_key)) or self._contains_any(
            location, rules["fit"]["priority_location_keywords"]
        ):
            p = float(w["fit"]["location_priority"])
            fit_score += p
            breakdown["fit_location_priority"] = p

        admin_present_key = rules["fit"]["admin_present_detail_key"]
        if self._truthy(lead.details.get(admin_present_key)):
            p = float(w["fit"]["admin_present"])
            fit_score += p
            breakdown["fit_admin_present"] = p

        fit_score = self._cap_section("fit", fit_score, breakdown, self.caps["fit"])
        score += fit_score

        # 2) Pain (0-35)
        pain_score = 0.0
        desc = (lead.company.description or "").lower()
        pain_rules = rules["pain"]

        if self._truthy(lead.details.get(pain_rules["vague_booking_detail_key"])) or self._contains_any(
            desc, pain_rules["vague_booking_keywords_any"]
        ):
            p = float(w["pain"]["vague_booking"])
            pain_score += p
            breakdown["pain_vague_booking"] = p

        if self._truthy(lead.details.get(pain_rules["no_faq_detail_key"])):
            p = float(w["pain"]["no_faq"])
            pain_score += p
            breakdown["pain_no_faq"] = p

        if self._truthy(lead.details.get(pain_rules["missing_essentials_detail_key"])):
            p = float(w["pain"]["missing_essentials"])
            pain_score += p
            breakdown["pain_missing_essentials"] = p

        if self._contains_all(desc, pain_rules["high_friction_keywords_all"]):
            p = float(w["pain"]["high_friction"])
            pain_score += p
            breakdown["pain_high_friction"] = p

        if self._contains_any(desc, pain_rules["surcharge_signal_keywords_any"]):
            p = float(w["pain"]["surcharge_signals"])
            pain_score += p
            breakdown["pain_surcharge_signals"] = p

        pain_score = self._cap_section("pain", pain_score, breakdown, self.caps["pain"])
        score += pain_score

        # 3) Digital Weakness (0-20)
        digital_score = 0.0
        digital_rules = rules["digital"]

        if self._truthy(lead.details.get(digital_rules["low_mobile_detail_key"])):
            p = float(w["digital"]["bad_mobile"])
            digital_score += p
            breakdown["digital_weakness_mobile"] = p

        if self._truthy(lead.details.get(digital_rules["no_fold_cta_detail_key"])):
            p = float(w["digital"]["no_fold_cta"])
            digital_score += p
            breakdown["digital_no_fold_cta"] = p

        if self._truthy(lead.details.get(digital_rules["weak_contact_detail_key"])):
            p = float(w["digital"]["weak_contact"])
            digital_score += p
            breakdown["digital_weak_contact"] = p

        digital_score = self._cap_section("digital", digital_score, breakdown, self.caps["digital"])
        score += digital_score

        # 4) Access & Urgency (0-15)
        access_urgency_score = 0.0
        access_rules = rules["access"]

        if lead.email and "placeholder.com" not in lead.email:
            p = float(w["access"]["direct_email"])
            access_urgency_score += p
            breakdown["access_direct_email"] = p
        elif self._truthy(lead.details.get(access_rules["contact_form_detail_key"])):
            p = float(w["access"]["contact_form"])
            access_urgency_score += p
            breakdown["access_contact_form"] = p

        if self._truthy(lead.details.get(access_rules["active_social_detail_key"])):
            p = float(w["access"]["active_social"])
            access_urgency_score += p
            breakdown["access_active_social"] = p

        urgency_rules = rules["urgency"]
        if self._truthy(lead.details.get(urgency_rules["recent_post_detail_key"])):
            p = float(w["urgency"]["recent_post"])
            access_urgency_score += p
            breakdown["urgency_recent_post"] = p
        if self._truthy(lead.details.get(urgency_rules["hiring_detail_key"])):
            p = float(w["urgency"]["hiring"])
            access_urgency_score += p
            breakdown["urgency_hiring"] = p
        if self._truthy(lead.details.get(urgency_rules["new_service_detail_key"])):
            p = float(w["urgency"]["new_service"])
            access_urgency_score += p
            breakdown["urgency_new_service"] = p

        access_urgency_score = self._cap_section(
            "access_urgency", access_urgency_score, breakdown, self.caps["access_urgency"]
        )
        score += access_urgency_score

        total_icp = self._cap(score, self.caps["total_icp"])
        if total_icp < score:
            breakdown["icp_total_cap_adjustment"] = round(total_icp - score, 4)
        return float(total_icp), breakdown

    def calculate_heat_score(self, lead: Lead) -> Tuple[float, Dict[str, float]]:
        breakdown: Dict[str, float] = {}
        w = self.heat_weights
        rules = self.rules

        email_engagement_score = 0.0
        site_reply_score = 0.0
        timing_score = 0.0

        # Count opens for the "2+ open" bonus.
        type_counts: Dict[str, int] = {}
        for interaction in lead.interactions:
            interaction_type = (
                interaction.type.value if hasattr(interaction.type, "value") else str(interaction.type)
            )
            type_counts[interaction_type] = type_counts.get(interaction_type, 0) + 1

        heat_rules = rules["heat"]
        click_detail_key = heat_rules["click_detail_key"]
        forward_detail_key = heat_rules["forward_detail_key"]

        for idx, interaction in enumerate(lead.interactions):
            interaction_type = (
                interaction.type.value if hasattr(interaction.type, "value") else str(interaction.type)
            )
            interaction_key = f"{interaction_type}_{interaction.timestamp.strftime('%Y%m%d')}_{idx}"

            if interaction_type == InteractionType.EMAIL_OPENED.value:
                p = float(w["email"]["open"])
                email_engagement_score += p
                breakdown[interaction_key] = p
                if type_counts.get(InteractionType.EMAIL_OPENED.value, 0) >= 2:
                    bonus = float(w["email"]["double_open"]) / type_counts[InteractionType.EMAIL_OPENED.value]
                    email_engagement_score += bonus
                    breakdown[f"{interaction_key}_double_open_bonus"] = bonus

            if self._truthy(interaction.details.get(click_detail_key)):
                p = float(w["email"]["click"])
                email_engagement_score += p
                breakdown[f"{interaction_key}_click"] = p

            if self._truthy(interaction.details.get(forward_detail_key)):
                p = float(w["email"]["forward"])
                email_engagement_score += p
                breakdown[f"{interaction_key}_forward"] = p

            if interaction_type == InteractionType.EMAIL_REPLIED.value:
                intent = str(interaction.details.get("intent", "curiosity")).lower()
                p = float(w["reply"].get(intent, w["reply"]["curiosity"]))
                site_reply_score += p
                breakdown[f"{interaction_key}_reply"] = p

            if interaction_type == InteractionType.EMAIL_SENT.value:
                site_event_score, site_breakdown = self._score_site_event(interaction.details, interaction_key)
                site_reply_score += site_event_score
                breakdown.update(site_breakdown)

        # Additional site events can be provided from enrichment telemetry.
        site_events_key = heat_rules["site_event_detail_key"]
        site_events = lead.details.get(site_events_key, [])
        if isinstance(site_events, list):
            for idx, event in enumerate(site_events):
                if not isinstance(event, dict):
                    continue
                site_event_score, site_breakdown = self._score_site_event(event, f"site_event_{idx}")
                site_reply_score += site_event_score
                breakdown.update(site_breakdown)

        # Timing bonus from latest interaction.
        if lead.interactions:
            last_interaction = max(lead.interactions, key=lambda x: x.timestamp)
            # Use timezone-aware now for comparison if timestamp is aware
            now = datetime.now(timezone.utc) if last_interaction.timestamp.tzinfo else datetime.now()
            delta_hours = (now - last_interaction.timestamp).total_seconds() / 3600
            timing_hours = rules["timing"]["buckets_hours"]
            if delta_hours < float(timing_hours["within_24h"]):
                p = float(w["timing"]["within_24h"])
                timing_score += p
                breakdown["timing_bonus_24h"] = p
            elif delta_hours < float(timing_hours["within_48h"]):
                p = float(w["timing"]["within_48h"])
                timing_score += p
                breakdown["timing_bonus_48h"] = p
            elif delta_hours < float(timing_hours["within_7d"]):
                p = float(w["timing"]["within_7d"])
                timing_score += p
                breakdown["timing_bonus_7d"] = p

        # Intent enrichment contributes to heat.
        intent_rules = rules.get("intent", {})
        if intent_rules.get("enabled", False):
            intent_payload = lead.details.get(intent_rules.get("detail_key", "intent"), {})
            if isinstance(intent_payload, dict):
                supported_levels = set(intent_rules.get("supported_levels", []))
                level = str(intent_payload.get("intent_level", "none")).lower()
                if level not in supported_levels:
                    level = "none"

                level_points = float(w["intent"].get(level, 0))
                if level_points:
                    site_reply_score += level_points
                    breakdown["intent_level"] = level_points

                try:
                    topic_count = max(0, int(intent_payload.get("topic_count", 0)))
                except (ValueError, TypeError):
                    topic_count = 0
                    
                max_topics = int(intent_rules.get("max_topic_bonus_count", 5))
                topic_points = float(w["intent"]["topic_bonus"]) * min(topic_count, max_topics)
                if topic_points:
                    site_reply_score += topic_points
                    breakdown["intent_topic_bonus"] = topic_points

                try:
                    surge_score = float(intent_payload.get("surge_score", 0))
                except (ValueError, TypeError):
                    surge_score = 0.0
                surge_points = surge_score * float(w["intent"]["surge_multiplier"])
                if surge_points:
                    site_reply_score += surge_points
                    breakdown["intent_surge_bonus"] = surge_points

        email_engagement_score = self._cap_section(
            "heat_email_engagement", email_engagement_score, breakdown, self.caps["email_engagement"]
        )
        site_reply_score = self._cap_section(
            "heat_site_reply", site_reply_score, breakdown, self.caps["site_reply"]
        )
        timing_score = self._cap_section("heat_timing", timing_score, breakdown, self.caps["timing"])

        total_heat = email_engagement_score + site_reply_score + timing_score
        total_heat = self._cap(total_heat, self.caps["total_heat"])
        return float(total_heat), breakdown

    def score_lead(self, lead: Lead) -> Lead:
        icp_val, icp_break = self.calculate_icp_score(lead)
        heat_val, heat_break = self.calculate_heat_score(lead)

        tier = self.determine_tier(icp_val)
        heat_status = self.determine_heat_status(heat_val)
        next_best_action = self._resolve_automated_action(tier, heat_status)

        lead.score = ScoringData(
            icp_score=icp_val,
            heat_score=heat_val,
            total_score=(icp_val + heat_val) / 2,  # Keep combined score for legacy decision logic.
            tier=tier,
            heat_status=heat_status,
            next_best_action=next_best_action,
            icp_breakdown=icp_break,
            heat_breakdown=heat_break,
            last_scored_at=datetime.now(timezone.utc),
        )

        lead.tags = [tag for tag in lead.tags if not str(tag).startswith("Tier ")]
        lead.tags.append(tier)

        industry_text = f"{lead.company.industry or ''} {lead.company.description or ''}".lower()
        if self._contains_any(industry_text, self.rules["fit"]["medical_industry_keywords"]):
            lead.segment = "Clinic"
        elif not lead.segment:
            lead.segment = "General"

        lead.details["tier"] = tier
        lead.details["heat_status"] = heat_status
        lead.details["next_best_action"] = next_best_action
        lead.details["tier_action"] = self.rules["actions"]["tier"].get(tier.lower().replace(" ", "_"), "")
        lead.details["heat_action"] = self.rules["actions"]["heat"].get(heat_status.lower(), "")
        lead.details["should_send_loom"] = tier == "Tier A" or heat_val >= float(self.thresholds["heat_warm_min"])
        lead.details["propose_stripe_link"] = heat_status == "Hot"

        return lead

