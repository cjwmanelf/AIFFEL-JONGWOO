"""task1 채점기. 수정 금지."""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
EXPECTED = "code,count\nE401,4\nE500,3\nE404,2\nE502,1"


def main() -> int:
    target = HERE / "parse.py"
    if not target.exists():
        print("FAIL: parse.py 가 없습니다.")
        return 1

    proc = subprocess.run(
        [sys.executable, str(target)],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode != 0:
        print("FAIL: parse.py 가 0이 아닌 코드로 끝났습니다.")
        print(proc.stderr.strip()[:2000])
        return 1

    got = "\n".join(line.rstrip() for line in proc.stdout.strip().splitlines())
    if got == EXPECTED:
        print("PASS")
        return 0

    print("FAIL: 출력이 기대값과 다릅니다.")
    print("--- expected ---")
    print(EXPECTED)
    print("--- got ---")
    print(got)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
