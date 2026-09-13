import { cva } from "class-variance-authority";
export const badgeVariants = cva(
  "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12px] font-semibold leading-none transition-colors",
  {
    variants: {
      variant: {
        default: "border-transparent bg-secondary text-secondary-foreground",
        wash: "border-transparent bg-primary/12 text-primary",
        warn: "border-transparent bg-accent/14 text-accent",
        destructive: "border-transparent bg-destructive/12 text-destructive",
        outline: "border-border text-muted-foreground",
      },
    },
    defaultVariants: { variant: "default" },
  },
);
