/** X402 CORE TYPES - VERIFIED EXPORT **/
export interface Payment {
  id: string;
  amount: bigint;
  fee: bigint;
  nonce: number;
  recipient: string;
  signature: string[];
}

export interface RelayedPayment {
  payment: Payment;
  sourceChain: number;
  proofHash: string;
  timestamp: number;
}

export interface ExecutionBatch {
  batchId: string;
  hash: string;
  previousHash: string;
  height: number;
  txs: Payment[];
  executions: any[];
  timestamp: number;
}
