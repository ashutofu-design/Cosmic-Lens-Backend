import type { NextFunction, Request, Response } from "express";
import { FirebaseAuthError, verifyFirebaseIdToken } from "../lib/firebaseAdmin";

function extractBearerToken(req: Request): string | undefined {
  const header = req.header("authorization") ?? req.header("Authorization");
  if (!header) {
    return undefined;
  }
  const match = header.match(/^Bearer\s+(.+)$/i);
  return match?.[1]?.trim() || undefined;
}

export async function requireFirebaseAuth(
  req: Request,
  res: Response,
  next: NextFunction,
): Promise<void> {
  const token = extractBearerToken(req);
  if (!token) {
    res.status(401).json({ error: "Missing Authorization: Bearer <token>" });
    return;
  }

  try {
    const decoded = await verifyFirebaseIdToken(token);
    req.firebaseUser = decoded;
    next();
  } catch (err) {
    if (err instanceof FirebaseAuthError) {
      res.status(401).json({ error: err.message, code: err.code });
      return;
    }
    res.status(401).json({ error: "Unauthorized" });
  }
}

