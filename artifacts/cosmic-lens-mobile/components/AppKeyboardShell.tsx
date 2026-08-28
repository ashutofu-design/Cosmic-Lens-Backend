import React, { type PropsWithChildren } from "react";

/** Web: browser handles the keyboard. Native file wraps KeyboardProvider. */
export function AppKeyboardShell({ children }: PropsWithChildren) {
  return <>{children}</>;
}
