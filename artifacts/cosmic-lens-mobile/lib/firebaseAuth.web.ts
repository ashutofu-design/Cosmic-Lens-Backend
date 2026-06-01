/** Firebase auth — web: phone OTP (firebase/auth) + Google popup. */
export {
  sendPhoneOtp,
  confirmPhoneOtp,
  resetPendingVerification,
  hasPendingVerification,
} from "./firebaseAuth.impl";
export { signInWithGoogle, signOutFromFirebase } from "./googleSignIn";
