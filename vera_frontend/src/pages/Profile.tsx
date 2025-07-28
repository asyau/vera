import React, { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { api, User } from '@/lib/api';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { useToast } from '@/hooks/use-toast';
import { User as UserIcon, Mail, Shield, Building, Calendar, Edit, Save, X, ArrowLeft } from 'lucide-react';
import { format } from 'date-fns';

const Profile = () => {
  const { user, logout } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [userData, setUserData] = useState<User | null>(null);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
  });

  useEffect(() => {
    const fetchUserData = async () => {
      if (user?.id) {
        try {
          const data = await api.getUser(user.id);
          setUserData(data);
          setFormData({
            name: data.name,
            email: data.email,
          });
        } catch (error) {
          toast({
            title: "Error",
            description: "Failed to load profile data",
            variant: "destructive",
          });
        }
      }
    };

    fetchUserData();
  }, [user?.id, toast]);

  const handleSave = async () => {
    if (!user?.id) return;

    setIsLoading(true);
    try {
      const updatedUser = await api.updateUser(user.id, {
        name: formData.name,
        email: formData.email,
      });
      
      setUserData(updatedUser);
      setIsEditing(false);
      
      toast({
        title: "Success",
        description: "Profile updated successfully",
      });
    } catch (error: any) {
      toast({
        title: "Error",
        description: error.message || "Failed to update profile",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleCancel = () => {
    setFormData({
      name: userData?.name || '',
      email: userData?.email || '',
    });
    setIsEditing(false);
  };

  if (!userData) {
    return (
      <div className="container mx-auto px-6 py-8">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading profile...</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-6 py-8 max-w-4xl">
        <div className="space-y-6">
                  {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Button
              onClick={() => navigate('/')}
              variant="ghost"
              size="sm"
              className="flex items-center space-x-2 text-gray-600 hover:text-gray-900"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back to Home</span>
            </Button>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Profile</h1>
              <p className="text-gray-600 mt-1">Manage your account information and preferences</p>
            </div>
          </div>
            <div className="flex space-x-2">
            {isEditing ? (
              <>
                <Button
                  onClick={handleSave}
                  disabled={isLoading}
                  className="bg-blue-600 hover:bg-blue-700"
                >
                  <Save className="h-4 w-4 mr-2" />
                  {isLoading ? 'Saving...' : 'Save Changes'}
                </Button>
                <Button
                  onClick={handleCancel}
                  variant="outline"
                  disabled={isLoading}
                >
                  <X className="h-4 w-4 mr-2" />
                  Cancel
                </Button>
              </>
            ) : (
              <Button
                onClick={() => setIsEditing(true)}
                variant="outline"
              >
                <Edit className="h-4 w-4 mr-2" />
                Edit Profile
              </Button>
            )}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Profile Card */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader className="text-center">
                <div className="flex justify-center mb-4">
                  <Avatar className="h-24 w-24">
                    <AvatarImage src="" alt={userData.name} />
                    <AvatarFallback className="text-2xl bg-gradient-to-r from-blue-500 to-indigo-600 text-white">
                      {userData.name.charAt(0).toUpperCase()}
                    </AvatarFallback>
                  </Avatar>
                </div>
                <CardTitle className="text-xl">{userData.name}</CardTitle>
                <CardDescription className="flex items-center justify-center space-x-2">
                  <Mail className="h-4 w-4" />
                  <span>{userData.email}</span>
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex items-center justify-center">
                  <Badge variant={userData.role === 'supervisor' ? 'default' : 'secondary'} className="text-sm">
                    {userData.role === 'supervisor' ? (
                      <>
                        <Shield className="h-3 w-3 mr-1" />
                        Supervisor
                      </>
                    ) : (
                      'Employee'
                    )}
                  </Badge>
                </div>
                
                <Separator />
                
                <div className="space-y-3 text-sm">
                  <div className="flex items-center space-x-2 text-gray-600">
                    <Building className="h-4 w-4" />
                    <span>Company: {userData.company?.name || 'N/A'}</span>
                  </div>
                  <div className="flex items-center space-x-2 text-gray-600">
                    <Calendar className="h-4 w-4" />
                    <span>Member since: {format(new Date(userData.created_at), 'MMM yyyy')}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Details Card */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <UserIcon className="h-5 w-5" />
                  <span>Personal Information</span>
                </CardTitle>
                <CardDescription>
                  Update your personal details and contact information
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="name">Full Name</Label>
                    {isEditing ? (
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder="Enter your full name"
                      />
                    ) : (
                      <div className="p-3 bg-gray-50 rounded-md border">
                        {userData.name}
                      </div>
                    )}
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    {isEditing ? (
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        placeholder="Enter your email address"
                      />
                    ) : (
                      <div className="p-3 bg-gray-50 rounded-md border">
                        {userData.email}
                      </div>
                    )}
                  </div>
                </div>

                <Separator />

                <div className="space-y-4">
                  <h3 className="text-lg font-semibold">Account Details</h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div className="space-y-2">
                      <Label>Role</Label>
                      <div className="p-3 bg-gray-50 rounded-md border">
                        <Badge variant={userData.role === 'supervisor' ? 'default' : 'secondary'}>
                          {userData.role === 'supervisor' ? 'Supervisor' : 'Employee'}
                        </Badge>
                      </div>
                    </div>
                    
                    <div className="space-y-2">
                      <Label>User ID</Label>
                      <div className="p-3 bg-gray-50 rounded-md border font-mono text-sm">
                        {userData.id}
                      </div>
                    </div>
                  </div>
                </div>

                {userData.team && (
                  <>
                    <Separator />
                    <div className="space-y-4">
                      <h3 className="text-lg font-semibold">Team Information</h3>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div className="space-y-2">
                          <Label>Team</Label>
                          <div className="p-3 bg-gray-50 rounded-md border">
                            {userData.team.name}
                          </div>
                        </div>
                        
                        {userData.project && (
                          <div className="space-y-2">
                            <Label>Project</Label>
                            <div className="p-3 bg-gray-50 rounded-md border">
                              {userData.project.name}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Profile; 