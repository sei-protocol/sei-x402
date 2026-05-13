import { EventEmitter } from "events";
import { MempoolState } from "../state/MempoolState.ts";
import { X402ExecutionLayer } from "./X402ExecutionLayer.ts";

export class X402Mempool extends EventEmitter {
  private queue: any[] = [];
  private state = new MempoolState();
  private executionLayer = new X402ExecutionLayer();
  private startTime = Date.now();

  ingest(relayed: any) {
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
    return { height: 0, queueSize: this.queue.length, startTime: this.startTime };
  }
}
