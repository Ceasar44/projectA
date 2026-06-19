from app.infrastructure.integrations.extern_agent_adapter import (
    CrmExternAgentAdapter,
    CrmExternAgentModel,
    CrmSupportTool,
)


SrcAgentAdapter = CrmExternAgentAdapter
BackendSrcAgentModel = CrmExternAgentModel

__all__ = [
    "BackendSrcAgentModel",
    "CrmExternAgentAdapter",
    "CrmExternAgentModel",
    "CrmSupportTool",
    "SrcAgentAdapter",
]
