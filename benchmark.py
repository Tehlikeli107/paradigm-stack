"""Benchmark: compare ParadigmStack vs Transformer on Shakespeare."""
import torch, torch.nn as nn, torch.nn.functional as F, time, math, os
from paradigm_stack import ParadigmStack

DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

SHAKESPEARE_PATH = os.path.join(os.path.dirname(__file__), 'shakespeare.txt')
if not os.path.exists(SHAKESPEARE_PATH):
    import urllib.request
    print("Downloading Shakespeare...")
    urllib.request.urlretrieve(
        'https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt',
        SHAKESPEARE_PATH
    )

with open(SHAKESPEARE_PATH, 'r', encoding='utf-8') as f:
    text = f.read()
chars = sorted(set(text))
c2i = {c: i for i, c in enumerate(chars)}
V = len(chars)
data = torch.tensor([c2i[c] for c in text], dtype=torch.long, device=DEVICE)

SEQ = 256
train_data = data[:int(len(data)*0.9)]
val_data = data[int(len(data)*0.9):]

def get_batch(split, bs=32):
    d = train_data if split == 'train' else val_data
    ix = torch.randint(len(d) - SEQ - 1, (bs,))
    return torch.stack([d[i:i+SEQ] for i in ix]), torch.stack([d[i+1:i+SEQ+1] for i in ix])

class TransformerBaseline(nn.Module):
    def __init__(self, V, d, nh, nl, maxN):
        super().__init__()
        self.embed = nn.Embedding(V, d); self.pos = nn.Embedding(maxN, d); self.drop = nn.Dropout(0.1)
        el = nn.TransformerEncoderLayer(d, nh, d*4, batch_first=True, activation='gelu', dropout=0.1)
        self.enc = nn.TransformerEncoder(el, nl); self.norm_f = nn.LayerNorm(d); self.head = nn.Linear(d, V)
    def forward(self, ids):
        B, N = ids.shape; x = self.drop(self.embed(ids) + self.pos(torch.arange(N, device=ids.device)))
        return self.head(self.norm_f(self.enc(x, mask=torch.triu(torch.ones(N,N,device=ids.device),1).bool())))

def train_and_eval(name, model, steps=8000, bs=24):
    model = model.to(DEVICE); np_ = sum(p.numel() for p in model.parameters())
    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=1e-5)
    t0 = time.time()
    for step in range(steps):
        model.train(); inp, tgt = get_batch('train', bs)
        loss = F.cross_entropy(model(inp).reshape(-1, V), tgt.reshape(-1))
        opt.zero_grad(); loss.backward(); torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0); opt.step(); sched.step()
        if (step + 1) % 2000 == 0:
            model.eval()
            with torch.no_grad():
                vls = []
                for _ in range(5):
                    vi, vt = get_batch('val', 48)
                    vls.append(F.cross_entropy(model(vi).reshape(-1,V), vt.reshape(-1)).item())
            print(f"  {name} step {step+1}/{steps}: val_loss={sum(vls)/5:.3f}")
    elapsed = time.time() - t0
    model.eval()
    with torch.no_grad():
        losses = []
        for _ in range(50):
            vi, vt = get_batch('val', 48)
            losses.append(F.cross_entropy(model(vi).reshape(-1,V), vt.reshape(-1)).item())
        vl = sum(losses)/len(losses); vp = math.exp(vl)
    return vl, vp, np_, elapsed

if __name__ == "__main__":
    D = 192
    print(f"Benchmark: Shakespeare char-level (d={D}, seq={SEQ})")
    print(f"Data: {len(text)} chars, vocab={V}")
    print("=" * 55)
    configs = [
        ("Transformer 6L", TransformerBaseline(V, D, 4, 6, SEQ+1)),
        ("Stack AAMM", ParadigmStack(V, D, "AAMM", SEQ, n_heads=4)),
        ("Stack AAMMA", ParadigmStack(V, D, "AAMMA", SEQ, n_heads=4)),
        ("Stack MMMMMM", ParadigmStack(V, D, "MMMMMM", SEQ, n_heads=4)),
    ]
    results = []
    for name, model in configs:
        torch.manual_seed(42)
        vl, vp, np_, elapsed = train_and_eval(name, model)
        results.append((name, vl, vp, np_, elapsed))
        print(f"  >> {name:18s}: PPL={vp:.1f} loss={vl:.3f} params={np_:,} time={elapsed:.0f}s\n")
    print("\n--- FINAL RANKING ---")
    for r in sorted(results, key=lambda x: x[1]):
        print(f"  {r[0]:18s}: PPL={r[2]:.1f} params={r[3]:,} time={r[4]:.0f}s")
