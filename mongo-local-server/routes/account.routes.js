import express from "express";
import Account from "../models/account.model.js";

const router = express.Router();

// Create account
router.post("/", async (req, res) => {
  try {
    const account = new Account(req.body);
    await account.save();
    res.status(201).json(account);
  } catch (err) {
    res.status(400).json({ error: err.message });
  }
});

// Get all accounts
router.get("/", async (req, res) => {
  const accounts = await Account.find();
  res.json(accounts);
});

export default router;
