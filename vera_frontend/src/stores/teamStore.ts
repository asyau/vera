/**
 * Team Store using Zustand
 * Implements MVP pattern - Model layer for team management state
 */
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';

export interface TeamMember {
  id: string;
  name: string;
  email: string;
  role: 'employee' | 'supervisor' | 'admin';
  team_id: string | null;
  is_active: boolean;
  last_login: string | null;
  avatar?: string;
}

export interface Team {
  id: string;
  name: string;
  description: string;
  company_id: string;
  supervisor_id: string;
  members: TeamMember[];
  created_at: string;
  updated_at: string;
}

export interface TeamStats {
  total_members: number;
  active_members: number;
  total_tasks: number;
  completed_tasks: number;
  overdue_tasks: number;
  completion_rate: number;
}

export interface TeamState {
  // State
  teams: Team[];
  currentTeam: Team | null;
  teamMembers: TeamMember[];
  teamStats: TeamStats | null;
  isLoading: boolean;
  error: string | null;

  // Actions - Teams
  fetchTeams: () => Promise<void>;
  fetchTeam: (teamId: string) => Promise<void>;
  setCurrentTeam: (team: Team | null) => void;

  // Actions - Members
  fetchTeamMembers: (teamId: string) => Promise<void>;
  addTeamMember: (teamId: string, userId: string) => Promise<void>;
  removeTeamMember: (teamId: string, userId: string) => Promise<void>;
  updateMemberRole: (userId: string, role: string) => Promise<void>;

  // Actions - Stats
  fetchTeamStats: (teamId: string) => Promise<void>;

  // Actions - UI
  clearError: () => void;

  // Selectors
  getTeamById: (teamId: string) => Team | undefined;
  getMemberById: (memberId: string) => TeamMember | undefined;
  getActiveMembers: () => TeamMember[];
  getSupervisors: () => TeamMember[];
}

export const useTeamStore = create<TeamState>()(
  devtools(
    (set, get) => ({
      // Initial state
      teams: [],
      currentTeam: null,
      teamMembers: [],
      teamStats: null,
      isLoading: false,
      error: null,

      // Team actions
      fetchTeams: async () => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call
          const teams: Team[] = [];
          set({ teams, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch teams',
            isLoading: false
          });
        }
      },

      fetchTeam: async (teamId: string) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call
          const team: Team | null = null;
          set({ currentTeam: team, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch team',
            isLoading: false
          });
        }
      },

      setCurrentTeam: (team: Team | null) => {
        set({ currentTeam: team });

        // Fetch team members when team changes
        if (team) {
          get().fetchTeamMembers(team.id);
          get().fetchTeamStats(team.id);
        }
      },

      // Member actions
      fetchTeamMembers: async (teamId: string) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call
          const teamMembers: TeamMember[] = [];
          set({ teamMembers, isLoading: false });
        } catch (error: any) {
          set({
            error: error.message || 'Failed to fetch team members',
            isLoading: false
          });
        }
      },

      addTeamMember: async (teamId: string, userId: string) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call

          // Update local state
          set(state => ({
            isLoading: false
          }));
        } catch (error: any) {
          set({
            error: error.message || 'Failed to add team member',
            isLoading: false
          });
        }
      },

      removeTeamMember: async (teamId: string, userId: string) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call

          // Update local state
          set(state => ({
            teamMembers: state.teamMembers.filter(member => member.id !== userId),
            isLoading: false
          }));
        } catch (error: any) {
          set({
            error: error.message || 'Failed to remove team member',
            isLoading: false
          });
        }
      },

      updateMemberRole: async (userId: string, role: string) => {
        set({ isLoading: true, error: null });

        try {
          // TODO: Implement API call

          // Update local state
          set(state => ({
            teamMembers: state.teamMembers.map(member =>
              member.id === userId ? { ...member, role: role as any } : member
            ),
            isLoading: false
          }));
        } catch (error: any) {
          set({
            error: error.message || 'Failed to update member role',
            isLoading: false
          });
        }
      },

      // Stats actions
      fetchTeamStats: async (teamId: string) => {
        try {
          // TODO: Implement API call
          const stats: TeamStats = {
            total_members: 0,
            active_members: 0,
            total_tasks: 0,
            completed_tasks: 0,
            overdue_tasks: 0,
            completion_rate: 0
          };

          set({ teamStats: stats });
        } catch (error: any) {
          set({ error: error.message || 'Failed to fetch team stats' });
        }
      },

      // UI actions
      clearError: () => {
        set({ error: null });
      },

      // Selectors
      getTeamById: (teamId: string) => {
        const { teams } = get();
        return teams.find(team => team.id === teamId);
      },

      getMemberById: (memberId: string) => {
        const { teamMembers } = get();
        return teamMembers.find(member => member.id === memberId);
      },

      getActiveMembers: () => {
        const { teamMembers } = get();
        return teamMembers.filter(member => member.is_active);
      },

      getSupervisors: () => {
        const { teamMembers } = get();
        return teamMembers.filter(member => member.role === 'supervisor');
      }
    }),
    {
      name: 'team-store'
    }
  )
);
