"""runs/*/record.md 를 읽어 결과 표를 만들고 사전 판정식을 그대로 적용한다.

    python scripts/tally.py

판정식은 코드에 박혀 있다. 결과를 보고 기준을 고치지 않기 위해서다.
"""
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parent.parent

# --- 사전 판정식 (실행 전 확정, 수정 금지) ---------------------------
APPROVAL_RATIO = 0.5   # B 승인 횟수 <= A 승인 횟수 x 0.5
WALL_RATIO = 0.8       # B 완료 시간 <= A 완료 시간 x 0.8
MIN_TASKS = 2          # 3개 과업 중 2개 이상에서 위 둘을 동시에 만족
COST_BLOWUP = 1.5      # B 총비용이 A 의 1.5배를 넘으면 부작용으로 기각
# ---------------------------------------------------------------------

NUM_FIELDS = {
    "wall_seconds", "wait_seconds", "prompted_latency_sum", "approvals",
    "approvals_observed", "approvals_bash", "approvals_other", "attempts",
    "cost_usd", "tokens_total",
}

REQUIRED_MODE = "acceptEdits"


def parse_record(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.search(r"<!-- DATA -->(.*?)<!-- /DATA -->", text, re.S)
    if not m:
        return {}
    data = {}
    for line in m.group(1).splitlines():
        if ":" not in line:
            continue
        k, _, v = line.partition(":")
        k, v = k.strip(), v.strip()
        if not k or not v:
            continue
        if k in NUM_FIELDS:
            try:
                data[k] = float(v)
            except ValueError:
                continue
        else:
            data[k] = v
    return data


def fmt(v, unit=""):
    if v is None:
        return "-"
    if isinstance(v, float) and v.is_integer():
        return f"{int(v)}{unit}"
    return f"{v}{unit}"


def main() -> int:
    records = []
    for rec_path in sorted((ROOT / "runs").glob("*/record.md")):
        d = parse_record(rec_path)
        if not d or d.get("excluded", "no").lower() == "yes":
            continue
        if "task" not in d or "condition" not in d:
            continue
        records.append(d)

    if not records:
        print("집계할 기록이 없습니다. runs/*/record.md 를 채운 뒤 다시 돌리세요.")
        return 1

    by = {(r["task"], r["condition"]): r for r in records}
    tasks = sorted({r["task"] for r in records})

    lines = ["# 결과 표", "", "`python scripts/tally.py` 가 생성한 파일. 손으로 고치지 말 것.", ""]
    lines.append("| 과업 | 조건 | 승인 횟수 | 완료 시간(s) | 승인 호출 지연 합(s) | 나머지 시간(s) "
                 "| verify 시도 | 통과 | 토큰 |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for t in tasks:
        for c in ("A", "B"):
            r = by.get((t, c))
            if not r:
                lines.append(f"| task{t} | {c} | - | - | - | - | - | - | - |")
                continue
            wall = r.get("wall_seconds")
            pls = r.get("prompted_latency_sum")
            rest = wall - pls if (wall is not None and pls is not None) else wall
            lines.append(
                f"| task{t} | {c} | {fmt(r.get('approvals'))} | {fmt(wall)} | {fmt(pls)} | "
                f"{fmt(round(rest, 1) if rest is not None else None)} | "
                f"{fmt(r.get('attempts'))} | {r.get('verified', '-')} | "
                f"{fmt(r.get('tokens_total'))} |"
            )
    lines.append("")
    lines.append("> `승인 호출 지연 합` = 승인이 필요했던 Bash 호출들의 지연 합. 승인 대기와 "
                 "명령 실행 시간이 섞여 있어 **승인 대기의 상한**으로만 읽는다. "
                 "조건 B 는 승인 호출이 없어 빈칸이다.")

    # ── 고정 조건 감사 ──────────────────────────────────────────────
    # 아직 안 돌린 회차는 필드가 비어 있다. 그것을 '다른 값'으로 세면 없는 위반이 생긴다.
    versions = sorted({r["cli_version"] for r in records if r.get("cli_version")})
    modes = sorted({r["permission_mode"] for r in records if r.get("permission_mode")})
    version_drift = len(versions) > 1
    mode_broken = any(m != REQUIRED_MODE for m in modes)
    ran = len(versions) > 0

    lines.append("")
    lines.append("## 고정 조건 감사")
    lines.append("")
    if not ran:
        lines.append("- 아직 실행된 회차가 없어 감사할 것이 없다.")
    else:
        lines.append(f"- CLI 버전: {', '.join(versions)} "
                     f"→ {'**위반: 회차마다 다르다**' if version_drift else '일치'}")
        lines.append(f"- permissionMode: {', '.join(modes)} "
                     f"→ {'**위반**' if mode_broken else '일치'}")

    # 유도한 승인 횟수와 사람이 실제로 센 횟수가 맞는지 (측정 도구 교정 확인)
    mism = [
        (r["run_id"], r.get("approvals"), r.get("approvals_observed"))
        for r in records
        if r.get("approvals_observed") is not None
        and r.get("approvals") is not None
        and r["approvals"] != r["approvals_observed"]
    ]
    checked = sum(1 for r in records if r.get("approvals_observed") is not None)
    if mism:
        lines.append(f"- 승인 횟수 교차 확인: **{len(mism)}건 불일치** "
                     + ", ".join(f"{rid}(유도 {a:.0f} vs 관찰 {o:.0f})" for rid, a, o in mism))
        lines.append("")
        lines.append("> 유도값이 관찰값과 다르다. `approvals` 는 규칙으로 유도한 값이므로 "
                     "규칙이 실제 하네스 동작과 어긋났다는 뜻이다. "
                     "`extract_run.py` 의 `HARNESS_SAFE` 를 교정하고 다시 집계할 것.")
    elif checked:
        lines.append(f"- 승인 횟수 교차 확인: {checked}건 확인, 전부 일치")
    else:
        lines.append("- 승인 횟수 교차 확인: 사람이 센 값(`approvals_observed`)이 아직 없음")
    if version_drift:
        lines.append("")
        lines.append("> CLI 가 회차 사이에 자동 업데이트되었다. '같은 버전'은 고정 조건이므로 "
                     "조건 간 차이에 버전 차이가 섞여 있다. 이 상태의 결과는 판정에 쓰지 않는다.")
    if mode_broken:
        lines.append("")
        lines.append(f"> 권한 모드가 `{REQUIRED_MODE}` 하나로 유지되지 않았다. 승인 여부가 "
                     "allowlist 때문인지 모드 때문인지 구분되지 않는다.")

    lines.append("")
    lines.append("## 사전 판정식 적용")
    lines.append("")
    lines.append(
        f"- 지지 조건: 3개 과업 중 **{MIN_TASKS}개 이상**에서 "
        f"`B 승인 <= A 승인 x {APPROVAL_RATIO}` 이면서 `B 시간 <= A 시간 x {WALL_RATIO}`"
    )
    lines.append(
        f"- 기각 조건: 위 미달, 또는 조건 B 에 verify 실패가 하나라도 있음, "
        f"또는 B 총비용 > A 총비용 x {COST_BLOWUP}"
    )
    lines.append("")
    lines.append("| 과업 | 승인 조건 | 시간 조건 | 이 과업의 판정 |")
    lines.append("|---|---|---|---|")

    met = 0
    incomplete = False
    for t in tasks:
        a, b = by.get((t, "A")), by.get((t, "B"))
        if not a or not b:
            lines.append(f"| task{t} | - | - | 기록 부족 |")
            incomplete = True
            continue
        ap_a, ap_b = a.get("approvals"), b.get("approvals")
        wa, wb = a.get("wall_seconds"), b.get("wall_seconds")
        if None in (ap_a, ap_b, wa, wb):
            lines.append(f"| task{t} | - | - | 기록 부족 |")
            incomplete = True
            continue
        ok_ap = ap_b <= ap_a * APPROVAL_RATIO
        ok_w = wb <= wa * WALL_RATIO
        both = ok_ap and ok_w
        met += 1 if both else 0
        ap_mark = "O" if ok_ap else "X"
        w_mark = "O" if ok_w else "X"
        lines.append(
            f"| task{t} | {ap_b:.0f} <= {ap_a * APPROVAL_RATIO:.1f} -> {ap_mark} "
            f"| {wb:.0f} <= {wa * WALL_RATIO:.1f} -> {w_mark} "
            f"| {'지지 방향' if both else '아님'} |"
        )

    b_failed = [
        r for r in records
        if r["condition"] == "B" and r.get("verified", "").lower() == "no"
    ]
    # 설계 4절의 측정 항목은 '비용/토큰' 이다. /cost 를 못 받았을 때는 토큰으로 대신 본다.
    cost_a = sum(r.get("cost_usd", 0) or 0 for r in records if r["condition"] == "A")
    cost_b = sum(r.get("cost_usd", 0) or 0 for r in records if r["condition"] == "B")
    cost_unit = "USD"
    if cost_a == 0 and cost_b == 0:
        cost_a = sum(r.get("tokens_total", 0) or 0 for r in records if r["condition"] == "A")
        cost_b = sum(r.get("tokens_total", 0) or 0 for r in records if r["condition"] == "B")
        cost_unit = "토큰"
    blowup = cost_a > 0 and cost_b > cost_a * COST_BLOWUP

    lines.append("")
    lines.append(f"- 조건을 만족한 과업 수: **{met} / {MIN_TASKS} 필요**")
    lines.append(f"- 조건 B verify 실패: **{len(b_failed)}건**")
    lines.append(
        f"- 자원 사용({cost_unit}) A={cost_a:,.0f} / B={cost_b:,.0f} "
        f"(B/A = {cost_b / cost_a:.2f}배) -> 부작용 기각 "
        f"{'해당' if blowup else '없음'}" if cost_a else "- 자원 사용: 기록 없음"
    )

    if version_drift or mode_broken:
        verdict = "무효 (고정 조건 위반)"
    elif incomplete:
        verdict = "판정 불가 (기록 부족)"
    elif b_failed or blowup:
        verdict = "기각"
    elif met >= MIN_TASKS:
        verdict = "지지"
    else:
        verdict = "기각"

    lines.append("")
    lines.append(f"## 판정: **{verdict}**")
    lines.append("")
    lines.append("실행 전에 정한 식을 그대로 대입한 결과다. 기각도 실패가 아니다.")
    lines.append("어느 과업에서 왜 줄지 않았는지가 다음 실험의 재료다.")

    out = ROOT / "results" / "results.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print()
    print(f"-> {out} 에 썼습니다.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
