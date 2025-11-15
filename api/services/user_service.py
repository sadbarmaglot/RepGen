from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import Optional

from api.models.entities import User, Project, Object, ObjectMember
from api.models.database.enums import GlobalRoleType


class UserService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _find_new_owner_for_projects(self, exclude_user_id: int) -> Optional[int]:
        """
        Находит нового владельца для проектов удаляемого пользователя
        
        Сначала ищет администратора, если нет - первого пользователя
        
        Args:
            exclude_user_id: ID пользователя, которого исключаем из поиска
            
        Returns:
            Optional[int]: ID нового владельца или None, если нет других пользователей
        """
        # Сначала пытаемся найти администратора
        admin_result = await self.db.execute(
            select(User.id)
            .where(
                User.id != exclude_user_id,
                User.global_role == GlobalRoleType.admin
            )
            .limit(1)
        )
        admin_id = admin_result.scalar_one_or_none()
        
        if admin_id:
            return admin_id
        
        # Если администраторов нет, берем первого пользователя
        user_result = await self.db.execute(
            select(User.id)
            .where(User.id != exclude_user_id)
            .order_by(User.created_at.asc())
            .limit(1)
        )
        user_id = user_result.scalar_one_or_none()
        
        return user_id

    async def delete_user(self, user_id: int) -> bool:
        """
        Удаление пользователя и всех связанных данных
        
        При удалении:
        - Проекты пользователя передаются другому пользователю (администратору или первому пользователю)
        - Если новый владелец был участником объектов в передаваемых проектах, его записи ObjectMember удаляются
          (так как владелец проекта автоматически имеет доступ ко всем объектам)
        - Записи ObjectMember удаляемого пользователя удаляются автоматически через CASCADE
        - Сам пользователь удаляется
        
        Примечание: Проекты и связанные данные (объекты, планы, отметки, фотографии) НЕ удаляются.
        
        Args:
            user_id: ID пользователя для удаления
            
        Returns:
            bool: True если удаление прошло успешно, False если пользователь не найден
        """
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        
        if not user:
            return False
        
        try:
            # Получаем все проекты пользователя
            projects_result = await self.db.execute(
                select(Project).where(Project.owner_id == user_id)
            )
            projects = projects_result.scalars().all()
            
            # Если у пользователя есть проекты, передаем их другому пользователю
            if projects:
                new_owner_id = await self._find_new_owner_for_projects(user_id)
                
                if not new_owner_id:
                    raise ValueError(
                        "Невозможно удалить пользователя: нет других пользователей для передачи проектов"
                    )
                
                project_ids = [project.id for project in projects]
                
                # Удаляем записи ObjectMember для нового владельца в объектах этих проектов
                # (так как владелец проекта автоматически имеет доступ ко всем объектам)
                objects_result = await self.db.execute(
                    select(Object.id).where(Object.project_id.in_(project_ids))
                )
                object_ids = [obj_id for obj_id in objects_result.scalars().all()]
                
                if object_ids:
                    members_to_delete_result = await self.db.execute(
                        select(ObjectMember)
                        .where(
                            ObjectMember.object_id.in_(object_ids),
                            ObjectMember.user_id == new_owner_id
                        )
                    )
                    members_to_delete = members_to_delete_result.scalars().all()
                    for member in members_to_delete:
                        await self.db.delete(member)
                
                # Передаем все проекты новому владельцу
                for project in projects:
                    project.owner_id = new_owner_id
            
            await self.db.delete(user)
            await self.db.commit()
            
            return True
        except IntegrityError as e:
            await self.db.rollback()
            raise ValueError(f"Ошибка при удалении пользователя: {str(e)}")

