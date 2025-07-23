
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Calendar, Menu, MessageSquare, Settings, User, Users, LogOut, Shield } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import DailyBriefing from "@/components/briefing/DailyBriefing";
import { useAuth } from '@/contexts/AuthContext';

const Navbar = () => {
  const [showBriefing, setShowBriefing] = useState(false);
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuth();
  
  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-gray-100/50 py-4 z-10 sticky top-0">
      <div className="container px-6 mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Link to="/" className="flex items-center group">
            <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl w-10 h-10 flex items-center justify-center mr-3 shadow-lg group-hover:shadow-xl transition-all duration-200 group-hover:scale-105">
              <span className="text-white font-bold text-lg">V</span>
            </div>
            <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600">
              Vira
            </span>
          </Link>
        </div>
        
        <div className="flex items-center space-x-3">
          {hasRole('supervisor') && (
            <Button 
              onClick={() => navigate('/users')} 
              variant="outline" 
              size="sm" 
              className="hidden md:flex bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white hover:shadow-md transition-all duration-200"
            >
              <Users className="mr-2 h-4 w-4" />
              Team Dashboard
            </Button>
          )}
          
          <Button 
            onClick={() => setShowBriefing(true)} 
            variant="outline" 
            size="sm" 
            className="hidden md:flex bg-white/50 backdrop-blur-sm border-gray-200 hover:bg-white hover:shadow-md transition-all duration-200"
          >
            <Calendar className="mr-2 h-4 w-4" />
            Daily Briefing
          </Button>
          
          <div className="flex items-center space-x-1">
            <Button variant="ghost" size="icon" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200">
              <MessageSquare className="h-5 w-5" />
            </Button>
            
            <Button variant="ghost" size="icon" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200 relative">
              <Bell className="h-5 w-5" />
              <div className="absolute -top-1 -right-1 w-2 h-2 bg-red-500 rounded-full animate-pulse" />
            </Button>
            
            <Button variant="ghost" size="icon" className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200">
              <Settings className="h-5 w-5" />
            </Button>
          </div>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-10 w-10 rounded-full hover:bg-gray-100/50 transition-all duration-200">
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md hover:shadow-lg transition-all duration-200">
                  <User className="h-5 w-5" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56 bg-white/95 backdrop-blur-md border border-gray-200/50 shadow-xl">
              <DropdownMenuLabel className="text-gray-700 font-semibold">
                <div className="flex flex-col space-y-1">
                  <span>{user?.name}</span>
                  <div className="flex items-center space-x-2">
                    <Badge variant={user?.role === 'supervisor' ? 'default' : 'secondary'} className="text-xs">
                      {user?.role === 'supervisor' ? (
                        <>
                          <Shield className="h-3 w-3 mr-1" />
                          Supervisor
                        </>
                      ) : (
                        'Employee'
                      )}
                    </Badge>
                  </div>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              {hasRole('supervisor') && (
                <DropdownMenuItem onClick={() => navigate('/users')} className="hover:bg-gray-50 transition-colors duration-150">
                  <Users className="h-4 w-4 mr-2" />
                  Team Dashboard
                </DropdownMenuItem>
              )}
              <DropdownMenuItem className="hover:bg-gray-50 transition-colors duration-150">Profile</DropdownMenuItem>
              <DropdownMenuItem className="hover:bg-gray-50 transition-colors duration-150">Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="hover:bg-red-50 text-red-600 transition-colors duration-150">
                <LogOut className="h-4 w-4 mr-2" />
                Sign out
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
      
      <DailyBriefing 
        open={showBriefing} 
        onClose={() => setShowBriefing(false)} 
      />
    </header>
  );
};

export default Navbar;
