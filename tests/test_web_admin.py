"""Тесты для фильтрации клиентов по visible_group в web admin."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from api.models.database.enums import RoleType, ViewMode
from api.models.entities import WebUser, WebUserProjectAccess, Project, User
from api.services.web_auth_service import WebAuthService


def _make_admin(visible_group=None):
    admin = MagicMock(spec=WebUser)
    admin.id = 100
    admin.role = "admin"
    admin.visible_group = visible_group
    return admin


def _make_client(id, visible_group=None):
    client = MagicMock(spec=WebUser)
    client.id = id
    client.role = "client"
    client.visible_group = visible_group
    client.email = f"client{id}@test.com"
    client.name = f"Client {id}"
    client.company = None
    client.view_mode = ViewMode.simplified
    client.is_active = True
    return client


class TestListClients:

    @pytest.mark.asyncio
    async def test_admin_without_group_sees_all(self):
        admin = _make_admin(visible_group=None)
        all_clients = [_make_client(1, RoleType.sr), _make_client(2, RoleType.npk)]

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = all_clients
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        result = await service.list_clients(admin)

        assert result == all_clients
        # WHERE не содержит фильтр по visible_group (только в SELECT как колонка)
        query = db.execute.call_args[0][0]
        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        where_part = compiled.split("WHERE")[1] if "WHERE" in compiled else ""
        assert "visible_group" not in where_part

    @pytest.mark.asyncio
    async def test_admin_with_group_filters_clients(self):
        admin = _make_admin(visible_group=RoleType.sr)
        sr_clients = [_make_client(1, RoleType.sr)]

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = sr_clients
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        result = await service.list_clients(admin)

        assert result == sr_clients
        call_args = db.execute.call_args
        query = call_args[0][0]
        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "visible_group" in compiled


class TestGetClientForAdmin:

    @pytest.mark.asyncio
    async def test_admin_without_group_gets_any_client(self):
        admin = _make_admin(visible_group=None)
        client = _make_client(1, RoleType.npk)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = client
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        result = await service.get_client(1, admin)
        assert result.id == 1

    @pytest.mark.asyncio
    async def test_admin_with_group_gets_own_group_client(self):
        admin = _make_admin(visible_group=RoleType.sr)
        client = _make_client(1, RoleType.sr)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = client
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        result = await service.get_client(1, admin)
        assert result.id == 1
        # Проверяем, что в запросе есть фильтр по visible_group
        query = db.execute.call_args[0][0]
        compiled = str(query.compile(compile_kwargs={"literal_binds": True}))
        assert "visible_group" in compiled

    @pytest.mark.asyncio
    async def test_admin_with_group_404_for_other_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.sr)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.get_client(2, admin)
        assert exc_info.value.status_code == 404


class TestCreateClient:

    @pytest.mark.asyncio
    async def test_inherits_admin_visible_group(self):
        admin = _make_admin(visible_group=RoleType.sr)

        db = AsyncMock()
        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_existing

        captured_user = []
        db.add = lambda obj: captured_user.append(obj)

        service = WebAuthService(db)
        with patch.object(service, "_generate_password", return_value="test-pass"), \
             patch("api.services.web_auth_service.pwd_context") as mock_pwd:
            mock_pwd.hash.return_value = "hashed"
            await service.create_client("new@test.com", admin, "New Client")

        assert len(captured_user) == 1
        created = captured_user[0]
        assert created.visible_group == RoleType.sr
        assert created.role == "client"

    @pytest.mark.asyncio
    async def test_no_group_for_unrestricted_admin(self):
        admin = _make_admin(visible_group=None)

        db = AsyncMock()
        mock_existing = MagicMock()
        mock_existing.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_existing

        captured_user = []
        db.add = lambda obj: captured_user.append(obj)

        service = WebAuthService(db)
        with patch.object(service, "_generate_password", return_value="test-pass"), \
             patch("api.services.web_auth_service.pwd_context") as mock_pwd:
            mock_pwd.hash.return_value = "hashed"
            await service.create_client("new@test.com", admin, "New Client")

        assert captured_user[0].visible_group is None


class TestUpdateDeleteResetClient:

    @pytest.mark.asyncio
    async def test_update_checks_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.sr)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # клиент из другой группы
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.update_client(2, {"name": "New"}, admin)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_checks_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.npk)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.delete_client(3, admin)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_reset_password_checks_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.sr)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.reset_password(5, admin)
        assert exc_info.value.status_code == 404


class TestAssignProject:

    @pytest.mark.asyncio
    async def test_assign_checks_client_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.sr)

        db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # клиент не найден (другая группа)
        db.execute.return_value = mock_result

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.assign_project(2, 10, admin)
        assert exc_info.value.status_code == 404
        assert "Клиент" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_assign_checks_project_group(self):
        from fastapi import HTTPException

        admin = _make_admin(visible_group=RoleType.sr)
        client = _make_client(1, RoleType.sr)

        db = AsyncMock()
        call_count = [0]

        def execute_side_effect(*args, **kwargs):
            call_count[0] += 1
            mock_result = MagicMock()
            if call_count[0] == 1:
                # _get_client_for_admin — клиент найден
                mock_result.scalar_one_or_none.return_value = client
            else:
                # project query — проект не найден (владелец из другой группы)
                mock_result.scalar_one_or_none.return_value = None
            return mock_result

        db.execute = AsyncMock(side_effect=execute_side_effect)

        service = WebAuthService(db)
        with pytest.raises(HTTPException) as exc_info:
            await service.assign_project(1, 99, admin)
        assert exc_info.value.status_code == 404
        assert "Проект" in exc_info.value.detail


class TestRoutesPassAdmin:
    """Проверяем, что роуты передают объект admin в сервис."""

    @pytest.fixture
    def client_app(self):
        from main import app
        from api.dependencies.auth_dependencies import get_current_web_admin
        from api.services.database import get_db

        admin = _make_admin(visible_group=RoleType.sr)
        mock_db = AsyncMock()

        app.dependency_overrides[get_current_web_admin] = lambda: admin
        app.dependency_overrides[get_db] = lambda: mock_db

        from fastapi.testclient import TestClient
        yield TestClient(app), admin, mock_db
        app.dependency_overrides.clear()

    def test_list_clients_passes_admin(self, client_app):
        test_client, admin, _ = client_app

        with patch(
            "api.routes.web_admin.WebAuthService"
        ) as MockService:
            mock_service = AsyncMock()
            mock_service.list_clients.return_value = []
            MockService.return_value = mock_service

            resp = test_client.get("/repgen/web/admin/clients")
            assert resp.status_code == 200

            mock_service.list_clients.assert_called_once()
            passed_admin = mock_service.list_clients.call_args[0][0]
            assert passed_admin.visible_group == RoleType.sr

    def test_create_client_passes_admin(self, client_app):
        test_client, admin, _ = client_app

        with patch(
            "api.routes.web_admin.WebAuthService"
        ) as MockService:
            mock_user = _make_client(5, RoleType.sr)
            mock_service = AsyncMock()
            mock_service.create_client.return_value = (mock_user, "pass123")
            MockService.return_value = mock_service

            resp = test_client.post(
                "/repgen/web/admin/clients",
                json={"email": "new@test.com"},
            )
            assert resp.status_code == 201

            call_args = mock_service.create_client.call_args
            assert call_args[0][0] == "new@test.com"  # email
            assert call_args[0][1].visible_group == RoleType.sr  # admin
