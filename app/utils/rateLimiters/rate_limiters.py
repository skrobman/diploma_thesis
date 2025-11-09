from app.utils.rateLimiters.rate_limiter import RateLimiter

LOGIN_LIMITER = RateLimiter(
    prefix="login_failed",
    limit=3,
    period_seconds=3600
)

FORGOT_PASSWORD_LIMITER = RateLimiter(
    prefix="forgot_password",
    limit=3,
    period_seconds=3600,
    min_interval_seconds=60
)