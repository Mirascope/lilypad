export const diffDays = (expire_at: Date): number => {
  const current_day = new Date();

  const diffTime = expire_at.getTime() - current_day.getTime();
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  return diffDays;
};
