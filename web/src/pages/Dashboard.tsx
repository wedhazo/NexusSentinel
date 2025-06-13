import React from 'react';
import TopBottomSentiment from '../components/TopBottomSentiment';
import MarketOverview from '../components/MarketOverview';
import NewsHeadlines from '../components/NewsHeadlines';
import StockSearch from '../components/StockSearch';

const Dashboard: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">NexusSentinel Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Real-time stock market intelligence and sentiment analysis
        </p>
      </header>

      {/* Welcome / Search section */}
      <section className="mb-10">
        <h2 className="text-xl font-semibold text-gray-800 mb-4">Find a stock</h2>
        <StockSearch />
      </section>

      {/* Main dashboard grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
        {/* Market Overview */}
        <section className="order-2 md:order-1">
          <MarketOverview />
        </section>

        {/* Market Sentiment Analysis */}
        <section className="order-1 md:order-2">
          <TopBottomSentiment />
        </section>
      </div>

      {/* News Headlines – full width */}
      <section className="mt-8">
        <NewsHeadlines />
      </section>
    </div>
  );
};

export default Dashboard;
