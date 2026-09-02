"""실행 1회분 폴더를 만든다.

    python scripts/new_run.py --task 1 --cond A --seq 1

runs/<run_id>/work/ 에 픽스처를 깨끗이 복사하고, 조건에 맞는
.claude/settings.json 을 심고, 빈 기록지를 만든다.
"""
import argparse
import os
import shutil
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent


def find_claude() -> str:
    """claude 실행 파일의 전체 경로를 찾는다.

    이미 열려 있는 PowerShell 창은 PATH 가 낡아 'claude' 를 못 찾는 일이 있다.
    그래서 이름이 아니라 전체 경로를 박아서 출력한다.

    2026-09-02 이 PC 에서 실제로 확인된 위치는 네이티브 설치본
    C:\\Users\\<user>\\.local\\bin\\claude.exe 이고 PATH 에는 없다. 그래서 이 경로를 가장 먼저 본다.
    (npm 셰임 claude.cmd / claude.ps1 은 이 PC 에 없다.)
    """
    candidates = [
        Path.home() / ".local" / "bin" / "claude.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "claude" / "claude.exe",
        Path(os.environ.get("APPDATA", "")) / "npm" / "node_modules" / "@anthropic-ai"
        / "claude-code" / "bin" / "claude.exe",
        Path(os.environ.get("APPDATA", "")) / "npm" / "claude.cmd",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
    found = shutil.which("claude.exe") or shutil.which("claude.cmd") or shutil.which("claude")
    return found or str(Path.home() / ".local" / "bin" / "claude.exe")
TASK_DIRS = {
    "1": "task1-parse-log",
    "2": "task2-refactor-util",
    "3": "task3-fix-failing",
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", required=True, choices=sorted(TASK_DIRS))
    ap.add_argument("--cond", required=True, choices=["A", "B"])
    ap.add_argument("--seq", required=True, type=int, help="실행 순서 번호 (1~6)")
    ap.add_argument("--rehearsal", action="store_true", help="사전 점검용, 집계에서 제외")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    tag = "rehearsal_" if args.rehearsal else ""
    run_id = f"r{args.seq}_{tag}task{args.task}_{args.cond}"
    run_dir = ROOT / "runs" / run_id

    work = run_dir / "work"
    existed = run_dir.exists()

    if existed and args.force:
        shutil.rmtree(run_dir)
        existed = False

    if not existed:
        src = ROOT / "fixtures" / TASK_DIRS[args.task]
        shutil.copytree(src, work)

        claude_dir = work / ".claude"
        claude_dir.mkdir()
        settings = (ROOT / "protocol" / f"settings.{args.cond}.json").read_text(encoding="utf-8")
        (claude_dir / "settings.json").write_text(settings, encoding="utf-8")

        template = (ROOT / "results" / "record-template.md").read_text(encoding="utf-8")
        record = (
            template.replace("{{RUN_ID}}", run_id)
            .replace("{{TASK}}", args.task)
            .replace("{{COND}}", args.cond)
            .replace("{{SEQ}}", str(args.seq))
            .replace("{{EXCLUDED}}", "yes" if args.rehearsal else "no")
        )
        (run_dir / "record.md").write_text(record, encoding="utf-8")

    prompt = (ROOT / "protocol" / "prompt.txt").read_text(encoding="utf-8").strip()

    settings_path = ROOT / "protocol" / f"settings.{args.cond}.json"
    claude_exe = find_claude()
    # CLI 가 회차 사이에 자동 업데이트되면 '같은 버전'이라는 고정 조건이 깨진다.
    # 리허설 2건에서 실제로 2.1.226 -> 2.1.258 로 바뀌었다. 그래서 매번 끈다.
    # 이 환경 변수가 정말 먹는지는 extract_run.py 가 뽑는 cli_version 이 회차 간
    # 동일한지로 확인한다.
    launch = (
        '$env:DISABLE_AUTOUPDATER="1"; '
        f'Set-Location "{work}"; '
        f'& "{claude_exe}" --permission-mode acceptEdits --settings "{settings_path}"'
    )

    print(("이미 있습니다: " if existed else "만들었습니다: ") + f"runs/{run_id}  (조건 {args.cond})")
    if existed:
        print("(폴더를 비우고 다시 만들려면 --force)")
    print()
    print("1) 새 PowerShell 창에 아래 한 줄을 붙여넣는다")
    print("   ※ Windows PowerShell 5.1 은 '&&' 를 못 쓴다. 반드시 ';' 로 이어야 한다.")
    print()
    print("   " + launch)
    print()
    print("2) 세션이 열리면 아래 문장을 그대로 붙여넣기 (스톱워치 불필요, 시간은 트랜스크립트에서 추출)")
    print()
    print("   " + prompt)
    print()
    print("3) 승인창이 뜨면 3초 안에 '이번만 허용'. 'always allow' 는 절대 누르지 않는다.")
    print("   뜬 횟수만 정 표시로 센다.")
    print("4) DONE 이 나오면 세션 종료 -> python verify.py 로 PASS 확인")
    print("5) 수치 자동 추출:")
    print(f"   python scripts/extract_run.py {run_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
