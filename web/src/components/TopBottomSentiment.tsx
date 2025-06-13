import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { 
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter
} from './ui/card';
import { Badge } from './ui/badge';
import { SentimentGauge } from './ui/sentiment-gauge';
import { formatPercent, cn } from '../lib/utils';

// Types for sentiment data
interface StockSentiment {
  symbol: string;
  company_name?: string;
  sentiment_score: number;
  date: string;
}

interface SentimentResponse {
  top_20: StockSentiment[];
  bottom_20: StockSentiment[];
}

const TopBottomSentiment: React.FC = () => {
  // State for sentiment data
  const [topSentiment, setTopSentiment] = useState<StockSentiment[]>([]);
  const [bottomSentiment, setBottomSentiment] = useState<StockSentiment[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [overallSentiment, setOverallSentiment] = useState<number>(0);
  const [selectedStock, setSelectedStock] = useState<StockSentiment | null>(null);

  // Fetch sentiment data
  useEffect(() => {
    const fetchSentimentData = async () => {
      try {
        setLoading(true);
        
        // In a real implementation, fetch from the API
        const response = await axios.get<SentimentResponse>(
          `${import.meta.env.VITE_API_URL || ''}/api/v1/stocks/top-bottom-20`
        );
        
        setTopSentiment(response.data.top_20);
        setBottomSentiment(response.data.bottom_20);
        
        // Calculate overall market sentiment (average of top and bottom)
        const allScores = [...response.data.top_20, ...response.data.bottom_20].map(s => s.sentiment_score);
        const avgSentiment = allScores.reduce((sum, score) => sum + score, 0) / allScores.length;
        setOverallSentiment(avgSentiment);
        
        // Set the first top sentiment stock as selected by default
        if (response.data.top_20.length > 0) {
          setSelectedStock(response.data.top_20[0]);
        }
        
        setError(null);
      } catch (err) {
        console.error('Error fetching sentiment data:', err);
        setError('Failed to load sentiment data. Please try again later.');
      } finally {
        setLoading(false);
      }
    };
    
    fetchSentimentData();
  }, []);

  // Handle stock selection for detailed view
  const handleStockSelect = (stock: StockSentiment) => {
    setSelectedStock(stock);
  };

  // Get sentiment label based on score
  const getSentimentLabel = (score: number): string => {
    if (score >= 0.7) return "Very Positive";
    if (score >= 0.3) return "Positive";
    if (score >= -0.3) return "Neutral";
    if (score >= -0.7) return "Negative";
    return "Very Negative";
  };

  // Get color class based on sentiment score
  const getSentimentColorClass = (score: number): string => {
    if (score >= 0.3) return "text-success";
    if (score >= -0.3) return "text-amber-500";
    return "text-destructive";
  };

  // Render loading state
  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Market Sentiment</CardTitle>
          <CardDescription>Stock sentiment analysis</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center justify-center min-h-[300px]">
          <div className="flex flex-col items-center">
            <div className="w-12 h-12 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
            <p className="mt-4 text-muted-foreground">Loading sentiment data...</p>
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
          <CardTitle>Market Sentiment</CardTitle>
          <CardDescription>Stock sentiment analysis</CardDescription>
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
        <CardTitle>Market Sentiment</CardTitle>
        <CardDescription>Stock sentiment analysis based on news and social media</CardDescription>
      </CardHeader>
      
      <CardContent>
        <div className="mb-8 flex flex-col items-center">
          <h3 className="text-lg font-semibold mb-4">Overall Market Sentiment</h3>
          <SentimentGauge 
            value={overallSentiment} 
            size={180}
            showLabels={true}
          />
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Selected Stock Detail */}
          {selectedStock && (
            <div className="lg:col-span-2 mb-4">
              <Card className="overflow-hidden">
                <CardHeader className={cn(
                  "border-b",
                  selectedStock.sentiment_score >= 0.3 ? "bg-green-50 dark:bg-green-900/20" : 
                  selectedStock.sentiment_score <= -0.3 ? "bg-red-50 dark:bg-red-900/20" : 
                  "bg-amber-50 dark:bg-amber-900/20"
                )}>
                  <div className="flex justify-between items-center">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        {selectedStock.symbol}
                        <Badge variant={
                          selectedStock.sentiment_score >= 0.3 ? "success" : 
                          selectedStock.sentiment_score <= -0.3 ? "destructive" : 
                          "warning"
                        }>
                          {getSentimentLabel(selectedStock.sentiment_score)}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="mt-1">
                        {selectedStock.company_name || "Company Name Unavailable"}
                      </CardDescription>
                    </div>
                    <div className="flex items-center">
                      <SentimentGauge 
                        value={selectedStock.sentiment_score} 
                        size={80} 
                        showLabels={false}
                      />
                    </div>
                  </div>
                </CardHeader>
                <CardContent className="pt-4">
                  <p className="text-sm text-muted-foreground">
                    Sentiment is calculated based on news articles, social media mentions, and analyst reports.
                    This score represents the aggregated sentiment for {selectedStock.symbol} as of {new Date(selectedStock.date).toLocaleDateString()}.
                  </p>
                </CardContent>
              </Card>
            </div>
          )}
          
          {/* Top Sentiment Stocks */}
          <div>
            <h3 className="text-lg font-semibold text-success mb-4">Most Positive Sentiment</h3>
            <div className="space-y-2">
              {topSentiment.slice(0, 5).map((stock) => (
                <div 
                  key={stock.symbol} 
                  className={cn(
                    "p-3 rounded-md cursor-pointer transition-colors",
                    selectedStock?.symbol === stock.symbol 
                      ? "bg-primary/10 border border-primary/30" 
                      : "hover:bg-muted"
                  )}
                  onClick={() => handleStockSelect(stock)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span className="font-medium">{stock.symbol}</span>
                      {stock.company_name && (
                        <span className="ml-2 text-xs text-muted-foreground hidden sm:inline">
                          {stock.company_name.length > 20 
                            ? `${stock.company_name.substring(0, 20)}...` 
                            : stock.company_name}
                        </span>
                      )}
                    </div>
                    <div className={cn("font-medium", getSentimentColorClass(stock.sentiment_score))}>
                      {formatPercent(stock.sentiment_score, false)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
          
          {/* Bottom Sentiment Stocks */}
          <div>
            <h3 className="text-lg font-semibold text-destructive mb-4">Most Negative Sentiment</h3>
            <div className="space-y-2">
              {bottomSentiment.slice(0, 5).map((stock) => (
                <div 
                  key={stock.symbol} 
                  className={cn(
                    "p-3 rounded-md cursor-pointer transition-colors",
                    selectedStock?.symbol === stock.symbol 
                      ? "bg-primary/10 border border-primary/30" 
                      : "hover:bg-muted"
                  )}
                  onClick={() => handleStockSelect(stock)}
                >
                  <div className="flex justify-between items-center">
                    <div className="flex items-center">
                      <span className="font-medium">{stock.symbol}</span>
                      {stock.company_name && (
                        <span className="ml-2 text-xs text-muted-foreground hidden sm:inline">
                          {stock.company_name.length > 20 
                            ? `${stock.company_name.substring(0, 20)}...` 
                            : stock.company_name}
                        </span>
                      )}
                    </div>
                    <div className={cn("font-medium", getSentimentColorClass(stock.sentiment_score))}>
                      {formatPercent(stock.sentiment_score, false)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
      
      <CardFooter className="text-xs text-muted-foreground justify-end">
        Sentiment data updated daily based on news and social media analysis
      </CardFooter>
    </Card>
  );
};

export default TopBottomSentiment;
