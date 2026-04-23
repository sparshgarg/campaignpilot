"""Brand safety checker for CampaignPilot creative content."""

import re
import logging
from typing import Any, Literal

logger = logging.getLogger(__name__)

# Default prohibited phrases from Lumen Analytics brand guidelines
DEFAULT_PROHIBITED_PHRASES = [
    "game-changing",
    "revolutionary",
    "world-class",
    "best-in-class",
    "cutting-edge",
    "synergize",
    "paradigm shift",
    "disruptive",
    "unlock your potential",
    "leverage"  # as a verb
]


class SafetyChecker:
    """Brand safety checker for marketing content.

    Validates creative content against brand guidelines, prohibited phrases,
    and unsubstantiated claims.
    """

    def __init__(
        self,
        prohibited_phrases: list[str] | None = None,
        custom_rules: list[dict[str, str]] | None = None
    ) -> None:
        """Initialize safety checker with phrase list and custom regex rules.

        Args:
            prohibited_phrases: List of phrases to prohibit. Defaults to DEFAULT_PROHIBITED_PHRASES.
            custom_rules: List of regex rules with keys:
                - pattern (str): Regex pattern to match
                - description (str): Human-readable description
                - severity (str): "low", "medium", or "high"
        """
        self.prohibited_phrases = prohibited_phrases or DEFAULT_PROHIBITED_PHRASES
        self.custom_rules = custom_rules or []

    def check_safety(
        self,
        text: str,
        prohibited_phrases: list[str] | None = None
    ) -> dict[str, Any]:
        """Check text against prohibited phrases and custom rules.

        Args:
            text: Text to check.
            prohibited_phrases: Optional override for prohibited phrase list.

        Returns:
            Dictionary with keys:
                - passed (bool): True if no violations found
                - violations (list[str]): Human-readable violation descriptions
                - severity (str): "none", "low", "medium", or "high"
                - details (list[dict]): Violation details with phrase, context, severity
        """
        violations = []
        details = []
        phrases_to_check = prohibited_phrases or self.prohibited_phrases

        # Check prohibited phrases (case-insensitive, whole-word)
        for phrase in phrases_to_check:
            # Escape special regex characters and create whole-word pattern
            escaped = re.escape(phrase)
            pattern = rf"\b{escaped}\b"

            matches = list(re.finditer(pattern, text, re.IGNORECASE))
            for match in matches:
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 50)
                context = text[start:end].strip()

                violations.append(f"Prohibited phrase found: '{phrase}'")
                details.append({
                    "phrase": phrase,
                    "context": context,
                    "severity": "medium"
                })

        # Check custom rules
        for rule in self.custom_rules:
            pattern = rule.get("pattern", "")
            description = rule.get("description", "")
            rule_severity = rule.get("severity", "medium")

            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()

                    violations.append(description)
                    details.append({
                        "phrase": match.group(),
                        "context": context,
                        "severity": rule_severity
                    })
            except re.error as e:
                logger.warning(f"Invalid regex pattern in custom rule: {e}")

        # Determine overall severity
        if not violations:
            severity: Literal["none", "low", "medium", "high"] = "none"
        elif len(violations) == 1:
            severity = "low"
        elif len(violations) <= 3:
            severity = "medium"
        else:
            severity = "high"

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "severity": severity,
            "details": details
        }

    def check_brand_safety(self, text: str) -> dict[str, Any]:
        """Alias for check_safety() for compatibility with agent interfaces."""
        return self.check_safety(text)

    def check_unsubstantiated_claims(self, text: str) -> dict[str, Any]:
        """Check for unsubstantiated marketing claims.

        Looks for patterns like percentages, rankings, guarantees without citations.

        Args:
            text: Text to check.

        Returns:
            Dictionary with same structure as check_safety().
        """
        violations = []
        details = []

        # Patterns for unsubstantiated claims
        rules = [
            {
                "pattern": r"\d+%\s+(?:better|faster|cheaper|more)",
                "description": "Unsubstantiated percentage claim without source",
                "severity": "high"
            },
            {
                "pattern": r"(?:^|\s)#\d+(?:\s|$|[,.])",
                "description": "Ranking claim without context or source",
                "severity": "high"
            },
            {
                "pattern": r"\b(?:guaranteed|guarantee)\b",
                "description": "Guarantee claim without terms or conditions",
                "severity": "medium"
            },
            {
                "pattern": r"\b(?:always|never)\s+(?:fails|breaks|disappoints|works)",
                "description": "Absolute claim (always/never) without qualification",
                "severity": "medium"
            },
            {
                "pattern": r"\b(?:proven|clinically|scientifically)\b",
                "description": "Scientific/clinical claim without study reference",
                "severity": "high"
            }
        ]

        for rule in rules:
            pattern = rule["pattern"]
            description = rule["description"]
            rule_severity = rule["severity"]

            try:
                matches = list(re.finditer(pattern, text, re.IGNORECASE))
                for match in matches:
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 50)
                    context = text[start:end].strip()

                    violations.append(description)
                    details.append({
                        "phrase": match.group(),
                        "context": context,
                        "severity": rule_severity
                    })
            except re.error as e:
                logger.warning(f"Invalid regex pattern: {e}")

        # Determine overall severity
        if not violations:
            severity: Literal["none", "low", "medium", "high"] = "none"
        elif len(violations) == 1:
            severity = "low"
        elif len(violations) <= 3:
            severity = "medium"
        else:
            severity = "high"

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "severity": severity,
            "details": details
        }

    def batch_check(self, texts: list[str]) -> list[dict[str, Any]]:
        """Run safety check on multiple texts.

        Args:
            texts: List of texts to check.

        Returns:
            List of safety check results in same order as input.
        """
        return [self.check_safety(text) for text in texts]
