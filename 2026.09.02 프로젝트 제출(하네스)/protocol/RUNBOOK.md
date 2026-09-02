# 실행 절차서

한 번에 6회 실행한다. 3개 과업 x 2개 조건. 걸리는 시간은 대략 60~90분.

## 0. 사전 점검 (한 번만, 집계에서 제외)

**반드시 조건 B 로 리허설한다.** 조건 A 는 "규칙 없음"이라 설정 파일이 아예 안 읽혀도 겉보기가 똑같다.
조건 B 에서 승인창이 사라지는 것을 확인해야 **조작이 실제로 걸렸다**고 말할 수 있다.

```bash
python scripts/new_run.py --task 1 --cond B --seq 0 --rehearsal
```

출력된 명령으로 세션을 열고 프롬프트를 넣는다. 확인할 것:

1. **조건 B 에서 `python ...` 실행이 안 묻고 지나가는가** → 통과하면 P-1 확인 (규칙이 매칭됨)
   - 여전히 묻는다면 규칙 문법이 이 버전과 다르다는 뜻. `protocol/settings.B.json` 을 고치고
     근거 카드에 기록한 뒤 `runs/` 를 지우고 처음부터 다시 만든다.
2. 파일 편집은 `acceptEdits` 덕분에 **묻지 않는가** → P-2 확인
3. 그다음 조건 A 로 같은 확인을 한 번 더 해서 **승인창이 실제로 뜨는가** → P-4 확인

> **PowerShell 주의.** 이 PC 의 Windows PowerShell 5.1 은 `&&` 를 파싱하지 못한다
> (`'&&' 토큰은 이 버전에서 올바른 문 구분 기호가 아닙니다`). 폴더 이동과 세션 시작을 한 줄로 붙일 때는
> 반드시 `;` 를 쓴다. `new_run.py` 가 출력하는 한 줄이 이미 그렇게 되어 있으니 그대로 복사해 쓴다.

### 이미 확인된 것 (2026-09-02)

- **CLI 위치**: `C:\Users\cjwma\.local\bin\claude.exe` (네이티브 설치본, **PATH 에 없음**).
  `claude` 라고만 쓰면 `CommandNotFound` 가 난다. 반드시 전체 경로를 호출 연산자 `&` 와 함께 쓴다.
  `new_run.py` 가 그 한 줄을 출력한다.
