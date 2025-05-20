# backend/app/schemas/__init__.py
from .user_schema import UserBase, UserCreate, UserRead, UserUpdate, UserInDB

from .project_schema import (  # Add these lines
    ProjectBase,
    ProjectCreate,
    ProjectUpdate,
    ProjectRead,
    ProjectMemberBase,
    ProjectMemberCreate,
    ProjectMemberUpdate,
    ProjectMemberRead,
    ProjectWithMembersRead
)

# Add other schema imports here as you create them
# from .dataset_schema import ...
# from .analysis_run_schema import ...