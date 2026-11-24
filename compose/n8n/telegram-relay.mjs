// Telegram long-polling relay for a private n8n instance.
//
// n8n's Telegram Trigger registers a public webhook, which would need inbound internet access.
// This relay instead polls Telegram (outbound only) and forwards each allowed update to a
// local-only n8n Webhook node, authenticated with a shared header secret.
//
// Delivery is at-least-once: the Telegram offset only advances after n8n accepts the update,
// so a restart or an n8n outage can deliver the same update twice. Telegram keeps undelivered
// updates for 24 hours.
//
// Runs on the n8n image's own Node runtime with no dependencies. Secrets are read from files
// (Compose secrets) and never logged.

import { readFileSync } from "node:fs";
import { pathToFileURL } from "node:url";

export const ALLOWED_UPDATE_TYPES = ["message", "callback_query"];
const POLL_TIMEOUT_SECONDS = 50;
const MAX_BACKOFF_MS = 60_000;

export function parseIdList(value) {
  const ids = String(value ?? "")
    .split(",")
    .map((part) => part.trim())
    .filter(Boolean);
  if (ids.length === 0 || ids.some((id) => !/^-?\d+$/.test(id))) {
    throw new Error("TELEGRAM_ALLOWED_USER_IDS must be a comma-separated list of numeric IDs");
  }
  return new Set(ids);
}

// The sender of a message or button press, or null for update types we do not forward.
export function senderId(update) {
  for (const type of ALLOWED_UPDATE_TYPES) {
    if (update && update[type]) {
      const from = update[type].from;
      return from && from.id !== undefined ? String(from.id) : null;
    }
  }
  return null;
}

export function shouldForward(update, allowedIds) {
  const id = senderId(update);
  return id !== null && allowedIds.has(id);
}

export function nextOffset(update) {
  return Number(update.update_id) + 1;
}

export function backoff(attempt) {
  return Math.min(MAX_BACKOFF_MS, 1000 * 2 ** Math.min(attempt, 6));
}

// Hide the bot token if an error message ever includes a Telegram URL.
export function redact(text, secrets) {
  let out = String(text);
  for (const secret of secrets) {
    if (secret) out = out.split(secret).join("[REDACTED]");
  }
  return out;
}

export function readSecret(path) {
  const value = readFileSync(path, "utf8").trim();
  if (!value) throw new Error(`Secret file is empty: ${path}`);
  return value;
}

export function loadConfig(env) {
  const webhookUrl = env.RELAY_TARGET_URL;
  if (!webhookUrl || !/^http:\/\/n8n:5678\/webhook\/[A-Za-z0-9_-]{16,}$/.test(webhookUrl)) {
    throw new Error("RELAY_TARGET_URL must be http://n8n:5678/webhook/<random path of 16+ characters>");
  }
  return {
    botToken: readSecret(env.TELEGRAM_BOT_TOKEN_FILE ?? "/run/secrets/telegram_bot_token"),
    relaySecret: readSecret(env.RELAY_SHARED_SECRET_FILE ?? "/run/secrets/relay_shared_secret"),
    allowedIds: parseIdList(env.TELEGRAM_ALLOWED_USER_IDS),
    webhookUrl,
  };
}

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function telegram(config, method, body) {
  const response = await fetch(`https://api.telegram.org/bot${config.botToken}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
    signal: AbortSignal.timeout((POLL_TIMEOUT_SECONDS + 15) * 1000),
  });
  const payload = await response.json();
  if (!payload.ok) throw new Error(`Telegram ${method} failed: ${payload.error_code} ${payload.description}`);
  return payload.result;
}

async function forward(config, update) {
  const response = await fetch(config.webhookUrl, {
    method: "POST",
    headers: { "content-type": "application/json", "x-relay-secret": config.relaySecret },
    body: JSON.stringify(update),
    signal: AbortSignal.timeout(30_000),
  });
  if (!response.ok) throw new Error(`n8n webhook returned HTTP ${response.status}`);
}

function log(config, message) {
  console.log(`${new Date().toISOString()} ${redact(message, [config.botToken, config.relaySecret])}`);
}

export async function run(config) {
  // getUpdates is refused while a webhook is registered, e.g. by the cloud instance's trigger.
  await telegram(config, "deleteWebhook", { drop_pending_updates: false });
  log(config, "relay started; webhook cleared, long polling");
  let offset;
  let failures = 0;
  for (;;) {
    try {
      const updates = await telegram(config, "getUpdates", {
        offset,
        timeout: POLL_TIMEOUT_SECONDS,
        allowed_updates: ALLOWED_UPDATE_TYPES,
      });
      for (const update of updates) {
        if (shouldForward(update, config.allowedIds)) {
          await forward(config, update);
        } else {
          log(config, `dropped update ${update.update_id} from a sender outside the allowlist`);
        }
        offset = nextOffset(update);
      }
      failures = 0;
    } catch (error) {
      failures += 1;
      log(config, `error (attempt ${failures}): ${error.message}`);
      await sleep(backoff(failures));
    }
  }
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  let config;
  try {
    config = loadConfig(process.env);
  } catch (error) {
    console.error(`relay configuration error: ${error.message}`);
    process.exit(2);
  }
  run(config);
}
