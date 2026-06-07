import type { ReactNode } from "react";
import { cn } from "../lib/utils";

export function GlassCard({
  className,
  children,
  accent = false,
}: {
  className?: string;
  children: ReactNode;
  accent?: boolean;
}) {
  return (
    <div
      className={cn(
        "glass-card rounded-xl",
        accent && "border-cosmic-400/30 bg-gradient-to-br from-white/95 to-cosmic-50/90",
        className,
      )}
    >
      {children}
    </div>
  );
}
