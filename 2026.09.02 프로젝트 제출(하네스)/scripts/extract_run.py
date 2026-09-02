"""세션 트랜스크립트에서 회차 수치를 뽑아 record.md 를 채운다.

    python scripts/extract_run.py r1_task1_A
    python scripts/extract_run.py --all

~/.claude/projects/**/*.jsonl 에서 해당 run 의 work 폴더를 cwd 로 가진 세션을 찾는다.

직접 측정되는 값 : 완료 시간, Bash 호출 수와 명령 원문, 호출별 지연, 토큰, 턴 수, permissionMode
규칙으로 유도하는 값: approvals (= 그 조건의 allowlist 에 걸리지 않는 Bash 호출 수)
직접 세어야 하는 값: 사람이 실제로 본 승인창 수 (교차 확인용, 기록지에 손으로 적는다)

승인 이벤트는 트랜스크립트에 남지 않는다. approvals 는 '측정'이 아니라 '유도'다.
"""
import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = Path.home() / ".claude" / "projects"

# 6회 내내 이 모드 하나로 유지되어야 한다. 세션 도중 바뀌면 그 회차는 무효다.
REQUIRED_MODE = "acceptEdits"


def norm(p: str) -> str:
    return str(p).replace("/", "\\").rstrip("\\").lower()


def ts(s):
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def prompt_head(n: int = 20) -> str:
    """고정 프롬프트의 앞부분. 실험 세션을 식별하는 지문으로 쓴다."""
    return (ROOT / "protocol" / "prompt.txt").read_text(encoding="utf-8").strip()[:n]


def starts_with_experiment_prompt(records) -> bool:
    """이 세션의 첫 사용자 발화가 고정 프롬프트인가.

    작업 폴더를 cwd 로 가진 세션은 실험 세션 말고도 있을 수 있다. 실험을 설계·집계하는
    에이전트가 그 폴더에서 명령 한 번만 돌려도 cwd 가 같게 찍힌다. 그래서 cwd 만으로
    고르면 엉뚱한 세션을 집는다. 고정 프롬프트로 시작했는지까지 봐야 한다.
    """
    head = prompt_head()
    for r in sorted(records, key=lambda x: x.get("timestamp") or ""):
        if r.get("type") != "user":
            continue
        content = (r.get("message") or {}).get("content")
        text = content if isinstance(content, str) else None
        if text is None and isinstance(content, list):
            for it in content:
                if isinstance(it, dict) and it.get("type") == "text":
                    text = it.get("text")
                    break
        if not text:
            continue
        return text.strip().startswith(head)
    return False


