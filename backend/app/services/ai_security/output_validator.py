from dataclasses import dataclass, field

from app.services.ai_security.risk_classifier import RiskClassifier, RiskLevel, risk_classifier


@dataclass
class ValidationResult:
    approved: bool
    risk_level: RiskLevel
    flags: list[str] = field(default_factory=list)
    validated_text: str = ""


class OutputValidator:
    SENSITIVE_PATTERNS = [
        r"-----BEGIN RSA PRIVATE KEY-----",
        r"-----BEGIN OPENSSH PRIVATE KEY-----",
        r"-----BEGIN PGP PRIVATE KEY BLOCK-----",
        r"ghp_[a-zA-Z0-9]{36}",
        r"gho_[a-zA-Z0-9]{36}",
        r"sk-[a-zA-Z0-9]{32,}",
        r"pk-[a-zA-Z0-9]{32,}",
        r"AKIA[0-9A-Z]{16}",
        r"xox[bpsa]-[0-9A-Za-z-]{10,}",
    ]

    def __init__(self, classifier: RiskClassifier | None = None) -> None:
        self.classifier = classifier or risk_classifier

    async def validate(self, text: str, user_id: str = "") -> ValidationResult:
        import re

        risk_level, flags = self.classifier.classify_output(text)

        for pattern in self.SENSITIVE_PATTERNS:
            if re.search(pattern, text):
                flags.append("secret_leaked_in_output")
                risk_level = max(risk_level, RiskLevel.HIGH)

        validated = self._strip_sensitive_data(text)

        return ValidationResult(
            approved=risk_level < RiskLevel.HIGH,
            risk_level=risk_level,
            flags=flags,
            validated_text=validated,
        )

    def _strip_sensitive_data(self, text: str) -> str:
        import re

        result = text
        for pattern in self.SENSITIVE_PATTERNS:
            result = re.sub(pattern, "[REDACTED]", result)
        return result


output_validator = OutputValidator()
