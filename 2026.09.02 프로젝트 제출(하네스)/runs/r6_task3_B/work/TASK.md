# task3 — fix-failing

`test_me.py` 의 실패 2건이 통과하도록 `shipping.py` 를 고친다.

## 요구 사항

1. **`test_me.py` 는 수정하지 않는다.** (채점기가 해시로 확인한다)
2. `shipping.py` 만 고쳐 테스트 5건이 모두 통과하게 한다.
3. 지금 통과하는 3건이 깨지면 안 된다.
4. 표준 라이브러리만 쓴다. 이 환경에는 pytest 가 없으므로 `python -m unittest` 를 쓴다.

## 완료 판정

```
python verify.py
```

가 `PASS` 를 출력하면 완료. `verify.py` 는 채점기이며 읽어 봐도 된다. **수정하면 안 된다.**
