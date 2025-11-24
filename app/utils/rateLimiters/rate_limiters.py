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

PROJECT_CREATE_LIMITER = RateLimiter(
    prefix="project_create",
    limit=5,
    period_seconds=60
)

PROJECT_UPDATE_LIMITER = RateLimiter(
    prefix="project_update",
    limit=5,
    period_seconds=60
)

PROJECT_READ_LIMITER = RateLimiter(
    prefix="project_read",
    limit=100,
    period_seconds=60
)

PROJECT_DELETE_LIMITER = RateLimiter(
    prefix="project_delete",
    limit=2,
    period_seconds=60
)

