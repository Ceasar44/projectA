__all__ = ["CustomerSupportAgentService"]


def __getattr__(name: str):
    if name == "CustomerSupportAgentService":
        from app.domain.customer_support.service import CustomerSupportAgentService

        return CustomerSupportAgentService
    raise AttributeError(name)
