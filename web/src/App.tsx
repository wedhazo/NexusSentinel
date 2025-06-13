import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Navbar from './components/Navbar';
import Footer from './components/Footer';

const App: React.FC = () => {
  return (
    <Router>
      <div className="flex flex-col min-h-screen bg-gray-50">
        {/* Global Navbar */}
        <Navbar />

      {/* Main Content */}
      <main className="flex-grow container mx-auto px-4 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          {/* Future routes can be added here */}
        </Routes>
      </main>

        {/* Global Footer */}
        <Footer />
    </div>
    </Router>
  );
};

export default App;
