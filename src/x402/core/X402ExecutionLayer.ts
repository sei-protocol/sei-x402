import crypto from "crypto";
import { safeHashInput } from "../utils/jsonCodec.ts";
import { ExecutionStore } from "../storage/executionStore.ts";

export class X402ExecutionLayer {
  private height = 0;
  private lastHash = "GENESIS";

  constructor() {
    const history = ExecutionStore.loadAll();
    if (history.length > 0) {
      const last = history[history.length - 1];
      this.height = last.height;
      this.lastHash = last.hash;
    }
  }

  execute(txs: any[]) {
    const height = ++this.height;
    const timestamp = Date.now();
    const payload = { height, previousHash: this.lastHash, txs, timestamp };
    const hash = crypto.createHash("sha256").update(safeHashInput(payload)).digest("hex");
    const batch = { batchId: hash, hash, previousHash: this.lastHash, height, txs, timestamp };
    
    ExecutionStore.save(batch);
    this.lastHash = hash;
    return batch;
  }
}
