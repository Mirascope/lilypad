// scripts/generate-api-types.js

import _ from "lodash";
import path from "path";
import { generateApi } from "swagger-typescript-api";
import { fileURLToPath } from "url";
import yargs from "yargs";
import { hideBin } from "yargs/helpers";
import fs from "fs/promises";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Read OpenAPI spec from stdin
 * @returns {Promise<string>} - The OpenAPI spec
 */
async function getStdinData() {
  return new Promise((resolve, reject) => {
    let data = "";
    process.stdin.on("data", (chunk) => {
      data += chunk;
    });
    process.stdin.on("end", () => {
      resolve(data);
    });
    process.stdin.on("error", (err) => {
      reject(err);
    });
  });
}

/**
 * Generate TypeScript API types from OpenAPI spec
 * @param {Object} options - Generator options
 */
async function generateApiTypes(options) {
  try {
    // Default values matching original script
    const name = "types.ts";
    const generateClient = false;
    const codeGenConstructs = () => ({
      EnumField: (key, value) => {
        return `${_.snakeCase(key).toUpperCase()} = ${value}`;
      },
    });

    const { url, file, stdin, api, output } = options;

    // Convert output path to absolute path
    const absoluteOutputPath = path.isAbsolute(output)
      ? output
      : path.resolve(process.cwd(), output);

    console.log(`Using absolute output path: ${absoluteOutputPath}`);

    // Prepare input options
    const apiOptions = {
      name,
      output: absoluteOutputPath,
      generateClient,
      codeGenConstructs,
    };

    // Handle different input sources
    if (stdin) {
      console.log("Reading from stdin...");
      const data = await getStdinData();

      try {
        const parsedData = JSON.parse(data);
        apiOptions.spec = parsedData;
      } catch (e) {
        console.error("Failed to parse stdin data as JSON:", e);
        throw new Error("Invalid JSON from stdin");
      }
    } else if (file) {
      const fileContent = await fs.readFile(file, "utf-8");
      try {
        const parsedData = JSON.parse(fileContent);
        apiOptions.spec = parsedData;
      } catch (e) {
        console.error("Failed to parse file as JSON:", e);
        throw new Error(`Invalid JSON in file: ${file}`);
      }
    } else if (url) {
      apiOptions.url = url;
    } else {
      throw new Error("Must specify either --url, --file, or --stdin");
    }

    // Make sure the output directory exists
    await fs.mkdir(apiOptions.output, { recursive: true });

    // Generate the API types
    console.log(`Generating TypeScript types to ${apiOptions.output}/${name}...`);
    const result = await generateApi(apiOptions);

    console.log(`Generated types at ${path.join(apiOptions.output, name)}`);
    return result;
  } catch (error) {
    console.error("Error generating API types:", error.message);
    process.exit(1);
  }
}

// Configure the CLI
yargs(hideBin(process.argv))
  .command(
    "generate",
    "Generate TypeScript types from OpenAPI spec",
    (yargs) => {
      return yargs
        .option("url", {
          describe: "URL to fetch OpenAPI spec from",
          type: "string",
        })
        .option("file", {
          describe: "File path to read OpenAPI spec from",
          type: "string",
        })
        .option("stdin", {
          describe: "Read OpenAPI spec from stdin",
          type: "boolean",
          default: false,
        })
        .option("api", {
          describe: "API type when using stdin (v0 or ee-v0)",
          type: "string",
          choices: ["v0", "ee-v0"],
        })
        .option("output", {
          describe: "Output directory for generated types",
          type: "string",
          alias: "o",
          required: true
        })
        .check((argv) => {
          // At least one input source is required
          if (!argv.url && !argv.file && !argv.stdin) {
            throw new Error("Must specify either --url, --file, or --stdin");
          }
          return true;
        });
    },
    async (argv) => {
      await generateApiTypes(argv);
    }
  )
  // Default command for backward compatibility
  .command(
    "$0",
    "Generate TypeScript types for default APIs",
    () => {},
    async () => {
      try {
        // First API - v0
        await generateApiTypes({
          url: "http://127.0.0.1:8000/v0/openapi.json",
          output: path.resolve(__dirname, "../src/types/"),
        });

        // Second API - ee-v0
        await generateApiTypes({
          url: "http://127.0.0.1:8000/v0/ee/openapi.json",
          output: path.resolve(__dirname, "../src/ee/types/"),
        });
        
        console.log("Generated types for both APIs using default configuration");
      } catch (error) {
        process.exit(1);
      }
    }
  )
  .help()
  .argv;