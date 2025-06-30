var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { RUNTIME } from "../runtime/index.mjs";
/**
 * Returns a fetch function based on the runtime
 */
export function getFetchFn() {
    return __awaiter(this, void 0, void 0, function* () {
        // In Node.js 18+ environments, use native fetch
        if (RUNTIME.type === "node" && RUNTIME.parsedVersion != null && RUNTIME.parsedVersion >= 18) {
            return fetch;
        }
        // In Node.js 18 or lower environments, the SDK always uses`node-fetch`.
        if (RUNTIME.type === "node") {
            return (yield import("node-fetch")).default;
        }
        // Otherwise the SDK uses global fetch if available,
        // and falls back to node-fetch.
        if (typeof fetch == "function") {
            return fetch;
        }
        // Defaults to node `node-fetch` if global fetch isn't available
        return (yield import("node-fetch")).default;
    });
}
