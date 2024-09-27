import { ReactNode } from "react";

enum TypographyVariant {
  H1 = "h1",
  H2 = "h2",
  H3 = "h3",
  H4 = "h4",
  P = "p",
  LEAD = "lead",
  LARGE = "large",
  SMALL = "small",
  MUTED = "muted",
}
export function Typography({
  variant = TypographyVariant.H1,
  children,
}: {
  variant: string;
  children: ReactNode;
}) {
  let element;
  switch (variant) {
    case TypographyVariant.H1:
      element = (
        <h1 className='scroll-m-20 text-4xl font-extrabold tracking-tight lg:text-5xl'>
          {children}
        </h1>
      );
      break;
    case TypographyVariant.H2:
      element = (
        <h2 className='scroll-m-20 border-b pb-2 text-3xl font-semibold tracking-tight first:mt-0'>
          {children}
        </h2>
      );
      break;
    case TypographyVariant.H3:
      element = (
        <h3 className='scroll-m-20 text-2xl font-semibold tracking-tight'>
          {children}
        </h3>
      );
      break;
    case TypographyVariant.H4:
      element = (
        <h4 className='scroll-m-20 text-xl font-semibold tracking-tight'>
          {children}
        </h4>
      );
      break;
    case TypographyVariant.P:
      element = (
        <p className='leading-7 [&:not(:first-child)]:mt-6'>{children}</p>
      );
      break;
    case TypographyVariant.LEAD:
      element = <p className='text-xl text-muted-foreground'>{children}</p>;
      break;
    case TypographyVariant.LARGE:
      element = <p className='text-lg font-semibold'>{children}</p>;
      break;
    case TypographyVariant.SMALL:
      element = <p className='text-sm font-medium leading-none'>{children}</p>;
      break;
    case TypographyVariant.MUTED:
      element = <p className='text-sm text-muted-foreground'>{children}</p>;
      break;
  }
  return element;
}
