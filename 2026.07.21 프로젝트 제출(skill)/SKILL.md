---
name: project-sync
description: MANDATORY — use this skill every time file work wraps up in an existing, ongoing coding/software project (has package.json, requirements.txt, a .git repo, a prior PRD.md, or user has called it "the project"/"my repo"). Applies to any feature, bug fix, refactor, or even a single edited/created/deleted file — no explicit "commit this"/"push this" needed. IMPORTANT — don't skip this just because committing and pushing feels like something you could quickly do yourself with a couple of git commands; that instinct is exactly why this gets missed. Use the skill workflow instead of hand-rolling git, since it also keeps PRD.md in sync, which ad hoc commits miss. Run it last, right before ending your turn. It rewrites PRD.md to match the project current state, then commits and pushes changes to GitHub. Do NOT trigger for one-off files, reports, essays, or standalone documents unrelated to a software project. Also trigger when the user explicitly asks to sync with GitHub, checkpoint progress, or update the PRD.
---

# Project Sync (PRD 갱신 + Git 체크포인트)

이 스킬은 프로젝트 폴더에서 파일 작업(생성/수정/삭제)을 마칠 때마다 두 가지를 자동으로 처리합니다:
1. **PRD.md를 프로젝트의 현재 상태에 맞춰 전체적으로 다시 작성**
2. **변경된 파일들을 git으로 커밋하고 GitHub 원격 저장소에 push**

사용자가 매번 "커밋해줘", "push해줘"라고 요청하지 않아도, 파일을 하나라도 만들었거나 고쳤거나 지웠다면 이 워크플로우를 실행하세요. 큰 작업일 필요도, 여러 파일일 필요도 없습니다. 왜냐하면 이 스킬의 목적 자체가 "매번 신경 쓰지 않아도 프로젝트 상태와 저장소가 항상 최신으로 동기화되어 있게 하는 것"이기 때문입니다.

**주의**: "이 정도는 그냥 git commit/push 몇 줄이면 되니까 스킬까지 쓸 필요는 없겠다"는 생각이 든다면, 그게 바로 이 스킬을 건너뛰게 되는 가장 흔한 함정입니다. 커밋 자체는 간단해 보여도 PRD.md 갱신은 별도로 챙기지 않으면 누락되므로, git 명령어를 직접 조합하지 말고 항상 이 스킬의 워크플로우(1단계 PRD 재작성 → 2단계 git 체크포인트)를 그대로 따르세요.

## 언제 실행하지 않아도 되는지 (아래 3가지뿐)

- 아직 작업이 진행 중이고 명백히 미완성 상태일 때 (예: 파일을 만들다 만 중간 단계)
- 사용자가 명시적으로 "아직 커밋하지 마", "나중에 한번에 정리할게"라고 말했을 때
- 프로젝트 폴더가 아니라 임시 스크래치 작업(예: 계산, 일회성 파일)일 때

이 3가지 중 하나에 해당하지 않는 한, 이 턴을 끝내기 전에 예외 없이 실행하세요. "이번엔 그냥 넘어가도 되겠지"라는 판단은 하지 마세요 — 매번 무엇을 했는지 채팅에 짧게 요약해서 사용자가 항상 상황을 파악할 수 있게 하세요.

---

## 1단계 — PRD.md 재작성

PRD.md는 **변경 로그가 아니라 살아있는 문서**입니다. 새로운 내용을 아래에 추가하는 대신, 프로젝트의 현재 상태를 정확히 반영하도록 문서 전체를 다시 씁니다.

1. 프로젝트 루트에서 기존 `PRD.md`를 찾습니다. 있다면 읽어서 기존 구조/톤을 참고하고, 없다면 `references/prd_template.md`를 뼈대로 사용합니다.
2. 프로젝트 폴더의 실제 파일 구조와 이번 세션에서 방금 변경한 내용을 근거로 각 섹션을 갱신합니다. 추측하지 말고 실제로 존재하는 파일과 방금 한 작업을 근거로 쓰세요.
3. 최소한 다음 섹션은 항상 최신 상태로 유지합니다 (자세한 템플릿은 `references/prd_template.md` 참고):
   - **개요/목적**: 이 프로젝트가 무엇을 위한 것인지 한두 문단
   - **핵심 기능**: 지금 실제로 구현되어 있는 기능 목록 (계획 중인 것과 구분)
   - **아키텍처/파일 구조**: 주요 폴더/파일과 역할
   - **최근 변경사항**: 이번 세션을 포함해 최근에 무엇이 바뀌었는지 간단히 (오래된 항목은 정리하거나 요약해서 문서가 계속 길어지지 않게 하세요)
   - **남은 작업/TODO**: 아직 안 된 것, 알려진 이슈
