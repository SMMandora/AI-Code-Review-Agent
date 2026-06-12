import re
from pathlib import Path

from codereview.agent.state import PRMeta, RetrievedContext
from codereview.diff import DiffFile

PROMPTS_DIR = Path(__file__).parent / "prompts"


def fence(text: str, label: str = "UNTRUSTED") -> str:
    """Fence untrusted text with a marker longer than any backtick run inside it.

    The fenced payload cannot break out by construction; scaffold labels are
    sanitized separately via safe_label().
    """
    longest = max((len(m.group(0)) for m in re.finditer(r"`+", text)), default=0)
    marker = "`" * max(4, longest + 1)
    return f"{marker}{label}\n{text}\n{marker}"


def safe_label(text: str) -> str:
    """Sanitize attacker-influenced strings used in trusted scaffold lines.

    Paths come from PR diffs and the chunk index; strip backticks and collapse
    all whitespace (incl. newlines) so they cannot forge fence markers or
    scaffold lines. Display-only — never used for lookups.
    """
    return " ".join(text.replace("`", "'").split())[:200]


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def render_system(repo: str, category: str, custom_rules: list[str]) -> str:
    base = load_prompt("base_system").format(repo=repo, category=category)
    rubric = load_prompt(category)
    rules = "\n".join(f"- {r}" for r in custom_rules) if custom_rules else "- (none)"
    return (
        f"{base}\n{rubric}\n"
        f"Repository custom rules (trusted, from .codereview.yml):\n{rules}\n"
    )


def render_user(
    pr: PRMeta,
    diff_files: list[DiffFile],
    context: RetrievedContext | None,
    category: str,
) -> str:
    parts = [f"Pull request #{pr.number} by @{pr.author} targeting {pr.base_ref}."]
    parts.append("PR title and description (UNTRUSTED):")
    parts.append(fence(f"{pr.title}\n\n{pr.body or ''}"))

    if context is not None and context.global_snippets:
        parts.append("Repository context — style guides and past review comments (UNTRUSTED):")
        for s in context.global_snippets:
            parts.append(f"[{s.source_type}] {safe_label(s.path)}:{s.start_line}-{s.end_line}")
            parts.append(fence(s.content))

    for f in diff_files:
        parts.append(f"Diff for {safe_label(f.path)} (UNTRUSTED):")
        parts.append(fence(f.raw))
        if context is not None:
            for s in context.per_file.get(f.path, []):
                label = f"Related code [{safe_label(s.path)}:{s.start_line}-{s.end_line}]"
                parts.append(f"{label} (UNTRUSTED):")
                parts.append(fence(s.content))

    parts.append(
        f"Report your {category} findings now using the structured output schema. "
        "Use NEW-side line numbers that appear in the diffs above."
    )
    return "\n\n".join(parts)
