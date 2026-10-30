import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { JSDOM } from "jsdom";

const html = readFileSync(
  new URL("../web/index.html", import.meta.url),
  "utf8",
);
const source = readFileSync(new URL("../web/app.js", import.meta.url), "utf8");
const flush = () => new Promise((resolve) => setImmediate(resolve));
const deferred = () => {
  let resolve, reject;
  const promise = new Promise((a, b) => {
    resolve = a;
    reject = b;
  });
  return { promise, resolve, reject };
};
const response = (data) => ({ ok: true, json: async () => data });
const inventory = {
  entries: [],
  total: 46,
  ready: 0,
  previewable: 46,
  alphabet_ready: 0,
  alphabet_previewable: 26,
};
const sequence = (...words) => ({
  sequence: words.map((text) => ({
    id: text,
    text,
    url: `/api/media/${text}`,
    ready: false,
    type: "word",
    input: text,
  })),
  preview: true,
  warnings: [],
  normalized: words.join(" "),
  matched_words: words.length,
  input_words: words.length,
  elapsed_ms: 1,
});

async function fixture(t, fetcher, customInventory = inventory) {
  const dom = new JSDOM(html, {
    url: "http://localhost/",
    runScripts: "outside-only",
  });
  const w = dom.window;
  w.HTMLMediaElement.prototype.pause = function () {
    this._paused = true;
  };
  w.HTMLMediaElement.prototype.load = function () {};
  w.HTMLMediaElement.prototype.play = async function () {
    this._paused = false;
    this.dispatchEvent(new w.Event("playing"));
  };
  Object.defineProperty(w.HTMLMediaElement.prototype, "paused", {
    get() {
      return this._paused !== false;
    },
  });
  w.fetch = (url, options) =>
    url === "/api/dictionary"
      ? Promise.resolve(response(customInventory))
      : fetcher(url, options);
  w.eval(source);
  t.after(() => w.close());
  await flush();
  const $ = (id) => w.document.getElementById(id);
  const convert = async (text) => {
    $("message").value = text;
    $("message").dispatchEvent(
      new w.KeyboardEvent("keydown", {
        key: "Enter",
        ctrlKey: true,
        bubbles: true,
      }),
    );
    await flush();
  };
  return { w, $, convert };
}

test("late conversion response cannot replace the newer queue", async (t) => {
  const first = deferred(),
    second = deferred();
  let calls = 0;
  const f = await fixture(t, () =>
    ++calls === 1 ? first.promise : second.promise,
  );
  await f.convert("hello");
  await f.convert("water");
  second.resolve(response(sequence("water")));
  await flush();
  first.resolve(response(sequence("hello")));
  await flush();
  assert.equal(f.$("current-label").textContent, "water");
  assert.equal(f.$("convert-button").disabled, false);
});

test("clear invalidates in-flight conversion even when transport ignores abort", async (t) => {
  const request = deferred();
  const f = await fixture(t, () => request.promise);
  await f.convert("hello");
  f.$("clear-button").click();
  request.resolve(response(sequence("hello")));
  await flush();
  assert.equal(f.$("sequence-count").textContent, "0 signs");
  assert.equal(f.$("sign-video").hidden, true);
});

test("late ended event from a replaced clip cannot advance new sequence", async (t) => {
  const f = await fixture(t, async () => response(sequence("hello", "friend")));
  await f.convert("hello friend");
  const old = f.$("sign-video");
  f.$("stop-button").click();
  old.dispatchEvent(new f.w.Event("ended"));
  await flush();
  assert.equal(f.$("current-label").textContent, "hello");
  assert.equal(f.$("player-state").textContent, "STOPPED");
});

test("paused clip cannot advance on a delayed ended event", async (t) => {
  const f = await fixture(t, async () => response(sequence("hello", "friend")));
  await f.convert("hello friend");
  f.$("play-button").click();
  await flush();
  f.$("play-button").click();
  f.$("sign-video").dispatchEvent(new f.w.Event("ended"));
  await flush();
  assert.equal(f.$("current-label").textContent, "hello");
  assert.equal(f.$("player-state").textContent, "PAUSED");
});

test("media failure during playback skips visibly and completes", async (t) => {
  const f = await fixture(t, async () => response(sequence("hello", "friend")));
  await f.convert("hello friend");
  f.$("play-button").click();
  await flush();
  f.$("sign-video").dispatchEvent(new f.w.Event("error"));
  await flush();
  assert.equal(f.$("current-label").textContent, "friend");
  assert.match(f.$("warnings").textContent, /Skipping/);
  f.$("sign-video").dispatchEvent(new f.w.Event("ended"));
  await flush();
  assert.equal(f.$("player-state").textContent, "SEQUENCE COMPLETE");
});

