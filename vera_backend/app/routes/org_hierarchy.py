"""
Organizational Hierarchy Routes
Provides graph data for visualizing company structure
"""
from typing import Dict, List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload

from app.core.api_gateway import AuthenticationMiddleware
from app.database import get_db
from app.models.sql_models import Company, Project, Team, Task, User
from app.services.websocket_service import connection_manager

router = APIRouter()


# Response Models
class NodeData(BaseModel):
    id: str
    label: str
    type: str  # company, project, team, user
    role: Optional[str] = None
    avatar: Optional[str] = None
    email: Optional[str] = None
    task_count: int = 0
    completed_tasks: int = 0
    overdue_tasks: int = 0
    team_size: Optional[int] = None
    online: bool = False


class EdgeData(BaseModel):
    id: str
    source: str
    target: str
    label: Optional[str] = None
    type: str  # manages, belongs_to, supervises, works_on


class GraphData(BaseModel):
    nodes: List[NodeData]
    edges: List[EdgeData]


class UserWorkload(BaseModel):
    user_id: str
    user_name: str
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    overdue_tasks: int
    completion_rate: float


# Endpoints
@router.get("/graph", response_model=GraphData)
async def get_organization_graph(
    company_id: Optional[str] = Query(None, description="Filter by company"),
    project_id: Optional[str] = Query(None, description="Filter by project"),
    team_id: Optional[str] = Query(None, description="Filter by team"),
    depth: int = Query(3, description="Graph depth (1-5)"),
    include_users: bool = Query(True, description="Include individual users"),
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    Get organizational hierarchy graph data

    Returns nodes and edges for visualization with React Flow or D3.js
    """
    try:
        # Get current user to determine company context
        current_user = db.query(User).filter(User.id == UUID(current_user_id)).first()

        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")

        # Use user's company if not specified
        if not company_id:
            company_id = str(current_user.company_id)

        nodes: List[NodeData] = []
        edges: List[EdgeData] = []

        # Get company
        company = (
            db.query(Company).filter(Company.id == UUID(company_id)).first()
        )

        if not company:
            raise HTTPException(status_code=404, detail="Company not found")

        # Add company node
        nodes.append(
            NodeData(
                id=str(company.id),
                label=company.name,
                type="company",
                task_count=0,
                completed_tasks=0,
                overdue_tasks=0,
            )
        )

        # Get projects
        projects_query = db.query(Project).filter(Project.company_id == company.id)

        if project_id:
            projects_query = projects_query.filter(Project.id == UUID(project_id))

        projects = projects_query.all()

        for project in projects:
            nodes.append(
                NodeData(
                    id=str(project.id),
                    label=project.name,
                    type="project",
                    task_count=len(project.tasks) if hasattr(project, 'tasks') else 0,
                    completed_tasks=0,
                    overdue_tasks=0,
                )
            )

            # Add edge from company to project
            edges.append(
                EdgeData(
                    id=f"c_{company.id}_p_{project.id}",
                    source=str(company.id),
                    target=str(project.id),
                    label="owns",
                    type="manages",
                )
            )

        # Get teams
        teams_query = db.query(Team).options(
            joinedload(Team.supervisor), joinedload(Team.users)
        ).filter(Team.company_id == company.id)

        if project_id:
            teams_query = teams_query.filter(Team.project_id == UUID(project_id))
        if team_id:
            teams_query = teams_query.filter(Team.id == UUID(team_id))

        teams = teams_query.all()

        for team in teams:
            nodes.append(
                NodeData(
                    id=str(team.id),
                    label=team.name,
                    type="team",
                    team_size=len(team.users) if team.users else 0,
                    task_count=0,
                    completed_tasks=0,
                    overdue_tasks=0,
                )
            )

            # Edge from project to team (if team belongs to project)
            if team.project_id:
                edges.append(
                    EdgeData(
                        id=f"p_{team.project_id}_t_{team.id}",
                        source=str(team.project_id),
                        target=str(team.id),
                        label="has team",
                        type="belongs_to",
                    )
                )
            else:
                # Edge from company to team
                edges.append(
                    EdgeData(
                        id=f"c_{company.id}_t_{team.id}",
                        source=str(company.id),
                        target=str(team.id),
                        label="has team",
                        type="belongs_to",
                    )
                )

            # Add users if requested
            if include_users and team.users:
                for user in team.users:
                    # Get user task statistics
                    task_stats = (
                        db.query(Task)
                        .filter(Task.assigned_to == user.id)
                        .all()
                    )

                    total_tasks = len(task_stats)
                    completed = sum(1 for t in task_stats if t.status == "complete")
                    overdue = sum(
                        1
                        for t in task_stats
                        if t.due_date
                        and t.due_date < datetime.utcnow()
                        and t.status != "complete"
                    )

                    nodes.append(
                        NodeData(
                            id=str(user.id),
                            label=user.name,
                            type="user",
                            role=user.role,
                            email=user.email,
                            task_count=total_tasks,
                            completed_tasks=completed,
                            overdue_tasks=overdue,
                            online=connection_manager.is_user_online(str(user.id)),
                        )
                    )

                    # Edge from team to user
                    edges.append(
                        EdgeData(
                            id=f"t_{team.id}_u_{user.id}",
                            source=str(team.id),
                            target=str(user.id),
                            label="member",
                            type="belongs_to",
                        )
                    )

                    # Edge from supervisor to team members
                    if team.supervisor_id and team.supervisor_id != user.id:
                        edges.append(
                            EdgeData(
                                id=f"u_{team.supervisor_id}_supervises_u_{user.id}",
                                source=str(team.supervisor_id),
                                target=str(user.id),
                                label="supervises",
                                type="supervises",
                            )
                        )

        return GraphData(nodes=nodes, edges=edges)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get organization graph: {str(e)}"
        )


@router.get("/workload/{user_id}", response_model=UserWorkload)
async def get_user_workload(
    user_id: str,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get workload statistics for a specific user"""
    try:
        user = db.query(User).filter(User.id == UUID(user_id)).first()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Get all tasks
        tasks = db.query(Task).filter(Task.assigned_to == user.id).all()

        total_tasks = len(tasks)
        pending = sum(1 for t in tasks if t.status == "pending")
        in_progress = sum(1 for t in tasks if t.status == "in-progress")
        completed = sum(1 for t in tasks if t.status == "complete")
        overdue = sum(
            1
            for t in tasks
            if t.due_date
            and t.due_date < datetime.utcnow()
            and t.status != "complete"
        )

        completion_rate = (completed / total_tasks * 100) if total_tasks > 0 else 0.0

        return UserWorkload(
            user_id=str(user.id),
            user_name=user.name,
            total_tasks=total_tasks,
            pending_tasks=pending,
            in_progress_tasks=in_progress,
            completed_tasks=completed,
            overdue_tasks=overdue,
            completion_rate=round(completion_rate, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get user workload: {str(e)}"
        )


@router.get("/team-workload/{team_id}")
async def get_team_workload(
    team_id: str,
    current_user_id: str = Depends(AuthenticationMiddleware.get_current_user_id),
    db: Session = Depends(get_db),
):
    """Get aggregated workload for entire team"""
    try:
        team = (
            db.query(Team)
            .options(joinedload(Team.users))
            .filter(Team.id == UUID(team_id))
            .first()
        )

        if not team:
            raise HTTPException(status_code=404, detail="Team not found")

        team_workloads = []

        for user in team.users:
            workload = await get_user_workload(str(user.id), current_user_id, db)
            team_workloads.append(workload)

        return {
            "team_id": str(team.id),
            "team_name": team.name,
            "member_count": len(team.users),
            "workloads": team_workloads,
            "total_tasks": sum(w.total_tasks for w in team_workloads),
            "total_overdue": sum(w.overdue_tasks for w in team_workloads),
            "average_completion_rate": (
                sum(w.completion_rate for w in team_workloads) / len(team_workloads)
                if team_workloads
                else 0.0
            ),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get team workload: {str(e)}"
        )
