import "dotenv/config";
import mongoose from "mongoose";

import Account from "../models/account.model.js";
import LuckySpin from "../models/luckySpin.model.js";

const MONGO_URI = process.env.MONGO_URI;

async function seedLuckySpin() {
  try {
    // 1️⃣ Connect FIRST
    await mongoose.connect(MONGO_URI);
    console.log("✅ MongoDB connected");

    // 2️⃣ Fetch accounts
    const accounts = await Account.find();
    console.log(`📦 Found ${accounts.length} accounts`);

    if (accounts.length === 0) {
      console.log("⚠️ No accounts found, aborting seed");
      return;
    }

    // 3️⃣ Build jobs
    const jobs = accounts.map((acc) => ({
      accountId: acc._id,
      eventType: "lucky_spin",
      eventPeriod: "2025-12",
      version: 1,
      status: "pending",
      attempts: 0,
    }));

    // 4️⃣ Insert (ignore duplicates safely)
    const result = await LuckySpin.insertMany(jobs, {
      ordered: false,
    });

    console.log(`🎉 Seeded ${result.length} LuckySpin jobs`);
  } catch (err) {
    // Duplicate key errors are EXPECTED if re-running
    if (err.code === 11000) {
      console.log("ℹ️ Some jobs already existed (duplicate key ignored)");
    } else {
      console.error("❌ Seed error:", err);
    }
  } finally {
    // 5️⃣ Always close connection
    await mongoose.disconnect();
    console.log("🔌 MongoDB disconnected");
  }
}

seedLuckySpin();
