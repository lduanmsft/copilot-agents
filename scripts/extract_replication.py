from __future__ import annotations

import html
import os
import re
from collections import Counter
from pathlib import Path
from typing import Iterable

import yaml


REPO_ROOT = Path(r"C:\Users\lduan\repos\mi-tsg\TSG-SQL-MI-TransactionalReplication")
OUTPUT_DIR = Path(r"C:\Users\lduan\.copilot\agents\skills\kql-templates\mi\replication")
OUTPUT_PATH = OUTPUT_DIR / "replication.yaml"
REPO_NAME = REPO_ROOT.name

TABLE_PATTERN = re.compile(r"\b(?:cluster\([^\n]*?\)\.database\([^\n]*?\)\.)?((?:Mon|Alr)\w+)\b")
TOP_LEVEL_TABLE_PATTERN = re.compile(r"^(?:cluster\([^\n]*?\)\.database\([^\n]*?\)\.)?((?:Mon|Alr)\w+)\b")
LET_PATTERN = re.compile(r"^let\s+[A-Za-z_][A-Za-z0-9_]*\s*=")
CODE_FENCE_PATTERN = re.compile(r"^```")
PROMPT_STOP_WORDS = {
    "timestamp",
    "precisetimestamp",
    "originaleventtimestamp",
    "clustername",
    "nodename",
    "appname",
    "apptypename",
    "subscriptionid",
    "count_",
}
COLUMN_NAME_PATTERN = re.compile(r"\b([A-Za-z_][A-Za-z0-9_]*)\b")
KQL_OPERATORS = {
    "where",
    "project",
    "project-away",
    "project-reorder",
    "project-keep",
    "summarize",
    "extend",
    "join",
    "sort",
    "order",
    "take",
    "limit",
    "render",
    "distinct",
    "top",
    "parse",
    "mv-expand",
    "make-series",
    "invoke",
    "serialize",
    "evaluate",
    "union",
    "lookup",
    "sample",
}
COLUMN_SKIP_WORDS = KQL_OPERATORS | {
    "by",
    "bin",
    "ago",
    "contains",
    "startswith",
    "endswith",
    "has",
    "has_any",
    "has_all",
    "between",
    "and",
    "or",
    "not",
    "in",
    "in~",
    "kind",
    "fullouter",
    "inner",
    "leftouter",
    "rightouter",
    "on",
    "asc",
    "desc",
    "true",
    "false",
    "count",
    "min",
    "max",
    "sum",
    "avg",
    "arg_max",
    "arg_min",
    "iff",
    "strcat",
    "row_cumsum",
    "prev",
    "datetime",
    "now",
    "toint",
    "tostring",
    "datatable",
    "cluster",
    "database",
    "table",
    "if",
}

TABLE_DESCRIPTIONS = {
    "MonTranReplTraces": "MI transactional replication telemetry",
    "MonLogReaderTraces": "MI log reader phase telemetry",
    "MonCDCTraces": "MI CDC capture telemetry",
    "MonCTTraces": "MI change tracking cleanup telemetry",
    "MonSqlAgent": "MI SQL Agent job telemetry",
    "MonSQLSystemHealth": "MI SQL system health telemetry",
    "AlrSQLErrorsReported": "MI SQL error alert telemetry",
    "MonDmRealTimeResourceStats": "MI real-time database resource telemetry",
    "MonDatabaseMetadata": "MI database metadata telemetry",
    "MonManagedDatabaseInfo": "MI managed database metadata",
    "MonSQLXStoreIOStats": "MI SQL XStore IO telemetry",
    "AlrWinFabHealthDeployedAppEvent": "MI deployed application event alerts",
    "MonDmDbHadrReplicaStates": "MI HADR replica state telemetry",
    "MonRgLoad": "MI resource governor load telemetry",
}

