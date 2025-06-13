import React, { useState } from 'react';
import {
  useTopMovers,
  useBottomMovers,
  StockMover,
} from '../lib/api';
import { formatCurrency, formatPercent, cn } from '../lib/utils';
import { HorizontalBarChart } from './ui/horizontal-bar-chart';
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from './ui/card';

type ViewMode = 'split' | 'gainers' | 'losers';

const TopBottomMovers: React.FC = () => {
  // State for view mode
  const [viewMode, setViewMode] = useState<ViewMode>('split');
  
  // Queries
  const {
    data: topData,
    isLoading: topLoading,
    error: topError,
  } = useTopMovers();

  const {
    data: bottomData,
    isLoading: bottomLoading,
    error: bottomError,
  } = useBottomMovers();

  // Derived state
  const loading = topLoading || bottomLoading;
  const error =
    (topError as Error)?.message ||
    (bottomError as Error)?.message ||
    null;

  const topMovers: StockMover[] = topData?.movers ?? [];
  const bottomMovers: StockMover[] = bottomData?.movers ?? [];
  const tradeDate = topData
    ? new Date(topData.date).toLocaleDateString()
    : '';

  // Prepare data for horizontal bar chart
  const topMoversChartData = topMovers.map(stock => ({
    label: stock.symbol,
    value: stock.percent_change,
    color: 'hsl(var(--success, 142.1 76.2% 36.3%))',
    metadata: {
      name: stock.company_name,
      price: stock.current_price,
      change: stock.current_price - stock.previous_price,
    }
  }));

  const bottomMoversChartData = bottomMovers.map(stock => ({
    label: stock.symbol,
    value: stock.percent_change,
    color: 'hsl(var(--destructive))',
    metadata: {
      name: stock.company_name,
      price: stock.current_price,
      change: stock.current_price - stock.previous_price,
    }
  }));

  // Format numbers for display
  const formatPrice = (price: number): string => {
    return formatCurrency(price, 'USD');
  };

  // Render loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Movers</CardTitle>
          <CardDescription>Top gainers and losers by percentage change</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-muted-foreground">Loading market movers...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Render error state
  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardHeader>
          <CardTitle>Market Movers</CardTitle>
          <CardDescription>Top gainers and losers by percentage change</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center min-h-[300px]">
          <svg 
            className="w-12 h-12 text-destructive mx-auto mb-4" 
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
          <h3 className="text-lg font-medium text-destructive mb-2">Error</h3>
          <p className="text-destructive/80">{error}</p>
          <button 
            onClick={() => window.location.reload()} 
            className="mt-4 px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 transition-colors"
          >
            Try Again
          </button>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-4">
          <div>
            <CardTitle>Market Movers</CardTitle>
            <CardDescription>{tradeDate ? `Trading data for: ${tradeDate}` : ''}</CardDescription>
          </div>
          
          {/* View mode tabs */}
          <div className="flex rounded-md border border-border overflow-hidden">
            <button
              onClick={() => setViewMode('split')}
              className={cn(
                "px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === 'split' 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-card hover:bg-muted"
              )}
            >
              Split View
            </button>
            <button
              onClick={() => setViewMode('gainers')}
              className={cn(
                "px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === 'gainers' 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-card hover:bg-muted"
              )}
            >
              Top Gainers
            </button>
            <button
              onClick={() => setViewMode('losers')}
              className={cn(
                "px-3 py-1.5 text-sm font-medium transition-colors",
                viewMode === 'losers' 
                  ? "bg-primary text-primary-foreground" 
                  : "bg-card hover:bg-muted"
              )}
            >
              Top Losers
            </button>
          </div>
        </div>
      </CardHeader>
      
      <CardContent>
        {viewMode === 'split' && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Top Gainers */}
            <div>
              <h3 className="text-lg font-semibold text-success mb-4">Top Gainers</h3>
              {topMovers.length > 0 ? (
                <div className="space-y-3">
                  {topMovers.map((stock) => (
                    <Card key={stock.symbol} className="p-3 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-center mb-1">
                        <div className="flex items-center">
                          <span className="font-bold">{stock.symbol}</span>
                          <span className="ml-2 text-sm text-muted-foreground hidden sm:inline">
                            {stock.company_name.length > 20 
                              ? `${stock.company_name.substring(0, 20)}...` 
                              : stock.company_name}
                          </span>
                        </div>
                        <div className="text-success font-medium">
                          {formatPercent(stock.percent_change / 100, true)}
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">{formatPrice(stock.current_price)}</span>
                        <span className="text-success">
                          +{formatPrice(stock.current_price - stock.previous_price)}
                        </span>
                      </div>
                      
                      {/* Percentage Bar Chart */}
                      <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-success rounded-full" 
                          style={{ 
                            width: `${Math.min(Math.abs(stock.percent_change) / 20, 1) * 100}%`
                          }}
                        ></div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No data available
                </div>
              )}
            </div>
            
            {/* Top Losers */}
            <div>
              <h3 className="text-lg font-semibold text-destructive mb-4">Top Losers</h3>
              {bottomMovers.length > 0 ? (
                <div className="space-y-3">
                  {bottomMovers.map((stock) => (
                    <Card key={stock.symbol} className="p-3 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-center mb-1">
                        <div className="flex items-center">
                          <span className="font-bold">{stock.symbol}</span>
                          <span className="ml-2 text-sm text-muted-foreground hidden sm:inline">
                            {stock.company_name.length > 20 
                              ? `${stock.company_name.substring(0, 20)}...` 
                              : stock.company_name}
                          </span>
                        </div>
                        <div className="text-destructive font-medium">
                          {formatPercent(stock.percent_change / 100, true)}
                        </div>
                      </div>
                      
                      <div className="flex justify-between items-center text-sm">
                        <span className="text-muted-foreground">{formatPrice(stock.current_price)}</span>
                        <span className="text-destructive">
                          {formatPrice(stock.current_price - stock.previous_price)}
                        </span>
                      </div>
                      
                      {/* Percentage Bar Chart */}
                      <div className="mt-2 h-1.5 bg-muted rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-destructive rounded-full" 
                          style={{ 
                            width: `${Math.min(Math.abs(stock.percent_change) / 20, 1) * 100}%`
                          }}
                        ></div>
                      </div>
                    </Card>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No data available
                </div>
              )}
            </div>
          </div>
        )}
        
        {viewMode === 'gainers' && (
          <div className="w-full">
            <h3 className="text-lg font-semibold text-success mb-4">Top Gainers</h3>
            {topMoversChartData.length > 0 ? (
              <HorizontalBarChart 
                data={topMoversChartData}
                height={500}
                valueFormatter={(value) => formatPercent(value / 100, true)}
                positiveColor="hsl(var(--success, 142.1 76.2% 36.3%))"
                valueLabel="Percent Change"
              />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No data available
              </div>
            )}
          </div>
        )}
        
        {viewMode === 'losers' && (
          <div className="w-full">
            <h3 className="text-lg font-semibold text-destructive mb-4">Top Losers</h3>
            {bottomMoversChartData.length > 0 ? (
              <HorizontalBarChart 
                data={bottomMoversChartData}
                height={500}
                valueFormatter={(value) => formatPercent(value / 100, true)}
                negativeColor="hsl(var(--destructive))"
                valueLabel="Percent Change"
              />
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                No data available
              </div>
            )}
          </div>
        )}
      </CardContent>
      
      <CardFooter className="text-xs text-muted-foreground justify-end">
        Data refreshes every market day
      </CardFooter>
    </Card>
  );
};

export default TopBottomMovers;
