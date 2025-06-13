import React from 'react';
import { Link } from 'react-router-dom';

const Footer: React.FC = () => {
  const currentYear = new Date().getFullYear();
  
  // Footer navigation links
  const footerLinks = [
    { name: 'Home', path: '/' },
    { name: 'About', path: '/about' },
    { name: 'Stocks', path: '/stocks' },
    { name: 'Sentiment Analysis', path: '/sentiment' },
    { name: 'Watchlists', path: '/watchlists' },
    { name: 'API Documentation', path: '/docs' },
  ];
  
  // Legal links
  const legalLinks = [
    { name: 'Privacy Policy', path: '/privacy' },
    { name: 'Terms of Service', path: '/terms' },
    { name: 'Cookie Policy', path: '/cookies' },
  ];
  
  // Social media links
  const socialLinks = [
    { 
      name: 'Twitter',
      path: 'https://twitter.com/nexussentinel',
      icon: (
        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M8.29 20.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0022 5.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.072 4.072 0 012.8 9.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 012 18.407a11.616 11.616 0 006.29 1.84" />
        </svg>
      ),
    },
    { 
      name: 'LinkedIn',
      path: 'https://linkedin.com/company/nexussentinel',
      icon: (
        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
          <path d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
        </svg>
      ),
    },
    { 
      name: 'GitHub',
      path: 'https://github.com/wedhazo/NexusSentinel',
      icon: (
        <svg className="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
        </svg>
      ),
    },
  ];

  return (
    <footer className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Top section with logo and navigation */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          {/* Logo and description */}
          <div className="col-span-1 md:col-span-1">
            <div className="flex items-center">
              <svg 
                className="h-8 w-8 text-blue-600 dark:text-blue-400" 
                viewBox="0 0 24 24" 
                fill="currentColor"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" />
              </svg>
              <span className="ml-2 text-xl font-bold text-gray-900 dark:text-white">NexusSentinel</span>
            </div>
            <p className="mt-4 text-sm text-gray-600 dark:text-gray-300">
              Stock-market intelligence & sentiment-analysis platform powered by FastAPI, PostgreSQL and SQLAlchemy.
            </p>
          </div>
          
          {/* Navigation links */}
          <div className="col-span-1 md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider mb-4">
              Navigation
            </h3>
            <ul className="space-y-2">
              {footerLinks.slice(0, 3).map((link) => (
                <li key={link.path}>
                  <Link 
                    to={link.path}
                    className="text-base text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="col-span-1 md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider mb-4">
              Resources
            </h3>
            <ul className="space-y-2">
              {footerLinks.slice(3).map((link) => (
                <li key={link.path}>
                  <Link 
                    to={link.path}
                    className="text-base text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
                  >
                    {link.name}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
          
          {/* Newsletter signup */}
          <div className="col-span-1 md:col-span-1">
            <h3 className="text-sm font-semibold text-gray-500 dark:text-gray-300 uppercase tracking-wider mb-4">
              Subscribe to our newsletter
            </h3>
            <p className="text-sm text-gray-600 dark:text-gray-300 mb-4">
              Get the latest market insights and sentiment analysis delivered to your inbox.
            </p>
            <form className="flex flex-col sm:flex-row gap-2">
              <input
                type="email"
                placeholder="Enter your email"
                className="px-4 py-2 text-sm border border-gray-300 dark:border-gray-600 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                required
              />
              <button
                type="submit"
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Subscribe
              </button>
            </form>
          </div>
        </div>
        
        {/* Middle section with social links */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-8 mb-8">
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="flex space-x-6 mb-4 md:mb-0">
              {socialLinks.map((link) => (
                <a
                  key={link.name}
                  href={link.path}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-gray-500 hover:text-blue-600 dark:text-gray-400 dark:hover:text-blue-400"
                  aria-label={link.name}
                >
                  {link.icon}
                </a>
              ))}
            </div>
            <div className="flex space-x-6">
              {legalLinks.map((link) => (
                <Link
                  key={link.name}
                  to={link.path}
                  className="text-sm text-gray-600 dark:text-gray-300 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  {link.name}
                </Link>
              ))}
            </div>
          </div>
        </div>
        
        {/* Bottom section with copyright */}
        <div className="text-center text-sm text-gray-600 dark:text-gray-300">
          <p>&copy; {currentYear} NexusSentinel. All rights reserved.</p>
          <p className="mt-1">
            Developed by <a href="https://github.com/wedhazo" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 hover:underline">Kibrom Wedhazo</a>
          </p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
