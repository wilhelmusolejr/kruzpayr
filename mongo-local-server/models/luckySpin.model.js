import mongoose from "mongoose";

const luckySpinSchema = new mongoose.Schema(
  {
    accountId: {
      type: mongoose.Schema.Types.ObjectId,
      ref: "Account",
      required: true,
      index: true,
    },

    // Event identity
    eventType: {
      type: String,
      required: true,
      default: "lucky_spin",
      index: true,
    },

    eventPeriod: {
      type: String,
      required: true,
      index: true,
      // e.g. "YYYY-MM"
    },

    version: {
      type: Number,
      required: true,
      default: 1,
    },

    // Progress
    isClaimed: {
      type: Boolean,
      default: false,
    },

    claimedAt: {
      type: Date,
    },

    attempts: {
      type: Number,
      default: 0,
    },

    lastAttemptAt: {
      type: Date,
    },

    status: {
      type: String,
      enum: ["pending", "processing", "success", "failed", "skipped"],
      default: "pending",
    },
  },
  { timestamps: true }
);

// Enforce one progress record per account per event
luckySpinSchema.index(
  { accountId: 1, eventType: 1, eventPeriod: 1, version: 1 },
  { unique: true }
);

export default mongoose.model("LuckySpin", luckySpinSchema);
