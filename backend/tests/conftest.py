import uuid
from datetime import datetime, timezone

import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from app.main import app
from app.database import get_db, Base
from app.auth import get_current_user, get_optional_user
from app.db_models import User

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def test_db():
    engine = create_async_engine(TEST_DB_URL, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with session_factory() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def test_user(test_db):
    result = await test_db.execute(select(User).where(User.email == "test@test.com"))
    user = result.scalar_one_or_none()
    if not user:
        user = User(
            id=uuid.uuid4(),
            email="test@test.com",
            hashed_password="does-not-matter-for-override",
            display_name="Test User",
            created_at=datetime.now(timezone.utc),
        )
        test_db.add(user)
        await test_db.commit()
        await test_db.refresh(user)
    return user


@pytest_asyncio.fixture
async def client(test_db, test_user):
    async def override_get_db():
        yield test_db

    async def override_get_current_user():
        return test_user

    async def override_get_optional_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
