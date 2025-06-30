var __awaiter = (this && this.__awaiter) || function (thisArg, _arguments, P, generator) {
    function adopt(value) { return value instanceof P ? value : new P(function (resolve) { resolve(value); }); }
    return new (P || (P = Promise))(function (resolve, reject) {
        function fulfilled(value) { try { step(generator.next(value)); } catch (e) { reject(e); } }
        function rejected(value) { try { step(generator["throw"](value)); } catch (e) { reject(e); } }
        function step(result) { result.done ? resolve(result.value) : adopt(result.value).then(fulfilled, rejected); }
        step((generator = generator.apply(thisArg, _arguments || [])).next());
    });
};
import { RUNTIME } from "../../runtime/index.mjs";
export function chooseStreamWrapper(responseBody) {
    return __awaiter(this, void 0, void 0, function* () {
        if (RUNTIME.type === "node" && RUNTIME.parsedVersion != null && RUNTIME.parsedVersion >= 18) {
            return new (yield import("./Node18UniversalStreamWrapper.mjs")).Node18UniversalStreamWrapper(responseBody);
        }
        else if (RUNTIME.type !== "node" && typeof fetch === "function") {
            return new (yield import("./UndiciStreamWrapper.mjs")).UndiciStreamWrapper(responseBody);
        }
        else {
            return new (yield import("./NodePre18StreamWrapper.mjs")).NodePre18StreamWrapper(responseBody);
        }
    });
}
