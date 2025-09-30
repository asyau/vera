"""
Supabase Row Level Security Integration for Vira
Implements advanced RLS policies and helper functions for secure data access
"""
import uuid
from typing import Any, Dict, Optional

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sql_models import Company, Message, Task, User


class SupabaseRLSManager:
    """Manages Supabase Row Level Security policies and enforcement"""

    def __init__(self, db: Session):
        self.db = db

    def create_vira_rls_policies(self) -> Dict[str, str]:
        """Create comprehensive RLS policies for Vira tables"""

        policies = {}

        # Users table RLS
        policies[
            "users_rls"
        ] = """
        -- Enable RLS for users table
        ALTER TABLE users ENABLE ROW LEVEL SECURITY;

        -- Users can view their own profile
        CREATE POLICY "users_select_own" ON users
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = id);

        -- Users can update their own profile
        CREATE POLICY "users_update_own" ON users
        FOR UPDATE TO authenticated
        USING ((SELECT auth.uid()) = id)
        WITH CHECK ((SELECT auth.uid()) = id);

        -- CEOs and managers can view all users in their company
        CREATE POLICY "users_select_company_managers" ON users
        FOR SELECT TO authenticated
        USING (
            company_id IN (
                SELECT company_id FROM users
                WHERE (SELECT auth.uid()) = id
                AND role IN ('CEO', 'CTO', 'PM')
            )
        );

        -- Supervisors can view their team members
        CREATE POLICY "users_select_team_supervisor" ON users
        FOR SELECT TO authenticated
        USING (
            team_id IN (
                SELECT team_id FROM users
                WHERE (SELECT auth.uid()) = id
                AND role = 'Supervisor'
            )
        );
        """

        # Tasks table RLS
        policies[
            "tasks_rls"
        ] = """
        -- Enable RLS for tasks table
        ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

        -- Users can view tasks assigned to them
        CREATE POLICY "tasks_select_assigned" ON tasks
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = assigned_to);

        -- Users can view tasks they created
        CREATE POLICY "tasks_select_created" ON tasks
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = created_by);

        -- Users can update tasks assigned to them
        CREATE POLICY "tasks_update_assigned" ON tasks
        FOR UPDATE TO authenticated
        USING ((SELECT auth.uid()) = assigned_to);

        -- Managers can view all tasks in their company
        CREATE POLICY "tasks_select_company_managers" ON tasks
        FOR SELECT TO authenticated
        USING (
            project_id IN (
                SELECT p.id FROM projects p
                JOIN users u ON u.company_id = p.company_id
                WHERE (SELECT auth.uid()) = u.id
                AND u.role IN ('CEO', 'CTO', 'PM')
            )
        );

        -- Supervisors can view tasks for their team
        CREATE POLICY "tasks_select_team_supervisor" ON tasks
        FOR SELECT TO authenticated
        USING (
            assigned_to IN (
                SELECT id FROM users
                WHERE team_id IN (
                    SELECT team_id FROM users
                    WHERE (SELECT auth.uid()) = id
                    AND role = 'Supervisor'
                )
            )
        );

        -- Task creation with proper assignment validation
        CREATE POLICY "tasks_insert_authorized" ON tasks
        FOR INSERT TO authenticated
        WITH CHECK (
            -- Can create tasks if you're a manager or supervisor
            (SELECT auth.uid()) IN (
                SELECT id FROM users
                WHERE role IN ('CEO', 'CTO', 'PM', 'Supervisor')
            )
            AND
            -- Assigned user must be in same company
            assigned_to IN (
                SELECT u2.id FROM users u1
                JOIN users u2 ON u1.company_id = u2.company_id
                WHERE (SELECT auth.uid()) = u1.id
            )
        );
        """

        # Messages table RLS (for chat functionality)
        policies[
            "messages_rls"
        ] = """
        -- Enable RLS for messages table
        ALTER TABLE messages ENABLE ROW LEVEL SECURITY;

        -- Users can view messages in conversations they participate in
        CREATE POLICY "messages_select_participant" ON messages
        FOR SELECT TO authenticated
        USING (
            conversation_id IN (
                SELECT id FROM conversations
                WHERE (SELECT auth.uid()) = ANY(participant_ids)
            )
        );

        -- Users can send messages to conversations they participate in
        CREATE POLICY "messages_insert_participant" ON messages
        FOR INSERT TO authenticated
        WITH CHECK (
            (SELECT auth.uid()) = sender_id
            AND
            conversation_id IN (
                SELECT id FROM conversations
                WHERE (SELECT auth.uid()) = ANY(participant_ids)
            )
        );

        -- Hierarchy-based message access (managers can view team communications)
        CREATE POLICY "messages_select_hierarchy" ON messages
        FOR SELECT TO authenticated
        USING (
            -- CEOs can view all company messages
            (SELECT role FROM users WHERE (SELECT auth.uid()) = id) = 'CEO'
            OR
            -- Supervisors can view team messages
            (
                (SELECT role FROM users WHERE (SELECT auth.uid()) = id) = 'Supervisor'
                AND
                conversation_id IN (
                    SELECT c.id FROM conversations c
                    JOIN users u ON u.id = ANY(c.participant_ids)
                    WHERE u.team_id IN (
                        SELECT team_id FROM users
                        WHERE (SELECT auth.uid()) = id
                    )
                )
            )
        );
        """

        # Documents table RLS
        policies[
            "documents_rls"
        ] = """
        -- Enable RLS for documents table
        ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

        -- Users can view documents they uploaded
        CREATE POLICY "documents_select_uploaded" ON documents
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = uploaded_by);

        -- Users can view documents in their projects
        CREATE POLICY "documents_select_project" ON documents
        FOR SELECT TO authenticated
        USING (
            project_id IN (
                SELECT p.id FROM projects p
                JOIN users u ON u.project_id = p.id OR u.company_id = p.company_id
                WHERE (SELECT auth.uid()) = u.id
            )
        );

        -- Team members can view team documents
        CREATE POLICY "documents_select_team" ON documents
        FOR SELECT TO authenticated
        USING (
            team_id IN (
                SELECT team_id FROM users
                WHERE (SELECT auth.uid()) = id
            )
        );

        -- Document upload permissions
        CREATE POLICY "documents_insert_authorized" ON documents
        FOR INSERT TO authenticated
        WITH CHECK (
            (SELECT auth.uid()) = uploaded_by
            AND
            -- Must be uploading to own company's project/team
            (
                project_id IN (
                    SELECT p.id FROM projects p
                    JOIN users u ON u.company_id = p.company_id
                    WHERE (SELECT auth.uid()) = u.id
                )
                OR
                team_id IN (
                    SELECT team_id FROM users
                    WHERE (SELECT auth.uid()) = id
                )
            )
        );
        """

        # Memory vectors RLS (for AI memory)
        policies[
            "memory_vectors_rls"
        ] = """
        -- Enable RLS for memory_vectors table
        ALTER TABLE memory_vectors ENABLE ROW LEVEL SECURITY;

        -- Users can view their own memory vectors
        CREATE POLICY "memory_select_user" ON memory_vectors
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = user_id);

        -- Users can view company-wide memory vectors
        CREATE POLICY "memory_select_company" ON memory_vectors
        FOR SELECT TO authenticated
        USING (
            company_id IN (
                SELECT company_id FROM users
                WHERE (SELECT auth.uid()) = id
            )
        );

        -- Memory creation permissions
        CREATE POLICY "memory_insert_authorized" ON memory_vectors
        FOR INSERT TO authenticated
        WITH CHECK (
            (SELECT auth.uid()) = user_id
            OR
            (
                user_id IS NULL
                AND
                company_id IN (
                    SELECT company_id FROM users
                    WHERE (SELECT auth.uid()) = id
                )
            )
        );
        """

        # Notifications RLS
        policies[
            "notifications_rls"
        ] = """
        -- Enable RLS for notifications table
        ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

        -- Users can only view their own notifications
        CREATE POLICY "notifications_select_own" ON notifications
        FOR SELECT TO authenticated
        USING ((SELECT auth.uid()) = user_id);

        -- Users can update their own notifications (mark as read)
        CREATE POLICY "notifications_update_own" ON notifications
        FOR UPDATE TO authenticated
        USING ((SELECT auth.uid()) = user_id)
        WITH CHECK ((SELECT auth.uid()) = user_id);

        -- System can create notifications for users
        CREATE POLICY "notifications_insert_system" ON notifications
        FOR INSERT TO authenticated
        WITH CHECK (
            user_id IN (
                SELECT id FROM users
                WHERE company_id IN (
                    SELECT company_id FROM users
                    WHERE (SELECT auth.uid()) = id
                )
            )
        );
        """

        return policies

    def create_rls_helper_functions(self) -> Dict[str, str]:
        """Create helper functions for RLS policies"""

        functions = {}

        # Helper function to check if user can access another user
        functions[
            "can_access_user"
        ] = """
        CREATE OR REPLACE FUNCTION private.can_access_user(target_user_id UUID)
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            current_user_role TEXT;
            current_company_id UUID;
            current_team_id UUID;
            target_user_role TEXT;
            target_company_id UUID;
            target_team_id UUID;
        BEGIN
            -- Get current user info
            SELECT role, company_id, team_id INTO current_user_role, current_company_id, current_team_id
            FROM users WHERE id = (SELECT auth.uid());

            -- Get target user info
            SELECT role, company_id, team_id INTO target_user_role, target_company_id, target_team_id
            FROM users WHERE id = target_user_id;

            -- Self access
            IF (SELECT auth.uid()) = target_user_id THEN
                RETURN TRUE;
            END IF;

            -- CEO can access all company users
            IF current_user_role = 'CEO' AND current_company_id = target_company_id THEN
                RETURN TRUE;
            END IF;

            -- CTO/PM can access company users
            IF current_user_role IN ('CTO', 'PM') AND current_company_id = target_company_id THEN
                RETURN TRUE;
            END IF;

            -- Supervisor can access team members
            IF current_user_role = 'Supervisor' AND current_team_id = target_team_id THEN
                RETURN TRUE;
            END IF;

            RETURN FALSE;
        END;
        $$;
        """

        # Helper function to check task access permissions
        functions[
            "can_access_task"
        ] = """
        CREATE OR REPLACE FUNCTION private.can_access_task(task_id UUID)
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        DECLARE
            current_user_id UUID := (SELECT auth.uid());
            task_assigned_to UUID;
            task_created_by UUID;
            task_project_id UUID;
        BEGIN
            -- Get task info
            SELECT assigned_to, created_by, project_id
            INTO task_assigned_to, task_created_by, task_project_id
            FROM tasks WHERE id = task_id;

            -- Task assignee can access
            IF current_user_id = task_assigned_to THEN
                RETURN TRUE;
            END IF;

            -- Task creator can access
            IF current_user_id = task_created_by THEN
                RETURN TRUE;
            END IF;

            -- Check if user can access via hierarchy
            IF private.can_access_user(task_assigned_to) THEN
                RETURN TRUE;
            END IF;

            RETURN FALSE;
        END;
        $$;
        """

        # Helper function for MFA enforcement
        functions[
            "requires_mfa"
        ] = """
        CREATE OR REPLACE FUNCTION private.requires_mfa()
        RETURNS BOOLEAN
        LANGUAGE plpgsql
        SECURITY DEFINER
        AS $$
        BEGIN
            -- Check if current user's JWT has MFA (aal2)
            RETURN (SELECT auth.jwt()->>'aal') = 'aal2';
        END;
        $$;
        """

        return functions

    def create_mfa_policies(self) -> Dict[str, str]:
        """Create MFA-enforced policies for sensitive operations"""

        policies = {}

        # MFA required for sensitive task operations
        policies[
            "tasks_mfa_sensitive"
        ] = """
        CREATE POLICY "tasks_sensitive_operations_mfa" ON tasks
        AS RESTRICTIVE
        FOR ALL TO authenticated
        USING (
            -- High priority tasks require MFA
            (priority != 'urgent' OR private.requires_mfa())
            AND
            -- Tasks with sensitive keywords require MFA
            (
                NOT (description ILIKE '%confidential%' OR description ILIKE '%sensitive%')
                OR private.requires_mfa()
            )
        );
        """

        # MFA required for company-wide document access
        policies[
            "documents_mfa_company"
        ] = """
        CREATE POLICY "documents_company_access_mfa" ON documents
        AS RESTRICTIVE
        FOR SELECT TO authenticated
        USING (
            -- Company-wide documents require MFA for non-owners
            (
                uploaded_by = (SELECT auth.uid())
                OR private.requires_mfa()
            )
        );
        """

        return policies

    def apply_all_policies(self) -> Dict[str, Any]:
        """Apply all RLS policies to the database"""

        results = {"success": True, "applied_policies": [], "errors": []}

        try:
            # Create private schema for helper functions
            self.db.execute(text("CREATE SCHEMA IF NOT EXISTS private;"))

            # Apply helper functions
            functions = self.create_rls_helper_functions()
            for func_name, func_sql in functions.items():
                try:
                    self.db.execute(text(func_sql))
                    results["applied_policies"].append(f"function_{func_name}")
                except Exception as e:
                    results["errors"].append(f"Function {func_name}: {str(e)}")

            # Apply RLS policies
            policies = self.create_vira_rls_policies()
            for policy_name, policy_sql in policies.items():
                try:
                    self.db.execute(text(policy_sql))
                    results["applied_policies"].append(policy_name)
                except Exception as e:
                    results["errors"].append(f"Policy {policy_name}: {str(e)}")

            # Apply MFA policies
            mfa_policies = self.create_mfa_policies()
            for policy_name, policy_sql in mfa_policies.items():
                try:
                    self.db.execute(text(policy_sql))
                    results["applied_policies"].append(f"mfa_{policy_name}")
                except Exception as e:
                    results["errors"].append(f"MFA Policy {policy_name}: {str(e)}")

            self.db.commit()

        except Exception as e:
            results["success"] = False
            results["errors"].append(f"General error: {str(e)}")
            self.db.rollback()

        return results

    def check_user_permissions(
        self, user_id: uuid.UUID, resource_type: str, resource_id: uuid.UUID
    ) -> bool:
        """Check if user has permissions for a specific resource"""

        permission_queries = {
            "user": "SELECT private.can_access_user(%s)",
            "task": "SELECT private.can_access_task(%s)",
        }

        if resource_type not in permission_queries:
            return False

        try:
            result = self.db.execute(
                text(permission_queries[resource_type]), (str(resource_id),)
            ).scalar()
            return bool(result)
        except Exception:
            return False

    def get_accessible_resources(
        self, user_id: uuid.UUID, resource_type: str
    ) -> list[uuid.UUID]:
        """Get list of resource IDs the user can access"""

        # This would implement efficient queries to get accessible resources
        # based on RLS policies without having to check each one individually

        resource_queries = {
            "tasks": """
                SELECT id FROM tasks
                WHERE (SELECT auth.uid()) = assigned_to
                   OR (SELECT auth.uid()) = created_by
                   OR private.can_access_task(id)
            """,
            "users": """
                SELECT id FROM users
                WHERE (SELECT auth.uid()) = id
                   OR private.can_access_user(id)
            """,
        }

        if resource_type not in resource_queries:
            return []

        try:
            result = self.db.execute(text(resource_queries[resource_type]))
            return [uuid.UUID(row[0]) for row in result.fetchall()]
        except Exception:
            return []
