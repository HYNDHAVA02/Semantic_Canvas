import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";

let firebaseConfig = null;
try {
  const raw = process.env.NEXT_PUBLIC_FIREBASE_CONFIG;
  if (raw) firebaseConfig = JSON.parse(raw);
} catch {
  // Config not available or invalid — Firebase will be disabled
}

const app = firebaseConfig
  ? getApps().length > 0
    ? getApp()
    : initializeApp(firebaseConfig)
  : null;

export const auth = app ? getAuth(app) : null;
