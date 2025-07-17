import { useAuth } from '@/src/auth';
import { Button } from '@/src/components/ui/button';

export function HomePage() {
  const { user, logout } = useAuth();
  return (
    <div className="w-screen h-screen flex flex-col gap-y-4 justify-center items-center font-handwriting">
      <div className="text-2xl">
        {user!.name ? `Welcome, ${user!.name?.split(' ')[0]}!` : 'Welcome!'}
      </div>
      <Button variant="secondary" onClick={logout}>
        Logout
      </Button>
    </div>
  );
}