def load_sessions(target_cwd: str):
    """target_cwd 를 cwd 로 가지고 고정 프롬프트로 시작한 세션만 모은다."""
    want = norm(target_cwd)
    sessions = {}
    if not PROJECTS.exists():
        return sessions
    for f in PROJECTS.rglob("*.jsonl"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if want.split("\\")[-2] not in text.lower():
            continue  # 빠른 사전 거르기 (run 폴더 이름)
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if norm(r.get("cwd", "")) != want:
                continue
            sessions.setdefault(r.get("sessionId"), []).append(r)

    return {
        sid: recs for sid, recs in sessions.items()
        if starts_with_experiment_prompt(recs)
    }


def allowlist_patterns(cond: str):
    cfg = json.loads((ROOT / "protocol" / f"settings.{cond}.json").read_text(encoding="utf-8"))
    pats = []
    for rule in cfg.get("permissions", {}).get("allow", []):
        m = re.fullmatch(r"Bash\((.*)\)", rule)
        if m:
            pats.append(m.group(1))
    return pats


# 2026-09-02 리허설로 관찰·교정된 목록.
#
# Claude Code 는 모든 Bash 호출 앞에 cd "<작업폴더>" && 를 붙인다.
# 그리고 allowlist 가 완전히 비어 있는 조건 A 에서도 아래 명령들은 승인 없이 지나갔다.
#   근거: 조건 A 리허설의 호출 `ls -la; echo "---"; cat TASK.md` 는 지연이 1.2초였고
#   사람이 실제로 본 승인창은 1회(python verify.py)뿐이었다. 1.2초는 사람이 누른 시간이
#   아니다. 즉 이 명령들은 allowlist 와 무관하게 하네스가 자체적으로 통과시킨다.
#
# 이 사실의 결과: 조건 B allowlist 의 ls / cat / type / git status / git diff 항목은
# 실질적으로 무효다. 두 조건의 실제 차이를 만드는 것은 python 계열 규칙뿐이다.
# (조작을 지금 바꾸면 사전 등록이 깨지므로 그대로 두고 보고서에 이 사실을 적는다.)
HARNESS_SAFE = ("cd", "echo", "ls", "cat")


def split_parts(command: str):
    """복합 명령을 조각으로 쪼갠다. 맨 앞의 cd "<작업폴더>" 접두사도 한 조각으로 나온다."""
    return [p.strip() for p in re.split(r"&&|\|\||;|\|", command) if p.strip()]


def _matches(part: str, patterns) -> bool:
    for pat in patterns:
        if pat.endswith(":*"):
            if part.startswith(pat[:-2].strip()):
                return True
        elif part == pat:
            return True
    return False


def is_allowed(command: str, patterns) -> bool:
    """Bash(prefix:*) 규칙의 근사 구현.

    복합 명령은 조각으로 쪼개 모든 조각이 통과할 때만 허용으로 센다.
    HARNESS_SAFE 조각(cd, echo)은 allowlist 와 무관하게 통과로 본다.
    """
    parts = split_parts(command)
    if not parts:
        return False
    for part in parts:
        head = part.split()[0] if part.split() else ""
        if head in HARNESS_SAFE:
            continue
        if not _matches(part, patterns):
            return False
    return True


def blocking_parts(command: str, patterns):
    """승인을 유발했을 조각만 돌려준다 (기록·디버깅용)."""
    out = []
    for part in split_parts(command):
        head = part.split()[0] if part.split() else ""
        if head in HARNESS_SAFE:
            continue
        if not _matches(part, patterns):
            out.append(part)
    return out


def analyse(records, cond: str):
    records.sort(key=lambda r: r.get("timestamp") or "")
    uses, results = {}, {}
    first_user = last_msg = None
    tok_in = tok_out = 0
    modes, versions = set(), set()

    for r in records:
        t = ts(r.get("timestamp"))
        if r.get("permissionMode"):
            modes.add(r["permissionMode"])
        if r.get("version"):
            versions.add(r["version"])
        msg = r.get("message") or {}
        content = msg.get("content")
        usage = msg.get("usage") or {}
        tok_in += usage.get("input_tokens", 0) + usage.get("cache_read_input_tokens", 0)
        tok_out += usage.get("output_tokens", 0)

        if r.get("type") == "user" and isinstance(content, str) and first_user is None:
            first_user = t
        if r.get("type") == "assistant" and t:
            last_msg = t
        if isinstance(content, list):
            for item in content:
                if not isinstance(item, dict):
                    continue
                if item.get("type") == "tool_use":
                    uses[item["id"]] = (t, item.get("name"), (item.get("input") or {}))
                elif item.get("type") == "tool_result":
                    results[item.get("tool_use_id")] = t
                elif item.get("type") == "text" and r.get("type") == "user" and first_user is None:
                    first_user = t

    patterns = allowlist_patterns(cond)
    calls = []
    for tid, (t0, name, inp) in uses.items():
        if name != "Bash":
            continue
        t1 = results.get(tid)
        latency = (t1 - t0).total_seconds() if (t0 and t1) else None
        cmd = inp.get("command", "")
        calls.append({
            "command": cmd,
            "latency": latency,
            "allowed_by_rule": is_allowed(cmd, patterns),
            "blocking": blocking_parts(cmd, patterns),
        })
    calls.sort(key=lambda c: c["command"])

    prompted = [c for c in calls if not c["allowed_by_rule"]]
    wall = (last_msg - first_user).total_seconds() if (first_user and last_msg) else None
    verify_attempts = sum(1 for c in calls if "verify.py" in c["command"])

    # 승인이 필요했던 호출들의 지연 합. 승인 대기 + 실행 시간이 섞여 있으므로
    # '승인 대기의 상한'으로만 읽는다. 순수 승인 대기를 따로 떼어낼 방법은 없다.
    lat = [c["latency"] for c in prompted if c["latency"] is not None]
    prompted_latency_sum = round(sum(lat), 1) if lat else None

    return {
        "started_at": first_user.isoformat() if first_user else "",
        "ended_at": last_msg.isoformat() if last_msg else "",
        "wall_seconds": round(wall, 1) if wall is not None else None,
        "bash_calls": len(calls),
        "approvals": len(prompted),
        "attempts": verify_attempts,
        "prompted_latency_sum": prompted_latency_sum,
        "tokens_total": tok_in + tok_out,
        "permission_mode": ",".join(sorted(modes)) or "?",
        "cli_version": ",".join(sorted(versions)) or "?",
        "calls": calls,
    }


def write_record(run_dir: Path, m: dict):
    rec = run_dir / "record.md"
    text = rec.read_text(encoding="utf-8")

    def setf(t, key, val):
        """DATA 블록의 key 값을 채운다. 줄이 없으면 새로 끼워 넣는다.

        기록지가 예전 템플릿으로 만들어져 필드가 없을 수 있다. 그때 조용히 넘어가면
        수치가 소리 없이 사라지므로 반드시 추가한다.
        """
        if val is None or val == "":
            return t
        if re.search(rf"(?m)^{key}:", t):
            return re.sub(rf"(?m)^{key}:.*$", f"{key}: {val}", t, count=1)
        return t.replace("<!-- /DATA -->", f"{key}: {val}\n<!-- /DATA -->", 1)

    for key in ("started_at", "ended_at", "wall_seconds", "approvals", "attempts", "tokens_total"):
        text = setf(text, key, m[key])
    text = setf(text, "approvals_bash", m["approvals"])
    text = setf(text, "approvals_other", 0)
    text = setf(text, "cli_version", m["cli_version"])
    text = setf(text, "permission_mode", m["permission_mode"])
    text = setf(text, "prompted_latency_sum", m["prompted_latency_sum"])

    table = ["", "## 자동 추출 (scripts/extract_run.py)", "",
             f"- CLI 버전: `{m['cli_version']}` / permissionMode: `{m['permission_mode']}`",
             f"- Bash 호출 {m['bash_calls']}건, 그중 규칙에 안 걸려 승인이 필요한 호출 {m['approvals']}건",
             "", "| # | 규칙 허용 | 지연(s) | 승인 유발 조각 | 명령 (cd 접두사 제거) |",
             "|---|---|---|---|---|"]
    for i, c in enumerate(m["calls"], 1):
        lat = f"{c['latency']:.1f}" if c["latency"] is not None else "-"
        shown = re.sub(r'^cd\s+"[^"]*"\s*&&\s*', "", c["command"])
        shown = shown.replace("|", "\\|").replace("\n", " ")[:160]
        blk = ", ".join(f"`{b[:40]}`" for b in c["blocking"]) or "-"
        table.append(
            f"| {i} | {'O' if c['allowed_by_rule'] else '승인 필요'} | {lat} | {blk} | `{shown}` |"
        )
    table.append("")
    table.append("> `approvals` 는 측정값이 아니라 allowlist 규칙을 명령 원문에 대입해 **유도한** 값이다.")
    table.append("> 사람이 실제로 본 승인창 수를 위 승인 로그 표에 적어 교차 확인할 것.")

    marker = "\n## 자동 추출 (scripts/extract_run.py)"
    if marker in text:
        text = text.split(marker)[0].rstrip() + "\n"
    rec.write_text(text.rstrip() + "\n" + "\n".join(table) + "\n", encoding="utf-8")


def process(run_id: str) -> bool:
    run_dir = ROOT / "runs" / run_id
    if not run_dir.exists():
        print(f"  {run_id}: 폴더 없음")
        return False
    cond = run_id.rsplit("_", 1)[-1]
    sessions = load_sessions(str(run_dir / "work"))
    if not sessions:
        print(f"  {run_id}: 아직 세션 기록이 없습니다 (실행 전이거나 다른 폴더에서 실행함)")
        return False
    sid = max(sessions, key=lambda s: max(r.get("timestamp") or "" for r in sessions[s]))
    m = analyse(sessions[sid], cond)
    write_record(run_dir, m)
    print(f"  {run_id}: 세션 {sid[:8]} | Bash {m['bash_calls']}건 | 승인 필요 {m['approvals']}건 "
          f"| {m['wall_seconds']}s | 토큰 {m['tokens_total']} | mode={m['permission_mode']}")

    # 고정 조건 감사: 모드가 acceptEdits 하나로 유지되지 않았으면 그 회차는 못 쓴다.
    if m["permission_mode"] != REQUIRED_MODE:
        print(f"    !! 무효 위험: permissionMode 가 '{m['permission_mode']}' 였다 "
              f"(요구: '{REQUIRED_MODE}' 하나로 유지)")
        print("    !! 세션 도중 모드가 바뀌면 승인 여부가 allowlist 때문인지 모드 때문인지 "
              "구분되지 않는다. record.md 를 excluded: yes 로 바꾸고 다시 돌릴 것.")
    return True


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("run_id", nargs="?")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    if args.all or not args.run_id:
        ids = sorted(p.name for p in (ROOT / "runs").iterdir() if p.is_dir())
    else:
        ids = [args.run_id]

    print("트랜스크립트에서 추출 중...")
    done = sum(1 for i in ids if process(i))
    print(f"\n{done}/{len(ids)} 회차 반영. verified 와 cost_usd, 사람이 센 승인 수는 손으로 채우세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
