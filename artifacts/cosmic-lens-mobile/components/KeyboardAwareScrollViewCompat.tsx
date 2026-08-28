import { ScrollView, type ScrollViewProps } from "react-native";

/** Web: plain ScrollView. Native implementation uses keyboard-controller. */
export function KeyboardAwareScrollViewCompat({
  children,
  keyboardShouldPersistTaps = "handled",
  ...props
}: ScrollViewProps) {
  return (
    <ScrollView keyboardShouldPersistTaps={keyboardShouldPersistTaps} {...props}>
      {children}
    </ScrollView>
  );
}
