import "../globals.css";
import { useRouter } from "next/router";

export default function App({ Component, pageProps }) {
  const router = useRouter();
  return <Component {...pageProps} />;
}
