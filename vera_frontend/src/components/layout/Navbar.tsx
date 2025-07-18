
import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Bell, Calendar, Menu, MessageSquare, Settings, User, Users } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import DailyBriefing from "@/components/briefing/DailyBriefing";

const Navbar = () => {
  const [showBriefing, setShowBriefing] = useState(false);
  const navigate = useNavigate();
  
  return (
    <header className="bg-white shadow-sm border-b border-gray-100 py-3 z-10">
      <div className="container px-4 mx-auto flex justify-between items-center">
        <div className="flex items-center space-x-4">
          <Link to="/" className="flex items-center">
            <div className="bg-gradient-to-r from-vira-primary to-vira-accent rounded-lg w-8 h-8 flex items-center justify-center mr-2">
              <span className="text-white font-bold">V</span>
            </div>
            <span className="text-xl font-semibold bg-clip-text text-transparent bg-gradient-to-r from-vira-primary to-vira-accent">
              Vira
            </span>
          </Link>
        </div>
        
        <div className="flex items-center space-x-2">
          <Button 
            onClick={() => navigate('/users')} 
            variant="outline" 
            size="sm" 
            className="hidden md:flex"
          >
            <Users className="mr-2 h-4 w-4" />
            Team Dashboard
          </Button>
          
          <Button 
            onClick={() => setShowBriefing(true)} 
            variant="outline" 
            size="sm" 
            className="hidden md:flex"
          >
            <Calendar className="mr-2 h-4 w-4" />
            Daily Briefing
          </Button>
          
          <Button variant="ghost" size="icon" className="text-gray-500">
            <MessageSquare className="h-5 w-5" />
          </Button>
          
          <Button variant="ghost" size="icon" className="text-gray-500">
            <Bell className="h-5 w-5" />
          </Button>
          
          <Button variant="ghost" size="icon" className="text-gray-500">
            <Settings className="h-5 w-5" />
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="relative h-8 w-8 rounded-full">
                <div className="flex h-8 w-8 items-center justify-center rounded-full bg-vira-light text-vira-primary">
                  <User className="h-4 w-4" />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/users')}>
                <Users className="h-4 w-4 mr-2" />
                Team Dashboard
              </DropdownMenuItem>
              <DropdownMenuItem>Profile</DropdownMenuItem>
              <DropdownMenuItem>Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem>Sign out</DropdownMenuItem>
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
