import logging
from dataclasses import dataclass, field

from app.services.ai_security.input_scanner import InputScanner, input_scanner
from app.services.ai_security.output_validator import OutputValidator, output_validator
from app.services.ai_security.risk_classifier import RiskLevel
from app.services.ai_security.tool_permission import ToolPermissionChecker, tool_permission_checker

logger = logging.getLogger("omniai.ai_security")


@dataclass
class GuardResult:
    allowed: bool
    blocked_reason: str = ""
    flags: list[str] = field(default_factory=list)
    sanitized_input: str = ""
    validated_output: str = ""


class PromptGuard:
    def __init__(
        self,
        scanner: InputScanner | None = None,
        validator: OutputValidator | None = None,
        permission_checker: ToolPermissionChecker | None = None,
    ) -> None:
        self.scanner = scanner or input_scanner
        self.validator = validator or output_validator
        self.permission_checker = permission_checker or tool_permission_checker

    async def check_input(
        self,
        text: str,
        user_id: str = "",
        organization_id: str = "",
    ) -> GuardResult:
        scan = await self.scanner.scan(text, user_id=user_id)

        if scan.blocked:
            logger.warning(
                "Input blocked by AI security guard",
                extra={
                    "event": "ai_input_blocked",
                    "risk_level": scan.risk_level.name,
                    "flags": scan.flags,
                    "user_id": user_id,
                },
            )
            return GuardResult(
                allowed=False,
                blocked_reason=f"Input blocked: {scan.risk_level.name} risk",
                flags=scan.flags,
            )

        if scan.risk_level >= RiskLevel.MEDIUM:
            logger.info(
                "Input flagged with medium risk",
                extra={
                    "event": "ai_input_flagged",
                    "risk_level": scan.risk_level.name,
                    "flags": scan.flags,
                    "user_id": user_id,
                },
            )

        return GuardResult(
            allowed=True,
            flags=scan.flags,
            sanitized_input=scan.sanitized_text,
        )

    async def check_output(
        self,
        text: str,
        user_id: str = "",
    ) -> GuardResult:
        validation = await self.validator.validate(text, user_id=user_id)

        if not validation.approved:
            logger.warning(
                "Output blocked by AI security guard",
                extra={
                    "event": "ai_output_blocked",
                    "risk_level": validation.risk_level.name,
                    "flags": validation.flags,
                    "user_id": user_id,
                },
            )
            return GuardResult(
                allowed=False,
                blocked_reason=f"Output blocked: {validation.risk_level.name} risk",
                flags=validation.flags,
            )

        return GuardResult(
            allowed=True,
            flags=validation.flags,
            validated_output=validation.validated_text,
        )

    async def check_tool_execution(
        self,
        tool_name: str,
        user_id: str = "",
        organization_id: str = "",
        resource_id: str = "",
    ) -> GuardResult:
        permitted, reason = await self.permission_checker.check_permission(
            tool_name=tool_name,
            user_id=user_id,
            organization_id=organization_id,
            resource_id=resource_id,
        )

        if not permitted:
            logger.warning(
                "Tool execution blocked by permission check",
                extra={
                    "event": "ai_tool_blocked",
                    "tool": tool_name,
                    "user_id": user_id,
                    "reason": reason,
                },
            )
            return GuardResult(
                allowed=False,
                blocked_reason=reason,
            )

        return GuardResult(allowed=True)


prompt_guard = PromptGuard()
