# Paradigm Stack

**Heterogeneous computation architecture that beats Transformer on both synthetic and real language tasks.**

Instead of repeating the same layer type (e.g., 6x attention), Paradigm Stack uses **different computation paradigms in each layer** -- like how the brain uses different processing in visual cortex vs auditory cortex vs motor cortex.

## Results

### Synthetic Tasks (6 diverse algorithmic tasks, seq=50)
| Model | Accuracy | Params |
|---|---|---|
| **Paradigm Stack (FLC)** | **99.9%** | **102K** |
| Transformer (6L) | 48.7% | 206K |

### Real Language (Shakespeare character-level, d=192, seq=256)
| Model | PPL | Params | Speed |
|---|---|---|---|
| **Stack MMMMMM** | **4.5** | **2.55M** | **391s** |
| Stack AAMMA | 4.6 | 2.23M | 447s |
| Stack AAMM | 4.7 | 1.79M | 346s |
| Transformer 6L | 4.8 | 2.74M | 518s |

## Quick Start

```python
from paradigm_stack import ParadigmStack

model = ParadigmStack(
    vocab_size=50257,
    d_model=256,
    pattern="AAMM",   # 2x Attention + 2x MultiScaleConv
    seq_len=512,
)
logits = model(input_ids)  # [B, N, vocab_size]
```

## Available Paradigms

| Code | Name | What it does | Complexity |
|---|---|---|---|
| **A** | Attention | Causal self-attention (selective long-range) | O(N^2) |
| **M** | MultiScaleConv | Depthwise causal conv at k=3,7,15 | O(N) |
| **P** | CausalPool | Gated cumulative mean (global context) | O(N) |
| **L** | CausalLocal | Causal sliding window (w=7) | O(N) |
| **D** | CausalDiff | Change detection (derivatives) | O(N) |

## Recommended Patterns

- `"AAMM"` -- Fast, param-efficient, good quality **(recommended for most uses)**
- `"AAMMA"` -- Better quality, slightly more params
- `"MMMMMM"` -- Best PPL, no attention, fully O(N)
- `"AMAMP"` -- Balanced mix of all paradigm types

## Why It Works

Different paradigms capture different types of information:
- **Attention**: Selective pairwise relationships (who is related to whom)
- **MultiScaleConv**: Local patterns at multiple scales (n-gram features)
- **CausalPool**: Running global statistics (what's the overall context)
- **CausalDiff**: Rate of change (what just changed)

Repeating the same paradigm (e.g., 6x attention) creates **redundancy**. Mixing paradigms creates **complementary representations** that are more parameter-efficient.

## Citation

If you use this work, please cite:
```
@software{paradigm_stack,
  title={Paradigm Stack: Heterogeneous Computation Architecture},
  year={2026},
  url={https://github.com/Tehlikeli107/paradigm-stack}
}
```

## License

MIT
