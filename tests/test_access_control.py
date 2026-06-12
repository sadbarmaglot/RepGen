"""Тесты группового доступа в AccessControlService.

Группа проекта = role_type его владельца. Пользователь той же группы (кроме
role_type=all) получает доступ ко всем проектам/сущностям группы. ObjectMember
сохранён как дополнительный механизм.

Сессия БД мокается (как в test_web_admin.py). Чтобы тесты не зависели от
порядка lookup'а роли, role_type пользователя пред-заполняется в кэш сервиса.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock

from api.models.database.enums import RoleType
from api.services.access_control_service import AccessControlService

USER_ID = 1
PROJECT_ID = 10
OBJECT_ID = 100


def _scalar(value):
    """Результат execute() с .scalar_one_or_none()."""
    r = MagicMock()
    r.scalar_one_or_none.return_value = value
    return r


def _first(value):
    """Результат execute() с .scalars().first()."""
    r = MagicMock()
    r.scalars.return_value.first.return_value = value
    return r


def _service(is_admin=False, role=RoleType.sr, cache_role=True):
    db = AsyncMock()
    service = AccessControlService(db, is_admin=is_admin)
    if cache_role and role is not None:
        # Пропускаем lookup роли — тестируем само решение о доступе
        service._role_type_cache[USER_ID] = role
    return db, service


class TestCheckGroupAccess:

    @pytest.mark.asyncio
    async def test_same_group_grants_access(self):
        db, service = _service(role=RoleType.sr)
        db.execute.return_value = _scalar(PROJECT_ID)  # найден проект с owner.role_type=sr

        assert await service._check_group_access(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_different_group_denied(self):
        db, service = _service(role=RoleType.sr)
        db.execute.return_value = _scalar(None)  # нет проекта с совпадающей группой владельца

        assert await service._check_group_access(PROJECT_ID, USER_ID) is False

    @pytest.mark.asyncio
    async def test_all_role_never_uses_group_rule(self):
        db, service = _service(role=RoleType.all)

        assert await service._check_group_access(PROJECT_ID, USER_ID) is False
        db.execute.assert_not_called()  # для all даже не ходим в БД

    @pytest.mark.asyncio
    async def test_unknown_role_denied(self):
        db, service = _service(role=None, cache_role=False)
        db.execute.return_value = _scalar(None)  # _get_role_type вернёт None

        assert await service._check_group_access(PROJECT_ID, USER_ID) is False


class TestCanManageProject:

    @pytest.mark.asyncio
    async def test_admin_can_manage(self):
        db, service = _service(is_admin=True)

        assert await service.can_manage_project(PROJECT_ID, USER_ID) is True
        db.execute.assert_not_called()  # admin не требует запросов

    @pytest.mark.asyncio
    async def test_owner_can_manage(self):
        db, service = _service(role=RoleType.sr)
        db.execute.return_value = _scalar(MagicMock())  # is_project_owner находит проект

        assert await service.can_manage_project(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_same_group_can_manage(self):
        db, service = _service(role=RoleType.sr)
        # 1) is_project_owner → None, 2) _check_group_access → найден проект группы
        db.execute.side_effect = [_scalar(None), _scalar(PROJECT_ID)]

        assert await service.can_manage_project(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_different_group_cannot_manage(self):
        db, service = _service(role=RoleType.sr)
        db.execute.side_effect = [_scalar(None), _scalar(None)]  # не владелец, не та группа

        assert await service.can_manage_project(PROJECT_ID, USER_ID) is False

    @pytest.mark.asyncio
    async def test_all_role_cannot_manage_others(self):
        db, service = _service(role=RoleType.all)
        db.execute.side_effect = [_scalar(None)]  # не владелец; группа не проверяется для all

        assert await service.can_manage_project(PROJECT_ID, USER_ID) is False


class TestCheckProjectAccess:

    @pytest.mark.asyncio
    async def test_admin_has_access(self):
        db, service = _service(is_admin=True)

        assert await service.check_project_access(PROJECT_ID, USER_ID) is True
        db.execute.assert_not_called()

    @pytest.mark.asyncio
    async def test_owner_has_access(self):
        db, service = _service(role=RoleType.sr)
        db.execute.side_effect = [_scalar(MagicMock())]  # владелец найден

        assert await service.check_project_access(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_object_member_has_access(self):
        db, service = _service(role=RoleType.sr)
        # 1) не владелец, 2) член объекта найден
        db.execute.side_effect = [_scalar(None), _first(MagicMock())]

        assert await service.check_project_access(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_group_member_has_access(self):
        db, service = _service(role=RoleType.sr)
        # 1) не владелец, 2) не член объекта, 3) проект группы найден
        db.execute.side_effect = [_scalar(None), _first(None), _scalar(PROJECT_ID)]

        assert await service.check_project_access(PROJECT_ID, USER_ID) is True

    @pytest.mark.asyncio
    async def test_outsider_denied(self):
        db, service = _service(role=RoleType.sr)
        # не владелец, не член, не та группа
        db.execute.side_effect = [_scalar(None), _first(None), _scalar(None)]

        assert await service.check_project_access(PROJECT_ID, USER_ID) is False

    @pytest.mark.asyncio
    async def test_all_role_without_membership_denied(self):
        db, service = _service(role=RoleType.all)
        # не владелец, не член; групповое правило для all не применяется
        db.execute.side_effect = [_scalar(None), _first(None)]

        assert await service.check_project_access(PROJECT_ID, USER_ID) is False


class TestRoleTypeCache:

    @pytest.mark.asyncio
    async def test_role_looked_up_once(self):
        db = AsyncMock()
        service = AccessControlService(db)
        db.execute.return_value = _scalar(RoleType.sr)

        first = await service._get_role_type(USER_ID)
        second = await service._get_role_type(USER_ID)

        assert first == second == RoleType.sr
        db.execute.assert_called_once()  # второй вызов берётся из кэша
