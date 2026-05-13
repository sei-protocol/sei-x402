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

export interface ExecutedPayment {
  payment: Payment;
  success: boolean;
  gasUsed: number;
  executedAt: number;
}

export interface ExecutionBatch {
  batchId: string;
  hash: string;
  previousHash: string;
  height: number;
  txs: Payment[];
  executions: ExecutedPayment[];
  timestamp: number;
}
