// クオンタイズ → 小節/休符/音価 → 表示モデル生成
import { CONFIG, makeAssigner } from "./tabMapper.js";

const SHARP = ["c", "c#", "d", "d#", "e", "f", "f#", "g", "g#", "a", "a#", "b"];

function midiToKey(m) {
  const pc = SHARP[((m % 12) + 12) % 12];
  const oct = Math.floor(m / 12) - 1;
  const acc = pc.length > 1 ? "#" : null;
  return { key: `${pc}/${oct}`, acc };
}

// 音価テーブル: [16分単位の長さ, VexFlow基本音価, 付点数]（降順）
const DUR = [
  [16, "w", 0],
  [12, "h", 1],
  [8, "h", 0],
  [6, "q", 1],
  [4, "q", 0],
  [3, "8", 1],
  [2, "8", 0],
  [1, "16", 0],
];

// 16分単位の長さ len を、演奏可能な音価の並びに貪欲分解
function decompose(len) {
  const out = [];
  let r = len;
  while (r > 0) {
    const m = DUR.find((x) => x[0] <= r) || DUR[DUR.length - 1];
    out.push({ base: m[1], dots: m[2] });
    r -= m[0];
  }
  return out;
}

// midi: Midiオブジェクト, trackIndex, instrument('bass4'|'bass5'|'guitar'), gridDiv(8|16)
export function buildModel(midi, trackIndex, instrument, gridDiv) {
  const conf = CONFIG[instrument];
  const ppq = midi.header.ppq || 480;
  const track = midi.tracks[trackIndex];
  const tsArr =
    (midi.header.timeSignatures &&
      midi.header.timeSignatures[0] &&
      midi.header.timeSignatures[0].timeSignature) || [4, 4];
  const num = tsArr[0];
  const den = tsArr[1];

  const snap = (ppq * 4) / gridDiv; // グリッド1ステップのtick数
  const f = 16 / gridDiv; // グリッド1ステップ = 16分いくつ分か
  const measureSix = (num * 16) / den; // 1小節 = 16分いくつ分か

  // 音符を16分単位へクオンタイズ
  const qnotes = (track.notes || [])
    .map((n) => ({
      start: Math.round(n.ticks / snap) * f,
      len: Math.max(f, Math.round(n.durationTicks / snap) * f),
      midi: n.midi,
    }))
    .filter((n) => n.len > 0)
    .sort((a, b) => a.start - b.start || a.midi - b.midi);

  // 同時刻開始をグループ化（和音）
  const groups = [];
  for (const n of qnotes) {
    const g = groups[groups.length - 1];
    if (g && g.start === n.start) {
      g.pitches.push(n.midi);
      g.len = Math.max(g.len, n.len);
    } else {
      groups.push({ start: n.start, len: n.len, pitches: [n.midi] });
    }
  }

  // 連続した単声セグメントへ（重なりは後発開始でクランプ、空きは休符）
  const segments = [];
  let pos = 0;
  for (let i = 0; i < groups.length; i++) {
    let start = groups[i].start;
    if (start < pos) start = pos;
    const nextStart = i + 1 < groups.length ? groups[i + 1].start : Infinity;
    const len = Math.min(groups[i].len, nextStart - start);
    if (len <= 0) continue;
    if (start > pos) segments.push({ start: pos, len: start - pos, rest: true });
    segments.push({ start, len, pitches: groups[i].pitches });
    pos = start + len;
  }
  const totalMeasures = Math.max(1, Math.ceil(pos / measureSix));
  if (pos < totalMeasures * measureSix) {
    segments.push({
      start: pos,
      len: totalMeasures * measureSix - pos,
      rest: true,
    });
  }

  // 小節へ分配（境界で分割 → 音価へ分解）
  const measures = Array.from({ length: totalMeasures }, () => ({ tokens: [] }));
  const assign = makeAssigner(conf.tuning);
  for (const seg of segments) {
    let s = seg.start;
    let rem = seg.len;
    while (rem > 0) {
      const mi = Math.min(totalMeasures - 1, Math.floor(s / measureSix));
      const mEnd = (mi + 1) * measureSix;
      const take = Math.min(rem, mEnd - s);
      for (const frag of decompose(take)) {
        if (seg.rest) {
          measures[mi].tokens.push({ rest: true, base: frag.base, dots: frag.dots });
        } else {
          const keys = seg.pitches.map((p) => midiToKey(p + conf.shift).key);
          const accs = seg.pitches.map((p) => midiToKey(p + conf.shift).acc);
          const positions = assign(seg.pitches).map((x) => ({ str: x.str, fret: x.fret }));
          measures[mi].tokens.push({
            rest: false,
            base: frag.base,
            dots: frag.dots,
            keys,
            accs,
            positions,
          });
        }
      }
      s += take;
      rem -= take;
    }
  }

  return {
    measures,
    clef: conf.clef,
    numStrings: conf.tuning.length,
    timeSig: `${num}/${den}`,
    tsNum: num,
    tsDen: den,
  };
}
