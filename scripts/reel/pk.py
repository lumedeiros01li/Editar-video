import sys,json,numpy as np,wave
import sherpa_onnx
M=sys.argv[1]
rec=sherpa_onnx.OfflineRecognizer.from_transducer(encoder=M+"/encoder.int8.onnx",decoder=M+"/decoder.int8.onnx",joiner=M+"/joiner.int8.onnx",tokens=M+"/tokens.txt",model_type="nemo_transducer",num_threads=4)
for f in sys.argv[2:]:
    w=wave.open(f); a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    st=rec.create_stream(); st.accept_waveform(16000,a); rec.decode_stream(st); r=st.result
    print(r.text)
    # group tokens into words
    words=[]
    for tok,t in zip(r.tokens,r.timestamps):
        if tok.startswith("▁") or tok.startswith(" ") or not words:
            words.append({"w":tok.lstrip("▁ "),"s":float(t)})
        else: words[-1]["w"]+=tok
    for i,wd in enumerate(words):
        wd["e"]=words[i+1]["s"] if i+1<len(words) else wd["s"]+0.4
    json.dump(words,open(f.replace(".wav","_words.json"),"w"),ensure_ascii=False)
    print(" ".join(f"{x['w']}@{x['s']:.2f}" for x in words)); print("----")
