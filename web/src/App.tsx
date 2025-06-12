import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Dashboard from './pages/Dashboard';

const App: React.FC = () => {
  return (
    <Router>
      <div className="min-h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <header className="bg-blue-600 text-white shadow-md">
        <div className="container mx-auto px-4 py-6">
          <div className="flex justify-between items-center">
            <h1 className="text-3xl font-bold">NexusSentinel</h1>
            <nav className="space-x-4">
              <Link
                to="/"
                className="px-4 py-2 rounded hover:bg-blue-700 transition-colors"
              >
                Dashboard
              </Link>
              {/* Future routes can be added here */}
            </nav>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* Future routes can be added here */}
        </Routes>
      </main>

      {/* Footer */}
      <footer className="bg-gray-800 text-white py-6">
        <div className="container mx-auto px-4">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="mb-4 md:mb-0">
              <h2 className="text-xl font-bold">NexusSentinel</h2>
              <p className="text-gray-400">Stock-market intelligence & sentiment-analysis platform</p>
            </div>
            <div className="text-gray-400">
              &copy; {new Date().getFullYear()} NexusSentinel. All rights reserved.
            </div>
          </div>
        </div>
      </footer>
    </div>
    </Router>
  );
};

export default App;
