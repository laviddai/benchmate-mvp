# backend/app/db/base.py

# Import the Base class itself
from app.db.base_class import Base

# Import all the models you will create.
# This ensures that SQLAlchemy's Base class knows about them when Alembic
# runs autogenerate. The '# noqa' comments prevent linters from complaining
# about unused imports, as their side effect (registering with Base) is the goal.

from app.models.user import User  # noqa
from app.models.project import Project  # noqa
from app.models.project_member import ProjectMember # noqa

# Future models will be added here:
# from app.models.dataset import Dataset # noqa
# from app.models.analysis_run import AnalysisRun # noqa
# ... import other models here as you create them ...