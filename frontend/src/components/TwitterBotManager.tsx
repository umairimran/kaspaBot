import React, { useState, useEffect } from 'react';

interface TwitterBotStatus {
  is_running: boolean;
  start_time: string | null;
  error_count: number;
  last_error: string | null;
  uptime_seconds: number | null;
  queue_stats?: {
    total: number;
    posted: number;
    pending: number;
  };
  posts_remaining_today?: number;
  rate_limits?: {
    search_interval_minutes: number;
    daily_post_limit: number;
  };
  last_search_time?: string;
  next_search_time?: string;
}

interface QueueResponse {
  mention_id: string;
  response_text: string;
  priority: number;
  queued_at: string;
}

interface Interaction {
  timestamp: string;
  mention_id: string;
  conversation_id: string;
  reply_posted: boolean;
  ai_response: string;
  mention_text: string;
}

const TwitterBotManager: React.FC = () => {
  const baseUrl = (import.meta as any)?.env?.VITE_API_URL ||
    (typeof window !== 'undefined'
      ? `${window.location.protocol}//${window.location.hostname}:8000`
      : 'http://0.0.0.0:8000');
  const [status, setStatus] = useState<TwitterBotStatus | null>(null);
  const [queue, setQueue] = useState<QueueResponse[]>([]);
  const [interactions, setInteractions] = useState<Interaction[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStatus = async () => {
    try {
      const response = await fetch(`${baseUrl}/twitter/status`);
      const data = await response.json();
      if (data.success) {
        setStatus(data.status);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to fetch bot status');
    }
  };

  const fetchQueue = async () => {
    try {
      const response = await fetch(`${baseUrl}/twitter/queue`);
      const data = await response.json();
      if (data.success) {
        setQueue(data.pending_responses || []);
      } else {
        // If bot is not initialized, show empty queue
        if (data.message === 'Bot not initialized') {
          setQueue([]);
        } else {
          console.error('Queue fetch error:', data.message);
        }
      }
    } catch (err) {
      console.error('Failed to fetch queue:', err);
      setQueue([]);
    }
  };

  const fetchInteractions = async () => {
    try {
      const response = await fetch(`${baseUrl}/twitter/interactions?limit=5`);
      const data = await response.json();
      if (data.success) {
        setInteractions(data.interactions || []);
      }
    } catch (err) {
      console.error('Failed to fetch interactions:', err);
    }
  };

  const startBot = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/twitter/start`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchStatus();
        setError(null);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to start bot');
    } finally {
      setLoading(false);
    }
  };

  const stopBot = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/twitter/stop`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchStatus();
        setError(null);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to stop bot');
    } finally {
      setLoading(false);
    }
  };

  const clearQueue = async () => {
    if (!confirm('Are you sure you want to clear all pending responses?')) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/twitter/queue/clear`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchQueue();
        setError(null);
      } else {
        if (data.message === 'Bot not initialized') {
          setError('Cannot clear queue: Bot is not running');
        } else {
          setError(data.message);
        }
      }
    } catch (err) {
      setError('Failed to clear queue');
    } finally {
      setLoading(false);
    }
  };

  const clearInteractions = async () => {
    if (!confirm('Are you sure you want to clear all interaction history? This action cannot be undone.')) {
      return;
    }
    
    setLoading(true);
    try {
      const response = await fetch(`${baseUrl}/twitter/interactions/clear`, { method: 'POST' });
      const data = await response.json();
      if (data.success) {
        await fetchInteractions();
        setError(null);
      } else {
        setError(data.message);
      }
    } catch (err) {
      setError('Failed to clear interactions');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchQueue();
    fetchInteractions();
    
    // Refresh every 30 seconds
    const interval = setInterval(() => {
      fetchStatus();
      fetchQueue();
      fetchInteractions();
    }, 30000);

    return () => clearInterval(interval);
  }, []);

  const formatUptime = (seconds: number | null) => {
    if (!seconds) return 'N/A';
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    return `${hours}h ${minutes}m`;
  };

  const formatTime = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  return (
    <div className="bg-white dark:bg-gray-800 rounded-lg shadow-md p-6 border border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-2xl font-bold text-gray-800 dark:text-white">🤖 Twitter Bot Manager</h2>
        <div className="flex gap-2">
          <button
            onClick={() => {
              fetchStatus();
              fetchQueue();
              fetchInteractions();
            }}
            disabled={loading}
            className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
          >
            Refresh
          </button>
          {status?.is_running ? (
            <button
              onClick={stopBot}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
            >
              {loading ? 'Stopping...' : 'Stop Bot'}
            </button>
          ) : (
            <button
              onClick={startBot}
              disabled={loading}
              className="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded-lg disabled:opacity-50 transition-colors"
            >
              {loading ? 'Starting...' : 'Start Bot'}
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-100 dark:bg-red-900/20 border border-red-400 dark:border-red-600 text-red-700 dark:text-red-300 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {/* Status Section */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
          <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2">Bot Status</h3>
          <div className="flex items-center gap-2">
            <div className={`w-3 h-3 rounded-full ${status?.is_running ? 'bg-green-500' : 'bg-red-500'}`}></div>
            <span className="text-sm text-gray-600 dark:text-gray-300">{status?.is_running ? 'Running' : 'Stopped'}</span>
          </div>
          {status?.uptime_seconds && (
            <p className="text-xs text-gray-600 dark:text-gray-400 mt-1">Uptime: {formatUptime(status.uptime_seconds)}</p>
          )}
          {status?.error_count && status.error_count > 0 && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1">Errors: {status.error_count}</p>
          )}
          {status?.last_error && (
            <p className="text-xs text-red-600 dark:text-red-400 mt-1" title={status.last_error}>
              Last error: {status.last_error.substring(0, 30)}...
            </p>
          )}
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
          <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2">Queue Status</h3>
          {status?.is_running ? (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Pending: <span className="font-semibold text-gray-800 dark:text-white">{status?.queue_stats?.pending || 0}</span>
              </p>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Posted: <span className="font-semibold text-gray-800 dark:text-white">{status?.queue_stats?.posted || 0}</span>
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">Bot not running</p>
          )}
        </div>

        <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
          <h3 className="font-semibold text-gray-700 dark:text-gray-200 mb-2">Daily Limits</h3>
          {status?.is_running ? (
            <>
              <p className="text-sm text-gray-600 dark:text-gray-300">
                Posts Remaining: <span className="font-semibold text-gray-800 dark:text-white">{status?.posts_remaining_today || 0}</span>
              </p>
              <p className="text-xs text-gray-600 dark:text-gray-400">
                Limit: {status?.rate_limits?.daily_post_limit || 17}/day
              </p>
            </>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400">Bot not running</p>
          )}
        </div>
      </div>

      {/* Queue Management */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Response Queue</h3>
          {queue.length > 0 && (
            <button
              onClick={clearQueue}
              disabled={loading}
              className="bg-orange-500 hover:bg-orange-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50 transition-colors"
            >
              Clear Queue
            </button>
          )}
        </div>
        
        {queue.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">
            {status?.is_running ? 'No pending responses in queue' : 'Bot not running - queue unavailable'}
          </p>
        ) : (
          <div className="space-y-2">
            {queue.map((item, index) => (
              <div key={item.mention_id} className="bg-gray-50 dark:bg-gray-700 p-3 rounded border-l-4 border-blue-500 border border-gray-200 dark:border-gray-600">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800 dark:text-white">Mention ID: {item.mention_id}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{item.response_text}</p>
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      Priority: {item.priority} | Queued: {formatTime(item.queued_at)}
                    </p>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Search Timing */}
      {status?.is_running && (
        <div className="mb-6">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white mb-4">Search Timing</h3>
          <div className="bg-gray-50 dark:bg-gray-700 p-4 rounded-lg border border-gray-200 dark:border-gray-600">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Last Search: <span className="font-semibold text-gray-800 dark:text-white">
                    {status.last_search_time ? formatTime(status.last_search_time) : 'Never'}
                  </span>
                </p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-300">
                  Next Search: <span className="font-semibold text-gray-800 dark:text-white">
                    {status.next_search_time ? formatTime(status.next_search_time) : 'Unknown'}
                  </span>
                </p>
              </div>
            </div>
            <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
              Search interval: {status.rate_limits?.search_interval_minutes || 15} minutes
            </p>
          </div>
        </div>
      )}

      {/* Recent Interactions */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-800 dark:text-white">Recent Interactions</h3>
          {interactions.length > 0 && (
            <button
              onClick={clearInteractions}
              disabled={loading}
              className="bg-red-500 hover:bg-red-600 text-white px-3 py-1 rounded text-sm disabled:opacity-50 transition-colors"
            >
              Clear History
            </button>
          )}
        </div>
        {interactions.length === 0 ? (
          <p className="text-gray-500 dark:text-gray-400 text-sm">No recent interactions</p>
        ) : (
          <div className="space-y-3">
            {interactions.map((interaction, index) => (
              <div key={interaction.mention_id} className="bg-gray-50 dark:bg-gray-700 p-3 rounded border border-gray-200 dark:border-gray-600">
                <div className="flex justify-between items-start">
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-800 dark:text-white">{interaction.mention_text}</p>
                    <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{interaction.ai_response}</p>
                    <div className="flex items-center gap-4 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <span>{formatTime(interaction.timestamp)}</span>
                      <span className={`px-2 py-1 rounded ${
                        interaction.reply_posted 
                          ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-300' 
                          : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-300'
                      }`}>
                        {interaction.reply_posted ? 'Posted' : 'Pending'}
                      </span>
                      {interaction.ai_response === "Sorry, I'm currently unavailable." && (
                        <span className="px-2 py-1 rounded bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-300">
                          AI Unavailable
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default TwitterBotManager;
