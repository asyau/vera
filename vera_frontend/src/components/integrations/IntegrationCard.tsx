import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Settings,
  RefreshCw,
  Trash2,
  CheckCircle,
  AlertCircle,
  Clock,
  ExternalLink,
  Activity
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface Integration {
  id: string;
  type: string;
  name: string;
  status: string;
  created_at: string;
  updated_at: string;
  config: any;
  healthy: boolean;
}

interface IntegrationCardProps {
  integration: Integration;
  onUpdate: () => void;
  onConfigure: (integration: Integration) => void;
}

const IntegrationCard: React.FC<IntegrationCardProps> = ({
  integration,
  onUpdate,
  onConfigure
}) => {
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const getStatusColor = (status: string, healthy: boolean) => {
    if (!healthy) return 'destructive';

    switch (status) {
      case 'connected':
        return 'default';
      case 'pending':
        return 'secondary';
      case 'error':
        return 'destructive';
      default:
        return 'outline';
    }
  };

  const getStatusIcon = (status: string, healthy: boolean) => {
    if (!healthy) return <AlertCircle className="w-4 h-4" />;

    switch (status) {
      case 'connected':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4" />;
    }
  };

  const getIntegrationIcon = (type: string) => {
    const iconMap: { [key: string]: string } = {
      slack: '💬',
      jira: '📊',
      google_calendar: '📅',
      microsoft_teams: '💼',
      github: '🐙',
      trello: '📋'
    };

    return iconMap[type] || '🔗';
  };

  const handleTest = async () => {
    setLoading(true);
    try {
      const result = await api.testIntegration(integration.id);
      if (result.success) {
        toast({
          title: "Connection Test Successful",
          description: "Integration is working properly",
        });
      } else {
        toast({
          title: "Connection Test Failed",
          description: result.error || "Unknown error occurred",
          variant: "destructive",
        });
      }
      onUpdate();
    } catch (error) {
      toast({
        title: "Test Failed",
        description: "Could not test integration connection",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async () => {
    setLoading(true);
    try {
      const result = await api.syncIntegrationData(integration.id, 'incremental');
      if (result.success) {
        toast({
          title: "Sync Completed",
          description: "Integration data has been synchronized",
        });
      } else {
        toast({
          title: "Sync Failed",
          description: result.error || "Unknown error occurred",
          variant: "destructive",
        });
      }
      onUpdate();
    } catch (error) {
      toast({
        title: "Sync Failed",
        description: "Could not sync integration data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    try {
      const result = await api.refreshIntegrationCredentials(integration.id);
      if (result.success) {
        toast({
          title: "Credentials Refreshed",
          description: "Integration credentials have been updated",
        });
      } else {
        toast({
          title: "Refresh Failed",
          description: result.message || "Could not refresh credentials",
          variant: "destructive",
        });
      }
      onUpdate();
    } catch (error) {
      toast({
        title: "Refresh Failed",
        description: "Could not refresh integration credentials",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleDisconnect = async () => {
    if (!confirm('Are you sure you want to disconnect this integration? This action cannot be undone.')) {
      return;
    }

    setLoading(true);
    try {
      const result = await api.disconnectIntegration(integration.id);
      if (result.success) {
        toast({
          title: "Integration Disconnected",
          description: "Integration has been successfully disconnected",
        });
        onUpdate();
      } else {
        toast({
          title: "Disconnect Failed",
          description: result.message || "Could not disconnect integration",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Disconnect Failed",
        description: "Could not disconnect integration",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <Card className="w-full">
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getIntegrationIcon(integration.type)}</span>
          <div>
            <CardTitle className="text-base">{integration.name}</CardTitle>
            <CardDescription className="text-sm">
              {integration.type.replace('_', ' ').toUpperCase()}
            </CardDescription>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <Badge variant={getStatusColor(integration.status, integration.healthy)}>
            {getStatusIcon(integration.status, integration.healthy)}
            <span className="ml-1 capitalize">{integration.status}</span>
          </Badge>

          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" disabled={loading}>
                <Settings className="w-4 h-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleTest} disabled={loading}>
                <Activity className="w-4 h-4 mr-2" />
                Test Connection
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleSync} disabled={loading}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Sync Data
              </DropdownMenuItem>
              <DropdownMenuItem onClick={handleRefresh} disabled={loading}>
                <RefreshCw className="w-4 h-4 mr-2" />
                Refresh Credentials
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onConfigure(integration)}>
                <Settings className="w-4 h-4 mr-2" />
                Configure
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleDisconnect}
                disabled={loading}
                className="text-red-600 focus:text-red-600"
              >
                <Trash2 className="w-4 h-4 mr-2" />
                Disconnect
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Connected:</span>
            <span>{formatDate(integration.created_at)}</span>
          </div>

          <div className="flex justify-between text-sm">
            <span className="text-muted-foreground">Last Updated:</span>
            <span>{formatDate(integration.updated_at)}</span>
          </div>

          {integration.config?.last_sync && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Last Sync:</span>
              <span>{formatDate(integration.config.last_sync)}</span>
            </div>
          )}

          {integration.config?.user_info?.email && (
            <div className="flex justify-between text-sm">
              <span className="text-muted-foreground">Account:</span>
              <span className="truncate ml-2">{integration.config.user_info.email}</span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
};

export default IntegrationCard;
