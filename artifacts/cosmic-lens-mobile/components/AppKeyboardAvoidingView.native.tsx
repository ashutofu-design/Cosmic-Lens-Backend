import React, { type ComponentProps } from "react";
import { KeyboardAvoidingView } from "react-native-keyboard-controller";

export function AppKeyboardAvoidingView(
  props: ComponentProps<typeof KeyboardAvoidingView>,
) {
  return <KeyboardAvoidingView {...props} />;
}