- **P-3 (재확인 필요)**: 아래는 설계 에이전트 쪽에서 읽은 값이다. 바탕화면 트리는 양쪽이 공유하는 것으로
  보이지만(그 창에서 실험 폴더로 이동이 됐다), 사용자 프로필 아래 경로는 다를 수 있다.
  실험 PC 에서 한 줄로 재확인하고 결과를 여기에 적는다:

  ```powershell
  @("$env:USERPROFILE\.claude\settings.json","$env:USERPROFILE\.claude\settings.local.json","$env:USERPROFILE\OneDrive\바탕 화면\.claude\settings.local.json") | ForEach-Object { "{0}`t{1}" -f (Test-Path $_), $_ }
  ```

  재확인 결과: ____

  설계 쪽에서 읽은 값: 바탕화면에 `.claude/settings.local.json` 이 있고 allow 규칙 12개가 들어 있다.
  전부 git / ssh / clip / PowerShell 관련이고 **python 규칙은 하나도 없다.**
  핵심 조작(python 실행 승인)은 오염되지 않는다. 다만 `git status` / `git diff` 는 조건 A 에서도
  이미 허용되어 있을 수 있으므로, 조건 B allowlist 의 git 항목은 효과 계산에서 빼고 본다.
  이 파일은 두 조건에 똑같이 작용하므로 **비교 자체는 성립한다.** 6회 내내 건드리지 않는다.
- 세션은 `--settings <조건 파일 절대경로>` 로 시작한다. 폴더 위치에 따라 프로젝트 설정이
  어디서 읽히는지에 기대지 않기 위해서다. `new_run.py` 가 그 명령을 그대로 출력한다.

여기서 규칙 문법을 고쳤다면 `protocol/settings.B.json` 을 고치고, 근거 카드에 기록하고,
`runs/` 를 전부 지운 뒤 다시 만든다. 리허설 결과는 집계에 넣지 않는다.

## 1. 고정 조건 확인표

실행 전에 하나씩 눈으로 확인하고 체크한다.

- [ ] 같은 Claude Code 버전 (6회 도중 업데이트하지 않는다).
      버전은 1회차 트랜스크립트에서 `extract_run.py` 가 자동으로 뽑아 적는다.
- [ ] 같은 모델 (세션에서 확인, 기록: ____)
- [ ] **CLI 로그인이 살아 있다.** 6회 시작 전에 한 번 확인한다.
      만료되어 있으면 세션이 `Login expired · Please run /login` 만 내고 아무 도구도 부르지 않는다.
      2026-09-02 리허설에서 실제로 이 상태였다. 세션 안에서 `/login` 후 재개한다.
      **실험 도중 만료되면 그 회차는 `excluded: yes` 로 버리고 같은 조건으로 다시 돌린다.**
- [ ] 6회 모두 `--permission-mode acceptEdits` 로 시작
- [ ] 6회 모두 `protocol/prompt.txt` 의 **문장을 그대로** 붙여넣기 (한 글자도 바꾸지 않는다)
- [ ] 6회 모두 **새 세션**. 이전 세션을 이어 쓰지 않는다 (`--continue`, `--resume` 금지)
- [ ] 6회 모두 `new_run.py` 가 만든 **새 폴더**에서 시작 (픽스처 오염 방지)
- [ ] 전역 설정(`~/.claude/settings.json`)을 6회 내내 건드리지 않는다
- [ ] 같은 날, 가능한 한 연속된 시간대에 실행 (네트워크·서버 부하 차이를 줄인다)

## 2. 승인 응답 규약 (사람 쪽 변수를 고정)

- 승인창이 뜨면 **3초 안에** 반응한다. 내용을 읽고 고민하지 않는다.
- **오직 `1. Yes` 만 누른다.** 2026-09-02 실측으로 확인된 실제 선택지는 이렇게 나온다:

  ```
  Do you want to proceed?
  > 1. Yes
    2. Yes, and don't ask again for: python *
    3. Yes, and switch to auto mode · auto mode handles these prompts for you
    4. No
  ```

  - **2번 금지** — 그 세션의 allowlist 를 실행 중에 바꿔 버린다. 조건 A 가 조건 B 로 변한다.
  - **3번 금지** — 권한 모드를 `auto` 로 바꿔 버린다. 고정 조건이 깨진다.
    B 리허설이 이것 때문에 무효가 됐다. 승인창 위에 "auto mode handles these prompts for you"
    라는 안내가 붙어 나오므로 **누르기 쉽다. 특히 주의한다.**
  - **4번(No) 도 쓰지 않는다** — 단, 픽스처 밖을 건드리려 할 때만 거절하고 기록에 남긴다.
  - 2번이나 3번을 눌렀다면 그 run 은 `excluded: yes` 로 버리고 같은 조건으로 다시 돌린다.
    `extract_run.py` 가 모드 변화를 잡아 경고하지만, allowlist 변화는 잡지 못하므로 스스로 지킨다.
- 거절은 하지 않는다. 단, 픽스처 밖을 건드리려 하면 거절하고 기록에 남긴다.
- 승인창이 뜬 시각과 누른 시각을 기록지의 승인 로그 표에 적는다.

## 3. 실행 순서 (순서 효과를 흩기 위해 교차 배치)

| 순번 | 과업 | 조건 | 폴더 |
|---|---|---|---|
| 1 | task1 parse-log | A (대조) | `runs/r1_task1_A` |
| 2 | task2 refactor-util | B (처치) | `runs/r2_task2_B` |
| 3 | task3 fix-failing | A (대조) | `runs/r3_task3_A` |
| 4 | task1 parse-log | B (처치) | `runs/r4_task1_B` |
| 5 | task2 refactor-util | A (대조) | `runs/r5_task2_A` |
| 6 | task3 fix-failing | B (처치) | `runs/r6_task3_B` |

폴더는 이미 만들어져 있다. 다시 만들려면:

```bash
python scripts/new_run.py --task 1 --cond A --seq 1 --force
```

> 과업이 3개라 A 선행/B 선행을 완전히 균형 잡을 수 없다(A 선행 2, B 선행 1).
> 남은 순서 효과는 잔여 교란으로 보고서에 적고, 2회차에서 순서를 뒤집어 확인한다.

## 4. 한 회 실행 절차

1. `runs/<run_id>/work` 로 이동
2. `claude --permission-mode acceptEdits` 로 새 세션 시작
3. `protocol/prompt.txt` 문장 붙여넣고 엔터
   - 스톱워치는 **필요 없다.** 완료 시간과 호출별 지연은 트랜스크립트에서 정확히 추출된다.
4. 승인창은 규약대로 3초 내 "이번만 허용". **뜬 횟수만 손으로 센다** (정 표시로 충분)
5. 모델이 `DONE` 을 출력하면 세션 종료
6. 내가 직접 `python verify.py` 를 한 번 돌려 `PASS` 를 눈으로 확인한다
   - PASS 가 아니면 `verified: no` 로 적고 그 run 은 그대로 둔다. 대신 고쳐 주지 않는다.
7. 수치 자동 추출:

   ```bash
   python scripts/extract_run.py r1_task1_A
   ```

   완료 시간, Bash 호출 원문과 호출별 지연, 토큰, `permissionMode` 가 `record.md` 에 채워진다.
8. `record.md` 에서 **손으로만 채울 수 있는 3가지**를 적는다
   - `verified` (PASS 여부)
   - `cost_usd` (세션 종료 전 `/cost` 로 확인했다면)
   - 승인 로그 표의 **사람이 실제로 센 승인창 수** — 추출기가 유도한 `approvals` 와 맞는지 교차 확인

> **1회차는 사전 점검을 겸한다.** 조건 A 인데 승인창이 한 번도 안 뜨면 P-3(전역 설정 오염)이므로
> 즉시 멈추고 `~/.claude/settings.json` 의 `allow` 목록을 확인한다.

## 5. 집계

```bash
python scripts/tally.py
```

`results/results.md` 가 생성되고, **사전 판정식이 코드 그대로 적용된 판정**이 찍힌다.
숫자를 보고 나서 `scripts/tally.py` 의 판정 상수를 고치지 않는다. 그러면 실험이 아니게 된다.

## 6. 보고서 마무리

`experiment-01.md` 의 `실행 기록`, `결과`, `판정`, `원인 검토`, `다음 실험` 절을 채운다.
`results/results.md` 의 표를 그대로 옮기거나 링크한다.

## 중단 규칙

아래 중 하나가 생기면 그 run 은 `excluded: yes` 로 표시하고 같은 조건으로 다시 실행한다.

- `always allow` 를 눌렀다
- 네트워크 오류나 rate limit 으로 세션이 끊겼다
- 픽스처를 실수로 미리 수정했다
- 모델이 10분이 지나도 `DONE` 을 못 냈다 (이때는 `verified: no` 로 기록하고 타임아웃으로 종료)
