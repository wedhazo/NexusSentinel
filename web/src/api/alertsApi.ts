import { api } from './apiClient';
import { AlertCreate, AlertResponse } from '../types/apiTypes';

/**
 * Alerts API client
 * 
 * This module provides functions for interacting with the sentiment alerts endpoints.
 */

/**
 * Get all alerts with optional filtering
 * @param symbol Optional symbol to filter alerts by
 * @param triggered Optional boolean to filter by triggered status
 * @returns Promise resolving to an array of alert items
 */
export const getAlerts = async (
  symbol?: string,
  triggered?: boolean
): Promise<AlertResponse[]> => {
  try {
    // Build query parameters
    const params: Record<string, string> = {};
    if (symbol) params.symbol = symbol;
    if (triggered !== undefined) params.triggered = triggered.toString();
    
    const response = await api.get<AlertResponse[]>('/alerts', { params });
    return response;
  } catch (error) {
    console.error('Error fetching alerts:', error);
    throw error;
  }
};

/**
 * Create a new sentiment alert
 * @param symbol The stock symbol to monitor
 * @param threshold The sentiment threshold (-1.0 to 1.0)
 * @param direction The direction ("above" or "below")
 * @returns Promise resolving to the created alert
 */
export const createAlert = async (
  symbol: string,
  threshold: number,
  direction: 'above' | 'below'
): Promise<AlertResponse> => {
  try {
    const payload: AlertCreate = { 
      symbol: symbol.toUpperCase(),
      threshold,
      direction
    };
    
    const response = await api.post<AlertResponse>('/alerts', payload);
    return response;
  } catch (error) {
    console.error(`Error creating alert for ${symbol}:`, error);
    throw error;
  }
};

/**
 * Delete a sentiment alert
 * @param id The ID of the alert to delete
 * @returns Promise resolving to void on success
 */
export const deleteAlert = async (id: number): Promise<void> => {
  try {
    await api.delete<void>(`/alerts/${id}`);
  } catch (error) {
    console.error(`Error deleting alert ${id}:`, error);
    throw error;
  }
};

/**
 * Check alerts against current sentiment scores
 * @returns Promise resolving to an array of newly triggered alerts
 */
export const checkAlerts = async (): Promise<AlertResponse[]> => {
  try {
    const response = await api.post<AlertResponse[]>('/alerts/check');
    return response;
  } catch (error) {
    console.error('Error checking alerts:', error);
    throw error;
  }
};
