import type { DocsThemeConfig } from "nextra-theme-docs";
import { LilypadLogo } from "./components/LilypadLogo";
import { SlackLogo } from "./components/SlackLogo";
import Script from "next/script";

const config: DocsThemeConfig = {
  logo: <LilypadLogo width="48" height="48" />,
  color: {
    hue: 123,
    saturation: 47,
    lightness: {
      dark: 42,
      light: 34,
    },
  },
  head: (
    <>
      <title>Lilypad</title>
      <meta name="description" content="The future of prompt engineering" />
      <meta name="viewport" content="width=device-width, initial-scale=1.0" />
      <meta property="og:title" content="Lilypad" />
      <meta
        property="og:description"
        content="The future of prompt engineering"
      />
      <Script
        async
        src="https://www.googletagmanager.com/gtag/js?id=G-Y1LHCGR6YM"
      ></Script>
      <Script>
        {`
          window.dataLayer = window.dataLayer || [];
          function gtag(){dataLayer.push(arguments);}
          gtag('js', new Date());
          gtag('config', 'G-Y1LHCGR6YM');
        `}
      </Script>
    </>
  ),
  footer: {
    content: (
      <span>
        © 2024{" "}
        <a href="https://mirascope.com" target="_blank">
          Mirascope
        </a>
        . All rights reserved.
      </span>
    ),
  },
  navigation: {
    prev: true,
    next: true,
  },
  project: {
    link: "https://github.com/Mirascope/lilypad",
  },
  chat: {
    link: "https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA",
    icon: <SlackLogo width="18" height="18" />,
  },
  docsRepositoryBase: "https://github.com/Mirascope/lilypad/tree/main/docs",
};
export default config;
