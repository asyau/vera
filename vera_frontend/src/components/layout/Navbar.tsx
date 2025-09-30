
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Calendar, Menu, MessageSquare, Settings, User, Users, LogOut, Shield, Home, Link as LinkIcon } from 'lucide-react';
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
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import DailyBriefing from "@/components/briefing/DailyBriefing";
import { useAuthStore } from '@/stores/authStore';

const Navbar = () => {
  const [showBriefing, setShowBriefing] = useState(false);
  const navigate = useNavigate();
  const { user, logout, hasRole } = useAuthStore();

  return (
    <header className="bg-white/80 backdrop-blur-md border-b border-gray-100/50 py-4 z-10 sticky top-0">
      <div className="container px-6 mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                onClick={() => navigate('/')}
                variant="ghost"
                className="flex items-center group hover:bg-gray-50 rounded-lg px-2 py-1 transition-all duration-200"
              >
                <div className="bg-gradient-to-r from-blue-600 to-indigo-600 rounded-xl w-10 h-10 flex items-center justify-center mr-3 shadow-lg group-hover:shadow-xl transition-all duration-200 group-hover:scale-105">
                  <span className="text-white font-bold text-lg">V</span>
                </div>
                <span className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-600 to-indigo-600 group-hover:from-blue-700 group-hover:to-indigo-700 transition-all duration-200">
                  Vira
                </span>
              </Button>
            </TooltipTrigger>
            <TooltipContent>
              <div className="flex items-center space-x-2">
                <Home className="h-4 w-4" />
                <span>Go to Home</span>
              </div>
            </TooltipContent>
          </Tooltip>
        </div>

        <div className="flex items-center space-x-3">
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

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate('/calendar')}
                  className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200"
                >
                  <Calendar className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Calendar</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate('/integrations')}
                  className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200"
                >
                  <LinkIcon className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Integrations</TooltipContent>
            </Tooltip>

            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigate('/settings')}
                  className="text-gray-500 hover:text-gray-700 hover:bg-gray-100/50 rounded-lg transition-all duration-200"
                >
                  <Settings className="h-5 w-5" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>Settings</TooltipContent>
            </Tooltip>
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
              <DropdownMenuItem
                onClick={() => navigate('/profile')}
                className="hover:bg-gray-50 transition-colors duration-150"
              >
                Profile
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => navigate('/calendar')}
                className="hover:bg-gray-50 transition-colors duration-150"
              >
                <Calendar className="h-4 w-4 mr-2" />
                Calendar
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => navigate('/integrations')}
                className="hover:bg-gray-50 transition-colors duration-150"
              >
                <LinkIcon className="h-4 w-4 mr-2" />
                Integrations
              </DropdownMenuItem>
              <DropdownMenuItem
                onClick={() => navigate('/settings')}
                className="hover:bg-gray-50 transition-colors duration-150"
              >
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
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
