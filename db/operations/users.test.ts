import { baseUser, db } from '@/tests/setup';
import { describe, expect, it, spyOn } from 'bun:test';
import { createOrUpdateUser } from './users';

describe('createOrUpdateUser', () => {
  it('inserts a new user on first call', async () => {
    const inserted = await createOrUpdateUser(db, baseUser);
    expect(inserted?.email).toBe(baseUser.email);
    expect(inserted?.name).toBe(baseUser.name);
    expect(inserted?.createdAt).toBeTruthy();
    expect(inserted?.updatedAt).toBeTruthy();
  });

  it('updates name + updatedAt when email already exists but name changes', async () => {
    const inserted = await createOrUpdateUser(db, baseUser);
    await new Promise((resolve) => setTimeout(resolve, 1));
    const updated = await createOrUpdateUser(db, {
      ...baseUser,
      name: 'Frog',
    });

    expect(updated?.id).toBe(inserted!.id);
    expect(updated?.name).toBe('Frog');
    expect(updated?.updatedAt?.getTime()).toBeGreaterThan(
      inserted!.updatedAt!.getTime()
    );
    expect(updated?.name).not.toBe(inserted?.name);
  });

  it('leaves updatedAt untouched when name is identical', async () => {
    const inserted = await createOrUpdateUser(db, baseUser);
    await new Promise((resolve) => setTimeout(resolve, 1));
    const updated = await createOrUpdateUser(db, baseUser);

    expect(updated?.updatedAt!.getTime()).toBe(inserted!.updatedAt!.getTime());
  });

  it('returns null when database error occurs', async () => {
    const consoleSpy = spyOn(console, 'error').mockImplementation(() => {});
    const dbSpy = spyOn(db, 'insert').mockImplementation(() => {
      throw new Error('Database connection failed');
    });

    const result = await createOrUpdateUser(db, baseUser);

    expect(result).toBeNull();
    expect(consoleSpy).toHaveBeenCalledWith(
      'Error creating or updating user atomically:',
      expect.any(Error)
    );

    consoleSpy.mockRestore();
    dbSpy.mockRestore();
  });
});
