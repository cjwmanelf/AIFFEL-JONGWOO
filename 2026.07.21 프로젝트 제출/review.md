# AIFFEL Campus Code Peer Review Templete
- 코더 : 이인석
- 리뷰어 : 최종우

> 리뷰 대상 : https://github.com/cjwmanelf/dessert-shop-backend (수제 디저트 선물샵 백엔드, FastAPI + Supabase)
> 평가 기준 : ① 보안 검토가 잘 되어 있고 실제로도 문제가 없는가 ② 실제 배포된 백엔드가 의도대로 동작하는가 ③ 서비스가 직관적이고 의도대로 잘 동작하는가
> 검증 방법 : 소스 코드 정독 + 배포 API(`https://dessert-shop-backend.onrender.com`)에 실제 요청을 보내 응답을 확인

---

# PRT(Peer Review Template)

[O] **1. 주어진 문제를 해결하는 완성된 코드가 제출되었나요?**

**요구 기능(저장 / 로그인 / 검색)이 모두 구현되었고, 배포 환경에서 실제로 정상 동작함을 직접 확인했습니다.**

- 상품 목록/검색/필터, 회원가입·로그인(JWT), 주문 생성/조회 엔드포인트가 모두 구현되어 있습니다. (`app/routers/products.py`, `app/routers/auth.py`, `app/routers/orders.py`)
- 배포된 API에 직접 요청을 보내 확인한 결과:

```
GET /health                 -> {"status":"ok"}
GET /products               -> 상품 6개 정상 반환 (레드벨벳 케이크, 초코칩 쿠키 …)
GET /products?category=쿠키          -> 초코칩 쿠키, 마카다미아 쿠키 (필터 정상)
GET /products?exclude_sold_out=true  -> 품절(당근 케이크·콜드브루 라떼) 제외 정상
GET /products?q=라떼                 -> 콜드브루 라떼 (검색 정상)
POST /auth/signup → POST /auth/login → GET /auth/me  -> 토큰 발급·본인 정보 조회 정상
POST /orders                -> 주문 생성 201, 주문 내역 영구 저장 확인
```

- "새로고침해도 데이터가 남는다"는 과제 핵심 요건도 Supabase(Postgres) 영구 저장으로 충족됩니다. 실제로 신규 계정으로 주문 생성 후 `GET /orders`에서 동일 주문이 조회됨을 확인했습니다.
- 테스트 코드(`tests/`)도 인증/상품/주문 3개 영역에 대해 잘 작성되어 있어 완성도가 높습니다.

---

[O] **2. 핵심적이거나 복잡하고 이해하기 어려운 부분에 작성된 설명을 보고 해당 코드가 잘 이해되었나요?**

**보안·인가와 직결되는 "왜 이렇게 짰는지"가 필요한 지점마다 주석/문서로 잘 설명되어 있어 이해에 무리가 없었습니다.**

- 주문 생성 시 가격을 서버에서 재계산하는 이유가 주석으로 명확합니다. (`app/routers/orders.py:36`)
  ```python
  # 가격은 클라이언트 입력을 신뢰하지 않고 DB에 저장된 현재 가격으로만 계산한다.
  line_total = product.price * item.quantity
  ```
- 남의 주문에 접근할 때 403이 아니라 404를 주는 이유(주문 ID 존재 여부 숨김)도 주석으로 설명됩니다. (`app/routers/orders.py:66-67`)
  ```python
  # 존재하지 않는 주문과 "내 것이 아닌" 주문을 동일하게 404로 응답해
  # 다른 사용자의 주문 ID 존재 여부가 드러나지 않게 한다.
  ```
- 회원가입에서 `is_admin`을 요청 바디로 받지 않고 항상 False로 고정하는 이유도 주석으로 남겨 두었습니다. (`app/routers/auth.py:21`)
- 특히 `supabase/rls.sql` 상단 주석은 "자체 JWT 인증이라 `auth.uid()` 정책을 못 쓰고, 정책을 하나도 안 만들어 기본 거부 상태를 유지하며, 소유자 접속은 RLS를 우회하므로 `FORCE ROW LEVEL SECURITY`는 걸지 않는다"까지 설계 의도를 상세히 설명하고 있어, 코드만 봐서는 놓치기 쉬운 부분을 잘 짚어 줍니다.

