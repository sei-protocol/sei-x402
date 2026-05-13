import fs from "fs";
import { ExecutionBatch } from "../types";
import { safeStringify } from "../utils/jsonCodec";

export class BatchStore {
  static basePath = "./batches";

  static save(batch: ExecutionBatch): string {
    const file = `${BatchStore.basePath}/${batch.batchId}.json`;
    if (!fs.existsSync(BatchStore.basePath)) {
      fs.mkdirSync(BatchStore.basePath, { recursive: true });
    }
    fs.writeFileSync(file, safeStringify(batch));
    return file;
  }
}
