"""
FastAPI Dependencies для аутентификации и проверки доступа к ресурсам
"""

from .auth_dependencies import (
    get_current_user,
    get_current_user_optional, 
    get_current_admin_user,
    require_admin_role
)

from .access_dependencies import (
    check_project_access,
    check_object_access,
    check_plan_access,
    check_mark_access,
    check_photo_access,
    check_project_owner,
    check_object_owner,
    check_plan_owner,
    check_mark_owner,
    check_photo_owner
)

__all__ = [
    # Auth dependencies
    "get_current_user",
    "get_current_user_optional",
    "get_current_admin_user", 
    "require_admin_role",
    # Access dependencies
    "check_project_access",
    "check_object_access", 
    "check_plan_access",
    "check_mark_access",
    "check_photo_access",
    "check_project_owner",
    "check_object_owner",
    "check_plan_owner", 
    "check_mark_owner",
    "check_photo_owner"
]
