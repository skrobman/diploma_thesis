from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.config.auth import security
from app.models.models import User

securityCred = HTTPBearer()

async def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(securityCred),
        db: AsyncSession = Depends(get_db)
) -> User:
    token = credentials.credentials

    try:
        #Получаем секретный ключ прямо из конфига 'security'
        SECRET_KEY = security.config.JWT_SECRET_KEY
        #Указываем алгоритм
        ALGORITHM = "HS256"
        #Декодируем токен
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type, 'access' token required"
            )

    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Получение id пользователя
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user ID")

    stmt = select(User).where(
        User.id == int(user_id)
    )
    result = await db.execute(stmt)
    user = result.scalars().first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.status != "active":
        raise HTTPException(status_code=403, detail="User account not active")

    return user