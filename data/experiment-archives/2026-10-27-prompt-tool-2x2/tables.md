## Arms

| Cell | Arm | Runs | Task errors | Health [95% CI] | SEC path (runs) | Hard tool errors/run | Runs at budget | Unknown-tool calls (runs) | Total cost USD |
|---|---|---|---|---|---|---|---|---|---|
| A | luna_medium | 90 | 0 | 0.91 [0.82, 0.99] | G×67 ∅×23 | 0.12 | 9 | 0 (0) | 1.25 |
| B | reader_luna_medium | 90 | 0 | 0.92 [0.83, 0.99] | S+G×3 ∅×5 S×82 | 0.12 | 5 | 0 (0) | 0.47 |
| C | luna_medium_plus_search | 90 | 0 | 0.93 [0.84, 1.00] | S+G×6 G×4 ∅×22 S×58 | 0.13 | 6 | 0 (0) | 0.60 |
| D | reader_prompt_no_search | 90 | 0 | 0.89 [0.78, 0.98] | G×81 ∅×9 | 0.20 | 4 | 0 (0) | 1.01 |

SEC path codes: S = search only, G = get_section only, S+G = both, ∅ = neither.

## Routing (label-scored) per arm

| Cell | Arm | Routing recall | Recall (success only) | Unnecessary-call rate | Entity coverage | SEC skips / SEC-必要 runs | …no successful SEC call | Skips at budget | Skipped rows (runs) |
|---|---|---|---|---|---|---|---|---|---|
| A | luna_medium | 0.89 [0.77, 0.99] | 0.89 [0.77, 0.99] | 0.34 [0.20, 0.51] | 0.83 [0.64, 1.00] | 10 / 69 | 10 | 0 | 10×1 14×3 26×3 3×3 |
| B | reader_luna_medium | 0.95 [0.89, 1.00] | 0.94 [0.87, 1.00] | 0.26 [0.11, 0.43] | 0.75 [0.58, 0.92] | 0 / 69 | 0 | 0 | – |
| C | luna_medium_plus_search | 0.87 [0.77, 0.97] | 0.86 [0.76, 0.95] | 0.28 [0.14, 0.41] | 0.81 [0.61, 0.97] | 7 / 69 | 7 | 0 | 14×2 26×2 3×2 7×1 |
| D | reader_prompt_no_search | 0.97 [0.91, 1.00] | 0.94 [0.87, 1.00] | 0.23 [0.10, 0.38] | 0.86 [0.69, 1.00] | 2 / 69 | 2 | 0 | 14×1 26×1 |

## Process means per arm (per-row means, row bootstrap 95% CI)

| Cell | Arm | SEC evidence tokens | E2E s | Cost USD / run |
|---|---|---|---|---|
| A | luna_medium | 39,392 [24,933, 59,296] | 33.0 [30.6, 35.6] | 0.0139 [0.0092, 0.0207] |
| B | reader_luna_medium | 9,615 [7,538, 11,907] | 25.1 [23.0, 27.3] | 0.0052 [0.0046, 0.0059] |
| C | luna_medium_plus_search | 12,493 [9,469, 15,717] | 33.1 [30.6, 35.7] | 0.0067 [0.0059, 0.0076] |
| D | reader_prompt_no_search | 37,515 [27,625, 49,591] | 32.4 [29.2, 36.3] | 0.0112 [0.0091, 0.0137] |

## Factorial readout (per-row contrast, row bootstrap 95% CI)

Recall and unnecessary-call rate: rows without a full coverage gap. SEC skip: rows with SEC 10-K labelled 必要 and no coverage gap. Others: all rows.

