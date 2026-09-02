import re
from pathlib import Path

HERE = Path(__file__).parent
LOG_PATH = HERE / "sample.log"

CODE_RE = re.compile(r"code=(E\d+)")


def main() -> None:
    counts: dict[str, int] = {}

    with LOG_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3 or parts[2] != "ERROR":
                continue

            m = CODE_RE.search(line)
            if not m:
                continue

            code = m.group(1)
            counts[code] = counts.get(code, 0) + 1

    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    print("code,count")
    for code, count in rows:
        print(f"{code},{count}")


if __name__ == "__main__":
    main()
