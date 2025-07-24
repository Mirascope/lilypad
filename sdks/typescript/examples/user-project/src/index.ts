/**
 * Example user application using Lilypad SDK with TypeScript extraction
 */

import lilypad, { trace } from '@lilypad/typescript-sdk';

// Configure Lilypad
lilypad.configure({
  apiKey: process.env.LILYPAD_API_KEY || 'your-api-key',
  projectId: process.env.LILYPAD_PROJECT_ID || 'your-project-id',
});

// Define types for better TypeScript experience
interface Product {
  id: string;
  name: string;
  price: number;
  category: 'electronics' | 'clothing' | 'food';
}

interface Order {
  id: string;
  items: OrderItem[];
  customer: Customer;
  createdAt: Date;
}

interface OrderItem {
  product: Product;
  quantity: number;
}

interface Customer {
  id: string;
  name: string;
  email: string;
  tier: 'bronze' | 'silver' | 'gold';
}

// Versioned function with TypeScript types
export const calculateOrderTotal = trace(
  async (
    order: Order,
  ): Promise<{
    subtotal: number;
    discount: number;
    tax: number;
    total: number;
  }> => {
    console.log(`Calculating total for order ${order.id}`);

    // Calculate subtotal
    const subtotal = order.items.reduce((sum, item) => sum + item.product.price * item.quantity, 0);

    // Apply customer tier discount
    let discountRate = 0;
    switch (order.customer.tier) {
      case 'bronze':
        discountRate = 0.05;
        break;
      case 'silver':
        discountRate = 0.1;
        break;
      case 'gold':
        discountRate = 0.15;
        break;
    }
    const discount = subtotal * discountRate;

    // Calculate tax (8%)
    const taxableAmount = subtotal - discount;
    const tax = taxableAmount * 0.08;

    // Final total
    const total = taxableAmount + tax;

    return {
      subtotal: Math.round(subtotal * 100) / 100,
      discount: Math.round(discount * 100) / 100,
      tax: Math.round(tax * 100) / 100,
      total: Math.round(total * 100) / 100,
    };
  },
  {
    versioning: 'automatic',
    name: 'calculateOrderTotal',
    tags: ['pricing', 'orders'],
  },
);

// Another versioned function with generics
export const filterProducts = trace(
  <T extends Product>(products: T[], predicate: (product: T) => boolean): T[] => {
    console.log(`Filtering ${products.length} products`);
    return products.filter(predicate);
  },
  { versioning: 'automatic', name: 'filterProducts' },
);

// Function with complex parameter types
export const processInventory = trace(
  async ({
    products,
    updates,
  }: {
    products: Map<string, Product>;
    updates: Array<{
      productId: string;
      quantity: number;
      operation: 'add' | 'remove' | 'set';
    }>;
  }): Promise<Map<string, number>> => {
    const inventory = new Map<string, number>();

    for (const update of updates) {
      const current = inventory.get(update.productId) || 0;

      switch (update.operation) {
        case 'add':
          inventory.set(update.productId, current + update.quantity);
          break;
        case 'remove':
          inventory.set(update.productId, Math.max(0, current - update.quantity));
          break;
        case 'set':
          inventory.set(update.productId, update.quantity);
          break;
      }
    }

    return inventory;
  },
  { versioning: 'automatic', name: 'processInventory' },
);

// Example usage
async function main() {
  const sampleOrder: Order = {
    id: 'order-123',
    customer: {
      id: 'cust-456',
      name: 'John Doe',
      email: 'john@example.com',
      tier: 'silver',
    },
    items: [
      {
        product: {
          id: 'prod-1',
          name: 'Laptop',
          price: 999.99,
          category: 'electronics',
        },
        quantity: 1,
      },
      {
        product: {
          id: 'prod-2',
          name: 'Mouse',
          price: 29.99,
          category: 'electronics',
        },
        quantity: 2,
      },
    ],
    createdAt: new Date(),
  };

  // Calculate order total
  const total = await calculateOrderTotal(sampleOrder);
  console.log('Order total:', total);

  // List versions (requires server connection)
  try {
    const versions = await calculateOrderTotal.versions();
    console.log(`Found ${versions.length} versions of calculateOrderTotal`);
  } catch (error) {
    console.log('Could not fetch versions (server not connected)');
  }
}

// Run if called directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(console.error);
}
