import { X402Mempool } from "./src/x402/core/X402Mempool.ts";
import express from "express";

const mempool = new X402Mempool();
mempool.on("batch_executed", (b) => console.log(`\n=== BATCH #${b.height} EXECUTED ===\nHash: ${b.hash.slice(0,20)}...`));

const app = express();
app.use(express.json());
app.get("/status", (req, res) => res.json(mempool.getStats()));
app.listen(4020, () => console.log("\n🌐 X402 Engine Live -> http://localhost:4020"));

setInterval(() => {
  mempool.ingest({
    payment: { id: `tx-${Date.now()}`, amount: 1000n, fee: 50n, recipient: "0xKeeper" }
  });
}, 1000);
