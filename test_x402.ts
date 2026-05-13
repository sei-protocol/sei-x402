import { X402Mempool } from "./src/x402/core/X402Mempool";
import express from "express";

const mempool = new X402Mempool();
(mempool as any).startTime = Date.now();

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
  console.log(`\n🌐 X402 API running on http://localhost:${PORT}`);
});

console.log("✅ X402 Full System Started - All Layers Loaded");
console.log("Press Ctrl+C to stop\n");

let counter = 0;
setInterval(() => {
  for (let i = 0; i < 5; i++) {
    mempool.ingest({
      payment: {
        id: `tx-${Date.now()}-${counter}`,
        amount: BigInt(500 + Math.floor(Math.random() * 5000)),
        fee: BigInt(30 + Math.floor(Math.random() * 300)),
        nonce: counter++,
        recipient: "0x" + Math.random().toString(16).slice(2, 42),
        signature: ["0xsig1", "0xsig2"]
      },
      sourceChain: 8453,
      proofHash: "0x" + Math.random().toString(16),
      timestamp: Date.now()
    });
  }
}, 700);

process.on("SIGINT", () => {
  console.log("\nShutting down X402...");
  mempool.stop();
  process.exit(0);
});
