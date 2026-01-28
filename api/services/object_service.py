from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional
from api.models.entities import Object
from api.models.entities import Project
from api.models.requests import ObjectCreateRequest, ObjectUpdateRequest
from api.models.responses import ObjectResponse, ObjectListResponse
from api.services.access_control_service import AccessControlService
from api.models.database.enums import ObjectStatus

class ObjectService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.access_control = AccessControlService(db)

    async def create_object(self, user_id: int, object_data: ObjectCreateRequest) -> ObjectResponse:
        """Создание нового объекта"""
        
        # Проверяем, что проект существует и принадлежит пользователю
        result = await self.db.execute(
            select(Project).where(
                Project.id == object_data.project_id,
                Project.owner_id == user_id
            )
        )
        project = result.scalar_one_or_none()
        
        if not project:
            raise ValueError("Проект не найден или у вас нет прав доступа к нему")
        
        object_ = Object(
            project_id=object_data.project_id,
            name=object_data.name,
            address=object_data.address,
            description=object_data.description,
            status=object_data.status if object_data.status else ObjectStatus.not_started
        )
        
        try:
            self.db.add(object_)
            await self.db.commit()
            await self.db.refresh(object_)
            return ObjectResponse.model_validate(object_)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при создании объекта: {str(e)}")

    async def get_object(self, object_id: int, user_id: int) -> Optional[ObjectResponse]:
        """Получение объекта по ID (для владельца проекта или участника объекта)"""
        # Проверяем доступ к объекту
        if not await self.access_control.check_object_access(object_id, user_id):
            return None
        
        result = await self.db.execute(
            select(Object).where(Object.id == object_id)
        )
        object_ = result.scalar_one_or_none()
        
        if not object_:
            return None
        
        return ObjectResponse.model_validate(object_)

    async def get_project_objects(self, project_id: int, user_id: int, skip: int = 0, limit: int = 100) -> ObjectListResponse:
        """Получение списка объектов проекта (доступных пользователю)"""
        
        # Проверяем доступ к проекту
        if not await self.access_control.check_project_access(project_id, user_id):
            raise ValueError("Проект не найден или у вас нет прав доступа к нему")
        
        # Получаем все объекты проекта
        all_objects_result = await self.db.execute(
            select(Object).where(Object.project_id == project_id)
        )
        all_objects = all_objects_result.scalars().all()
        
        # Фильтруем объекты по доступу пользователя
        accessible_objects = []
        for obj in all_objects:
            if await self.access_control.check_object_access(obj.id, user_id):
                accessible_objects.append(obj)
        
        total = len(accessible_objects)
        
        # Применяем пагинацию
        paginated_objects = accessible_objects[skip:skip + limit]
        
        object_responses = [ObjectResponse.model_validate(obj) for obj in paginated_objects]
        
        return ObjectListResponse(
            objects=object_responses,
            total=total
        )

    async def update_object(self, object_id: int, user_id: int, object_data: ObjectUpdateRequest) -> Optional[ObjectResponse]:
        """Обновление объекта (только владельцем проекта)"""
        # Получаем объект и проверяем что пользователь владелец проекта
        result = await self.db.execute(
            select(Object)
            .join(Project)
            .where(
                Object.id == object_id,
                Project.owner_id == user_id
            )
        )
        object_ = result.scalar_one_or_none()
        
        if not object_:
            return None
        
        if object_data.name is not None:
            object_.name = object_data.name
        if object_data.address is not None:
            object_.address = object_data.address
        if object_data.description is not None:
            object_.description = object_data.description
        if object_data.status is not None:
            object_.status = object_data.status
        
        try:
            await self.db.commit()
            await self.db.refresh(object_)
            return ObjectResponse.model_validate(object_)
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при обновлении объекта: {str(e)}")

    async def delete_object(self, object_id: int, user_id: int) -> bool:
        """Удаление объекта (только владельцем проекта)"""
        # Получаем объект и проверяем что пользователь владелец проекта
        result = await self.db.execute(
            select(Object)
            .join(Project)
            .where(
                Object.id == object_id,
                Project.owner_id == user_id
            )
        )
        object_ = result.scalar_one_or_none()
        
        if not object_:
            return False
        
        try:
            await self.db.delete(object_)
            await self.db.commit()
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении объекта: {str(e)}")
