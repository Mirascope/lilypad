import { createOrUpdateUser } from '@/db/operations';
import type { User } from '@/db/schema';
import { baseUser, db } from '@/tests/db-setup';
import { createMockContext } from '@/tests/worker-setup';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { handleMe } from './me';

describe('handleMe', () => {
  let mockContext: any;
  let testUser: User;

  beforeEach(async () => {
    vi.clearAllMocks();

    // Create a real test user in the database
    testUser = (await createOrUpdateUser(db, baseUser))!;

    mockContext = createMockContext();
  });

  it('should return user data successfully', async () => {
    // Set the user in context
    mockContext.set('user', testUser);

    await handleMe(mockContext);

    expect(mockContext.get).toHaveBeenCalledWith('user');
    expect(mockContext.json).toHaveBeenCalledWith({
      success: true,
      user: {
        id: testUser.id,
        email: testUser.email,
        name: testUser.name,
      },
    });
  });

  it('should only return id, email, and name fields', async () => {
    // Add extra fields to the user object
    const userWithExtraFields = {
      ...testUser,
      password: 'should-not-be-returned',
      someOtherField: 'also-should-not-be-returned',
    };

    mockContext.set('user', userWithExtraFields);

    await handleMe(mockContext);
    const returnedData = mockContext.json.mock.calls[0][0];

    expect(returnedData.user).toEqual({
      id: testUser.id,
      email: testUser.email,
      name: testUser.name,
    });
    expect(returnedData.user).not.toHaveProperty('password');
    expect(returnedData.user).not.toHaveProperty('someOtherField');
    expect(returnedData.user).not.toHaveProperty('createdAt');
    expect(returnedData.user).not.toHaveProperty('updatedAt');
  });

  it('should handle errors gracefully', async () => {
    // Override the get method to throw an error
    const originalGet = mockContext.get;
    mockContext.get = vi.fn(() => {
      throw new Error('Context error');
    });

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await handleMe(mockContext);

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error in handleMe:',
      expect.any(Error)
    );
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: false,
        error: 'Internal server error',
      },
      500
    );

    consoleErrorSpy.mockRestore();
    mockContext.get = originalGet;
  });

  it('should handle missing user gracefully', async () => {
    // Override the get method to return undefined
    const originalGet = mockContext.get;
    mockContext.get = vi.fn(() => undefined);

    const consoleErrorSpy = vi
      .spyOn(console, 'error')
      .mockImplementation(() => {});

    await handleMe(mockContext);

    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'Error in handleMe:',
      expect.any(Error)
    );
    expect(mockContext.json).toHaveBeenCalledWith(
      {
        success: false,
        error: 'Internal server error',
      },
      500
    );

    consoleErrorSpy.mockRestore();
    mockContext.get = originalGet;
  });

  it('should handle user with null name', async () => {
    // Create a user with null name
    const userWithNullName = await createOrUpdateUser(db, {
      email: 'null-name@example.com',
      name: null,
    });

    mockContext.set('user', userWithNullName);

    await handleMe(mockContext);

    expect(mockContext.json).toHaveBeenCalledWith({
      success: true,
      user: {
        id: userWithNullName!.id,
        email: userWithNullName!.email,
        name: null,
      },
    });
  });
});
