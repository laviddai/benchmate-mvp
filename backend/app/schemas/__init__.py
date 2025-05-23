# backend/app/schemas/__init__.py
from .user_schema import UserBase, UserCreate, UserRead, UserUpdate, UserInDB

from .project_schema import (
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

from .dataset_schema import (
    DatasetBase,
    DatasetCreate,
    DatasetUpdate,
    DatasetRead,
    DatasetReadMinimal
)

from .analysis_run_schema import (
    AnalysisRunBase,
    AnalysisRunCreate,
    AnalysisRunUpdateInternal,
    AnalysisRunUserUpdate,
    AnalysisRunRead
)
from app.models.analysis_run import AnalysisStatus # to expose Enum easily

# Add other schema imports here as you create them