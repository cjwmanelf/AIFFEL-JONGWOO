from collections import Counter
from pathlib import Path

HERE = Path(__file__).parent
LOG_PATH = HERE / "sample.log"


def main() -> None:
    counts: Counter[str] = Counter()
    with LOG_PATH.open(encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) < 3 or parts[2] != "ERROR":
                continue
            for token in parts:
                if token.startswith("code="):
                    counts[token[len("code="):]] += 1
                    break

    rows = sorted(counts.items(), key=lambda item: (-item[1], item[0]))

    print("code,count")
    for code, count in rows:
        print(f"{code},{count}")


if __name__ == "__main__":
    main()