test("source preview requires an explicit action and updates alphabet availability", async (t) => {
  const f = await fixture(t, async () => response(sequence("hello")));
  assert.equal(f.$("preview-mode").checked, false);
  assert.equal(f.$("source-onboarding").hidden, false);
  f.$("enable-preview").click();
  assert.equal(f.$("preview-mode").checked, true);
  assert.match(f.$("alphabet-status").textContent, /26\/26/);
  assert.equal(f.$("source-onboarding").hidden, true);
});

test("denied microphone permission leaves a usable text/upload path", async (t) => {
  const f = await fixture(t, async () => response({ text: "unused" }));
  f.w.MediaRecorder = class {
    static isTypeSupported() {
      return true;
    }
  };
  Object.defineProperty(f.w.navigator, "mediaDevices", {
    value: {
      getUserMedia: async () => {
        throw new f.w.DOMException("Declined", "NotAllowedError");
      },
    },
  });
  f.$("record-button").click();
  await flush();
  assert.match(f.$("toast").textContent, /permission was declined/);
  assert.equal(f.$("record-button").disabled, false);
  assert.equal(f.$("upload-button").disabled, false);
});

test("late microphone permission after clear releases acquired tracks", async (t) => {
  const permission = deferred();
  let stopped = 0;
  const f = await fixture(t, async () => response({ text: "unused" }));
  f.w.MediaRecorder = class {
    static isTypeSupported() {
      return true;
    }
  };
  Object.defineProperty(f.w.navigator, "mediaDevices", {
    value: { getUserMedia: () => permission.promise },
  });
  f.$("record-button").click();
  f.$("clear-button").click();
  permission.resolve({
    getTracks: () => [
      {
        stop() {
          stopped++;
        },
      },
    ],
  });
  await flush();
  assert.equal(stopped, 1);
  assert.equal(f.$("message").value, "");
  assert.equal(f.$("record-button").disabled, false);
});

test("record, stop and cancel prevent a late transcript from overwriting typed text", async (t) => {
  const transcript = deferred();
  let stopped = 0,
    uploads = 0;
  const f = await fixture(t, async () => {
    uploads++;
    return transcript.promise;
  });
  f.w.MediaRecorder = class extends f.w.EventTarget {
    static isTypeSupported() {
      return true;
    }
    constructor() {
      super();
      this.state = "inactive";
      this.mimeType = "audio/webm";
    }
    start() {
      this.state = "recording";
    }
    stop() {
      this.state = "inactive";
      const event = new f.w.Event("dataavailable");
      event.data = new f.w.Blob(["test-audio"]);
      this.dispatchEvent(event);
      queueMicrotask(() => this.dispatchEvent(new f.w.Event("stop")));
    }
  };
  Object.defineProperty(f.w.navigator, "mediaDevices", {
    value: {
      getUserMedia: async () => ({
        getTracks: () => [
          {
            stop() {
              stopped++;
            },
          },
        ],
      }),
    },
  });
  f.$("record-button").click();
  await flush();
  f.$("record-button").click();
  await flush();
  assert.equal(uploads, 1);
  assert.ok(stopped > 0);
  f.$("clear-button").click();
  f.$("message").value = "new typed message";
  transcript.resolve(response({ text: "stale transcript" }));
  await flush();
  assert.equal(f.$("message").value, "new typed message");
  assert.equal(f.$("record-button").disabled, false);
});

test("non-JSON server failures have readable feedback", async (t) => {
  const f = await fixture(t, async () => ({
    ok: false,
    json: async () => {
      throw new SyntaxError("bad json");
    },
  }));
  await f.convert("hello");
  assert.match(f.$("toast").textContent, /server could not complete/);
});

test("typing while transcription is in flight cancels stale transcript", async (t) => {
  const transcript = deferred();
  const f = await fixture(t, () => transcript.promise);
  Object.defineProperty(f.$("audio-file"), "files", {
    value: [new f.w.File(["audio"], "sample.wav")],
  });
  f.$("audio-file").dispatchEvent(new f.w.Event("change"));
  await flush();
  assert.equal(f.$("cancel-speech").hidden, false);
  f.$("message").value = "keep my typed words";
  f.$("message").dispatchEvent(new f.w.Event("input"));
  transcript.resolve(response({ text: "obsolete speech" }));
  await flush();
  assert.equal(f.$("message").value, "keep my typed words");
  assert.equal(f.$("cancel-speech").hidden, true);
});

