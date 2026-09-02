import re
from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
LOG_PATH = HERE / "sample.log"

CODE_RE = re.compile(r"code=(E\d+)")


def main() -> None:
    counts = Counter()

    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            parts = line.split(maxsplit=2)
            if len(parts) < 3:
                continue
            level = parts[2].split(maxsplit=1)[0]
            if level != "ERROR":
                continue
            match = CODE_RE.search(line)
            if match:
                counts[match.group(1)] += 1

    rows = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))

    print("code,count")
    for code, count in rows:
        print(f"{code},{count}")


if __name__ == "__main__":
    main()
