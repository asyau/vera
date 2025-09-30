import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { ExternalLink, CheckCircle, AlertCircle } from 'lucide-react';
import { api } from '@/services/api';
import { useToast } from '@/hooks/use-toast';

interface AvailableIntegration {
  type: string;
  name: string;
  description: string;
  features: string[];
  available: boolean;
}

interface IntegrationSetupModalProps {
  open: boolean;
  onClose: () => void;
  onSuccess: () => void;
  availableIntegrations: AvailableIntegration[];
}

const IntegrationSetupModal: React.FC<IntegrationSetupModalProps> = ({
  open,
  onClose,
  onSuccess,
  availableIntegrations
}) => {
  const [selectedIntegration, setSelectedIntegration] = useState<AvailableIntegration | null>(null);
  const [setupStep, setSetupStep] = useState<'select' | 'configure' | 'connecting'>('select');
  const [authMethod, setAuthMethod] = useState<string>('oauth');
  const [formData, setFormData] = useState({
    email: '',
    apiToken: '',
    serverUrl: '',
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    if (!open) {
      // Reset state when modal closes
      setSelectedIntegration(null);
      setSetupStep('select');
      setAuthMethod('oauth');
      setFormData({ email: '', apiToken: '', serverUrl: '' });
    }
  }, [open]);

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

  const handleIntegrationSelect = (integration: AvailableIntegration) => {
    setSelectedIntegration(integration);
    setSetupStep('configure');

    // Set default auth method based on integration type
    if (integration.type === 'jira') {
      setAuthMethod('api_token');
    } else {
      setAuthMethod('oauth');
    }
  };

  const handleOAuthSetup = async () => {
    if (!selectedIntegration) return;

    setLoading(true);
    try {
      const redirectUri = `${window.location.origin}/integrations/callback`;

      const result = await api.getIntegrationAuthUrl({
        integration_type: selectedIntegration.type,
        redirect_uri: redirectUri,
        auth_method: authMethod
      });

      if (result.success && result.authorization_url) {
        // Open OAuth flow in new window
        const width = 600;
        const height = 700;
        const left = (window.screen.width - width) / 2;
        const top = (window.screen.height - height) / 2;

        const authWindow = window.open(
          result.authorization_url,
          'integration_auth',
          `width=${width},height=${height},left=${left},top=${top},scrollbars=yes,resizable=yes`
        );

        if (authWindow) {
          setSetupStep('connecting');

          // Listen for the OAuth callback
          const handleMessage = (event: MessageEvent) => {
            if (event.origin !== window.location.origin) return;

            if (event.data.type === 'INTEGRATION_SUCCESS') {
              window.removeEventListener('message', handleMessage);
              authWindow.close();

              toast({
                title: "Integration Connected!",
                description: `${selectedIntegration.name} has been successfully connected.`,
              });

              onSuccess();
              onClose();
            } else if (event.data.type === 'INTEGRATION_ERROR') {
              window.removeEventListener('message', handleMessage);
              authWindow.close();

              toast({
                title: "Connection Failed",
                description: event.data.error || "Failed to connect integration",
                variant: "destructive",
              });

              setSetupStep('configure');
            }
          };

          window.addEventListener('message', handleMessage);

          // Check if window was closed manually
          const checkClosed = setInterval(() => {
            if (authWindow.closed) {
              clearInterval(checkClosed);
              window.removeEventListener('message', handleMessage);
              setSetupStep('configure');
            }
          }, 1000);
        }
      } else {
        toast({
          title: "Setup Error",
          description: result.error || "Could not initiate OAuth flow",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Setup Error",
        description: "Could not start integration setup",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleApiTokenSetup = async () => {
    if (!selectedIntegration) return;

    if (!formData.email || !formData.apiToken) {
      toast({
        title: "Missing Information",
        description: "Please provide both email and API token",
        variant: "destructive",
      });
      return;
    }

    setLoading(true);
    try {
      const result = await api.handleIntegrationCallback({
        integration_type: selectedIntegration.type,
        auth_method: 'api_token',
        email: formData.email,
        api_token: formData.apiToken,
        server_url: formData.serverUrl || undefined,
      });

      if (result.success) {
        toast({
          title: "Integration Connected!",
          description: `${selectedIntegration.name} has been successfully connected.`,
        });

        onSuccess();
        onClose();
      } else {
        toast({
          title: "Connection Failed",
          description: result.error || "Failed to connect integration",
          variant: "destructive",
        });
      }
    } catch (error) {
      toast({
        title: "Connection Failed",
        description: "Could not connect integration",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  const renderIntegrationSelection = () => (
    <div className="space-y-4">
      <div className="text-sm text-muted-foreground">
        Choose an integration to connect with your Vira workspace:
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {availableIntegrations.map((integration) => (
          <Card
            key={integration.type}
            className="cursor-pointer hover:shadow-md transition-shadow"
            onClick={() => handleIntegrationSelect(integration)}
          >
            <CardHeader className="pb-2">
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getIntegrationIcon(integration.type)}</span>
                <div>
                  <CardTitle className="text-sm">{integration.name}</CardTitle>
                  <CardDescription className="text-xs">
                    {integration.type.replace('_', ' ').toUpperCase()}
                  </CardDescription>
                </div>
                {integration.available && (
                  <Badge variant="secondary" className="ml-auto">
                    <CheckCircle className="w-3 h-3 mr-1" />
                    Available
                  </Badge>
                )}
              </div>
            </CardHeader>
            <CardContent className="pt-0">
              <p className="text-xs text-muted-foreground mb-2">
                {integration.description}
              </p>
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
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  const renderConfiguration = () => {
    if (!selectedIntegration) return null;

    const supportsOAuth = !['jira'].includes(selectedIntegration.type);
    const supportsApiToken = ['jira'].includes(selectedIntegration.type);

    return (
      <div className="space-y-4">
        <div className="flex items-center space-x-2">
          <span className="text-2xl">{getIntegrationIcon(selectedIntegration.type)}</span>
          <div>
            <h3 className="font-semibold">{selectedIntegration.name}</h3>
            <p className="text-sm text-muted-foreground">Configure your integration</p>
          </div>
        </div>

        {supportsOAuth && supportsApiToken ? (
          <Tabs value={authMethod} onValueChange={setAuthMethod}>
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="oauth">OAuth (Recommended)</TabsTrigger>
              <TabsTrigger value="api_token">API Token</TabsTrigger>
            </TabsList>

            <TabsContent value="oauth" className="space-y-4">
              <div className="p-4 bg-blue-50 rounded-lg">
                <h4 className="font-medium text-blue-900">OAuth Setup</h4>
                <p className="text-sm text-blue-700 mt-1">
                  Click the button below to securely connect your {selectedIntegration.name} account.
                  You'll be redirected to {selectedIntegration.name} to authorize access.
                </p>
              </div>

              <Button
                onClick={handleOAuthSetup}
                disabled={loading}
                className="w-full"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                Connect with {selectedIntegration.name}
              </Button>
            </TabsContent>

            <TabsContent value="api_token" className="space-y-4">
              <div className="space-y-4">
                <div>
                  <Label htmlFor="email">Email Address</Label>
                  <Input
                    id="email"
                    type="email"
                    value={formData.email}
                    onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                    placeholder="your.email@company.com"
                  />
                </div>

                <div>
                  <Label htmlFor="apiToken">API Token</Label>
                  <Input
                    id="apiToken"
                    type="password"
                    value={formData.apiToken}
                    onChange={(e) => setFormData({ ...formData, apiToken: e.target.value })}
                    placeholder="Your API token"
                  />
                </div>

                {selectedIntegration.type === 'jira' && (
                  <div>
                    <Label htmlFor="serverUrl">Server URL (Optional)</Label>
                    <Input
                      id="serverUrl"
                      value={formData.serverUrl}
                      onChange={(e) => setFormData({ ...formData, serverUrl: e.target.value })}
                      placeholder="https://your-domain.atlassian.net"
                    />
                  </div>
                )}

                <Button
                  onClick={handleApiTokenSetup}
                  disabled={loading}
                  className="w-full"
                >
                  Connect Integration
                </Button>
              </div>
            </TabsContent>
          </Tabs>
        ) : supportsOAuth ? (
          <div className="space-y-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <h4 className="font-medium text-blue-900">OAuth Setup</h4>
              <p className="text-sm text-blue-700 mt-1">
                Click the button below to securely connect your {selectedIntegration.name} account.
                You'll be redirected to {selectedIntegration.name} to authorize access.
              </p>
            </div>

            <Button
              onClick={handleOAuthSetup}
              disabled={loading}
              className="w-full"
            >
              <ExternalLink className="w-4 h-4 mr-2" />
              Connect with {selectedIntegration.name}
            </Button>
          </div>
        ) : (
          <div className="space-y-4">
            <div>
              <Label htmlFor="email">Email Address</Label>
              <Input
                id="email"
                type="email"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                placeholder="your.email@company.com"
              />
            </div>

            <div>
              <Label htmlFor="apiToken">API Token</Label>
              <Input
                id="apiToken"
                type="password"
                value={formData.apiToken}
                onChange={(e) => setFormData({ ...formData, apiToken: e.target.value })}
                placeholder="Your API token"
              />
            </div>

            {selectedIntegration.type === 'jira' && (
              <div>
                <Label htmlFor="serverUrl">Server URL (Optional)</Label>
                <Input
                  id="serverUrl"
                  value={formData.serverUrl}
                  onChange={(e) => setFormData({ ...formData, serverUrl: e.target.value })}
                  placeholder="https://your-domain.atlassian.net"
                />
              </div>
            )}

            <Button
              onClick={handleApiTokenSetup}
              disabled={loading}
              className="w-full"
            >
              Connect Integration
            </Button>
          </div>
        )}

        <div className="flex justify-between">
          <Button variant="outline" onClick={() => setSetupStep('select')}>
            Back
          </Button>
        </div>
      </div>
    );
  };

  const renderConnecting = () => (
    <div className="text-center space-y-4">
      <div className="flex justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
      </div>
      <div>
        <h3 className="font-semibold">Connecting...</h3>
        <p className="text-sm text-muted-foreground">
          Please complete the authorization in the popup window.
        </p>
      </div>
    </div>
  );

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>
            {setupStep === 'select' && 'Add New Integration'}
            {setupStep === 'configure' && `Setup ${selectedIntegration?.name}`}
            {setupStep === 'connecting' && 'Connecting...'}
          </DialogTitle>
          <DialogDescription>
            {setupStep === 'select' && 'Connect third-party tools to enhance your Vira experience'}
            {setupStep === 'configure' && 'Configure your integration settings'}
            {setupStep === 'connecting' && 'Completing the connection process'}
          </DialogDescription>
        </DialogHeader>

        <div className="py-4">
          {setupStep === 'select' && renderIntegrationSelection()}
          {setupStep === 'configure' && renderConfiguration()}
          {setupStep === 'connecting' && renderConnecting()}
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default IntegrationSetupModal;
