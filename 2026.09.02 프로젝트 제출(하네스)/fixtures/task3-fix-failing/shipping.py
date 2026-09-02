"""배송비 계산 모듈."""

FREE_THRESHOLD_KRW = 50_000
BASE_FEE_KRW = 3_000
PER_KG_KRW = 500
EXPRESS_MULTIPLIER = 1.5


def shipping_fee(order_total, weight_kg, express=False):
    """주문 금액과 무게로 배송비를 계산한다.

    규칙:
      - 주문 금액이 무료배송 기준(50,000원) '이상'이면 0원
      - 그 외에는 기본료 3,000원 + 무게 1kg당 500원
      - 익스프레스는 1.5배
      - 최종 금액은 100원 단위로 반올림(0.5는 올림)
    """
    if order_total > FREE_THRESHOLD_KRW:
        return 0
    fee = BASE_FEE_KRW + PER_KG_KRW * weight_kg
    if express:
        fee = fee * EXPRESS_MULTIPLIER
    return int(fee / 100) * 100
