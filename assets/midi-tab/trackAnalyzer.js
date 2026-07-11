// トラック要約・パート自動判定・トラック選択

function guessType(program, family, avg) {
  if (family === "bass" || (program >= 32 && program <= 39)) return "bass";
  if (family === "guitar" || (program >= 24 && program <= 31)) return "guitar";
  if (avg && avg < 48) return "bass";
  return "other";
}

export function summarizeTracks(midi) {
  return midi.tracks.map((t, i) => {
    const notes = t.notes || [];
    const avg = notes.length
      ? notes.reduce((s, n) => s + n.midi, 0) / notes.length
      : 0;
    const program = t.instrument ? (t.instrument.number ?? -1) : -1;
    const family = t.instrument ? (t.instrument.family ?? "") : "";
    return {
      index: i,
      name: t.name || (t.instrument && t.instrument.name) || `Track ${i + 1}`,
      count: notes.length,
      avg,
      program,
      family,
      guess: guessType(program, family, avg),
    };
  });
}

// 楽器に合ったトラックのindexを推定
export function pickTrack(summaries, instrument) {
  const want = instrument.startsWith("bass") ? "bass" : "guitar";
  const withNotes = summaries.filter((s) => s.count > 0);
  if (!withNotes.length) return summaries.length ? summaries[0].index : 0;
  const matched = withNotes.filter((s) => s.guess === want);
  const pool = matched.length ? matched : withNotes;
  pool.sort((a, b) => (want === "bass" ? a.avg - b.avg : b.count - a.count));
  return pool[0].index;
}
