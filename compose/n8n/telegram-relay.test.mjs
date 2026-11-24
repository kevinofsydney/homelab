import assert from "node:assert/strict";
import { mkdtempSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import test from "node:test";

import {
  backoff,
  loadConfig,
  nextOffset,
  parseIdList,
  redact,
  senderId,
  shouldForward,
} from "./telegram-relay.mjs";

const OWNER = "1001";
const allowed = new Set([OWNER]);

test("forwards messages and button presses from the owner only", () => {
  assert.equal(shouldForward({ update_id: 1, message: { from: { id: 1001 } } }, allowed), true);
  assert.equal(shouldForward({ update_id: 2, callback_query: { from: { id: 1001 } } }, allowed), true);
  assert.equal(shouldForward({ update_id: 3, message: { from: { id: 2002 } } }, allowed), false);
});

test("drops update types the router does not handle and senderless updates", () => {
  assert.equal(senderId({ update_id: 4, edited_message: { from: { id: 1001 } } }), null);
  assert.equal(senderId({ update_id: 5, message: {} }), null);
  assert.equal(shouldForward({ update_id: 6, channel_post: { chat: { id: 1001 } } }, allowed), false);
});

test("offset advances past the handled update", () => {
  assert.equal(nextOffset({ update_id: 41 }), 42);
});

test("backoff grows and is capped", () => {
  assert.equal(backoff(1), 2000);
  assert.ok(backoff(3) > backoff(2));
  assert.equal(backoff(50), 60_000);
});

test("redacts secrets from log text", () => {
  const text = "fetch https://api.telegram.org/botTOKEN123/getUpdates failed";
  assert.equal(redact(text, ["TOKEN123"]), "fetch https://api.telegram.org/bot[REDACTED]/getUpdates failed");
});

test("rejects malformed allowlists", () => {
  assert.throws(() => parseIdList(""));
  assert.throws(() => parseIdList("1001,owner"));
  assert.deepEqual([...parseIdList(" 1001, 2002 ")], ["1001", "2002"]);
});

test("loads secrets from files and requires a local random webhook path", () => {
  const dir = mkdtempSync(join(tmpdir(), "relay-test-"));
  writeFileSync(join(dir, "token"), "test-token\n");
  writeFileSync(join(dir, "secret"), "test-secret\n");
  const env = {
    TELEGRAM_BOT_TOKEN_FILE: join(dir, "token"),
    RELAY_SHARED_SECRET_FILE: join(dir, "secret"),
    TELEGRAM_ALLOWED_USER_IDS: OWNER,
    RELAY_TARGET_URL: "http://n8n:5678/webhook/abcdefghijklmnop",
  };
  const config = loadConfig(env);
  assert.equal(config.botToken, "test-token");
  assert.equal(config.relaySecret, "test-secret");
  assert.throws(() => loadConfig({ ...env, RELAY_TARGET_URL: "https://example.com/webhook/abcdefghijklmnop" }));
  assert.throws(() => loadConfig({ ...env, RELAY_TARGET_URL: "http://n8n:5678/webhook/short" }));
  writeFileSync(join(dir, "secret"), "\n");
  assert.throws(() => loadConfig(env));
});