---

[O] **3. 에러가 난 부분을 디버깅하여 "문제를 해결한 기록"을 남겼나요? 또는 "새로운 시도 및 추가 실험"을 해봤나요?**

**`homeworkReadme.md`에 배포 과정에서 겪은 시행착오가 질문–해결 형태로 시간순 정리되어 있어, 문제 해결 기록이 매우 충실합니다.**

- Render 배포 트러블슈팅 기록이 구체적입니다. (`homeworkReadme.md`)
  - 빌드 실패 `ip: command not found` → Build Command에 `pip install -e .`가 `ip install -e`로 오타 입력된 것을 원인으로 찾아 해결
  - DB 연결 실패 `password authentication failed` → ① Direct connection(IPv6 전용) 문자열 문제 → Session pooler(IPv4)로 교체 ② 비밀번호 특수문자가 URL 파싱을 깨뜨린 것 → 특수문자 없는 비밀번호로 재설정
  - `render.yaml`이 자동 인식 안 됨 → "New Web Service"(수동)와 "Blueprint" 흐름의 차이를 배움
- Vercel의 `NEXT_PUBLIC_API_BASE_URL`이 "Sensitive"로 지정되어 빌드 시점에 값이 안 박힌 원인까지 추적한 기록도 인상적입니다.
- 무료 티어(Render Shell 미지원) 제약을 우회해 로컬에서 운영 DB에 시드 스크립트를 실행한 것은 좋은 "추가 시도"입니다.
- 공통적으로 효과 있었던 질문 방식(에러 로그 전체 복붙, 화면 캡처 공유)까지 회고한 점이 좋습니다.

---

[O] **4. 회고를 잘 작성했나요?**

**보안 자체 평가와 시행착오 회고는 훌륭하나, "배운 점 / 아쉬운 점 / 느낀 점" 형태의 개인 회고는 상대적으로 얇습니다.**

- 잘된 점 : `homeworkReadme.md`의 "보안 체크리스트 자체 평가" 5개 항목은 근거(직접 확인함, `relrowsecurity`로 확인 등)를 들어 스스로를 검증한 좋은 회고입니다. "공통적으로 효과 있었던 질문 방식"도 학습 회고로 볼 수 있습니다.
- 아쉬운 점 : 프로젝트 전반에 대한 배운 점/아쉬운 점/느낀 점을 명시적으로 정리한 섹션이 없습니다. 예를 들어 "다음에 다시 한다면 RLS 정책을 처음부터 설계했을 것", "JWT 만료/갱신을 더 고민했을 것" 같은 개인 소회가 있으면 더 좋겠습니다.
- 백엔드 서비스라 딥러닝 아키텍처 도식은 해당 없으나, 대신 **요청 흐름도**(클라이언트 → CORS → 라우터 → 인증 의존성 → DB → 서버 가격 재계산 → 응답)를 한 장 그려 두면 리뷰어가 전체 흐름을 더 빨리 파악할 수 있을 것 같습니다.
- (판정: 자체 평가·트러블슈팅 회고는 충분하지만 표준적인 개인 회고 섹션이 없어 △로 표시)

---

[O] **5. 코드가 간결하고 효율적인가요?**

**계층 분리와 모듈화가 잘 되어 있고 PEP8/타입 힌트를 잘 지켜, 읽기 쉽고 중복이 적습니다.**

- `routers / models / schemas / deps / security / config / database`로 책임이 명확히 분리되어 있습니다.
- 인증·인가를 FastAPI 의존성(`get_current_user`, `require_admin`)으로 모듈화해 각 라우터에서 재사용합니다. (`app/deps.py`) — 상품 등록/수정/삭제 3개 엔드포인트가 `_admin=Depends(require_admin)` 한 줄로 동일하게 보호됩니다.
- 비밀값을 `pydantic-settings`로 환경변수에서만 로드하고, `cors_origin_list` 프로퍼티로 파싱 로직을 캡슐화했습니다. (`app/config.py`)
- Pydantic 스키마로 입력 검증을 선언적으로 처리(수량 `Field(ge=1, le=99)`, 가격 `Field(gt=0)`, 비밀번호 `min_length=8`)해 라우터가 깔끔합니다.
- 타입 힌트(`Mapped[...]`, `str | None`)와 명명이 일관되어 PEP8을 잘 준수합니다.
- (소소한 개선 여지) `create_order`가 장바구니 항목마다 `db.get(Product, ...)`를 호출해 N+1 조회가 발생합니다. 아래 개선안 참고.

