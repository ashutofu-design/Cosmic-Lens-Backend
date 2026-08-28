import React, { type PropsWithChildren } from "react";
import { KeyboardProvider } from "react-native-keyboard-controller";

export function AppKeyboardShell({ children }: PropsWithChildren) {
  return <KeyboardProvider>{children}</KeyboardProvider>;
}
