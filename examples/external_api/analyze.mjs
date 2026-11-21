// Run on the server with Node.js. The API key stays in the process environment.
import { request as httpRequest } from "node:http";
import { request as httpsRequest } from "node:https";

const [url] = process.argv.slice(2);
const key = process.env.GEOSEER_API_KEY;
if (!key || !url || process.argv.length !== 3) {
  console.error("Set GEOSEER_API_KEY and run: node analyze.mjs DIRECT_MEDIA_URL");
  process.exit(2);
}

const base = process.env.GEOSEER_BASE_URL || "https://geoseeer.com/api/v1";
try {
  const endpoint = new URL(`${base.replace(/\/$/, "")}/analyze`);
  const request = endpoint.protocol === "http:" ? httpRequest : httpsRequest;
  const body = JSON.stringify({ url });
  const response = await new Promise((resolve, reject) => {
    const call = request(endpoint, {
      method: "POST",
      headers: {
        "X-API-Key": key,
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(body),
      },
      signal: AbortSignal.timeout(450_000),
    }, resolve);
    call.on("error", reject);
    call.end(body);
  });
  if (response.statusCode !== 200) {
    response.destroy();
    console.error(`GeoSeer returned HTTP ${response.statusCode}.`);
    process.exitCode = 1;
  } else {
    response.setEncoding("utf8");
    let data = "";
    for await (const chunk of response) data += chunk;
    console.log(JSON.stringify(JSON.parse(data), null, 2));
  }
} catch (error) {
  console.error(error.name === "TimeoutError" || error.name === "AbortError"
    ? "GeoSeer timed out. The server may still be processing the request."
    : "Could not complete a JSON response from GeoSeer.");
  process.exitCode = 1;
}
