
function floatTo16BitPCM(input) {
  let i      = input.length;
  let output = new Int16Array(i);
  while (i--) {
    let s     = Math.max(-1, Math.min(1, input[i]));
    output[i] = (s < 0 ? s * 0x8000 : s * 0x7FFF);
  }
  return output;
}

function int16ToFloat32BitPCM(input) {
  let i      = input.length;
  let output = new Float32Array(i);
  while (i--) {
    let int   = input[i];
    output[i] = (int >= 0x8000) ? -(0x10000 - int) / 0x8000 : int / 0x7FFF;
  }
  return output;
}

