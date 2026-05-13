import fs from "fs";
import { ExecutionBatch } from "../types";
import { safeStringify } from "../utils/jsonCodec";

const FILE = "./execution_chain.json";

export class ExecutionStore {
  static loadAll(): ExecutionBatch[] {
    if (!fs.existsSync(FILE)) return [];
    try {
      return JSON.parse(fs.readFileSync(FILE, "utf-8"));
    } catch {
      return [];
    }
  }

  static save(batch: ExecutionBatch): void {
    const all = ExecutionStore.loadAll();
    all.push(batch);
    fs.writeFileSync(FILE, safeStringify(all));
  }
}