| Effect | Δ recall (29 rows) | Δ unnecessary (29 rows) | Δ sec_skip (23 rows) | Δ sec_skip_no_success (23 rows) | Δ sec_evidence_tokens (30 rows) | Δ tool_calls_total (30 rows) | Δ e2e_s (30 rows) | Δ est_cost_usd (30 rows) |
|---|---|---|---|---|---|---|---|---|
| tool, baseline prompt (C − A) | -0.01 [-0.10, +0.07] | -0.07 [-0.15, -0.00] | -0.04 [-0.10, +0.01] | -0.04 [-0.10, +0.01] | -26,899 [-46,001, -13,438] | -0.0 [-0.4, +0.3] | +0.1 [-1.1, +1.5] | -0.0072 [-0.0140, -0.0027] |
| tool, reader prompt (B − D) | -0.01 [-0.09, +0.07] | +0.03 [-0.07, +0.15] | -0.03 [-0.07, +0.00] | -0.03 [-0.07, +0.00] | -27,900 [-39,933, -18,130] | -1.5 [-2.1, -0.9] | -7.3 [-9.8, -5.2] | -0.0060 [-0.0084, -0.0040] |
| prompt, no search (D − A) | +0.08 [+0.01, +0.17] | -0.11 [-0.26, +0.01] | -0.12 [-0.23, -0.01] | -0.12 [-0.23, -0.01] | -1,877 [-11,295, +5,683] | -0.4 [-0.8, +0.0] | -0.6 [-2.6, +1.9] | -0.0027 [-0.0075, +0.0006] |
| prompt, with search (B − C) | +0.08 [-0.01, +0.17] | -0.01 [-0.14, +0.10] | -0.10 [-0.20, -0.03] | -0.10 [-0.20, -0.03] | -2,878 [-5,103, -691] | -1.8 [-2.3, -1.3] | -8.0 [-9.6, -6.6] | -0.0015 [-0.0020, -0.0009] |
| bundle (B − A) | +0.07 [-0.06, +0.22] | -0.08 [-0.20, +0.02] | -0.14 [-0.30, -0.01] | -0.14 [-0.30, -0.01] | -29,777 [-49,692, -15,480] | -1.8 [-2.4, -1.3] | -7.9 [-9.2, -6.6] | -0.0087 [-0.0155, -0.0040] |
| **prompt main effect** | +0.08 [+0.01, +0.17] | -0.06 [-0.17, +0.02] | -0.11 [-0.22, -0.02] | -0.11 [-0.22, -0.02] | -2,378 [-7,541, +2,020] | -1.1 [-1.4, -0.7] | -4.3 [-5.7, -2.9] | -0.0021 [-0.0045, -0.0003] |
| **tool main effect** | -0.01 [-0.09, +0.06] | -0.02 [-0.07, +0.03] | -0.04 [-0.09, +0.00] | -0.04 [-0.09, +0.00] | -27,400 [-42,680, -15,487] | -0.8 [-1.1, -0.4] | -3.6 [-4.9, -2.3] | -0.0066 [-0.0111, -0.0034] |
| **interaction** | +0.00 [-0.07, +0.07] | +0.10 [-0.05, +0.29] | +0.01 [-0.03, +0.07] | +0.01 [-0.03, +0.07] | -1,001 [-8,075, +8,044] | -1.4 [-2.1, -0.8] | -7.5 [-10.4, -5.1] | +0.0012 [-0.0020, +0.0060] |

Exact sign test on the per-row contrasts (rows < 0 / rows > 0, ties dropped; two-sided p). A check on the bootstrap where few rows carry the contrast:

