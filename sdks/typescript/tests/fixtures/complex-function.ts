import { trace } from '@lilypad/typescript-sdk';

interface User {
  name: string;
  isPremium: boolean;
}

interface Product {
  id: string;
  price: number;
}

const BASE_DISCOUNT = 0.05;
const PREMIUM_MULTIPLIER = 3;
const MAX_DISCOUNT = BASE_DISCOUNT * PREMIUM_MULTIPLIER;

function calculateDiscount(user: User): number {
  return user.isPremium ? MAX_DISCOUNT : BASE_DISCOUNT;
}

function applyDiscount(price: number, discount: number): number {
  return price * (1 - discount);
}

export const calculatePrice = trace(
  (product: Product, user: User): number => {
    const discount = calculateDiscount(user);
    return applyDiscount(product.price, discount);
  },
  { versioning: 'automatic', name: 'calculatePrice' },
);