test("a clip that failed during preload is skipped on Play", async (t) => {
  const f = await fixture(t, async () => response(sequence("hello", "friend")));
  await f.convert("hello friend");
  const video = f.$("sign-video");
  Object.defineProperty(video, "error", { value: { code: 4 } });
  video.play = async () => {
    throw new f.w.DOMException("Unsupported source", "NotSupportedError");
  };
  f.$("play-button").click();
  await flush();
  assert.equal(f.$("current-label").textContent, "friend");
  assert.match(f.$("warnings").textContent, /Skipping/);
});

test("expanded library paginates, filters categories and resets page on search", async (t) => {
  const entries = Array.from({ length: 60 }, (_, i) => ({
    id: `sign${i}`,
    text: `sign${String(i).padStart(2, "0")}`,
    type: "word",
    category: i % 2 ? "Health" : "Food",
    meaning: "Fixture",
    previewable: true,
    ready: false,
  }));
  const f = await fixture(t, async () => response(sequence("unused")), {
    ...inventory,
    total: 60,
    entries,
  });
  assert.equal(f.w.document.querySelectorAll(".library-item").length, 24);
  f.$("library-next").click();
  assert.match(f.$("library-page").textContent, /Page 2/);
  f.$("library-search").value = "sign59";
  f.$("library-search").dispatchEvent(new f.w.Event("input"));
  assert.equal(f.w.document.querySelectorAll(".library-item").length, 1);
  assert.equal(f.$("library-pagination").hidden, true);
  f.$("library-search").value = "";
  f.$("library-search").dispatchEvent(new f.w.Event("input"));
  f.$("library-category").value = "Food";
  f.$("library-category").dispatchEvent(new f.w.Event("change"));
  assert.match(f.$("library-summary").textContent, /30 entries/);
  assert.match(f.$("library-page").textContent, /Page 1/);
});

test("choosing a letter previews that exact asset even if a word shares its text", async (t) => {
  let converts = 0;
  const entries = [
    {
      id: "word_i",
      text: "i",
      type: "word",
      category: "People",
      meaning: "Pronoun",
      previewable: true,
      ready: false,
    },
    {
      id: "i",
      text: "i",
      type: "alphabet",
      category: "Alphabet",
      meaning: "Letter",
      previewable: true,
      ready: false,
    },
  ];
  const f = await fixture(
    t,
    async () => {
      converts++;
      return response(sequence("i"));
    },
    { ...inventory, total: 2, entries },
  );
  f.$("library-type").value = "alphabet";
  f.$("library-type").dispatchEvent(new f.w.Event("change"));
  f.w.document.querySelector(".library-item button").click();
  await flush();
  assert.equal(converts, 0);
  assert.match(f.$("current-label").textContent, /spelling/);
  assert.match(f.$("sign-video").getAttribute("src"), /\/api\/media\/i$/);
});

test('quality report measures loading and failure without retaining message text', async (t) => {
  const f = await fixture(t, async () => response(sequence('hello', 'friend')));
  await f.convert('private message');
  let video = f.$('sign-video');
  video.dispatchEvent(new f.w.Event('loadeddata'));
  f.$('play-button').click();
  await flush();
  video.dispatchEvent(new f.w.Event('waiting'));
  video.dispatchEvent(new f.w.Event('playing'));
  video.dispatchEvent(new f.w.Event('error'));
  await flush();
  f.$('sign-video').dispatchEvent(new f.w.Event('ended'));
  const report = f.w.SignBridgeDiagnostics.snapshot();
  assert.equal(report.runs[0].outcome, 'completed');
  assert.equal(report.runs[0].media_errors, 1);
  assert.equal(report.runs[0].ended_clips, 1);
  assert.equal(report.runs[0].stall_count, 1);
  assert.ok(report.runs[0].submit_to_loaded_ms >= 0);
  assert.ok(!JSON.stringify(report).includes('private message'));
});

test('reviewed sentence mode is explicit in the conversion request', async (t) => {
  let request;
  const f = await fixture(t, async (url, options) => {
    request = JSON.parse(options.body); return response(sequence('hello'));
  });
  f.$('sentence-mode').checked = true;
  await f.convert('hello');
  assert.equal(request.mode, 'reviewed_sentence');
});
