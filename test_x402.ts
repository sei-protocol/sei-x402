import { X402Mempool } from "./src/x402/core/X402Mempool";
import express from "express";

const mempool = new X402Mempool();

mempool.on("batch_executed", (batch: any) => {
  console.log(`\n=== BATCH #${batch.height} ===`);
  console.log("ID   :", batch.batchId.substring(0, 20) + "...");
  console.log("Hash :", batch.hash.substring(0, 20) + "...");
  console.log("Txs  :", batch.txs.length);
  console.log("Time :", new Date(batch.timestamp).toISOString());
});

const app = express();
app.use(express.json());

app.get("/status", (req, res) => {
  const stats = mempool.getStats();
  res.json({
    status: "running",
    height: stats.height,
    queueSize: stats.queueSize,
    uptime: Math.floor((Date.now() - stats.startTime) / 1000) + "s"
  });
});

app.post("/ingest", (req, res) => {
  try {
    mempool.ingest(req.body);
    res.json({ success: true });
  } catch (err: any) {
    res.status(400).json({ error: err.message });
  }
});

const PORT = 4020;
app.listen(PORT, () => {
  console.log(`\n🌐 X402 API running → http://localhost:${PORT}`);
});

console.log("X402 System Ready — All Layers Loaded");

let counter = 0;
setInterval(() => {
  mempool.ingest({
    payment: {
      id: `tx-${Date.now()}-${counter}`,
      amount: BigInt(1000),
      fee: BigInt(50),
      nonce: counter++,
      recipient: "0xKeeper",
      signature: ["0xsig"]
    },
    sourceChain: 8453,
    proofHash: "0xProof",
    timestamp: Date.now()
  });
}, 1000);
