import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/services/api';

const IntegrationCallback: React.FC = () => {
  const [searchParams] = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [message, setMessage] = useState('Processing integration...');

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const code = searchParams.get('code');
        const state = searchParams.get('state');
        const error = searchParams.get('error');
        const error_description = searchParams.get('error_description');

        if (error) {
          setStatus('error');
          setMessage(error_description || error || 'Authorization was denied or failed');

          // Notify parent window of error
          if (window.opener) {
            window.opener.postMessage({
              type: 'INTEGRATION_ERROR',
              error: error_description || error || 'Authorization failed'
            }, window.location.origin);
          }
          return;
        }

        if (!code) {
          setStatus('error');
          setMessage('No authorization code received');

          if (window.opener) {
            window.opener.postMessage({
              type: 'INTEGRATION_ERROR',
              error: 'No authorization code received'
            }, window.location.origin);
          }
          return;
        }

        // Parse state to get integration type
        let integrationType = 'unknown';
        try {
          if (state) {
            const stateData = JSON.parse(atob(state));
            integrationType = stateData.integration_type || 'unknown';
          }
        } catch (e) {
          console.warn('Could not parse state parameter:', e);
        }

        // Handle the callback with the backend
        const result = await api.handleIntegrationCallback({
          integration_type: integrationType,
          code,
          state: state || undefined,
          auth_method: 'oauth'
        });

        if (result.success) {
          setStatus('success');
          setMessage('Integration connected successfully!');

          // Notify parent window of success
          if (window.opener) {
            window.opener.postMessage({
              type: 'INTEGRATION_SUCCESS',
              integration: result.integration
            }, window.location.origin);
          }

          // Close window after a short delay
          setTimeout(() => {
            if (window.opener) {
              window.close();
            }
          }, 2000);
        } else {
          setStatus('error');
          setMessage(result.error || 'Failed to complete integration');

          if (window.opener) {
            window.opener.postMessage({
              type: 'INTEGRATION_ERROR',
              error: result.error || 'Failed to complete integration'
            }, window.location.origin);
          }
        }
      } catch (error) {
        console.error('Integration callback error:', error);
        setStatus('error');
        setMessage('An unexpected error occurred during integration');

        if (window.opener) {
          window.opener.postMessage({
            type: 'INTEGRATION_ERROR',
            error: 'An unexpected error occurred'
          }, window.location.origin);
        }
      }
    };

    handleCallback();
  }, [searchParams]);

  const renderContent = () => {
    switch (status) {
      case 'loading':
        return (
          <div className="flex flex-col items-center space-y-4">
            <Loader2 className="w-8 h-8 animate-spin text-blue-500" />
            <div className="text-center">
              <h2 className="text-lg font-semibold">Connecting Integration</h2>
              <p className="text-muted-foreground">{message}</p>
            </div>
          </div>
        );

      case 'success':
        return (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-green-100 flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
            <div className="text-center">
              <h2 className="text-lg font-semibold text-green-900">Success!</h2>
              <p className="text-green-700">{message}</p>
              <p className="text-sm text-muted-foreground mt-2">
                This window will close automatically.
              </p>
            </div>
          </div>
        );

      case 'error':
        return (
          <div className="flex flex-col items-center space-y-4">
            <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center">
              <AlertCircle className="w-6 h-6 text-red-600" />
            </div>
            <div className="text-center">
              <h2 className="text-lg font-semibold text-red-900">Connection Failed</h2>
              <p className="text-red-700">{message}</p>
              <p className="text-sm text-muted-foreground mt-2">
                You can close this window and try again.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardContent className="p-8">
          {renderContent()}
        </CardContent>
      </Card>
    </div>
  );
};

export default IntegrationCallback;
