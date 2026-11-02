import time


class CooldownTracker:
    def __init__(self):
        self.timestamps = {}

    def is_on_cooldown(self, guild_id: int, user_id: int, cooldown: int = 60) -> bool:
        key = (guild_id, user_id)
        now = time.time()
        last_time = self.timestamps.get(key, 0)

        if now - last_time < cooldown:
            return True

        self.timestamps[key] = now
        return False

    def reset(self, guild_id: int, user_id: int) -> None:
        self.timestamps.pop((guild_id, user_id), None)