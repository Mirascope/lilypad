import { createFileRoute } from '@tanstack/react-router';
import { AuthProvider } from '@/src/auth';
import { HomePage } from '@/src/components/home-page';
import { Protected } from '@/src/components/protected';

export const Route = createFileRoute('/')({
  component: App,
});

function App() {
  return (
    <AuthProvider>
      <Protected>
        <HomePage />
      </Protected>
    </AuthProvider>
  );
}
