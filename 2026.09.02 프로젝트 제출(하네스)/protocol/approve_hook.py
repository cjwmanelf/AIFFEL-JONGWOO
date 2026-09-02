"""사람 대신 승인창에 응답하는 훅. RUNBOOK 의 '3초 안에 1번 Yes' 규약을 기계로 재현한다.

    python approve_hook.py <조건 A|B> <로그파일경로>

PreToolUse 훅으로 붙는다. 표준입력으로 도구 호출 정보를 받고, 그 조건의 allowlist 에
걸리지 않는 호출이면 WAIT_SECONDS 만큼 기다린 뒤 허용한다. 걸리는 호출은 즉시 허용한다.

왜 이렇게 하나:
  헤드리스 실행에는 승인창을 누를 사람이 없다. 그냥 돌리면 allowlist 밖 호출이 '거절'되어
  '사람이 3초 뒤 승인'과 전혀 다른 상황이 된다. 그래서 규약을 그대로 기계화한다.

무엇이 달라지나 (보고서에 반드시 적을 것):
  사람의 반응 시간이 3.0초 상수로 고정된다. 통제는 좋아지지만, 실제 사람의 가변적 지연이나
  자리를 비우는 상황은 재현되지 않는다. 리허설에서 사람은 5초~134초까지 흔들렸다.
"""
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
from extract_run import allowlist_patterns, blocking_parts  # noqa: E402

WAIT_SECONDS = 3.0


def main() -> int:
    cond = sys.argv[1]
    log_path = Path(sys.argv[2])

    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    tool = payload.get("tool_name", "")
    tool_input = payload.get("tool_input") or {}
    command = tool_input.get("command", "")

    entry = {"ts": time.time(), "tool": tool, "command": command}

    if tool == "Bash" and command:
        blocking = blocking_parts(command, allowlist_patterns(cond))
        if blocking:
            entry.update(prompted=True, waited=WAIT_SECONDS, blocking=blocking)
            time.sleep(WAIT_SECONDS)
        else:
            entry.update(prompted=False, waited=0.0)
    else:
        entry.update(prompted=False, waited=0.0, note="Bash 아님")

    with log_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    json.dump({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "permissionDecisionReason": "실험 훅: 3초 응답 규약을 기계로 재현",
        }
    }, sys.stdout)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
