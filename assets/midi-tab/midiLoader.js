// MIDI読み込み: File → ArrayBuffer → @tonejs/midi でパース
import { Midi } from "https://esm.sh/@tonejs/midi@2.0.28";

export async function loadMidi(file) {
  const buf = await file.arrayBuffer();
  return new Midi(buf);
}
