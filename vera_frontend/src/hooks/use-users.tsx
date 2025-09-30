import { useState, useEffect } from 'react';
import { api } from '@/services/api';
import { AuthUser } from '@/types/auth';

export function useUsers() {
  const [users, setUsers] = useState<AuthUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch users on mount
  useEffect(() => {
    const fetchUsers = async () => {
      try {
        // We'll need to add this endpoint to the API service
        const fetchedUsers = await api.getUsers();
        setUsers(fetchedUsers);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch users');
        console.log('Users fetch failed, using empty array'); // For now
        setUsers([]);
      } finally {
        setLoading(false);
      }
    };

    fetchUsers();
  }, []);

  // Helper function to get user name by ID
  const getUserName = (userId: string | null): string => {
    if (!userId) return 'Unassigned';
    const user = users.find(u => u.id === userId);
    return user ? user.name : `User ${userId.slice(-8)}`;
  };

  // Helper function to get user by ID
  const getUserById = (userId: string | null): AuthUser | null => {
    if (!userId) return null;
    return users.find(u => u.id === userId) || null;
  };

  return {
    users,
    loading,
    error,
    getUserName,
    getUserById,
  };
}
