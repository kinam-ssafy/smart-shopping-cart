# uid_tracker.py
import time
from dataclasses import dataclass, field

def parse_msg(s: str):
    try:
        parts = s.strip().split(",")
        if len(parts) != 3 or not parts[0].startswith("R"):
            return None
        reader = int(parts[0][1:])
        uid_len = int(parts[1])
        hex_uid = parts[2].upper()
        uid = ":".join(hex_uid[i:i+2] for i in range(0, len(hex_uid), 2))
        return reader, uid_len, uid
    except:
        return None

@dataclass
class UIDInfo:
    last_seen: float
    uid_len: int
    readers: set[int] = field(default_factory=set)

class UIDTracker:
    def __init__(self, ttl_sec: float):
        self.ttl_sec = ttl_sec
        self.active: dict[str, UIDInfo] = {}

    def format_active(self):
        return "∅" if not self.active else ", ".join(sorted(self.active.keys()))

    def touch(self, reader: int, uid_len: int, uid: str) -> bool:
        """새 UID 추가되면 True"""
        now = time.monotonic()
        if uid not in self.active:
            self.active[uid] = UIDInfo(last_seen=now, uid_len=uid_len, readers={reader})
            return True
        info = self.active[uid]
        info.last_seen = now
        info.readers.add(reader)
        return False

    def expire(self) -> list[str]:
        """만료된 uid 리스트 반환"""
        now = time.monotonic()
        removed = []
        for uid, info in list(self.active.items()):
            if now - info.last_seen > self.ttl_sec:
                self.active.pop(uid, None)
                removed.append(uid)
        return removed
