// VexFlowで五線譜＋タブ譜を描画（両者を同じFormatterで整列）
import {
  Renderer,
  Stave,
  StaveNote,
  TabStave,
  TabNote,
  GhostNote,
  Voice,
  Formatter,
  Accidental,
  Dot,
} from "https://esm.sh/vexflow@4.2.3";

export function render(container, model, opts = {}) {
  container.innerHTML = "";
  const width = opts.width || 1000;
  const perRow = opts.measuresPerRow || 4;
  const mW = Math.max(160, Math.floor((width - 20) / perRow));
  const rowH = 200;
  const rows = Math.ceil(model.measures.length / perRow);

  const renderer = new Renderer(container, Renderer.Backends.SVG);
  renderer.resize(width, rows * rowH + 30);
  const ctx = renderer.getContext();

  model.measures.forEach((measure, mi) => {
    const col = mi % perRow;
    const row = Math.floor(mi / perRow);
    const x = 10 + col * mW;
    const yTop = 20 + row * rowH;
    const yTab = yTop + 95;
    const first = col === 0;

    const stave = new Stave(x, yTop, mW);
    const tab = new TabStave(x, yTab, mW);
    if (tab.setNumLines) tab.setNumLines(model.numStrings);
    if (first) {
      stave.addClef(model.clef);
      try {
        tab.addClef("tab");
      } catch (e) {
        /* tabクレフ未対応でも継続 */
      }
      if (row === 0) stave.addTimeSignature(model.timeSig);
    }
    stave.setContext(ctx).draw();
    tab.setContext(ctx).draw();

    const staveNotes = [];
    const tabNotes = [];
    for (const t of measure.tokens) {
      if (t.rest) {
        const sn = new StaveNote({
          keys: [model.clef === "bass" ? "d/3" : "b/4"],
          duration: t.base + "r",
          clef: model.clef,
        });
        if (t.dots) Dot.buildAndAttach([sn]);
        staveNotes.push(sn);
        tabNotes.push(new GhostNote(t.base));
      } else {
        const sn = new StaveNote({
          keys: t.keys,
          duration: t.base,
          clef: model.clef,
        });
        t.accs.forEach((a, i) => {
          if (a) sn.addModifier(new Accidental(a), i);
        });
        if (t.dots) Dot.buildAndAttach([sn]);
        staveNotes.push(sn);

        const tn = new TabNote({
          positions: t.positions.map((p) => ({ str: p.str, fret: p.fret })),
          duration: t.base,
        });
        if (t.dots) {
          try {
            Dot.buildAndAttach([tn]);
          } catch (e) {
            /* タブの付点は任意 */
          }
        }
        tabNotes.push(tn);
      }
    }
    if (!staveNotes.length) return;

    const v1 = new Voice({ num_beats: model.tsNum, beat_value: model.tsDen })
      .setMode(Voice.Mode.SOFT)
      .addTickables(staveNotes);
    const v2 = new Voice({ num_beats: model.tsNum, beat_value: model.tsDen })
      .setMode(Voice.Mode.SOFT)
      .addTickables(tabNotes);
    new Formatter()
      .joinVoices([v1])
      .joinVoices([v2])
      .format([v1, v2], mW - 30);
    v1.draw(ctx, stave);
    v2.draw(ctx, tab);
  });
}
