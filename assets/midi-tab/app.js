// エントリ: DOM制御・状態管理・各モジュール結線
import { loadMidi } from "./midiLoader.js";
import { summarizeTracks, pickTrack } from "./trackAnalyzer.js";
import { buildModel } from "./noteModel.js";
import { render } from "./renderer.js";
import { downloadPNG, printScore } from "./exporter.js";

const $ = (id) => document.getElementById(id);

let midi = null;
let summaries = [];

function setStatus(msg, isError = false) {
  const el = $("status");
  el.textContent = msg;
  el.className = "status" + (isError ? " error" : "");
}

function fillTracks() {
  const sel = $("track");
  sel.innerHTML = "";
  summaries.forEach((s) => {
    const label =
      `#${s.index} ${s.name} — ${s.count}音` +
      (s.guess !== "other" ? ` (推定:${s.guess})` : "");
    const opt = document.createElement("option");
    opt.value = String(s.index);
    opt.textContent = label;
    sel.appendChild(opt);
  });
}

function autoPickTrack() {
  const instrument = $("instrument").value;
  const idx = pickTrack(summaries, instrument);
  $("track").value = String(idx);
}

function doRender() {
  if (!midi) return;
  try {
    const trackIndex = parseInt($("track").value, 10) || 0;
    const instrument = $("instrument").value;
    const gridDiv = parseInt($("grid").value, 10) || 16;
    const perRow = parseInt($("perRow").value, 10) || 4;
    const model = buildModel(midi, trackIndex, instrument, gridDiv);
    if (!model.measures.length) {
      setStatus("この設定では表示できる音符がありません。", true);
      return;
    }
    render($("score"), model, {
      width: Math.min(1100, $("score").clientWidth || 1000),
      measuresPerRow: perRow,
    });
    setStatus(
      `${instrument} / トラック#${trackIndex} / ${model.measures.length}小節 を表示 ` +
        `（五線譜はオクターブ上げ=8vb表示）`
    );
  } catch (e) {
    console.error(e);
    setStatus("描画に失敗しました: " + e.message, true);
  }
}

async function onFile(file) {
  if (!file) return;
  try {
    setStatus("読み込み中… " + file.name);
    midi = await loadMidi(file);
    summaries = summarizeTracks(midi);
    if (!summaries.length) {
      setStatus("トラックが見つかりませんでした。", true);
      return;
    }
    fillTracks();
    autoPickTrack();
    doRender();
    $("controls").hidden = false;
    $("exports").hidden = false;
  } catch (e) {
    console.error(e);
    setStatus("MIDIの読み込みに失敗しました: " + e.message, true);
  }
}

function wire() {
  const drop = $("drop");
  const fileInput = $("file");

  drop.addEventListener("click", () => fileInput.click());
  drop.addEventListener("dragover", (e) => {
    e.preventDefault();
    drop.classList.add("over");
  });
  drop.addEventListener("dragleave", () => drop.classList.remove("over"));
  drop.addEventListener("drop", (e) => {
    e.preventDefault();
    drop.classList.remove("over");
    if (e.dataTransfer.files[0]) onFile(e.dataTransfer.files[0]);
  });
  fileInput.addEventListener("change", (e) => onFile(e.target.files[0]));

  // 楽器を変えたら対象トラックも自動で選び直す
  $("instrument").addEventListener("change", () => {
    autoPickTrack();
    doRender();
  });
  ["track", "grid", "perRow"].forEach((id) =>
    $(id).addEventListener("change", doRender)
  );

  $("png").addEventListener("click", () => downloadPNG($("score"), "tab.png"));
  $("print").addEventListener("click", printScore);
}

wire();
