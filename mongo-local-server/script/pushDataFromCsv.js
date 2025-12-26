import "dotenv/config";
import fs from "fs";
import axios from "axios";
import { parse } from "csv-parse/sync";
import crypto from "crypto";

const API_URL = "http://localhost:3000/accounts";
const CSV_FILE = "./script/dirty_database.csv";
const BATCH_SIZE = 200;
const SLEEP_MS = 60_000;

const ALGORITHM = "aes-256-gcm";

if (!process.env.PASSWORD_ENCRYPTION_KEY) {
  throw new Error("❌ PASSWORD_ENCRYPTION_KEY is not set");
}

const KEY = crypto
  .createHash("sha256")
  .update(process.env.PASSWORD_ENCRYPTION_KEY)
  .digest();

/* =========================
   Helper functions
========================= */

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function parseString(value) {
  if (!value) return undefined;
  const v = String(value).trim();
  return v === "" ? undefined : v;
}

function parseNumber(value) {
  if (value === undefined || value === null || value === "") return undefined;
  const num = Number(value);
  return isNaN(num) ? undefined : num;
}

function parseRegisterDate(value) {
  if (!value) return undefined;
  const date = new Date(value);
  return isNaN(date.getTime()) ? undefined : date;
}

function parseBirthDate(value) {
  if (!value) return undefined;

  if (value.includes("/")) {
    const [day, month, year] = value.split("/").map(Number);
    const d = new Date(year, month - 1, day);
    return isNaN(d.getTime()) ? undefined : d;
  }

  const d = new Date(value);
  return isNaN(d.getTime()) ? undefined : d;
}

function encryptPassword(password) {
  if (!password) return undefined;

  const iv = crypto.randomBytes(12);
  const cipher = crypto.createCipheriv(ALGORITHM, KEY, iv);

  const encrypted = Buffer.concat([
    cipher.update(password, "utf8"),
    cipher.final(),
  ]);

  const authTag = cipher.getAuthTag();

  return Buffer.concat([iv, authTag, encrypted]).toString("base64");
}

/* =========================
   CSV → Account mapper
========================= */

function mapCsvRowToAccount(row) {
  return {
    username: parseString(row[0]),
    password: parseString(row[1]),
    ign: parseString(row[2]),

    registerDate: parseRegisterDate(row[3]),

    ecoin: parseNumber(row[4]),
    goldCoin: parseNumber(row[5]),

    firstName: parseString(row[6]),
    lastName: parseString(row[7]),
    email: parseString(row[8]),

    securityAnswer: parseString(row[9]),
    birthDate: parseBirthDate(row[10]),

    accessToken: parseString(row[11]),
    refreshToken: parseString(row[12]),

    nickname: parseString(row[13]),
    lastLogin: parseString(row[14]),
  };
}

/* =========================
   Main import logic
========================= */

async function pushFromCsv() {
  try {
    const raw = fs.readFileSync(CSV_FILE, "utf-8");

    const records = parse(raw, {
      skip_empty_lines: true,
    });

    const existingRes = await axios.get(API_URL);
    const existingUsernames = new Set(
      existingRes.data.map((acc) => acc.username)
    );

    let offset = 0;
    let batchNumber = 1;

    while (offset < records.length) {
      const batch = records.slice(offset, offset + BATCH_SIZE);

      console.log(
        `🚀 Processing batch ${batchNumber} (${offset + 1}–${
          offset + batch.length
        })`
      );

      for (const row of batch) {
        const account = mapCsvRowToAccount(row);

        if (!account.username || !account.password) {
          console.log("⚠️ Skipped invalid row (missing username/password)");
          continue;
        }

        if (existingUsernames.has(account.username)) {
          console.log(`⏭️ ${account.username} already in database`);
          continue;
        }

        account.password = encryptPassword(account.password);

        try {
          const res = await axios.post(API_URL, account);
          existingUsernames.add(account.username);
          console.log(`✅ Inserted: ${res.data.username}`);
        } catch (err) {
          console.error(
            `❌ Failed inserting ${account.username}:`,
            err.response?.data || err.message
          );
        }
      }

      offset += BATCH_SIZE;
      batchNumber++;

      if (offset < records.length) {
        console.log(`⏳ Sleeping for 30 seconds...\n`);
        await sleep(SLEEP_MS);
      }
    }

    console.log("🎉 All batches processed");
  } catch (err) {
    console.error("❌ Fatal error:", err.message);
  }
}

pushFromCsv();
