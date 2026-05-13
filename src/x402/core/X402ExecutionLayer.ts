import crypto from "crypto";
import { safeHashInput } from "../utils/jsonCodec";
import { ExecutionStore } from "../storage/executionStore";
import { BatchStore } from "../storage/batchStore";
import { Payment, ExecutionBatch } from "../types";

export class X402ExecutionLayer {
  private height = 0;
  private lastHash = "GENESIS";

  constructor() {
    this.rehydrate();
  }

  private rehydrate() {
    const history = ExecutionStore.loadAll();
    if (history.length > 0) {
      const last = history[history.length - 1];
      this.height = last.height;
      this.lastHash = last.hash;
    }
  }

  execute(txs: Payment[]): ExecutionBatch {
    const height = ++this.height;
    const timestamp = Date.now();

    const executions = txs.map(p => ({
      payment: p,
      success: true,
      gasUsed: Math.floor(Math.random() * 8000) + 2000,
      executedAt: timestamp
    }));

    const payload = { height, previousHash: this.lastHash, txs, timestamp };
    const hash = crypto.createHash("sha256").update(safeHashInput(payload)).digest("hex");

    const batch: ExecutionBatch = {
      batchId: hash,
      hash,
      previousHash: this.lastHash,
      height,
      txs,
      executions,
      timestamp
    };

    ExecutionStore.save(batch);
    BatchStore.save(batch);

    this.lastHash = hash;
    return batch;
  }

  getHeight(): number { return this.height; }
}