SCENARIO_HINTS = [
    ("latency", "Troubleshoot replication latency"),
    ("lag", "Troubleshoot replication lag"),
    ("cleanup", "Troubleshoot cleanup backlog"),
    ("logfull", "Troubleshoot log full due to replication"),
    ("lognearfull", "Troubleshoot log growth due to replication"),
    ("geo-failover", "Investigate geo-failover side effects"),
    ("decrypt azure storage key", "Troubleshoot Azure storage key decryption failures"),
    ("pipe instances are busy", "Troubleshoot replication dispatcher saturation"),
    ("untrusted domain", "Troubleshoot replAgentUser authentication failures"),
    ("target principal name", "Troubleshoot target principal name errors"),
    ("cdc", "Troubleshoot CDC capture issues"),
    ("change tracking", "Troubleshoot change tracking issues"),
    ("replication", "Troubleshoot transactional replication issues"),
]

PROSE_PREFIXES = (
    "#",
    "##",
    "###",
    "- ",
    "* ",
    "1.",
    "2.",
    "3.",
    "4.",
    "5.",
    "6.",
    "7.",
    "8.",
    "9.",
)


def sanitize_text(value: str) -> str:
    placeholder_map: dict[str, str] = {}

    def preserve_placeholder(match: re.Match[str]) -> str:
        token = match.group(0)
        inner = match.group(1).strip()
        if not ("_" in inner or " " in inner or "-" in inner or any(ch.isupper() for ch in inner)):
            return token
        key = f"__PLACEHOLDER_{len(placeholder_map)}__"
        placeholder_map[key] = token
        return key

    value = html.unescape(value)
    value = re.sub(r"<\s*([A-Za-z0-9_][A-Za-z0-9_\- ]*)\s*>", preserve_placeholder, value)
    value = value.replace("\u00a0", " ")
    value = value.replace("\r", "")
    value = re.sub(r"!\[[^\]]*\]\([^\)]*\)", "", value)
    value = re.sub(r"\[([^\]]+)\]\([^\)]*\)", r"\1", value)
    value = re.sub(r"<https?://[^>]+>", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    for key, token in placeholder_map.items():
        value = value.replace(key, token)
    return value



def clean_line(line: str) -> str:
    line = sanitize_text(line)
    line = re.sub(r"^\s*>+\s?", "", line)
    line = re.sub(r"^\s*Execute(?:\s+in)?\s*:\s*\[(?:Web|Desktop)\].*$", "", line, flags=re.IGNORECASE)
    line = re.sub(r"^\s*Execute\s+in\s+\[(?:Web|Desktop)\](?:\s*\[(?:Web|Desktop)\])?.*$", "", line, flags=re.IGNORECASE)
    line = re.sub(r"^\s*From\s+https?://.*$", "", line, flags=re.IGNORECASE)
    line = line.replace("`", "")
    line = re.sub(r"\s+", " ", line).strip()
    return line



def is_probable_prose(line: str) -> bool:
    if not line:
        return True
    lower = line.lower()
    if line.startswith(PROSE_PREFIXES):
        return True
    if lower.startswith(("note:", "important:", "warning:", "example:", "instructions:", "title:", "filters ")):
        return True
    if "kusto query" in lower and "|" not in line:
        return True
    if "follow this" in lower or "click " in lower or "open " in lower or "refresh " in lower:
        return True
    if line.endswith(":") and "|" not in line and not LET_PATTERN.match(line):
        return True
    if re.match(r"^[A-Za-z][A-Za-z0-9 /_\-]+$", line) and not TABLE_PATTERN.search(line):
        return True
    return False



def is_query_start(line: str) -> bool:
    if LET_PATTERN.match(line):
        return True
    return bool(TOP_LEVEL_TABLE_PATTERN.match(line))



def is_continuation(line: str, previous_line: str | None, has_body: bool) -> bool:
    if not line:
        return False
    if line in {"{", "}", "};", ";"}:
        return True
    if line.startswith("|"):
        return True
    if line.startswith(")"):
        return True
    if line.startswith("_Execute"):
        return True
    if previous_line and previous_line.rstrip().endswith("(") and TABLE_PATTERN.search(line):
        return True
    first_token = line.split()[0].lower()
    if first_token in KQL_OPERATORS:
        return True
    if line.startswith("by ") or line.startswith("on "):
        return True
    if has_body and TOP_LEVEL_TABLE_PATTERN.match(line) and previous_line and previous_line.rstrip().endswith("("):
        return True
    return False



def normalize_query(query: str) -> str:
    query = re.sub(r"\n{3,}", "\n\n", query.strip())
    return query.strip()



def extract_queries_from_text(text: str) -> list[str]:
    lines = [clean_line(line) for line in text.splitlines()]
    queries: list[str] = []
    current: list[str] = []
    pending_lets: list[str] = []
    previous_line: str | None = None

    def flush() -> None:
        nonlocal current, pending_lets, previous_line
        if not current:
            pending_lets = []
            previous_line = None
            return
        query = normalize_query("\n".join(current))
        if is_valid_kql(query):
            queries.append(query)
        current = []
        pending_lets = []
        previous_line = None

    for raw_line in lines:
        line = raw_line.strip()
        if CODE_FENCE_PATTERN.match(line):
            continue
        if not line:
            continue

        if LET_PATTERN.match(line):
            if current:
                flush()
            pending_lets.append(line)
            previous_line = line
            continue

        if current and is_continuation(line, previous_line, has_body=bool(current)):
            current.append(line)
            previous_line = line
            continue

        if is_query_start(line):
            if current:
                flush()
            current = pending_lets + [line]
            pending_lets = []
            previous_line = line
            continue

        if current and TABLE_PATTERN.search(line) and previous_line and previous_line.rstrip().endswith("("):
            current.append(line)
            previous_line = line
            continue

        if current:
            flush()

        if pending_lets and is_probable_prose(line):
            pending_lets = []
            previous_line = None

    flush()

    unique: list[str] = []
    seen: set[str] = set()
    for query in queries:
        key = re.sub(r"\s+", " ", query)
        if key not in seen:
            seen.add(key)
            unique.append(query)
    return unique



def is_valid_kql(query: str) -> bool:
    if len(query) < 20:
        return False
    if not TABLE_PATTERN.search(query):
        return False
    if "|" not in query:
        return False
    stripped = query.strip()
    if stripped.endswith("("):
        return False
    if stripped.count("(") != stripped.count(")"):
        return False
    lines = [line.strip() for line in query.splitlines() if line.strip()]
    kql_like = 0
    for line in lines:
        if LET_PATTERN.match(line) or is_query_start(line) or is_continuation(line, None, True):
            kql_like += 1
    return kql_like / max(len(lines), 1) >= 0.5



def parameterize_query(query: str) -> str:
    replacements = [
        (r"<\s*(?:server_name|logical_server_name|managed_server_name|subscriber_server_name|ServerName)\s*>", "{ServerName}"),
        (r"<\s*(?:database_name|logical_database_name|DatabaseName)\s*>", "{DatabaseName}"),
        (r"LogicalServerName\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'LogicalServerName =~ "{ServerName}"'),
        (r"logical_server_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'logical_server_name =~ "{ServerName}"'),
        (r"managed_server_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'managed_server_name =~ "{ServerName}"'),
        (r"server_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'server_name =~ "{ServerName}"'),
        (r"LogicalServerName\s*(?:==|=~|contains)\s*'[^']+'", "LogicalServerName =~ '{ServerName}'"),
        (r"logical_server_name\s*(?:==|=~|contains)\s*'[^']+'", "logical_server_name =~ '{ServerName}'"),
        (r"managed_server_name\s*(?:==|=~|contains)\s*'[^']+'", "managed_server_name =~ '{ServerName}'"),
        (r"server_name\s*(?:==|=~|contains)\s*'[^']+'", "server_name =~ '{ServerName}'"),
        (r"logical_database_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'logical_database_name =~ "{DatabaseName}"'),
        (r"managed_database_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'managed_database_name =~ "{DatabaseName}"'),
        (r"database_name\s*(?:==|=~|contains)\s*\"[^\"]+\"", 'database_name =~ "{DatabaseName}"'),
        (r"logical_database_name\s*(?:==|=~|contains)\s*'[^']+'", "logical_database_name =~ '{DatabaseName}'"),
        (r"managed_database_name\s*(?:==|=~|contains)\s*'[^']+'", "managed_database_name =~ '{DatabaseName}'"),
        (r"database_name\s*(?:==|=~|contains)\s*'[^']+'", "database_name =~ '{DatabaseName}'"),
        (r"(let\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*)\"[^\"]+\"", r'\1"{ServerName}"'),
        (r"(let\s+[A-Za-z_][A-Za-z0-9_]*\s*=\s*)'[^']+'", r"\1'{ServerName}'"),
    ]
    result = query
    for pattern, replacement in replacements:
        result = re.sub(pattern, replacement, result)
    return result



def extract_tables(query: str) -> list[str]:
    seen: list[str] = []
    for table in TABLE_PATTERN.findall(query):
        if table not in seen:
            seen.append(table)
    return seen



def extract_primary_table(query: str) -> str:
    for line in query.splitlines():
        match = TOP_LEVEL_TABLE_PATTERN.match(line.strip())
        if match:
            return match.group(1)
    tables = extract_tables(query)
    return tables[0] if tables else "Unknown"



def extract_key_columns(query: str) -> list[str]:
    counts: Counter[str] = Counter()
    for line in query.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        if TABLE_PATTERN.search(stripped):
            for table in extract_tables(stripped):
                counts.pop(table, None)
        for token in COLUMN_NAME_PATTERN.findall(stripped):
            lower = token.lower()
            if lower in COLUMN_SKIP_WORDS:
                continue
            if token in extract_tables(query):
                continue
            if lower.startswith("http"):
                continue
            if re.fullmatch(r"\d+", token):
                continue
            counts[token] += 1
    prioritized: list[str] = []
    preferred = [
        "LogicalServerName",
        "logical_server_name",
        "database_name",
        "logical_database_name",
        "managed_database_name",
        "event",
        "error_code",
        "error_number",
        "message_type",
        "exception_message",
        "agent_id",
        "resource_id",
        "rows_in_delay",
        "latency",
        "replica_role",
        "collation_name",
        "code_package_version",
    ]
    for column in preferred:
        if counts[column] and column not in prioritized:
            prioritized.append(column)
    for column, _ in counts.most_common():
        if column.lower() in PROMPT_STOP_WORDS:
            continue
        if column not in prioritized:
            prioritized.append(column)
        if len(prioritized) >= 4:
            break
    return prioritized[:4]



def infer_focus_phrase(query: str, primary_table: str, key_columns: list[str]) -> str:
    lower = query.lower()
    base = TABLE_DESCRIPTIONS.get(primary_table, primary_table)
    if "render timechart" in lower:
        base += " trend"
    if "count()" in lower or "summarize count" in lower:
        base += " counts"
    event_match = re.search(r"event\s*(?:==|=~|in)\s*(.+)", query)
    if event_match:
        event_text = event_match.group(1)
        quoted = re.findall(r'"([^"]+)"|\'([^\']+)\'', event_text)
        flattened = [item for pair in quoted for item in pair if item]
        if flattened:
            base += f" for {' / '.join(flattened[:2]).replace('_', ' ')}"
    elif "error_number" in lower or "error_code" in lower:
        numbers = re.findall(r"(?:error_number|error_code)\s*==\s*\"?(\-?\d+)\"?", query)
        if numbers:
            base += f" for error {'/'.join(numbers[:2])}"
    elif key_columns:
        base += f" by {', '.join(key_columns[:2])}"
    return re.sub(r"\s+", " ", base).strip()



def prettify_topic(topic: str) -> str:
    text = re.sub(r"^(?:TSG|SOP)TRCL\d+[-:]*", "", topic, flags=re.IGNORECASE)
    text = text.replace("_", " ").replace("-", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text or topic



def infer_scenario_prompt(topic: str, query: str, primary_table: str) -> str:
    topic_phrase = prettify_topic(topic)
    combined = f"{topic_phrase} {query}".lower()
    for needle, prompt in SCENARIO_HINTS:
        if needle in combined:
            return prompt
    if primary_table == "MonCTTraces":
        return "Troubleshoot syscommittab cleanup backlog"
    if primary_table == "MonCDCTraces":
        return "Troubleshoot CDC capture job failures"
    if primary_table == "MonTranReplTraces":
        return "Troubleshoot transactional replication failures"
    return f"Investigate {topic_phrase}".strip()



def build_prompts(topic: str, query: str, primary_table: str) -> list[str]:
    key_columns = extract_key_columns(query)
    prompt1 = infer_focus_phrase(query, primary_table, key_columns)
    prompt2 = primary_table if not key_columns else f"{primary_table} {' '.join(key_columns[:4])}"
    prompt3 = infer_scenario_prompt(topic, query, primary_table)
    return [prompt1, prompt2, prompt3]



def iter_markdown_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*.md")):
        if path.is_file():
            yield path



def build_skills() -> list[dict]:
    skills: list[dict] = []
    skill_index = 1
    seen_queries: set[str] = set()

    for md_file in iter_markdown_files(REPO_ROOT):
        content = md_file.read_text(encoding="utf-8-sig", errors="replace")
        topic = md_file.stem
        rel_path = md_file.relative_to(REPO_ROOT).as_posix()
        for query in extract_queries_from_text(content):
            parameterized = parameterize_query(query)
            key = re.sub(r"\s+", " ", parameterized.strip())
            if key in seen_queries:
                continue
            seen_queries.add(key)
            primary_table = extract_primary_table(parameterized)
            skills.append(
                {
                    "id": f"MI-replication-{skill_index}",
                    "Topic": topic,
                    "Source": f"{REPO_NAME}/{rel_path}",
                    "Prompts": build_prompts(topic, parameterized, primary_table),
                    "CustomizedParameters": ["ServerName", "DatabaseName"],
                    "KustoQueries": [
                        {
                            "TableName": primary_table,
                            "ExecutedQuery": parameterized,
                        }
                    ],
                }
            )
            skill_index += 1
    return skills



def audit_skills(skills: list[dict]) -> list[str]:
    issues: list[str] = []
    for skill in skills:
        queries = skill.get("KustoQueries") or []
        if len(queries) != 1:
            issues.append(f"{skill.get('id')}: expected exactly one KustoQueries entry")
            continue
        kusto = queries[0]
        executed = kusto.get("ExecutedQuery", "")
        actual_table = extract_primary_table(executed)
        declared_table = kusto.get("TableName")
        if declared_table != actual_table:
            issues.append(f"{skill.get('id')}: TableName '{declared_table}' != actual '{actual_table}'")
        if not is_valid_kql(executed):
            issues.append(f"{skill.get('id')}: invalid or prose-heavy KQL")
        if re.search(r"(?:==|=~|contains)\s*[\"']\s*[\"']", executed):
            issues.append(f"{skill.get('id')}: blank placeholder/value detected in query")
        prompts = skill.get("Prompts") or []
        if len(prompts) != 3:
            issues.append(f"{skill.get('id')}: expected 3 prompts")
        else:
            if any(len(prompt.strip()) < 8 for prompt in prompts):
                issues.append(f"{skill.get('id')}: prompts too short")
            if len({prompt.strip().lower() for prompt in prompts}) != 3:
                issues.append(f"{skill.get('id')}: prompts are not unique")
    return issues



def write_yaml(skills: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with OUTPUT_PATH.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(
            {"SqlSkills": skills},
            handle,
            sort_keys=False,
            allow_unicode=True,
            width=160,
        )



def main() -> None:
    skills = build_skills()
    write_yaml(skills)
    loaded = yaml.safe_load(OUTPUT_PATH.read_text(encoding="utf-8"))
    issues = audit_skills(loaded.get("SqlSkills", []))
    tables = Counter()
    for skill in loaded.get("SqlSkills", []):
        for query in skill.get("KustoQueries", []):
            for table in extract_tables(query.get("ExecutedQuery", "")):
                tables[table] += 1

    print(f"Extracted {len(loaded.get('SqlSkills', []))} replication skills to {OUTPUT_PATH}")
    print("Tables found:")
    for table, count in sorted(tables.items()):
        print(f"  {table}: {count}")
    if issues:
        print("Audit issues:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("Audit issues: none")


if __name__ == "__main__":
    main()