4. `PRD.md`를 프로젝트 루트에 덮어씁니다.

## 2단계 — Git 체크포인트

`scripts/git_checkpoint.sh`를 사용해 커밋/push를 처리합니다. 스크립트가 안전장치(git 저장소인지, 변경사항이 있는지, merge 충돌 여부 등)를 이미 처리하므로 직접 매번 git 명령어를 조합하는 것보다 이 스크립트를 쓰는 게 더 안전합니다.

### 사전 확인

- **git 저장소인지 확인**: `git rev-parse --is-inside-work-tree`가 실패하면 아직 git 저장소가 아닌 것입니다. `git init`을 실행하세요 (로컬에서만 일어나는 되돌릴 수 있는 작업이라 바로 진행해도 됩니다).
- **원격 저장소(origin) 확인**: `git remote get-url origin`이 실패하면 아직 GitHub 저장소가 연결되지 않은 것입니다. 이 경우 **URL을 추측하지 말고 사용자에게 GitHub 저장소 주소를 물어보세요.** (예: "이 프로젝트를 push할 GitHub 저장소 주소가 있을까요? 없다면 먼저 GitHub에서 새 저장소를 만들어주세요.") 받은 주소로 `git remote add origin <url>`을 실행한 뒤 진행하세요.
- **인증**: Claude는 비밀번호나 토큰을 직접 입력하거나 저장하지 않습니다. push가 인증 오류로 실패하면, 사용자가 이미 설정한 git credential helper나 `gh auth login`, SSH 키에 의존해야 합니다. 인증 오류가 나면 원인이 되는 에러 메시지를 그대로 사용자에게 보여주고, 본인이 직접 `gh auth login` 등으로 인증을 완료해 달라고 안내하세요. 절대 사용자에게 토큰/비밀번호를 채팅으로 입력하라고 요청하거나 대신 입력하지 마세요.

### 실행

```bash
bash scripts/git_checkpoint.sh "<커밋 메시지>"
```

- 커밋 메시지는 이번에 실제로 한 작업을 요약해서 직접 작성하세요 (예: `feat: add user login form`, `fix: PRD 최신 파일 구조 반영`). Conventional Commits 스타일(`feat:`, `fix:`, `docs:`, `chore:` 등)을 기본으로 사용하되, 프로젝트에 이미 다른 컨벤션이 있다면 그것을 따르세요.
- 스크립트는 변경사항이 없으면 아무것도 하지 않고 조용히 종료합니다 — 빈 커밋을 만들지 않습니다.
- 원격 브랜치가 로컬보다 앞서 있어서(diverged) push가 거부되면, 스크립트가 강제로 덮어쓰지 않고 그대로 실패합니다. 이 경우 강제 push를 시도하지 말고, 상황을 사용자에게 설명하고 어떻게 처리할지 물어보세요 (예: `git pull --rebase` 먼저 실행할지).

## 3단계 — 사용자에게 결과 보고

"자동으로" 실행되는 워크플로우라 하더라도, 무엇을 했는지 항상 채팅에 짧게 요약하세요. 예:

> PRD.md를 최신 상태로 갱신했고, `feat: add CSV export button` 커밋으로 3개 파일을 origin/main에 push했습니다.

원격 저장소가 처음 연결되는 경우(새로 `git remote add`를 한 경우)나 `git init`을 새로 한 경우처럼 이전에 없던 상태 변화가 생겼을 때는 특히 명확히 언급하세요.

---

## 참고 파일

- `references/prd_template.md` — PRD.md가 아직 없을 때 사용할 기본 템플릿과 각 섹션 작성 가이드
- `scripts/git_checkpoint.sh` — add → commit → push를 안전하게 처리하는 스크립트 (저장소/원격/변경사항 여부를 먼저 확인함)
