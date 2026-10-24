import sys,json,numpy as np,torch,wave
from silero_vad import load_silero_vad,get_speech_timestamps
import sherpa_onnx
M=sys.argv[1]
rec=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+"/turbo-encoder.int8.onnx",decoder=M+"/turbo-decoder.int8.onnx",tokens=M+"/turbo-tokens.txt",language="pt",num_threads=4)
vad=load_silero_vad(onnx=True)
for f in sys.argv[2:]:
    w=wave.open(f); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    ts=get_speech_timestamps(torch.from_numpy(a),vad,sampling_rate=16000,min_silence_duration_ms=150,speech_pad_ms=30,threshold=0.5,return_seconds=True)
    out=[]
    for t in ts:
        s,e=t['start'],t['end']
        st=rec.create_stream(); st.accept_waveform(16000,a[int(max(0,s-0.1)*16000):int((e+0.1)*16000)])
        rec.decode_stream(st); txt=st.result.text.strip()
        out.append({"s":s,"e":e,"text":txt}); print(f"{s:6.2f}-{e:6.2f} {txt}",flush=True)
    json.dump(out,open(f.replace(".wav","_vad.json"),"w"),ensure_ascii=False,indent=0)
    print("----")
