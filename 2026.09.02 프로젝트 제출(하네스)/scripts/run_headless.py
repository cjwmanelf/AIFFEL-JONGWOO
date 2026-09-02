"""회차 하나를 헤드리스로 실행한다. 승인 응답은 approve_hook.py 가 대신한다.

    python scripts/run_headless.py --task 1 --cond A --seq 1
    python scripts/run_headless.py --task 1 --cond A --seq 1 --dry-run

runs/<run_id>/ 에 픽스처 복사본과 훅 로그, 헤드리스 결과 JSON 을 남긴다.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from new_run import TASK_DIRS, find_claude  # noqa: E402


def build_settings(cond: str, log_path: Path) -> dict:
    """조건 설정 + 승인 응답 훅을 합친 설정을 만든다."""
    base = json.loads((ROOT / "protocol" / f"settings.{cond}.json").read_text(encoding="utf-8"))
    hook_cmd = (
        f'python "{ROOT / "protocol" / "approve_hook.py"}" {cond} "{log_path}"'
    )
    base["hooks"] = {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": hook_cmd}]}
        ]
    }
    return base


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=sorted(TASK_DIRS))
    ap.add_argument("--cond", required=True, choices=["A", "B"])
    ap.add_argument("--seq", required=True, type=int)
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true", help="명령만 출력하고 실행하지 않는다")
    args = ap.parse_args()

    tag = "rehearsal_" if args.rehearsal else ""
    run_id = f"r{args.seq}_{tag}task{args.task}_{args.cond}"
    run_dir = ROOT / "runs" / run_id
    work = run_dir / "work"

    if run_dir.exists():
        shutil.rmtree(run_dir)
    shutil.copytree(ROOT / "fixtures" / TASK_DIRS[args.task], work)

    template = (ROOT / "results" / "record-template.md").read_text(encoding="utf-8")
    (run_dir / "record.md").write_text(
        template.replace("{{RUN_ID}}", run_id).replace("{{TASK}}", args.task)
        .replace("{{COND}}", args.cond).replace("{{SEQ}}", str(args.seq))
        .replace("{{EXCLUDED}}", "yes" if args.rehearsal else "no"),
        encoding="utf-8",
    )

    hook_log = run_dir / "hook_log.jsonl"
    settings = build_settings(args.cond, hook_log)
    settings_file = run_dir / "settings.used.json"
    settings_file.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    prompt = (ROOT / "protocol" / "prompt.txt").read_text(encoding="utf-8").strip()
    cmd = [
        find_claude(), "-p", prompt,
        "--output-format", "json",
        "--permission-mode", "acceptEdits",
        "--settings", str(settings_file),
    ]

    if args.dry_run:
        print("실행하지 않음. 명령:")
        print("  " + " ".join(f'"{c}"' if " " in c else c for c in cmd))
        print(f"  cwd={work}")
        return 0

    env = dict(os.environ, DISABLE_AUTOUPDATER="1")
    print(f"[{run_id}] 실행 시작 (조건 {args.cond}, task{args.task})")
    t0 = time.time()
    proc = subprocess.run(
        cmd, cwd=work, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=args.timeout, env=env,
    )
    elapsed = time.time() - t0

    (run_dir / "headless_result.json").write_text(proc.stdout or "", encoding="utf-8")
    if proc.stderr.strip():
        (run_dir / "headless_stderr.txt").write_text(proc.stderr, encoding="utf-8")

    try:
        res = json.loads(proc.stdout)
    except Exception:
        print(f"  결과 JSON 파싱 실패. headless_result.json 을 확인할 것. (exit={proc.returncode})")
        print("  stdout 앞부분:", (proc.stdout or "")[:300])
        return 1

    prompted = waited = 0
    if hook_log.exists():
        for line in hook_log.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            e = json.loads(line)
            prompted += 1 if e.get("prompted") else 0
            waited += e.get("waited", 0)

    print(f"  종료: is_error={res.get('is_error')} turns={res.get('num_turns')} "
          f"벽시계={elapsed:.1f}s 비용=${res.get('total_cost_usd', 0):.4f}")
    print(f"  훅: 승인 대체 {prompted}회, 대기 합 {waited:.1f}s")
    if res.get("permission_denials"):
        print(f"  !! 권한 거절 {len(res['permission_denials'])}건 — 훅이 안 먹었을 수 있다")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
