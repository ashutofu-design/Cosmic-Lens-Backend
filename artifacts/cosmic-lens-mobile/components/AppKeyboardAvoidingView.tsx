import React, { type ComponentProps } from "react";
import { KeyboardAvoidingView as RNKeyboardAvoidingView } from "react-native";

/** Web: RN KeyboardAvoidingView. Native file uses keyboard-controller. */
export function AppKeyboardAvoidingView(
  props: ComponentProps<typeof RNKeyboardAvoidingView>,
) {
  return <RNKeyboardAvoidingView {...props} />;
}
