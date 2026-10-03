from backend.rag.ingest import retrieve_policies

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class PolicyQuery(BaseModel):
    query: str = Field(..., min_length=3, max_length=500)


@tool("search_business_policies", args_schema=PolicyQuery)
def search_business_policies_tool(query: str) -> str:
    """Search synthetic demo business policies (shipping, returns, refunds, SLA, support).
    These are not official Olist policies. Use when the user asks about policy, eligibility,
    or why a delay matters under demo rules.
    """
    from backend.tools.order_tools import _dumps, _record

    try:
        hits = retrieve_policies(query)
        sources = sorted({h["source"] for h in hits})
        _record(
            "search_business_policies",
            "Retrieve demo policy documents",
            "ok" if hits else "empty",
            extra={"sources": sources},
        )
        if not hits:
            return _dumps(
                {
                    "found": False,
                    "message": "No matching demo policy was found. Do not invent a policy.",
                }
            )
        return _dumps({"found": True, "sources": sources, "chunks": hits})
    except Exception as exc:
        _record("search_business_policies", "Retrieve demo policy documents", "error")
        return _dumps(
            {
                "found": False,
                "error": "Policy search is unavailable",
                "detail": str(exc.__class__.__name__),
            }
        )
