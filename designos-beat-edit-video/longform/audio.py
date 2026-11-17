import numpy as np, soundfile as sf, sys
sys.argv=['x','info']
import build as b
SR=48000; T=b.TOTAL+1.0; N=int(T*SR)
voice=np.zeros(N,np.float32)
for k in b.ORDER:
    x,sr,_=b.VO[k]; s=int((b.gstart(k)+b.voff(k))*SR); voice[s:s+len(x)]+=x[:N-s].astype(np.float32)
# music: bright, 104 bpm, C major pentatonic plucks + pad + soft hat
rng=np.random.default_rng(7); bpm=104; beat=60/bpm; t=np.arange(N)/SR
mus=np.zeros(N,np.float32)
def note(f,dur,vel=1.0,kind="pluck"):
    n=int(dur*SR); tt=np.arange(n)/SR
    if kind=="pluck":
        w=np.sin(2*np.pi*f*tt)+0.4*np.sin(4*np.pi*f*tt)+0.15*np.sin(6*np.pi*f*tt); e=np.exp(-tt*6.5)*(1-np.exp(-tt*400))
    else:
        w=np.sin(2*np.pi*f*tt)+0.5*np.sin(2*np.pi*f*1.003*tt)+0.25*np.sin(4*np.pi*f*tt); e=np.minimum(1,tt/0.6)*np.minimum(1,(dur-tt)/0.8)
    return (w*e*vel).astype(np.float32)
def put(sig,at):
    s=int(at*SR); e=min(N,s+len(sig))
    if s<N: mus[s:e]+=sig[:e-s]
chords=[(261.63,329.63,392.0),(220.0,261.63,329.63),(174.61,220.0,261.63),(196.0,246.94,293.66)]
pent=[523.25,587.33,659.25,783.99,880.0,1046.5]
bar=4*beat; nb=int(T/bar)+1
for i in range(nb):
    ch=chords[i%4]; at=i*bar
    for f in ch: put(note(f/2,bar+0.3,0.09,"pad"),at)
    put(note(ch[0]/4,beat*1.8,0.22),at); put(note(ch[0]/4,beat*1.8,0.2),at+2*beat)
    pat=[0,2,4,2,1,3,5,3] if i%2==0 else [4,2,0,2,5,3,1,3]
    for j,p in enumerate(pat):
        f=pent[p]*(ch[0]/261.63)**0.0
        # keep inside chord-ish scale by snapping to chord tones on strong beats
        if j%2==0: f=ch[(j//2)%3]*2
        put(note(f,0.5,0.17 if j%2==0 else 0.11),at+j*beat/2)
    for j in range(8):  # hat
        n=int(0.04*SR); h=(rng.standard_normal(n)*np.exp(-np.arange(n)/SR*90)).astype(np.float32)*(0.035 if j%2 else 0.02); put(h,at+j*beat/2)
    n=int(0.12*SR); kk=np.sin(2*np.pi*(60+80*np.exp(-np.arange(n)/SR*40))*np.arange(n)/SR)*np.exp(-np.arange(n)/SR*25)
    for j in (0,2): put((kk*0.2).astype(np.float32),at+j*beat)
mus/= max(1e-6,np.abs(mus).max()); mus*=0.5
# sidechain: duck under voice
env=np.abs(voice); k=int(0.12*SR); env=np.convolve(env,np.ones(k)/k,'same'); env=np.clip(env/0.04,0,1)
sm=np.convolve(env,np.ones(int(0.25*SR))/int(0.25*SR),'same')
duck=1-0.78*sm
fade=np.minimum(1,t/2.0)*np.minimum(1,(T-t)/3.0)
mix_m=mus*duck*fade*0.55
v=voice/ max(1e-6,np.abs(voice).max()) *0.9
mix=v+mix_m; mix/=max(1,np.abs(mix).max()/0.92)
sf.write(b.ROOT+'/out/audio.wav',np.stack([mix,mix],1),SR)
print('ok',T)
