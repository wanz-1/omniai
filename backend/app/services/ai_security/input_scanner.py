import re
from dataclasses import dataclass, field

from app.services.ai_security.risk_classifier import RiskClassifier, RiskLevel, risk_classifier


@dataclass
class ScanResult:
    blocked: bool
    risk_level: RiskLevel
    flags: list[str] = field(default_factory=list)
    sanitized_text: str = ""


class InputScanner:
    MAX_INPUT_LENGTH = 100000
    MAX_SEGMENT_LENGTH = 10000
    REPEATED_PATTERN_THRESHOLD = 50

    def __init__(self, classifier: RiskClassifier | None = None) -> None:
        self.classifier = classifier or risk_classifier

    async def scan(self, text: str, user_id: str = "") -> ScanResult:
        if len(text) > self.MAX_INPUT_LENGTH:
            return ScanResult(
                blocked=True,
                risk_level=RiskLevel.CRITICAL,
                flags=["input_too_long"],
            )

        risk_level, flags = self.classifier.classify_input(text)

        if risk_level >= RiskLevel.HIGH:
            return ScanResult(
                blocked=True,
                risk_level=risk_level,
                flags=flags,
            )

        sanitized = self._sanitize(text)

        if self._has_repeated_pattern(sanitized):
            flags.append("repeated_pattern_detected")

        return ScanResult(
            blocked=risk_level >= RiskLevel.CRITICAL,
            risk_level=risk_level,
            flags=flags,
            sanitized_text=sanitized,
        )

    def _sanitize(self, text: str) -> str:
        text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)
        text = re.sub(r"\x1b\[[0-9;]*[a-zA-Z]", "", text)
        return text

    def _has_repeated_pattern(self, text: str) -> bool:
        for length in range(3, 20):
            for i in range(len(text) - length):
                segment = text[i : i + length]
                count = text.count(segment)
                if count > self.REPEATED_PATTERN_THRESHOLD:
                    return True
        return False


input_scanner = InputScanner()
