import { EventEmitter } from "events";
import { MempoolState } from "../state/MempoolState";
import { X402ExecutionLayer } from "./X402ExecutionLayer";
import { RelayedPayment } from "../types";

export class X402Mempool extends EventEmitter {
  private queue: any[] = [];
  private state = new MempoolState();
  private executionLayer: X402ExecutionLayer;
  private isRunning = true;
  private startTime = Date.now();

  constructor() {
    super();
    this.executionLayer = new X402ExecutionLayer();
  }

  ingest(relayed: RelayedPayment): void {
    if (!this.isRunning) return;
    const p = relayed.payment;
    if (this.state.isSeen(p)) return;

    this.state.markSeen(p);
    this.queue.push(p);

    if (this.queue.length >= 3) this.processBatch();
  }

  private processBatch() {
    const txs = [...this.queue];
    this.queue = [];
    const batch = this.executionLayer.execute(txs);
    this.emit("batch_executed", batch);
  }

  getStats() {
    return {
      height: this.executionLayer.getHeight(),
      queueSize: this.queue.length,
      startTime: this.startTime
    };
  }

  stop() {
    this.isRunning = false;
    if (this.queue.length > 0) this.processBatch();
  }
}
