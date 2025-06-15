import React, { useState, useEffect } from "react";
import { getAlerts, createAlert, deleteAlert, checkAlerts } from "../api/alertsApi";
import { AlertResponse } from "../types/apiTypes";

const Alerts: React.FC = () => {
  // State variables
  const [alerts, setAlerts] = useState<AlertResponse[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [symbol, setSymbol] = useState<string>("");
  const [threshold, setThreshold] = useState<string>("0.5");
  const [direction, setDirection] = useState<"above" | "below">("above");
  const [creating, setCreating] = useState<boolean>(false);
  const [createError, setCreateError] = useState<string | null>(null);
  const [deletingIds, setDeletingIds] = useState<Set<number>>(new Set());
  const [checking, setChecking] = useState<boolean>(false);
  const [checkMessage, setCheckMessage] = useState<string | null>(null);

  // Fetch alerts when component mounts
  useEffect(() => {
    const fetchAlerts = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await getAlerts();
        setAlerts(data);
      } catch (err: any) {
        console.error("Error fetching alerts:", err);
        setError(err.message || "Failed to load alerts. Please try again later.");
      } finally {
        setLoading(false);
      }
    };

    fetchAlerts();
  }, []);

  // Handle creating a new alert
  const handleCreateAlert = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!symbol.trim()) {
      setCreateError("Please enter a stock symbol");
      return;
    }

    const thresholdValue = parseFloat(threshold);
    if (isNaN(thresholdValue) || thresholdValue < -1 || thresholdValue > 1) {
      setCreateError("Threshold must be a number between -1.0 and 1.0");
      return;
    }

    try {
      setCreating(true);
      setCreateError(null);
      const newAlert = await createAlert(symbol.trim(), thresholdValue, direction);
      setAlerts(prev => [newAlert, ...prev]);
      
      // Reset form
      setSymbol("");
      setThreshold("0.5");
      setDirection("above");
    } catch (err: any) {
      console.error("Error creating alert:", err);
      setCreateError(err.message || "Failed to create alert. Please try again.");
    } finally {
      setCreating(false);
    }
  };

  // Handle deleting an alert
  const handleDeleteAlert = async (id: number) => {
    try {
      setDeletingIds(prev => new Set(prev).add(id));
      await deleteAlert(id);
      setAlerts(prev => prev.filter(alert => alert.id !== id));
    } catch (err: any) {
      console.error(`Error deleting alert ${id}:`, err);
      // Show error in a toast or alert
    } finally {
      setDeletingIds(prev => {
        const updated = new Set(prev);
        updated.delete(id);
        return updated;
      });
    }
  };

  // Handle checking alerts
  const handleCheckAlerts = async () => {
    try {
      setChecking(true);
      setCheckMessage(null);
      const triggered = await checkAlerts();
      
      if (triggered.length > 0) {
        // Update alerts that were triggered
        setAlerts(prev => prev.map(alert => {
          const triggeredAlert = triggered.find(t => t.id === alert.id);
          return triggeredAlert || alert;
        }));
        setCheckMessage(`${triggered.length} alert(s) were triggered!`);
      } else {
        setCheckMessage("No alerts were triggered.");
      }
      
      // Refresh all alerts to get latest data
      const updatedAlerts = await getAlerts();
      setAlerts(updatedAlerts);
    } catch (err: any) {
      console.error("Error checking alerts:", err);
      setCheckMessage(`Error checking alerts: ${err.message || "Unknown error"}`);
    } finally {
      setChecking(false);
      // Clear message after 5 seconds
      setTimeout(() => setCheckMessage(null), 5000);
    }
  };

  // Format threshold for display
  const formatThreshold = (value: number): string => {
    return value.toFixed(2);
  };

  // Get CSS class for sentiment score
  const getSentimentClass = (score?: number): string => {
    if (score === undefined || score === null) return "text-gray-500";
    if (score > 0.3) return "text-green-600 font-medium";
    if (score > 0) return "text-green-500";
    if (score > -0.3) return "text-red-500";
    return "text-red-600 font-medium";
  };

  // Format sentiment score for display
  const formatSentiment = (score?: number): string => {
    if (score === undefined || score === null) return "N/A";
    return score.toFixed(2);
  };

  // Get threshold class based on direction and value
  const getThresholdClass = (threshold: number, direction: string): string => {
    if (direction === "above") {
      return threshold > 0 ? "text-green-600" : "text-red-600";
    } else {
      return threshold > 0 ? "text-red-600" : "text-green-600";
    }
  };

  // Render loading state
  if (loading && alerts.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Sentiment Alerts</h1>
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-gray-600">Loading alerts...</p>
          </div>
        </div>
      </div>
    );
  }

  // Render error state
  if (error && alerts.length === 0) {
    return (
      <div className="container mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold text-gray-800 mb-6">Sentiment Alerts</h1>
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <svg 
            className="w-12 h-12 text-red-500 mx-auto mb-4" 
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24" 
            xmlns="http://www.w3.org/2000/svg"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth="2" 
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-lg font-medium text-red-800 mb-2">Error</h3>
          <p className="text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Sentiment Alerts</h1>
      
      {/* Create Alert Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-8">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Create New Alert</h2>
        <form onSubmit={handleCreateAlert} className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label htmlFor="symbol" className="block text-sm font-medium text-gray-700 mb-1">
                Stock Symbol
              </label>
              <input
                id="symbol"
                type="text"
                value={symbol}
                onChange={(e) => setSymbol(e.target.value)}
                placeholder="e.g., AAPL"
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={creating}
              />
            </div>
            
            <div>
              <label htmlFor="threshold" className="block text-sm font-medium text-gray-700 mb-1">
                Threshold (-1.0 to 1.0)
              </label>
              <input
                id="threshold"
                type="number"
                step="0.1"
                min="-1"
                max="1"
                value={threshold}
                onChange={(e) => setThreshold(e.target.value)}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={creating}
              />
            </div>
            
            <div>
              <label htmlFor="direction" className="block text-sm font-medium text-gray-700 mb-1">
                Direction
              </label>
              <select
                id="direction"
                value={direction}
                onChange={(e) => setDirection(e.target.value as "above" | "below")}
                className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                disabled={creating}
              >
                <option value="above">Above Threshold</option>
                <option value="below">Below Threshold</option>
              </select>
            </div>
          </div>
          
          {createError && (
            <div className="text-sm text-red-600">{createError}</div>
          )}
          
          <div className="flex justify-end">
            <button
              type="submit"
              disabled={creating || !symbol.trim()}
              className={`px-6 py-2 rounded-md text-white font-medium ${
                creating || !symbol.trim()
                  ? "bg-blue-300 cursor-not-allowed"
                  : "bg-blue-600 hover:bg-blue-700"
              }`}
            >
              {creating ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  <span>Creating...</span>
                </div>
              ) : (
                "Create Alert"
              )}
            </button>
          </div>
        </form>
      </div>
      
      {/* Alert Management */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-xl font-semibold text-gray-800">Your Alerts</h2>
          <div>
            <button
              onClick={handleCheckAlerts}
              disabled={checking || alerts.length === 0}
              className={`px-4 py-2 rounded-md text-white font-medium ${
                checking || alerts.length === 0
                  ? "bg-gray-300 cursor-not-allowed"
                  : "bg-green-600 hover:bg-green-700"
              }`}
            >
              {checking ? (
                <div className="flex items-center">
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin mr-2"></div>
                  <span>Checking...</span>
                </div>
              ) : (
                "Check Alerts Now"
              )}
            </button>
          </div>
        </div>
        
        {/* Check message */}
        {checkMessage && (
          <div className={`mb-4 p-3 rounded-lg ${
            checkMessage.includes("Error") 
              ? "bg-red-50 text-red-700 border border-red-200" 
              : "bg-green-50 text-green-700 border border-green-200"
          }`}>
            {checkMessage}
          </div>
        )}
        
        {/* Alerts Table */}
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Alert Condition
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Sentiment
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th scope="col" className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Created
                </th>
                <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={6} className="px-6 py-12 text-center text-gray-500">
                    <svg 
                      className="w-12 h-12 text-gray-300 mx-auto mb-4" 
                      fill="none" 
                      stroke="currentColor" 
                      viewBox="0 0 24 24" 
                      xmlns="http://www.w3.org/2000/svg"
                    >
                      <path 
                        strokeLinecap="round" 
                        strokeLinejoin="round" 
                        strokeWidth="2" 
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                      />
                    </svg>
                    <p className="text-lg">No alerts created yet</p>
                    <p className="text-sm mt-2">Create an alert using the form above</p>
                  </td>
                </tr>
              ) : (
                alerts.map((alert) => (
                  <tr key={alert.id} className={`${alert.triggered ? "bg-yellow-50" : "hover:bg-gray-50"}`}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-lg font-bold text-blue-600">{alert.symbol}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex items-center">
                        <span className="mr-2">Sentiment</span>
                        <span className={`font-medium ${getThresholdClass(alert.threshold, alert.direction)}`}>
                          {alert.direction === "above" ? ">" : "<"} {formatThreshold(alert.threshold)}
                        </span>
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className={`text-sm ${getSentimentClass(alert.current_sentiment)}`}>
                        {alert.current_sentiment !== undefined && alert.current_sentiment > 0 ? "+" : ""}
                        {formatSentiment(alert.current_sentiment)}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {alert.triggered ? (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
                          </svg>
                          Triggered
                        </span>
                      ) : (
                        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                          <svg className="w-4 h-4 mr-1" fill="currentColor" viewBox="0 0 20 20" xmlns="http://www.w3.org/2000/svg">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                          </svg>
                          Active
                        </span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-500">
                        {new Date(alert.created_at).toLocaleDateString("en-US", {
                          year: "numeric",
                          month: "short",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit"
                        })}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <button
                        onClick={() => handleDeleteAlert(alert.id)}
                        disabled={deletingIds.has(alert.id)}
                        className={`px-3 py-1 rounded-md text-sm font-medium ${
                          deletingIds.has(alert.id)
                            ? "bg-gray-300 text-gray-500 cursor-not-allowed"
                            : "bg-red-100 text-red-600 hover:bg-red-200"
                        }`}
                      >
                        {deletingIds.has(alert.id) ? (
                          <div className="flex items-center">
                            <div className="w-3 h-3 border-2 border-red-600 border-t-transparent rounded-full animate-spin mr-1"></div>
                            <span>Deleting...</span>
                          </div>
                        ) : (
                          "Delete"
                        )}
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
      
      {/* Loading indicator when refreshing */}
      {loading && alerts.length > 0 && (
        <div className="flex justify-center mt-6">
          <div className="flex items-center">
            <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mr-2"></div>
            <span className="text-sm text-gray-600">Refreshing alerts...</span>
          </div>
        </div>
      )}
      
      {/* Error message when refresh fails */}
      {error && alerts.length > 0 && (
        <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg">
          <p className="text-sm text-red-600">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-2 text-sm text-red-700 hover:text-red-800 underline"
          >
            Refresh page
          </button>
        </div>
      )}
    </div>
  );
};

export default Alerts;
