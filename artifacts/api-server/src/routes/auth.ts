import { Router, type IRouter } from "express";
import { requireFirebaseAuth } from "../middleware/firebaseAuth";
import { isFirebaseConfigured } from "../lib/firebaseAdmin";

const router: IRouter = Router();

router.get("/auth/config", (_req, res) => {
  res.json({ firebaseConfigured: isFirebaseConfigured() });
});

router.get("/auth/me", requireFirebaseAuth, (req, res) => {
  res.json({
    uid: req.firebaseUser?.uid,
    phone_number: req.firebaseUser?.phone_number,
    claims: req.firebaseUser,
  });
});

export default router;

