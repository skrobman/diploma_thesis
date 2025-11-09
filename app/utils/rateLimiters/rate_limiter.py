from app.redis_client import redis_client
import time


class RateLimiter:

    def __init__(
        self,
        prefix: str,
        limit: int,
        period_seconds: int,
        min_interval_seconds: int | None = None
    ):
        self.prefix = prefix
        self.limit = limit
        self.period_seconds = period_seconds
        self.min_interval_seconds = min_interval_seconds

    def is_allowed(self, key: str) -> bool:
        """
        Проверяет, можно ли выполнить действие.
        Возвращает:
            True - действие разрешено
            False - лимит достигнут
        """

        redis_key = f"rate:{self.prefix}:{key}"
        time_key = f"rate_time:{self.prefix}:{key}"

        #Проверка нижнего интервала между запросами
        if self.min_interval_seconds is not None:
            last_attempt = redis_client.get(time_key)

            if last_attempt is not None:
                elapsed = time.time() - float(last_attempt)
                if elapsed < self.min_interval_seconds:
                    return False

        #Проверка общего лимита за период
        current = redis_client.get(redis_key)

        if current is None:
            # Первая попытка — создаём ключ и TTL
            redis_client.set(redis_key, 1, ex=self.period_seconds)
        else:
            current = int(current)

            if current >= self.limit:
                return False

            redis_client.incr(redis_key)

        #Сохраняем время последней попытки (если включено ограничение интервала)
        if self.min_interval_seconds is not None:
            redis_client.set(time_key, str(time.time()), ex=self.period_seconds)

        return True

    def get_remaining(self, key: str) -> int:
        """
        Возвращает количество оставшихся попыток за период.
        """
        redis_key = f"rate:{self.prefix}:{key}"
        current = redis_client.get(redis_key)

        if current is None:
            return self.limit

        return self.limit - int(current)
