import express from "express";
import mongoose from "mongoose";
import "dotenv/config";

import accountRoutes from "./routes/account.routes.js";
import luckySpinRoutes from "./routes/luckySpin.routes.js";

const app = express();
app.use(express.json());

mongoose
  .connect(process.env.MONGO_URI)
  .then(() => console.log("✅ MongoDB connected"))
  .catch((err) => console.error(err));

app.use("/accounts", accountRoutes);
app.use("/lucky-spin", luckySpinRoutes);

app.listen(3000, "0.0.0.0", () => {
  console.log("Server listening on port 3000");
});
