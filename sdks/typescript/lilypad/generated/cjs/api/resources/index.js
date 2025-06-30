"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.ee = exports.settings = exports.comments = exports.tags = exports.userConsents = exports.environments = exports.externalApiKeys = exports.users = exports.auth = exports.spans = exports.webhooks = exports.apiKeys = exports.organizations = exports.projects = void 0;
exports.projects = __importStar(require("./projects/index.js"));
exports.organizations = __importStar(require("./organizations/index.js"));
exports.apiKeys = __importStar(require("./apiKeys/index.js"));
exports.webhooks = __importStar(require("./webhooks/index.js"));
exports.spans = __importStar(require("./spans/index.js"));
exports.auth = __importStar(require("./auth/index.js"));
exports.users = __importStar(require("./users/index.js"));
exports.externalApiKeys = __importStar(require("./externalApiKeys/index.js"));
exports.environments = __importStar(require("./environments/index.js"));
exports.userConsents = __importStar(require("./userConsents/index.js"));
exports.tags = __importStar(require("./tags/index.js"));
exports.comments = __importStar(require("./comments/index.js"));
exports.settings = __importStar(require("./settings/index.js"));
exports.ee = __importStar(require("./ee/index.js"));
__exportStar(require("./organizations/client/requests/index.js"), exports);
__exportStar(require("./apiKeys/client/requests/index.js"), exports);
__exportStar(require("./webhooks/client/requests/index.js"), exports);
__exportStar(require("./spans/client/requests/index.js"), exports);
__exportStar(require("./auth/client/requests/index.js"), exports);
__exportStar(require("./externalApiKeys/client/requests/index.js"), exports);
__exportStar(require("./environments/client/requests/index.js"), exports);
__exportStar(require("./userConsents/client/requests/index.js"), exports);
__exportStar(require("./comments/client/requests/index.js"), exports);
