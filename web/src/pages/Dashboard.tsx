import React from 'react';
import TopBottomSentiment from '../components/TopBottomSentiment';

const Dashboard: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8">
      <header className="mb-8">
        <h1 className="text-3xl font-bold text-gray-800">NexusSentinel Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Real-time stock market intelligence and sentiment analysis
        </p>
      </header>

      <div className="grid grid-cols-1 gap-8">
        {/* Market Sentiment Analysis Section */}
        <section>
          <TopBottomSentiment />
        </section>

        {/* Additional dashboard sections can be added here */}
        <section className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-2xl font-bold text-gray-800 mb-6">Market Overview</h2>
          <div className="h-64 bg-gray-100 rounded-lg flex items-center justify-center">
            <p className="text-gray-500">Market overview charts will be displayed here</p>
          </div>
        </section>
      </div>
    </div>
  );
};

export default Dashboard;
