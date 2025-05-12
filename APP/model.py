import torch.nn as nn
import torch.nn.functional as F
import torch
from config import CONFIG
from midi_processor import synchronized

class Head(nn.Module):
    def __init__(self, head_size, n_embd, block_size, dropout=0.1, relative_pos=True):
        super().__init__()
        self.key = nn.Linear(n_embd, head_size, bias=False)
        self.query = nn.Linear(n_embd, head_size, bias=False)
        self.value = nn.Linear(n_embd, head_size, bias=False)
        self.dropout = nn.Dropout(dropout)
        self.block_size = block_size
        self.relative_pos = relative_pos
        if relative_pos:
            # Er: [block_size, head_size]
            self.Er = nn.Parameter(torch.randn(CONFIG['max_sequence_len'], head_size))
        else:
            self.Er = None

    def _skew(self, x):
        B, T1, T2 = x.size()
        x = F.pad(x, (1, 0))              # (B, T, T+1)
        x = x.view(B, T2 + 1, T1)
        x = x[:, 1:, :]
        return x.transpose(1, 2)


    def forward(self, x):
        B, T, C = x.shape
        k = self.key(x)            # (B, T, head_size)
        q = self.query(x)          # (B, T, head_size)
        v = self.value(x)          # (B, T, head_size)

        # Compute attention scores
        att = q @ k.transpose(-2, -1) / (k.size(-1) ** 0.5)  # (B, T, T)

        if self.relative_pos:
            Er_t = self.Er[:T, :].transpose(0, 1)            # (head_size, T)
            rel_att = q @ Er_t                               # (B, T, T)
            rel_att = self._skew(rel_att)                    # Skew to match shape
            att = att + rel_att

        # Apply causal mask
        mask = torch.tril(torch.ones(T, T, device=x.device))
        att = att.masked_fill(mask == 0, float("-inf"))

        att = F.softmax(att, dim=-1)
        att = self.dropout(att)
        out = att @ v                                         # (B, T, head_size)
        return out

class MultiHeadAttention(nn.Module):
    def __init__(self, num_heads, n_embd, block_size, dropout=0.1, relative_pos=True):
        super().__init__()
        head_size = n_embd // num_heads
        self.heads = nn.ModuleList([
            Head(head_size, n_embd, block_size, dropout, relative_pos=relative_pos)
            for _ in range(num_heads)
        ])
        self.proj = nn.Linear(n_embd, n_embd)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        out = torch.cat([h(x) for h in self.heads], dim=-1)
        return self.dropout(self.proj(out))

class FeedForward(nn.Module):
    def __init__(self, n_embd, dropout=0.1):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(n_embd, 4 * n_embd),
            nn.GELU(),
            nn.Linear(4 * n_embd, n_embd),
            nn.Dropout(dropout)
        )

    def forward(self, x):
        return self.net(x)

class Block(nn.Module):
    def __init__(self, n_embd, n_head, block_size, dropout=0.1):
        super().__init__()
        self.sa = MultiHeadAttention(n_head, n_embd, block_size, dropout)
        self.ffwd = FeedForward(n_embd, dropout)
        self.ln1 = nn.LayerNorm(n_embd)
        self.ln2 = nn.LayerNorm(n_embd)

    def forward(self, x):
        x = x + self.sa(self.ln1(x))
        x = x + self.ffwd(self.ln2(x))
        return x
        


class TransformerMIDILanguageModel(nn.Module):
    def __init__(self, config):
        super().__init__()

        self.block_size    = config['block_size']
        self.vocab_size    = config['vocab_size']
        self.sos_token_id  = config['token_sos']
        self.pad_token_id  = config['token_pad']
        self.eos_token_id  = config['token_eos']

        self.token_embedding_table = nn.Embedding(
            self.vocab_size,
            config['embedding_dim'],
            padding_idx=self.pad_token_id
        )

        # self.position_embedding_table = nn.Embedding(self.block_size, config['embedding_dim'])

        self.blocks = nn.Sequential(*[
            Block(n_embd=config['embedding_dim'],
                  n_head=config['num_heads'],
                  block_size=config['block_size'],
                  dropout=0.1)
            for _ in range(config['num_layers'])
            ])

        self.ln_f = nn.LayerNorm(config['embedding_dim'])
        self.lm_head = nn.Linear(config['embedding_dim'], self.vocab_size)


    def forward(self, idx, targets=None):
        B, T = idx.shape
        tok_emb = self.token_embedding_table(idx)
        # pos_emb = self.position_embedding_table(torch.arange(T, device=idx.device))

        x = self.blocks(tok_emb)
        x = self.ln_f(x)

        logits = self.lm_head(x)

        loss = None
        if targets is not None:
            loss = F.cross_entropy(logits.view(-1, self.vocab_size), targets.view(-1), ignore_index=self.pad_token_id)
        return logits, loss


    
    @torch.no_grad()
    def generate(self, idx, max_new_tokens, eos_token_id, temperature=1.0, top_k=None):
        print("entered generate")
        idx = torch.tensor([idx], dtype=torch.long)
        

        for _ in range(max_new_tokens):
            idx_cond = idx[:, -self.block_size:]
            logits, _ = self(idx_cond)

            logits = logits[:, -1, :] / temperature

            if top_k is not None:
                v, _ = torch.topk(logits, top_k, dim=-1)
                min_vals = v[:, -1].unsqueeze(1)
                logits[logits < min_vals] = -float('Inf')

            probs = F.softmax(logits, dim=-1)
            idx_next = torch.multinomial(probs, num_samples=1)
            idx = torch.cat([idx, idx_next], dim=1)

            if eos_token_id is not None:
                # check every item in batch
                eos_mask = idx_next.eq(eos_token_id).view(-1)
                if eos_mask.all():
                    break
        
        return idx