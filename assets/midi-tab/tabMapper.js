// チューニング定義と、音高→(弦,フレット)割当（MVP=貪欲法）

export const TUNINGS = {
  bass4: [28, 33, 38, 43], // E1 A1 D2 G2
  bass5: [23, 28, 33, 38, 43], // B0 E1 A1 D2 G2
  guitar: [40, 45, 50, 55, 59, 64], // E2 A2 D3 G3 B3 E4
};

// 楽器ごとの設定。shift は五線譜の表示オクターブ調整（8vb相当で可読性確保）
export const CONFIG = {
  bass4: { tuning: TUNINGS.bass4, clef: "bass", shift: 12 },
  bass5: { tuning: TUNINGS.bass5, clef: "bass", shift: 12 },
  guitar: { tuning: TUNINGS.guitar, clef: "treble", shift: 12 },
};

// 直前のフレット位置を記憶し、手の移動を最小化しながら割り当てるアサイナを返す。
// pitches(midi配列) を受け取り、[{str, fret}, ...] を返す。
export function makeAssigner(tuning, maxFret = 24) {
  let prev = 0;
  return (pitches) => {
    const chord = pitches.map((p) => {
      let best = null;
      for (let i = 0; i < tuning.length; i++) {
        const fret = p - tuning[i];
        if (fret < 0 || fret > maxFret) continue;
        const cost = Math.abs(fret - prev) + fret * 0.15;
        if (!best || cost < best.cost) {
          best = { str: tuning.length - i, fret, cost };
        }
      }
      if (!best) best = { str: 1, fret: 0 }; // 演奏不能音のフォールバック
      return best;
    });
    if (chord.length) prev = chord[0].fret;
    return chord.map((c) => ({ str: c.str, fret: c.fret }));
  };
}
