import crypto from "crypto";
import Account from "../models/account.model.js";
import LuckySpin from "../models/luckySpin.model.js";

const EVENT_TYPE = "lucky_spin";
const EVENT_PERIOD = "2025-12";
const VERSION = 1;
const ALGORITHM = "aes-256-gcm";
const KEY = crypto
  .createHash("sha256")
  .update(process.env.PASSWORD_ENCRYPTION_KEY)
  .digest();

/**
 * Get ONE account that still needs to process Lucky Spin
 */

export async function getNextLuckySpinAccount(req, res) {
  try {
    const job = await LuckySpin.findOneAndUpdate(
      {
        status: "pending",
        eventType: "lucky_spin",
        eventPeriod: "2025-12",
        version: 1,
      },
      {
        $set: {
          status: "processing",
          lastAttemptAt: new Date(),
        },
        $inc: {
          attempts: 1,
        },
      },
      {
        new: true,
      }
    ).populate("accountId");

    if (!job || !job.accountId) {
      return res.status(404).json({
        message: "No pending Lucky Spin jobs available",
      });
    }

    return res.json({
      jobId: job._id,
      status: job.status,
      attempts: job.attempts,

      account: {
        id: job.accountId._id,
        username: job.accountId.username,
        password: decryptPassword(job.accountId.password),
        ign: job.accountId.ign,
      },
    });
  } catch (err) {
    console.error("LuckySpin controller error:", err);
    return res.status(500).json({
      error: "Internal server error",
    });
  }
}

export async function updateLuckySpinAccount(req, res) {
  try {
    const { id } = req.params;
    const updates = req.body;

    // Optional: always update timestamps-related fields safely
    updates.lastAttemptAt = new Date();

    const job = await LuckySpin.findByIdAndUpdate(
      id,
      { $set: updates },
      { new: true }
    );

    if (!job) {
      return res.status(404).json({
        message: "LuckySpin account not found",
      });
    }

    return res.json({
      message: "LuckySpin account updated",
      job,
    });
  } catch (err) {
    console.error("LuckySpin update error:", err);
    return res.status(500).json({
      error: "Internal server error",
    });
  }
}

function decryptPassword(encryptedValue) {
  if (!encryptedValue) return undefined;
  const buffer = Buffer.from(encryptedValue, "base64");
  const iv = buffer.subarray(0, 12);
  const authTag = buffer.subarray(12, 28);
  const encrypted = buffer.subarray(28);
  const decipher = crypto.createDecipheriv(ALGORITHM, KEY, iv);
  decipher.setAuthTag(authTag);
  const decrypted = Buffer.concat([
    decipher.update(encrypted),
    decipher.final(),
  ]);
  return decrypted.toString("utf8");
}
