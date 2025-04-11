import { useRouter } from "next/router";
import "../globals.css";
import "../overrides.css";

export default function App({ Component, pageProps }) {
  const router = useRouter();
  return <Component {...pageProps} />;
}