| Effect | recall | unnecessary | sec_skip | sec_skip_no_success |
|---|---|---|---|---|
| tool, baseline prompt (C − A) | 3 / 4 (p=1.000) | 6 / 2 (p=0.289) | 4 / 1 (p=0.375) | 4 / 1 (p=0.375) |
| tool, reader prompt (B − D) | 2 / 2 (p=1.000) | 3 / 3 (p=1.000) | 2 / 0 (p=0.500) | 2 / 0 (p=0.500) |
| prompt, no search (D − A) | 0 / 4 (p=0.125) | 7 / 3 (p=0.344) | 4 / 0 (p=0.125) | 4 / 0 (p=0.125) |
| prompt, with search (B − C) | 1 / 6 (p=0.125) | 4 / 4 (p=1.000) | 4 / 0 (p=0.125) | 4 / 0 (p=0.125) |
| bundle (B − A) | 2 / 4 (p=0.688) | 4 / 2 (p=0.688) | 4 / 0 (p=0.125) | 4 / 0 (p=0.125) |
| **prompt main effect** | 1 / 7 (p=0.070) | 6 / 2 (p=0.289) | 5 / 0 (p=0.062) | 5 / 0 (p=0.062) |
| **tool main effect** | 4 / 4 (p=1.000) | 4 / 3 (p=1.000) | 4 / 1 (p=0.375) | 4 / 1 (p=0.375) |
| **interaction** | 3 / 4 (p=1.000) | 3 / 5 (p=0.727) | 1 / 2 (p=1.000) | 1 / 2 (p=1.000) |

## Per row: SEC path by cell (and SEC skips on SEC-必要 rows)

| Row | SEC 必要 | A | B | C | D |
|---|---|---|---|---|---|
| 1 | yes | G×3 | S×3 | S×3 | G×3 |
| 2 | yes | G×3 | S×3 | G×1 S×2 | G×3 |
| 3 | yes | ∅×3 (**skip×3**) | S×3 | ∅×2 S×1 (**skip×2**) | G×3 |
| 4 |  | ∅×3 | S×3 | ∅×3 | ∅×3 |
| 5 |  | G×3 | S×3 | S×3 | G×3 |
| 6 | yes | G×3 | S×3 | S+G×1 S×2 | G×3 |
| 7 | yes | G×3 | S×3 | S+G×1 ∅×1 S×1 (**skip×1**) | G×3 |
| 8 | yes | G×3 | S×3 | S×3 | G×3 |
| 9 | yes | G×3 | S×3 | G×1 S×2 | G×3 |
| 10 | yes | G×2 ∅×1 (**skip×1**) | S×3 | S×3 | G×3 |
| 11 | yes | G×3 | S×3 | S×3 | G×3 |
| 12 | yes | G×3 | S×3 | S+G×2 S×1 | G×3 |
| 13 | yes | G×3 | S×3 | S×3 | G×3 |
| 14 | yes | ∅×3 (**skip×3**) | S×3 | ∅×2 S×1 (**skip×2**) | G×2 ∅×1 (**skip×1**) |
| 15 | yes | G×3 | S×3 | G×1 S×2 | G×3 |
| 16 | yes | G×3 | S×3 | S×3 | G×3 |
| 17 | yes | G×3 | S×3 | S×3 | G×3 |
| 18 | yes | G×3 | S×3 | S×3 | G×3 |
| 19 | yes | G×3 | S×3 | S×3 | G×3 |
| 20 | yes | G×3 | S×3 | S+G×1 S×2 | G×3 |
| 21 | yes | G×3 | S×3 | S×3 | G×3 |
| 22 | yes | G×3 | S×3 | S×3 | G×3 |
| 23 |  | G×2 ∅×1 | S×3 | ∅×2 S×1 | G×3 |
| 24 |  | ∅×3 | ∅×2 S×1 | ∅×3 | G×3 |
| 25 |  | ∅×3 | ∅×3 | ∅×3 | ∅×3 |
| 26 | yes | ∅×3 (**skip×3**) | S×3 | ∅×2 S×1 (**skip×2**) | G×2 ∅×1 (**skip×1**) |
| 27 | yes | G×3 | S×3 | S×3 | G×3 |
| 28 |  | ∅×3 | S×3 | ∅×2 S×1 | G×2 ∅×1 |
| 29 |  | G×3 | S×3 | ∅×2 S×1 | G×3 |
| 30 | yes | G×3 | S+G×3 | S+G×1 G×1 S×1 | G×3 |
