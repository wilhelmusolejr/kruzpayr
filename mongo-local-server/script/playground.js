import LuckySpin from "../models/luckySpin.model.js";

const job = await LuckySpin.findOneAndUpdate(
  {
    status: "pending",
    eventType: "lucky_spin",
    eventPeriod: "2025-12",
    version: 1,
  },
  {
    $set: { status: "processing", lastAttemptAt: new Date() },
    $inc: { attempts: 1 },
  },
  { new: true }
).populate("accountId");

console.log(job);
