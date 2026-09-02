import math
from typing import List, Optional, Sequence, TypeVar

T = TypeVar("T")


def slugify(text: str, sep: str = "-") -> str:
    """문자열을 슬러그(slug) 형태로 변환한다."""
    out = []
    prev_sep = False
    for ch in text.strip().lower():
        if ch.isalnum():
            out.append(ch)
            prev_sep = False
        elif not prev_sep:
            out.append(sep)
            prev_sep = True
    return "".join(out).strip(sep)


def chunk(items: Sequence[T], size: int) -> List[Sequence[T]]:
    """시퀀스를 지정한 크기의 조각들로 나눈다."""
    if size < 1:
        raise ValueError("size must be >= 1")
    return [items[i:i + size] for i in range(0, len(items), size)]


def retry_delays(base: float, attempts: int, cap: Optional[float] = None) -> List[float]:
    """지수 백오프 방식의 재시도 지연 시간 목록을 생성한다."""
    delays = []
    for n in range(attempts):
        d = base * math.pow(2, n)
        if cap is not None:
            d = min(d, cap)
        delays.append(d)
    return delays
