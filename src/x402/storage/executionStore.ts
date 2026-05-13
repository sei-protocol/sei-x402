import fs from "fs";
import { safeStringify } from "../utils/jsonCodec.ts";
const FILE = "./execution_chain.json";

export class ExecutionStore {
  static loadAll() {
    if (!fs.existsSync(FILE)) return [];
    return JSON.parse(fs.readFileSync(FILE, "utf-8"));
  }
  static save(batch: any) {
    const all = ExecutionStore.loadAll();
    all.push(batch);
    fs.writeFileSync(FILE, safeStringify(all));
  }
}
