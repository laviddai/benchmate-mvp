# backend/app/crud/__init__.py
from .crud_user import (
    get_user,
    get_user_by_email,
    get_user_by_orcid_id,
    get_users,
    create_user,
    update_user,
    remove_user
)

from .crud_project import ( # Add these lines
    get_project,
    get_projects_by_owner,
    get_projects_for_user,
    create_project,
    update_project,
    remove_project,
    get_project_member,
    get_project_members,
    add_project_member,
    update_project_member_role,
    remove_project_member
)

from .crud_dataset import (
    get_dataset,
    get_datasets_by_project,
    create_dataset,
    update_dataset,
    remove_dataset
)

from .crud_analysis_run import (
    get_analysis_run,
    get_analysis_runs_by_project,
    get_analysis_runs_by_user,
    create_analysis_run,
    update_analysis_run_status,
    update_analysis_run_outputs,
    update_analysis_run_internal,
    remove_analysis_run
)
# Add other CRUD module imports here as you create them