---

# 총평 (평가 기준별 결론)

- **① 보안 — 문서화도 충실하고, 실제로도 안전함을 배포 API에서 검증 완료.**
  - 가격 조작 방어: `price:1`을 실어 보내도 서버가 무시하고 DB 가격으로 재계산 → `total_price=13500 (=4500×3)`, `unit_price=4500` 확인
  - 품절 상품 주문 거부: 400 + "품절된 상품입니다: 당근 케이크"
  - 수량 검증: `quantity:0` → 422
  - 인가: 일반 사용자 상품 등록 → 403 / 토큰 없이 `/orders` → 401
  - IDOR 방어: 다른 사용자의 주문 조회 → 404 (본인 것은 200), 목록은 본인 것만 반환
  - `is_admin` self-assign 차단(스키마에 필드 없음 + 라우터에서 False 고정), 비밀번호 bcrypt 해싱, 코드/깃 히스토리에 하드코딩된 비밀값 없음(`.env.example`엔 플레이스홀더만), CORS는 환경변수 화이트리스트로 제한
  - RLS: 자체 JWT 구조에 맞춰 "정책 없이 기본 거부"로 PostgREST 우회 접근 차단 — 설계 근거가 타당함
- **② 백엔드 동작 — 배포된 모든 엔드포인트가 의도대로 동작함을 실제 요청으로 확인.** (위 1번·총평 근거 참조)
- **③ 직관성 — `/docs`(Swagger)로 즉시 테스트 가능하고, REST 관례에 맞는 경로·상태코드·한글 에러 메시지로 사용성이 좋음.**

전반적으로 과제 요구사항과 보안 체크리스트를 모두 충족한 완성도 높은 제출물입니다. 회고 섹션 보강만 하면 더할 나위 없겠습니다.

---

# 참고 링크 및 코드 개선

```
# 참고 링크
- FastAPI Security(OAuth2/JWT) 공식 문서: https://fastapi.tiangolo.com/tutorial/security/
  → 이 프로젝트의 OAuth2PasswordBearer + JWT 의존성 구조가 공식 권장 패턴과 일치함을 확인하는 데 참고.
- Supabase Row Level Security: https://supabase.com/docs/guides/database/postgres/row-level-security
  → "정책이 없으면 기본 거부"라는 rls.sql의 전제가 문서와 일치함을 확인.

# 코드 개선 제안 1) create_order의 N+1 조회 → 한 번에 배치 조회
# (현재: 장바구니 항목 수만큼 DB 왕복. 항목이 많아지면 비효율.)
# app/routers/orders.py
from sqlalchemy import select

product_ids = [item.product_id for item in payload.items]
products = {
    p.id: p
    for p in db.execute(select(Product).where(Product.id.in_(product_ids))).scalars()
}
total_price = 0
order_items = []
for item in payload.items:
    product = products.get(item.product_id)
    if product is None:
        raise HTTPException(status_code=400, detail=f"존재하지 않는 상품입니다 (product_id={item.product_id})")
    if product.sold_out:
        raise HTTPException(status_code=400, detail=f"품절된 상품입니다: {product.name}")
    total_price += product.price * item.quantity
    order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, unit_price=product.price))
# → DB 왕복 1회로 동일 로직 수행. 같은 상품을 중복으로 담아도 조회는 1번.

# 코드 개선 제안 2) (선택) 회고/요청 흐름도를 homeworkReadme.md에 추가
# 배운점/아쉬운점/느낀점 + "요청 → CORS → 라우터 → 인증 의존성 → DB → 가격 재계산 → 응답"
# 흐름도 한 장이면 PRT 4번 항목을 완전히 채울 수 있음.
```
