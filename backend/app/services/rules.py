from __future__ import annotations

from typing import Any

from ..models import TransformationRule


def matches_rule(rule: TransformationRule, context: dict[str, Any]) -> bool:
    conditions = rule.conditions or {}
    store = context.get("store")
    title = (context.get("title") or "").lower()

    store_in = conditions.get("store_in")
    if store_in and store not in store_in:
        return False

    keywords = conditions.get("title_contains")
    if keywords and not any(keyword.lower() in title for keyword in keywords):
        return False

    requires_coupon = conditions.get("requires_coupon")
    if requires_coupon and not context.get("coupon"):
        return False

    return True


def apply_actions(rule: TransformationRule, context: dict[str, Any], lines: list[str]) -> None:
    actions = rule.actions or {}

    set_fields = actions.get("set_fields") or {}
    for key, value in set_fields.items():
        context[key] = value

    prepend = actions.get("prepend_lines") or []
    append = actions.get("append_lines") or []
    benefits = actions.get("append_benefits") or []

    if prepend:
        for item in reversed(prepend):
            lines.insert(0, item)

    if append:
        lines.extend(append)

    if benefits:
        context.setdefault("benefits", [])
        for benefit in benefits:
            if benefit not in context["benefits"]:
                context["benefits"].append(benefit)


def apply_rules(rules: list[TransformationRule], context: dict[str, Any], lines: list[str]) -> None:
    for rule in rules:
        if matches_rule(rule, context):
            apply_actions(rule, context, lines)
