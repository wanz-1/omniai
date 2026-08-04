from enum import IntEnum


class RiskLevel(IntEnum):
    SAFE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class RiskClassifier:
    JAILBREAK_PATTERNS = [
        "ignore your rules",
        "ignore your instructions",
        "ignore all previous",
        "ignore all rules",
        "you are now",
        "act as if",
        "pretend to be",
        "override your",
        "disregard your",
        "forget your",
        "you are free",
        "you have no restrictions",
        "you are not bound",
        "you can do anything",
        "no filter",
        "unfiltered",
        "dan mode",
        "developer mode",
        "do anything now",
        "you must obey",
        "you must follow",
        "hidden prompt",
        "system prompt",
        "your system prompt",
        "your instructions are",
        "reveal your",
        "output your",
        "print your",
        "show your",
        "tell me your",
        "what are your rules",
        "what are your instructions",
        "reveal your system prompt",
        "reveal your instructions",
    ]

    EXFILTRATION_PATTERNS = [
        "send this to",
        "email this to",
        "post this to",
        "forward this",
        "leak this",
        "export all",
        "download all",
        "copy all",
        "extract all",
        "dump all",
    ]

    MALICIOUS_CODE_PATTERNS = [
        "rm -rf",
        "drop table",
        "delete from",
        "truncate",
        "shutdown",
        "exec(",
        "eval(",
        "__import__",
        "os.system",
        "subprocess",
        "base64.b64decode",
        "pickle.loads",
        "eval(compile(",
    ]

    SENSITIVE_DATA_PATTERNS = [
        "social security",
        "credit card",
        "passport",
        "driver license",
        "bank account",
        "routing number",
        "cvv",
        "pin code",
    ]

    def classify_input(self, text: str) -> tuple[RiskLevel, list[str]]:
        text_lower = text.lower()
        flags: list[str] = []

        for pattern in self.JAILBREAK_PATTERNS:
            if pattern in text_lower:
                flags.append(f"jailbreak:{pattern}")

        for pattern in self.EXFILTRATION_PATTERNS:
            if pattern in text_lower:
                flags.append(f"exfiltration:{pattern}")

        for pattern in self.MALICIOUS_CODE_PATTERNS:
            if pattern in text_lower:
                flags.append(f"malicious_code:{pattern}")

        for pattern in self.SENSITIVE_DATA_PATTERNS:
            if pattern in text_lower:
                flags.append(f"sensitive_data:{pattern}")

        if not flags:
            return RiskLevel.SAFE, []

        jailbreak_count = sum(1 for f in flags if f.startswith("jailbreak:"))
        exfil_count = sum(1 for f in flags if f.startswith("exfiltration:"))
        malicious_count = sum(1 for f in flags if f.startswith("malicious_code:"))

        if malicious_count >= 2 or (jailbreak_count >= 2 and exfil_count >= 1):
            return RiskLevel.CRITICAL, flags
        if malicious_count >= 1 or (jailbreak_count >= 1 and exfil_count >= 1):
            return RiskLevel.HIGH, flags
        if jailbreak_count >= 1 or exfil_count >= 1:
            return RiskLevel.MEDIUM, flags

        return RiskLevel.LOW, flags

    def classify_output(self, text: str) -> tuple[RiskLevel, list[str]]:
        text_lower = text.lower()
        flags: list[str] = []

        if any(sys_prompt in text_lower for sys_prompt in ["system instruction", "system prompt", "you are an ai"]):
            if any(phrase in text_lower for phrase in [
                "ignore", "disregard", "override", "you are free", "you have no"
            ]):
                flags.append("system_prompt_leak_risk")

        for pattern in self.MALICIOUS_CODE_PATTERNS:
            if pattern in text_lower:
                flags.append(f"output_malicious:{pattern}")

        if text.count("```") >= 4 and len(text) > 5000:
            flags.append("large_code_dump")

        if not flags:
            return RiskLevel.SAFE, []

        return RiskLevel.HIGH if any("malicious" in f for f in flags) else RiskLevel.MEDIUM, flags


risk_classifier = RiskClassifier()
