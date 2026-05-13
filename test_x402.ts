import fs from "fs";
import crypto from "crypto";
import { X402Mempool } from "./src/x402/core/X402Mempool.ts";
import express from "express";

const SECRET = fs.readFileSync("./sovereign.key", "utf-8").trim();
const mempool = new X402Mempool();

mempool.on("batch_executed", (b) => {
  console.log(`\n✅ SECURE BATCH #${b.height} | HASH: ${b.hash.slice(0,24)}...`);
});

const app = express();
app.use(express.json());
app.get("/status", (req, res) => res.json(mempool.getStats()));
app.listen(4020, () => console.log("\n🛡️ X402 SECURE ENGINE LIVE"));

// Simulation: Sign transactions before sending to mempool
setInterval(() => {
  const payment = { id: `tx-${Date.now()}`, amount: 1000n, recipient: "0xKeeper" };
  const signature = crypto.createHmac("sha256", SECRET).update(payment.id).digest("hex");

  mempool.ingest({
    payment,
    signature // Authorized by Sovereign Key
  });
}, 1000);
