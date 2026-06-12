import logging

from codereview.agent.state import AgentDeps, RetrievedContext, ReviewState

log = logging.getLogger(__name__)


def make_context_node(deps: AgentDeps):
    async def node(state: ReviewState) -> dict:
        if deps.retriever is None:
            return {"context": RetrievedContext()}
        try:
            ctx = await deps.retriever.retrieve(state["pr"], state["diff_files"])
        except Exception:
            log.exception("retrieval failed — proceeding without RAG context")
            ctx = RetrievedContext()
        return {"context": ctx}

    return node
