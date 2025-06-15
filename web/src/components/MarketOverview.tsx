import React, { useState, useEffect } from 'react';
import { api } from '../api/apiClient';
import { 
  LineChart, 
  Line, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts';

// Types for market data
interface MarketIndex {
  name: string;
  symbol: string;
  currentValue: number;
  change: number;
  changePercent: number;
  color: string;
}

interface HistoricalDataPoint {
  date: string;
  sp500: number;
  nasdaq: number;
  dowJones: number;
}

const MarketOverview: React.FC = () => {
  // State for market indices and historical data
  const [indices, setIndices] = useState<MarketIndex[]>([]);
  const [historicalData, setHistoricalData] = useState<HistoricalDataPoint[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<string>('1M'); // Default to 1 month

  // Fetch market data
  useEffect(() => {
    const fetchMarketData = async () => {
      try {
        setLoading(true);

        // Fetch data from backend API
        const response = await api.get<{
          indices: MarketIndex[];
          historical: HistoricalDataPoint[];
        }>('/market/overview');

        setIndices(response.indices);
        setHistoricalData(response.historical);
        setError(null);
      } catch (err) {
        console.error('Error fetching market data:', err);
        setError('Failed to load market data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchMarketData();
  }, []);

  // Filter historical data based on selected time range
  const getFilteredData = () => {
    if (historicalData.length === 0) return [];
    
    const today = new Date();
    let daysToShow = 30; // Default to 1 month
    
    switch (timeRange) {
      case '1W':
        daysToShow = 7;
        break;
      case '1M':
        daysToShow = 30;
        break;
      case '3M':
        daysToShow = 90;
        break;
      case '1Y':
        daysToShow = 365;
        break;
      default:
        daysToShow = 30;
    }
    
    // Only show the most recent days based on the selected range
    return historicalData.slice(-Math.min(daysToShow, historicalData.length));
  };

  // Format numbers with commas and 2 decimal places
  const formatNumber = (num: number): string => {
    return num.toLocaleString(undefined, { 
      minimumFractionDigits: 2, 
      maximumFractionDigits: 2 
    });
  };

  // Render loading state
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center">
          <div className="w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="mt-4 text-gray-600">Loading market data...</p>
        </div>
      </div>
    );
  }

  // Render error state
  if (error) {
    return (
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
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-800">Market Overview</h2>
        <div className="flex space-x-2">
          {['1W', '1M', '3M', '1Y'].map((range) => (
            <button
              key={range}
              onClick={() => setTimeRange(range)}
              className={`px-3 py-1 rounded-md text-sm font-medium ${
                timeRange === range
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {range}
            </button>
          ))}
        </div>
      </div>
      
      {/* Market Indices */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {indices.map((index) => (
          <div 
            key={index.symbol} 
            className="bg-gray-50 rounded-lg p-4 border border-gray-100"
          >
            <h3 className="text-sm font-medium text-gray-500">{index.name}</h3>
            <p className="text-xl font-bold mt-1">{formatNumber(index.currentValue)}</p>
            <div className={`flex items-center mt-1 ${index.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              <span className="text-sm font-medium">
                {index.change >= 0 ? '+' : ''}{formatNumber(index.change)} ({index.change >= 0 ? '+' : ''}{index.changePercent.toFixed(2)}%)
              </span>
              <svg 
                className="w-4 h-4 ml-1" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 24 24" 
                xmlns="http://www.w3.org/2000/svg"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth="2" 
                  d={index.change >= 0 
                    ? "M5 10l7-7m0 0l7 7m-7-7v18" 
                    : "M19 14l-7 7m0 0l-7-7m7 7V3"}
                />
              </svg>
            </div>
          </div>
        ))}
      </div>
      
      {/* Market Chart */}
      <div className="h-80 mt-6">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart
            data={getFilteredData()}
            margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
          >
            <CartesianGrid strokeDasharray="3 3" />
            <XAxis 
              dataKey="date" 
              tickFormatter={(date) => {
                const d = new Date(date);
                return `${d.getMonth() + 1}/${d.getDate()}`;
              }}
            />
            <YAxis />
            <Tooltip 
              formatter={(value: number) => [`${formatNumber(value)}`, '']}
              labelFormatter={(label) => `Date: ${new Date(label).toLocaleDateString()}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="sp500"
              name="S&P 500"
              stroke="#4f46e5"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="nasdaq"
              name="NASDAQ"
              stroke="#06b6d4"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
            <Line
              type="monotone"
              dataKey="dowJones"
              name="Dow Jones"
              stroke="#8b5cf6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      
      {/* Market Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-6">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-100">
          <h3 className="text-sm font-medium text-blue-700">Market Volatility</h3>
          <p className="text-2xl font-bold text-blue-800 mt-1">Moderate</p>
          <p className="text-sm text-blue-600 mt-1">VIX: 18.45 (-0.32)</p>
        </div>
        
        <div className="bg-purple-50 rounded-lg p-4 border border-purple-100">
          <h3 className="text-sm font-medium text-purple-700">Trading Volume</h3>
          <p className="text-2xl font-bold text-purple-800 mt-1">4.2B</p>
          <p className="text-sm text-purple-600 mt-1">+12% above average</p>
        </div>
        
        <div className="bg-green-50 rounded-lg p-4 border border-green-100">
          <h3 className="text-sm font-medium text-green-700">Advancing Stocks</h3>
          <p className="text-2xl font-bold text-green-800 mt-1">62%</p>
          <p className="text-sm text-green-600 mt-1">Bullish momentum</p>
        </div>
      </div>
    </div>
  );
};

export default MarketOverview;
