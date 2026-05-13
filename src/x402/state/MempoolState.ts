export class MempoolState {
  private seen = new Set<string>();
  isSeen(payment: { id: string }): boolean { return this.seen.has(payment.id); }
  markSeen(payment: { id: string }): void { this.seen.add(payment.id); }
}
