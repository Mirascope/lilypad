/**
 * Business Logic Functions
 *
 * These functions demonstrate various TypeScript features that will be
 * preserved when extracted at build time.
 */

import { trace } from '@lilypad/typescript-sdk';

// Types and interfaces
export interface PricingParams {
  originalPrice: number;
  customerTier: 'bronze' | 'silver' | 'gold' | 'platinum';
  quantity: number;
}

export interface OrderItem {
  id: string;
  name: string;
  price: number;
  quantity: number;
}

export interface OrderRequest {
  items: OrderItem[];
  customerId: string;
  shippingMethod: 'standard' | 'express' | 'overnight';
}

// Generic type
export type ValidationResult<T> = {
  isValid: boolean;
  data?: T;
  errors?: string[];
};

/**
 * Calculate discount based on customer tier and quantity
 * This function shows TypeScript types and JSDoc comments
 */
export const calculateDiscount = trace(
  async (
    params: PricingParams,
  ): Promise<{
    originalTotal: number;
    discountPercentage: number;
    discountAmount: number;
    finalPrice: number;
  }> => {
    const { originalPrice, customerTier, quantity } = params;

    // Calculate base total
    const originalTotal = originalPrice * quantity;

    // Determine discount percentage based on tier
    let discountPercentage = 0;
    switch (customerTier) {
      case 'bronze':
        discountPercentage = 5;
        break;
      case 'silver':
        discountPercentage = 10;
        break;
      case 'gold':
        discountPercentage = 15;
        break;
      case 'platinum':
        discountPercentage = 20;
        break;
    }

    // Apply quantity discount
    if (quantity >= 10) {
      discountPercentage += 5;
    } else if (quantity >= 5) {
      discountPercentage += 2;
    }

    // Calculate final amounts
    const discountAmount = originalTotal * (discountPercentage / 100);
    const finalPrice = originalTotal - discountAmount;

    return {
      originalTotal: Math.round(originalTotal * 100) / 100,
      discountPercentage,
      discountAmount: Math.round(discountAmount * 100) / 100,
      finalPrice: Math.round(finalPrice * 100) / 100,
    };
  },
  {
    versioning: 'automatic',
    name: 'calculateDiscount',
    tags: ['pricing', 'discounts'],
  },
);

/**
 * Process an order with complex nested types
 */
export const processOrder = trace(
  async function processOrderWithShipping(request: OrderRequest): Promise<{
    orderId: string;
    items: OrderItem[];
    subtotal: number;
    shipping: number;
    tax: number;
    total: number;
    estimatedDelivery: Date;
  }> {
    // Calculate subtotal
    const subtotal = request.items.reduce((sum, item) => sum + item.price * item.quantity, 0);

    // Calculate shipping based on method
    const shippingRates = {
      standard: 5.99,
      express: 15.99,
      overnight: 29.99,
    };
    const shipping = shippingRates[request.shippingMethod];

    // Calculate tax (8.5%)
    const tax = (subtotal + shipping) * 0.085;

    // Calculate total
    const total = subtotal + shipping + tax;

    // Estimate delivery
    const today = new Date();
    const deliveryDays = {
      standard: 5,
      express: 2,
      overnight: 1,
    };
    const estimatedDelivery = new Date(today);
    estimatedDelivery.setDate(today.getDate() + deliveryDays[request.shippingMethod]);

    return {
      orderId: `ORD-${Date.now()}-${request.customerId}`,
      items: request.items,
      subtotal: Math.round(subtotal * 100) / 100,
      shipping,
      tax: Math.round(tax * 100) / 100,
      total: Math.round(total * 100) / 100,
      estimatedDelivery,
    };
  },
  { versioning: 'automatic' },
);

/**
 * Validate user data with generic return type
 */
export const validateUser = trace(
  <T extends { email: string; age: number }>(
    userData: T & { country: string },
  ): ValidationResult<T> => {
    const errors: string[] = [];

    // Email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(userData.email)) {
      errors.push('Invalid email format');
    }

    // Age validation
    if (userData.age < 18) {
      errors.push('User must be 18 or older');
    }

    if (userData.age > 120) {
      errors.push('Invalid age');
    }

    // Country validation
    const allowedCountries = ['US', 'CA', 'UK', 'AU', 'NZ'];
    if (!allowedCountries.includes(userData.country)) {
      errors.push(`Country must be one of: ${allowedCountries.join(', ')}`);
    }

    return {
      isValid: errors.length === 0,
      data: errors.length === 0 ? userData : undefined,
      errors: errors.length > 0 ? errors : undefined,
    };
  },
  { versioning: 'automatic', name: 'validateUser' },
);

/**
 * Generate statistical report with array methods and async operations
 */
export const generateReport = trace(
  async (
    data: number[],
  ): Promise<{
    count: number;
    sum: number;
    average: number;
    min: number;
    max: number;
    median: number;
    standardDeviation: number;
  }> => {
    // Basic statistics
    const count = data.length;
    const sum = data.reduce((acc, val) => acc + val, 0);
    const average = sum / count;
    const min = Math.min(...data);
    const max = Math.max(...data);

    // Calculate median
    const sorted = [...data].sort((a, b) => a - b);
    const median =
      count % 2 === 0
        ? (sorted[count / 2 - 1] + sorted[count / 2]) / 2
        : sorted[Math.floor(count / 2)];

    // Calculate standard deviation
    const squaredDifferences = data.map((value) => Math.pow(value - average, 2));
    const avgSquaredDiff = squaredDifferences.reduce((acc, val) => acc + val, 0) / count;
    const standardDeviation = Math.sqrt(avgSquaredDiff);

    // Simulate async operation
    await new Promise((resolve) => setTimeout(resolve, 100));

    return {
      count,
      sum,
      average: Math.round(average * 100) / 100,
      min,
      max,
      median,
      standardDeviation: Math.round(standardDeviation * 100) / 100,
    };
  },
  { versioning: 'automatic', name: 'generateReport', tags: ['analytics', 'reporting'] },
);
