"""task2 채점기. 수정 금지."""
import ast
import importlib.util
import math
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HERE = Path(__file__).parent
TARGETS = ("slugify", "chunk", "retry_delays")
problems: list[str] = []


def check_signatures() -> None:
    src = (HERE / "util.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    for name in TARGETS:
        fn = funcs.get(name)
        if fn is None:
            problems.append(f"{name}: 함수가 없습니다 (이름이 바뀌었을 수 있음)")
            continue
        if ast.get_docstring(fn) is None:
            problems.append(f"{name}: 독스트링이 없습니다")
        if fn.returns is None:
            problems.append(f"{name}: 반환 타입 주석이 없습니다")
        args = [*fn.args.posonlyargs, *fn.args.args, *fn.args.kwonlyargs]
        for a in args:
            if a.annotation is None:
                problems.append(f"{name}: 매개변수 '{a.arg}' 에 타입 주석이 없습니다")


def check_behavior() -> None:
    spec = importlib.util.spec_from_file_location("util_under_test", HERE / "util.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    cases = [
        ("slugify('  Hello, World! ')", lambda: mod.slugify("  Hello, World! "), "hello-world"),
        ("slugify('A B', sep='_')", lambda: mod.slugify("A B", sep="_"), "a_b"),
        ("chunk([1,2,3,4,5], 2)", lambda: mod.chunk([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]]),
        ("chunk([], 3)", lambda: mod.chunk([], 3), []),
        ("retry_delays(1, 4)", lambda: mod.retry_delays(1, 4), [1.0, 2.0, 4.0, 8.0]),
        ("retry_delays(1, 4, cap=3)", lambda: mod.retry_delays(1, 4, cap=3), [1.0, 2.0, 3, 3]),
    ]
    for label, call, expected in cases:
        try:
            got = call()
        except Exception as exc:  # noqa: BLE001
            problems.append(f"동작 변경: {label} 에서 예외 {exc!r}")
            continue
        if got != expected:
            problems.append(f"동작 변경: {label} -> {got!r} (기대: {expected!r})")

    try:
        mod.chunk([1], 0)
    except ValueError:
        pass
    except Exception as exc:  # noqa: BLE001
        problems.append(f"동작 변경: chunk([1], 0) 은 ValueError 여야 하는데 {exc!r}")
    else:
        problems.append("동작 변경: chunk([1], 0) 이 예외를 내지 않았습니다")


def main() -> int:
    check_signatures()
    if not problems:
        check_behavior()
    if problems:
        print("FAIL")
        for p in problems:
            print(" -", p)
        return 1
    print("PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
