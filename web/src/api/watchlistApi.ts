import { api } from './apiClient';
import { WatchlistItem, WatchlistCreate, WatchlistResponse } from '../types/apiTypes';

/**
 * Watchlist API client
 * 
 * This module provides functions for interacting with the watchlist endpoints.
 */

/**
 * Get all items in the watchlist
 * @returns Promise resolving to an array of watchlist items
 */
export const getWatchlistItems = async (): Promise<WatchlistItem[]> => {
  try {
    const response = await api.get<WatchlistResponse>('/watchlist');
    return response;
  } catch (error) {
    console.error('Error fetching watchlist items:', error);
    throw error;
  }
};

/**
 * Add a stock to the watchlist
 * @param symbol The stock symbol to add (e.g., "AAPL")
 * @returns Promise resolving to the created watchlist item
 */
export const addToWatchlist = async (symbol: string): Promise<WatchlistItem> => {
  try {
    const payload: WatchlistCreate = { symbol };
    const response = await api.post<WatchlistItem>('/watchlist', payload);
    return response;
  } catch (error) {
    console.error(`Error adding ${symbol} to watchlist:`, error);
    throw error;
  }
};

/**
 * Remove a stock from the watchlist
 * @param symbol The stock symbol to remove (e.g., "AAPL")
 * @returns Promise resolving to void on success
 */
export const removeFromWatchlist = async (symbol: string): Promise<void> => {
  try {
    await api.delete<void>(`/watchlist/${symbol}`);
  } catch (error) {
    console.error(`Error removing ${symbol} from watchlist:`, error);
    throw error;
  }
};
