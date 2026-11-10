"""Giới hạn tần suất gọi API theo địa chỉ IP (trong bộ nhớ, cửa sổ trượt 60 giây).

Đủ cho một tiến trình máy chủ; chạy nhiều tiến trình thì mỗi tiến trình đếm riêng.
Cấu hình ở config.py (RATE_LIMIT_*; 0 = tắt). Dùng:  dependencies=[Depends(limit("generate"))]
"""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

import config

WINDOW_SECONDS = 60
_hits = defaultdict(deque)
_lock = threading.Lock()


def _allowed(bucket: str, key: str, per_minute: int, now: float) -> bool:
    with _lock:
        q = _hits[(bucket, key)]
        while q and now - q[0] >= WINDOW_SECONDS:
            q.popleft()
        if len(q) >= per_minute:
            return False
        q.append(now)
        if len(_hits) > 10000:  # dọn các IP đã hết hạn để không phình bộ nhớ
            for k in [k for k, v in _hits.items() if not v or now - v[-1] >= WINDOW_SECONDS]:
                del _hits[k]
        return True


def limit(bucket: str):
    """Dependency FastAPI: quá config.RATE_LIMITS[bucket] lần/phút từ một IP -> 429."""
    def check(request: Request) -> None:
        per_minute = config.RATE_LIMITS.get(bucket, 0)
        if per_minute <= 0:
            return
        ip = request.client.host if request.client else "unknown"
        if not _allowed(bucket, ip, per_minute, time.monotonic()):
            raise HTTPException(status_code=429, headers={"Retry-After": str(WINDOW_SECONDS)},
                                detail="Bạn thao tác quá nhanh. Vui lòng thử lại sau một phút.")
    return check


def reset() -> None:
    with _lock:
        _hits.clear()
