import fs from "fs";
import { EventEmitter } from "events";
import { MempoolState } from "../state/MempoolState.ts";
import { X402ExecutionLayer } from "./X402ExecutionLayer.ts";
import { Validator } from "../state/Validator.ts";

export class X402Mempool extends EventEmitter {
  private queue: any[] = [];
  private state = new MempoolState();
  private executionLayer = new X402ExecutionLayer();
  private secret = fs.readFileSync("./sovereign.key", "utf-8").trim();

  ingest(relayed: any) {
    // SECURITY CHECK: Verify the signature against our sovereign key
    const isValid = Validator.verify(relayed.payment, relayed.signature, this.secret);
    
    if (!isValid) {
      console.error(`🚨 UNAUTHORIZED TX REJECTED: ${relayed.payment.id}`);
      return;
    }

    if (this.state.isSeen(relayed.payment)) return;
    this.state.markSeen(relayed.payment);
    this.queue.push(relayed.payment);
    
    if (this.queue.length >= 3) {
      const batch = this.executionLayer.execute([...this.queue]);
      this.queue = [];
      this.emit("batch_executed", batch);
    }
  }

  getStats() {
    return { height: this.executionLayer.getHeight(), queueSize: this.queue.length };
  }
}
