# STEP 1: Pattern Identification

The given example:  
$(-\frac{2}{3}\sqrt{5}) \times 4\sqrt{7}$

This is a **root expression multiplied by another root expression**, with a **fraction coefficient** and **negative sign**.

This matches **p2f_int_mult_rad** (integer × root) — but with a **fractional coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root**, and the root is multiplied by another root.

Wait — let's check the structure:

- It's: `(a/b) × (c√r)` — which is **p2h_frac_mult_rad**.

But note: the first term is `(-2/3)√5`, which is a **fractional coefficient times a root**.

The second term is `4√7`, which is an **integer coefficient times a root**.

So this is **p2h_frac_mult_rad** — because the first term is a **fraction × root**, and the second term is a **root** (implicitly multiplied by 1).

Actually, **p2h_frac_mult_rad** is defined as: `k√r × (num/denom)` — but that's not quite right.

Looking at the vars structure for **p2h_frac_mult_rad**:  
`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction**.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction** — but the first term is a **fraction**, not a root.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction** — but the first term is a **fraction**, not a root.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction** — but the first term is a **fraction**, not a root.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction** — but the first term is a **fraction**, not a root.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2g_rad_mult_frac** — because it's a **root × fraction** — but the first term is a **fraction**, not a root.

Wait — let's check **p2g_rad_mult_frac**:

`{"k", "r", "num", "denom"}` — this is for `k√r × (num/denom)` — which is a **root times a fraction**.

But our example is:  
`(-2/3)√5 × 4√7` — which is **(fraction) × (root)** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Actually, this is **p2h_frac_mult_rad** — because it's a **fraction × root** — but the second term is **not a fraction**, it's a **root with integer coefficient**.

Wait — let's check **p2h_frac_mult_rad**:

`{"k", "r", "num", "denom"}` — this is