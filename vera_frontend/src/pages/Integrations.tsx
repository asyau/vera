import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Plus,
  RefreshCw,
  Activity,
  TrendingUp,
  AlertCircle,
  CheckCircle,
  Clock,
  Settings
} from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';
import IntegrationCard from '@/components/integrations/IntegrationCard';
import IntegrationSetupModal from '@/components/integrations/IntegrationSetupModal';

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

interface AvailableIntegration {
  type: string;
  name: string;
  description: string;
  features: string[];
  available: boolean;
}

interface IntegrationStats {
  total_integrations: number;
  active_integrations: number;
  by_type: { [key: string]: number };
  by_status: { [key: string]: number };
  health_summary: {
    healthy: number;
    unhealthy: number;
    unknown: number;
  };
}

const Integrations: React.FC = () => {
  const [integrations, setIntegrations] = useState<Integration[]>([]);
  const [availableIntegrations, setAvailableIntegrations] = useState<AvailableIntegration[]>([]);
  const [stats, setStats] = useState<IntegrationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [setupModalOpen, setSetupModalOpen] = useState(false);
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null);
  const [syncingAll, setSyncingAll] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const [integrationsData, availableData, statsData] = await Promise.all([
        api.getCompanyIntegrations(),
        api.getAvailableIntegrations(),
        api.getIntegrationStats()
      ]);

      setIntegrations(integrationsData);
      setAvailableIntegrations(availableData);
      setStats(statsData);
    } catch (error) {
      toast({
        title: "Error Loading Integrations",
        description: "Could not load integration data",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleSyncAll = async () => {
    setSyncingAll(true);
    try {
      const result = await api.syncAllIntegrations('incremental');
      if (result.success) {
        toast({
          title: "Sync Started",
          description: "All integrations are being synchronized in the background",
        });
      } else {
        toast({
          title: "Sync Failed",
          description: result.message || "Could not start synchronization",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Sync Failed",
        description: "Could not start synchronization",
        variant: "destructive",
      });
    } finally {
      setSyncingAll(false);
      // Refresh data after a short delay
      setTimeout(loadData, 2000);
    }
  };

  const handleConfigure = (integration: Integration) => {
    setSelectedIntegration(integration);
    // TODO: Open configuration modal
    toast({
      title: "Configuration",
      description: "Configuration panel coming soon",
    });
  };

  const getHealthColor = (healthy: number, total: number) => {
    if (total === 0) return 'text-gray-500';
    const percentage = (healthy / total) * 100;
    if (percentage >= 90) return 'text-green-500';
    if (percentage >= 70) return 'text-yellow-500';
    return 'text-red-500';
  };

  const renderStatsCards = () => {
    if (!stats) return null;

    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Integrations</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total_integrations}</div>
            <p className="text-xs text-muted-foreground">
              {stats.active_integrations} active
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Health Status</CardTitle>
            <CheckCircle className={`h-4 w-4 ${getHealthColor(stats.health_summary.healthy, stats.total_integrations)}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.health_summary.healthy}</div>
            <p className="text-xs text-muted-foreground">
              {stats.health_summary.unhealthy} unhealthy, {stats.health_summary.unknown} unknown
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Most Popular</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {Object.keys(stats.by_type).length > 0
                ? Object.entries(stats.by_type).sort(([,a], [,b]) => b - a)[0][0].replace('_', ' ')
                : 'None'
              }
            </div>
            <p className="text-xs text-muted-foreground">
              {Object.keys(stats.by_type).length} integration types
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Status Overview</CardTitle>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="space-y-1">
              {Object.entries(stats.by_status).map(([status, count]) => (
                <div key={status} className="flex justify-between text-sm">
                  <span className="capitalize">{status}:</span>
                  <span>{count}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    );
  };

  const renderActiveIntegrations = () => (
    <div className="space-y-4">
      {integrations.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <div className="text-center space-y-2">
              <h3 className="text-lg font-semibold">No Integrations Yet</h3>
              <p className="text-muted-foreground">
                Connect your favorite tools to get started with Vira integrations.
              </p>
              <Button onClick={() => setSetupModalOpen(true)} className="mt-4">
                <Plus className="w-4 h-4 mr-2" />
                Add Your First Integration
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {integrations.map((integration) => (
            <IntegrationCard
              key={integration.id}
              integration={integration}
              onUpdate={loadData}
              onConfigure={handleConfigure}
            />
          ))}
        </div>
      )}
    </div>
  );

  const renderAvailableIntegrations = () => (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Available integrations you can add to your workspace:
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {availableIntegrations.map((integration) => {
          const isAlreadyConnected = integrations.some(i => i.type === integration.type);

          return (
            <Card key={integration.type} className="relative">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <span className="text-2xl">
                      {integration.type === 'slack' && '💬'}
                      {integration.type === 'jira' && '📊'}
                      {integration.type === 'google_calendar' && '📅'}
                      {integration.type === 'microsoft_teams' && '💼'}
                      {integration.type === 'github' && '🐙'}
                      {integration.type === 'trello' && '📋'}
                      {!['slack', 'jira', 'google_calendar', 'microsoft_teams', 'github', 'trello'].includes(integration.type) && '🔗'}
                    </span>
                    <div>
                      <CardTitle className="text-base">{integration.name}</CardTitle>
                      <CardDescription className="text-sm">
                        {integration.type.replace('_', ' ').toUpperCase()}
                      </CardDescription>
                    </div>
                  </div>

                  {isAlreadyConnected && (
                    <Badge variant="secondary">
                      <CheckCircle className="w-3 h-3 mr-1" />
                      Connected
                    </Badge>
                  )}
                </div>
              </CardHeader>

              <CardContent>
                <p className="text-sm text-muted-foreground mb-3">
                  {integration.description}
                </p>

                <div className="space-y-2 mb-4">
                  <div className="text-xs font-medium">Features:</div>
                  <div className="flex flex-wrap gap-1">
                    {integration.features.slice(0, 3).map((feature, index) => (
                      <Badge key={index} variant="outline" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                    {integration.features.length > 3 && (
                      <Badge variant="outline" className="text-xs">
                        +{integration.features.length - 3} more
                      </Badge>
                    )}
                  </div>
                </div>

                <Button
                  size="sm"
                  className="w-full"
                  disabled={isAlreadyConnected}
                  onClick={() => {
                    // Pre-select this integration and open modal
                    setSetupModalOpen(true);
                  }}
                >
                  {isAlreadyConnected ? (
                    <>
                      <CheckCircle className="w-4 h-4 mr-2" />
                      Already Connected
                    </>
                  ) : (
                    <>
                      <Plus className="w-4 h-4 mr-2" />
                      Connect
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );

  if (loading) {
    return (
      <div className="container mx-auto p-6">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Integrations</h1>
          <p className="text-muted-foreground mt-2">
            Connect your favorite tools and services to enhance your Vira experience.
          </p>
        </div>

        <div className="flex space-x-2">
          <Button
            variant="outline"
            onClick={loadData}
            disabled={loading}
          >
            <RefreshCw className="w-4 h-4 mr-2" />
            Refresh
          </Button>

          {integrations.length > 0 && (
            <Button
              variant="outline"
              onClick={handleSyncAll}
              disabled={syncingAll}
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${syncingAll ? 'animate-spin' : ''}`} />
              Sync All
            </Button>
          )}

          <Button onClick={() => setSetupModalOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            Add Integration
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      {renderStatsCards()}

      {/* Main Content */}
      <Tabs defaultValue="active" className="space-y-4">
        <TabsList>
          <TabsTrigger value="active">
            Active Integrations ({integrations.length})
          </TabsTrigger>
          <TabsTrigger value="available">
            Available ({availableIntegrations.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="active" className="space-y-4">
          {renderActiveIntegrations()}
        </TabsContent>

        <TabsContent value="available" className="space-y-4">
          {renderAvailableIntegrations()}
        </TabsContent>
      </Tabs>

      {/* Setup Modal */}
      <IntegrationSetupModal
        open={setupModalOpen}
        onClose={() => setSetupModalOpen(false)}
        onSuccess={loadData}
        availableIntegrations={availableIntegrations}
      />
    </div>
  );
};

export default Integrations;
