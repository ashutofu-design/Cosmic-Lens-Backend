import { Router, type IRouter } from "express";
import healthRouter from "./health";
import kundliRouter from "./kundli";

const router: IRouter = Router();

router.use(healthRouter);
router.use(kundliRouter);

export default router;
