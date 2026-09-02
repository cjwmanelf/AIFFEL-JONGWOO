"""task3 채점기. 수정 금지."""
import hashlib
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
TEST_SHA256 = "d765b30dbed926ebf8eacd5022e8f792ae984d968879ce80c1d49fcc240d558f"


def main() -> int:
    test_file = HERE / "test_me.py"
    if not test_file.exists():
        print("FAIL: test_me.py 가 없습니다.")
        return 1

    # 줄바꿈(CRLF/LF) 차이로 오판하지 않도록 정규화한 뒤 해시한다
    raw = test_file.read_bytes().replace(b"\r\n", b"\n")
    digest = hashlib.sha256(raw).hexdigest()
    if digest != TEST_SHA256:
        print("FAIL: test_me.py 가 수정되었습니다. 테스트 파일은 고정 조건입니다.")
        print(f"  기대 sha256: {TEST_SHA256}")
        print(f"  현재 sha256: {digest}")
        return 1

    proc = subprocess.run(
        [sys.executable, "-m", "unittest", "-v", "test_me"],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if proc.returncode == 0:
        print("PASS")
        return 0

    print("FAIL: 테스트가 통과하지 않았습니다.")
    print(proc.stderr.strip()[-3000:])
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
