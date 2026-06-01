/** Firebase auth — native: phone OTP (@react-native-firebase) + Google Sign-In. */
export {
  sendPhoneOtp,
  confirmPhoneOtp,
  resetPendingVerification,
  hasPendingVerification,
} from "./firebaseAuth.impl";
export { signInWithGoogle, signOutFromFirebase } from "./googleSignIn";
