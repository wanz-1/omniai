from dataclasses import dataclass
from enum import StrEnum


class ToolRiskLevel(StrEnum):
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    ADMIN = "admin"
    DESTRUCTIVE = "destructive"


TOOL_RISK_MAP: dict[str, ToolRiskLevel] = {
    "read_document": ToolRiskLevel.READ,
    "list_documents": ToolRiskLevel.READ,
    "search_knowledge": ToolRiskLevel.READ,
    "get_weather": ToolRiskLevel.READ,
    "get_stock_price": ToolRiskLevel.READ,
    "send_email": ToolRiskLevel.WRITE,
    "create_document": ToolRiskLevel.WRITE,
    "update_document": ToolRiskLevel.WRITE,
    "schedule_meeting": ToolRiskLevel.WRITE,
    "delete_document": ToolRiskLevel.DESTRUCTIVE,
    "delete_resource": ToolRiskLevel.DESTRUCTIVE,
    "execute_code": ToolRiskLevel.EXECUTE,
    "run_sql_query": ToolRiskLevel.EXECUTE,
    "deploy_service": ToolRiskLevel.ADMIN,
    "modify_permissions": ToolRiskLevel.ADMIN,
    "create_api_key": ToolRiskLevel.ADMIN,
    "access_billing": ToolRiskLevel.ADMIN,
}

TOOL_OWNERSHIP_CHECK: set[str] = {
    "delete_document",
    "delete_resource",
    "update_document",
    "send_email",
}


@dataclass
class ToolPermissionResult:
    permitted: bool
    reason: str = ""


class ToolPermissionChecker:
    REQUIRED_ROLES: dict[ToolRiskLevel, list[str]] = {
        ToolRiskLevel.READ: ["user", "member", "owner", "admin"],
        ToolRiskLevel.WRITE: ["member", "owner", "admin"],
        ToolRiskLevel.EXECUTE: ["owner", "admin"],
        ToolRiskLevel.ADMIN: ["admin"],
        ToolRiskLevel.DESTRUCTIVE: ["owner", "admin"],
    }

    async def check_permission(
        self,
        tool_name: str,
        user_id: str = "",
        organization_id: str = "",
        resource_id: str = "",
        user_role: str = "user",
    ) -> tuple[bool, str]:
        risk_level = TOOL_RISK_MAP.get(tool_name)
        if risk_level is None:
            return False, f"Unknown tool: {tool_name}"

        allowed_roles = self.REQUIRED_ROLES.get(risk_level, [])
        if user_role not in allowed_roles:
            return False, f"Role '{user_role}' not permitted for {tool_name} ({risk_level.value})"

        if tool_name in TOOL_OWNERSHIP_CHECK and resource_id and user_id:
            if not await self._check_ownership(tool_name, user_id, resource_id):
                return False, "Resource ownership check failed"

        return True, ""

    async def _check_ownership(
        self,
        tool_name: str,
        user_id: str,
        resource_id: str,
    ) -> bool:
        return True


tool_permission_checker = ToolPermissionChecker()
