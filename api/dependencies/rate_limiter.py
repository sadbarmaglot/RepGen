from fastapi import HTTPException, Request, status
from api.services.redis_service import redis_service

# IP: max 10 attempts per minute
IP_MAX_ATTEMPTS = 10
IP_WINDOW_SECONDS = 60

# Email: max 5 failed attempts, then block for 15 minutes
EMAIL_MAX_ATTEMPTS = 5
EMAIL_BLOCK_SECONDS = 900


async def check_login_rate_limit(request: Request, email: str):
    """Check rate limits by IP and email before login attempt."""
    ip = request.client.host if request.client else "unknown"

    # Check IP rate limit
    ip_key = f"rate:login:ip:{ip}"
    ip_count = await redis_service.redis_client.incr(ip_key)
    if ip_count == 1:
        await redis_service.redis_client.expire(ip_key, IP_WINDOW_SECONDS)
    if ip_count > IP_MAX_ATTEMPTS:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Слишком много попыток входа. Попробуйте через минуту.",
        )

    # Check email block
    email_lower = email.lower().strip()
    block_key = f"rate:login:block:{email_lower}"
    if await redis_service.redis_client.exists(block_key):
        ttl = await redis_service.redis_client.ttl(block_key)
        minutes = max(1, ttl // 60)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Аккаунт временно заблокирован. Попробуйте через {minutes} мин.",
        )


async def record_failed_login(email: str):
    """Record a failed login attempt for the email."""
    email_lower = email.lower().strip()
    fail_key = f"rate:login:fail:{email_lower}"
    count = await redis_service.redis_client.incr(fail_key)
    if count == 1:
        await redis_service.redis_client.expire(fail_key, EMAIL_BLOCK_SECONDS)

    if count >= EMAIL_MAX_ATTEMPTS:
        block_key = f"rate:login:block:{email_lower}"
        await redis_service.redis_client.setex(block_key, EMAIL_BLOCK_SECONDS, "1")
        await redis_service.redis_client.delete(fail_key)


async def clear_failed_login(email: str):
    """Clear failed login counter on successful login."""
    email_lower = email.lower().strip()
    fail_key = f"rate:login:fail:{email_lower}"
    await redis_service.redis_client.delete(fail_key)
