import express from "express";
import {
  getNextLuckySpinAccount,
  updateLuckySpinAccount,
} from "../controller/luckySpin.controller.js";

const router = express.Router();

// Get next account for lucky spin processing
router.get("/next", getNextLuckySpinAccount);
router.patch("/:id", updateLuckySpinAccount);

export default router;
