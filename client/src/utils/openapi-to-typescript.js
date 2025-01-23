import _ from "lodash";
import path from "path";
import { generateApi } from "swagger-typescript-api";
import { fileURLToPath } from "url";

const __filename = fileURLToPath(import.meta.url);

const __dirname = path.dirname(__filename);
generateApi({
  name: "types.ts",
  url: "http://127.0.0.1:8000/v0/openapi.json",
  output: path.resolve(__dirname, "../types/"),
  generateClient: false,
  codeGenConstructs: () => ({
    EnumField: (key, value) => {
      return `${_.snakeCase(key).toUpperCase()} = ${value}`;
    },
  }),
});
