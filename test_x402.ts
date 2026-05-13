import fs from "fs";
import crypto from "crypto";
import { X402Mempool } from "./src/x402/core/X402Mempool.ts";
import { SeiSettlementBridge } from "./src/x402/core/SeiSettlementBridge.ts";
import express from "express";

const SECRET = fs.readFileSync("./sovereign.key", "utf-8").trim();
const mempool = new X402Mempool();
const bridge = new SeiSettlementBridge();

// E2E Workflow: Execution -> Settlement
mempool.on("batch_executed", async (batch) => {
  console.log(`\n📦 BATCH #${batch.height} EXECUTED | Hash: ${batch.hash.slice(0,24)}...`);
  
  // Trigger Sei Settlement
  const seiTx = await bridge.settleBatch(batch);
  console.log(`📜 PROOF ANCHORED: ${batch.hash.slice(0,8)} -> Sei:${seiTx.slice(0,12)}...`);
});

const app = express();
app.use(express.json());
app.get("/status", (req, res) => res.json(mempool.getStats()));
app.listen(4020, () => {
  console.log("\n⚔️ X402 E2E SOVEREIGN ENGINE ONLINE");
  console.log("----------------------------------");
});

// Auto-Signer Simulation
setInterval(() => {
  const payment = { id: `tx-${Date.now()}`, amount: 1000n, recipient: "0xKeeper" };
  const signature = crypto.createHmac("sha256", SECRET).update(payment.id).digest("hex");
  mempool.ingest({ payment, signature });
}, 1000);
