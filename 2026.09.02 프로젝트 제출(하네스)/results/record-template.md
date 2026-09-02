# run 기록: {{RUN_ID}}

<!-- DATA -->
run_id: {{RUN_ID}}
task: {{TASK}}
condition: {{COND}}
seq: {{SEQ}}
excluded: {{EXCLUDED}}
started_at:
ended_at:
wall_seconds:
wait_seconds:
prompted_latency_sum:
cli_version:
permission_mode:
approvals:
approvals_observed:
approvals_bash:
approvals_other:
attempts:
verified:
cost_usd:
tokens_total:
<!-- /DATA -->

## 기록 방법

| 항목 | 뜻 | 어떻게 채우나 |
|---|---|---|
| `wall_seconds` | 벽시계 완료 시간(초) | 프롬프트 제출 순간 ~ `verify.py` 가 PASS 를 낸 순간 |
| `wait_seconds` | 승인 대기로 멈춰 있던 총 시간(초) | 승인창이 뜬 순간 ~ 내가 키를 누른 순간의 합 |
| `approvals` | 승인 프롬프트 총 횟수 | 아래 승인 로그 줄 수 |
| `approvals_bash` | 그중 Bash 명령 승인 | |
| `approvals_other` | 그중 나머지(편집·웹 등) | `acceptEdits` 가 제대로 걸렸다면 0 이어야 정상 |
| `attempts` | `verify.py` 를 돌린 횟수 | PASS 가 나온 실행까지 포함 |
| `verified` | `yes` / `no` | PASS 를 못 받고 끝났으면 `no` |
| `cost_usd`, `tokens_total` | 세션 비용·토큰 | 세션 종료 직전 `/cost` 출력에서 옮겨 적기 |

## 승인 프롬프트 로그

무엇을 물었는지 한 줄씩. (조건 B 에서 뜬 승인은 allowlist 가 못 잡은 명령이므로 특히 중요)

| # | 시각 | 승인 요청 내용 | 대기 시간(초) |
|---|---|---|---|
| 1 | | | |

## 관찰 메모

- 

## 이상 징후 / 규약 위반

- (예: `always allow` 를 눌렀다, 네트워크가 끊겼다, 전역 설정이 바뀌어 있었다 → 있으면 `excluded: yes`)
