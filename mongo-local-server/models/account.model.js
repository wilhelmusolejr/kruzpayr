import mongoose from "mongoose";

const accountSchema = new mongoose.Schema(
  {
    username: { type: String, required: true, unique: true },
    password: { type: String, required: true },
    ign: { type: String },

    registerDate: { type: Date },

    ecoin: { type: Number, default: 0 },
    goldCoin: { type: Number, default: 0 },

    firstName: { type: String },
    lastName: { type: String },
    email: { type: String },

    securityAnswer: { type: String },
    birthDate: { type: Date },

    accessToken: { type: String },
    refreshToken: { type: String },

    nickname: { type: String },
    lastLogin: { type: String },
  },
  {
    timestamps: true,
    collection: "accounts",
  }
);

const Account = mongoose.model("Account", accountSchema);
export default Account;
