import os
import sys
from tqdm import tqdm

# Add the src directory to the Python path for standalone execution
# sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__))))
# sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# for dev
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.metrics import adjusted_rand_score
from itertools import combinations

# BIC = Bayesian Information Criterion
# A way to compare models with different numbers of clusters (or states), while penalizing complexity. Lower BIC is better.

# ICL = Integrated Completed Likelihood
# Similar to BIC, but it also penalizes uncertainty in cluster assignments. It is often preferred when you care about clear, well-separated clusters.

class SuggestRegions:
    def __init__(self, df, fixed_w=None):
        self.genomic_positions = df[["start", "end"]].to_numpy()
        self.np_df = df.drop(columns=["start", "end"]).to_numpy().T
        self.is_significant = None
        self.n_positions = self.np_df.shape[1]
        self.best_K = []
        self.best_labels = []
        self.bic_gap_weight = []
        self.mean_posterior_conf = []
        self.boundaries = []
        self.b_signal = None
        self.edge_scores = None
        self.edge_midpoints = None
        self.ari_dict = {}
        self.weight_dict = {}
        self.precomputed = False
        self.fixed_w = fixed_w if fixed_w is not None else int(self.n_positions // 100 + 1)

        self.main()

    def main(self):
        print("Starting search for regions...")
        self.gmm_assignment()
        print("Cluster assignment complete.")
        self.adjacent_window_scoring()
        print("Importance scoring complete.")
        self.set_region_values()
        print("Analysis complete.")

    def gmm_assignment(self):

        # n_positions = self.np_df.shape[1]

        for p in tqdm(range(self.n_positions)):
            y = self.np_df[:, p].reshape(-1, 1)
            labels = np.full(len(y), np.nan)

            y_no_nan = y[~np.isnan(y).any(axis=1)]
            models = {}
            bics = {}
            for k in [1, 2, 3]:
                gmm = GaussianMixture(
                    n_components=k,
                    covariance_type="full",
                    random_state=42,
                    n_init=10
                )
                gmm.fit(y_no_nan)
                models[k] = gmm
                bics[k] = gmm.bic(y_no_nan)

            k_best = min(bics, key=bics.get)
            sorted_bic = sorted(bics.items(), key=lambda z: z[1])
            gap = sorted_bic[1][1] - sorted_bic[0][1]

            gbest = models[k_best]
            labels[~np.isnan(y).any(axis=1)] = gbest.predict(y_no_nan)
            if k_best == 2:
                labels[~np.isnan(y).any(axis=1)] *= 2
            post = gbest.predict_proba(y_no_nan)
            conf = post.max(axis=1).mean()

            self.best_K.append(k_best)
            self.best_labels.append(labels)
            self.bic_gap_weight.append(max(gap, 0.0))
            self.mean_posterior_conf.append(conf)

        self.best_K = np.array(self.best_K)
        self.bic_gap_weight = np.array(self.bic_gap_weight)
        self.mean_posterior_conf = np.array(self.mean_posterior_conf)

        # normalize BIC-gap to [0,1]
        if self.bic_gap_weight.max() > 0:
            self.bic_gap_weight = self.bic_gap_weight / self.bic_gap_weight.max()
        else:
            self.bic_gap_weight = np.zeros_like(self.bic_gap_weight)

        self.is_significant = np.isin(self.best_K, [2, 3])

    def adjacent_window_scoring(self):
        # ------------------------------------------------------------
        # 6) Approach B: absolute difference of adjacent fixed windows (size=5) to find self.boundaries
        # ------------------------------------------------------------
        n_fixed = self.n_positions - self.fixed_w + 1
        fixed_scores = np.zeros(n_fixed)
        fixed_ranges = []

        # compute score for all the possible windows
        self.precompute_pairwise_scores(self.fixed_w)

        # get the score and save it for each window defined by the start position w == start
        for w in tqdm(range(n_fixed)):
            s = w
            e = w + self.fixed_w - 1
            fixed_ranges.append((s, e))
            # fixed_scores[w] = self.score_window(
            #     s, e
            #     )
            fixed_scores[w] = self.score_window_precomputed(
                s, e
                )

        left_scores = np.full(self.n_positions, np.nan)
        right_scores = np.full(self.n_positions, np.nan)
        self.b_signal = np.full(self.n_positions, np.nan)

        # for each position, get the left and right scores based on overlapping fixed windows
        for p in range(self.n_positions):
            left_vals = [fixed_scores[w] for w, (s, e) in enumerate(fixed_ranges) if e == p]
            right_vals = [fixed_scores[w] for w, (s, e) in enumerate(fixed_ranges) if s == p]

            if len(left_vals) > 0:
                left_scores[p] = np.mean(left_vals)
            if len(right_vals) > 0:
                right_scores[p] = np.mean(right_vals)

            if len(left_vals) > 0 and len(right_vals) > 0:
                # your modification: absolute difference
                self.b_signal[p] = np.abs(right_scores[p] - left_scores[p])

        # detect local peaks in B
        threshold = 0.10
        peak_idx = []
        for i in range(1, self.n_positions - 1):
            if np.isnan(self.b_signal[i]):
                continue
            if self.b_signal[i] >= self.b_signal[i - 1] and self.b_signal[i] >= self.b_signal[i + 1] and self.b_signal[i] > threshold:
                peak_idx.append(i)

        peak_idx = np.array(peak_idx, dtype=int)

        # remove very close duplicate peaks
        if len(peak_idx) > 1:
            keep = [True] * len(peak_idx)
            for a in range(len(peak_idx)):
                for b in range(a + 1, len(peak_idx)):
                    if abs(peak_idx[a] - peak_idx[b]) < 2:
                        if self.b_signal[peak_idx[a]] < self.b_signal[peak_idx[b]]:
                            keep[a] = False
                        else:
                            keep[b] = False
            peak_idx = peak_idx[np.array(keep, dtype=bool)]

        self.boundaries = np.sort(peak_idx)  # 0-based position self.boundaries

    def set_region_values(self):
        
        self.edge_midpoints = np.arange(1.5, self.n_positions, 1.0)  # 1.5,2.5,...,N-0.5
        self.edge_scores = np.full(self.edge_midpoints.shape, np.nan)

        # helper: check if window [s,e] crosses any boundary b (0-based position index)
        # boundary at b splits between b and b+1 in position coordinates.
        # a window crosses b if s <= b < e
        
        start = 0
        for bound in tqdm(self.boundaries):
            if (bound-1 -start < self.fixed_w and self.precomputed):
                score = self.score_window_precomputed(start, bound - 1)
            else:
                score = self.score_window(start, bound - 1)
            self.edge_scores[(self.edge_midpoints >= start) & (self.edge_midpoints < bound + 1)] = score
            start = bound + 1
        # last window left so it has to be computed
        if (self.n_positions - 1 - start < self.fixed_w and self.precomputed):
            score = self.score_window_precomputed(start, self.n_positions - 1)
        else:
            score = self.score_window(start, self.n_positions - 1)
        self.edge_scores[(self.edge_midpoints >= start) & (self.edge_midpoints < self.n_positions)] = score

    def precompute_pairwise_scores(self, fixed_w):

        n_fixed = self.n_positions - fixed_w + 1
        needed_pairs = set()
        for w in range(n_fixed):
            s = w
            e = w + fixed_w - 1
            idxs = np.arange(s, e + 1)
            
            sig_idxs = [i for i in idxs if self.is_significant[i]]
    
            for a in range(len(sig_idxs)):
                for b in range(a + 1, len(sig_idxs)):
                    needed_pairs.add((sig_idxs[a], sig_idxs[b]))

        self.ari_dict = {
            (b, d): self.compute_ari(b, d)
            for b, d in tqdm(needed_pairs, total=len(needed_pairs))
        }
        self.weight_dict = {
            (b, d): self.compute_weight(b, d)
            for b, d in tqdm(needed_pairs, total=len(needed_pairs))
        }
        self.precomputed = True

    def compute_weight(self, i, j):
        weight_i = 0.5 * self.bic_gap_weight[i] + 0.5 * self.mean_posterior_conf[i]
        weight_j = 0.5 * self.bic_gap_weight[j] + 0.5 * self.mean_posterior_conf[j]
        return weight_i * weight_j

    def compute_ari(self, i, j):
        labels_i = self.best_labels[i]
        labels_j = self.best_labels[j]

        nan_values = np.isnan(labels_i) | np.isnan(labels_j)
        labels_i = labels_i[~nan_values]
        labels_j = labels_j[~nan_values]

        return adjusted_rand_score(labels_i, labels_j)

    def score_window_precomputed(self, start, end):

        idxs = np.arange(start, end + 1)
        
        sig_idxs = [i for i in idxs if self.is_significant[i]]

        # Require enough informative positions
        if len(sig_idxs) < max(2, len(idxs) // 2):
            # print(f"Window [{start}, {end}] skipped due to insufficient significant positions.")
            return 0.0

        pairwise_aris = [
            self.ari_dict[(b, d)]
            for b, d in combinations(sig_idxs, 2)
        ]

        pairwise_weights = [
            self.weight_dict[(b, d)]
            for b, d in combinations(sig_idxs, 2)
        ]

        if len(pairwise_aris) == 0:
            return 0.0

        pairwise_aris = np.array(pairwise_aris)
        pairwise_weights = np.array(pairwise_weights)

        if pairwise_weights.sum() > 0:
            consistency = np.average(
                pairwise_aris,
                weights=pairwise_weights
            )
        else:
            consistency = pairwise_aris.mean()

        frac_sig = (end - start + 1) / self.n_positions

        return max(0.0, consistency) * frac_sig


    def score_window(self, start, end):
        
        idxs = np.arange(start, end + 1)

        sig_idxs = [i for i in idxs if self.is_significant[i]]

        # Require enough informative positions
        if len(sig_idxs) < max(2, len(idxs) // 2):
            # print(f"Window [{start}, {end}] skipped due to insufficient significant positions.")
            return 0.0

        pairwise_aris = []
        pairwise_weights = []

        for a in range(len(sig_idxs)):
            for b in range(a + 1, len(sig_idxs)):

                i = sig_idxs[a]
                j = sig_idxs[b]

                labels_i = self.best_labels[i]
                labels_j = self.best_labels[j]

                # compare non_nan values
                nan_values = np.isnan(labels_i) | np.isnan(labels_j)
                labels_i = labels_i[~nan_values]
                labels_j = labels_j[~nan_values]

                # ARI does not require label alignment
                ari = adjusted_rand_score(labels_i, labels_j)

                wi = (
                    0.5 * self.bic_gap_weight[i]
                    + 0.5 * self.mean_posterior_conf[i]
                )

                wj = (
                    0.5 * self.bic_gap_weight[j]
                    + 0.5 * self.mean_posterior_conf[j]
                )

                pairwise_aris.append(ari)
                pairwise_weights.append(wi * wj)

        if len(pairwise_aris) == 0:
            return 0.0

        pairwise_aris = np.array(pairwise_aris)
        pairwise_weights = np.array(pairwise_weights)

        if pairwise_weights.sum() > 0:
            consistency = np.average(
                pairwise_aris,
                weights=pairwise_weights
            )
        else:
            consistency = pairwise_aris.mean()

        frac_sig = len(sig_idxs) / len(idxs)

        return max(0.0, consistency) * frac_sig


if __name__ == "__main__":

    # input_parquet="/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/test_scan_results/OV121081.1_500000_100000_bypos_mean.parquet"
    input_parquet="/home/aantich/Nextcloud/2_PROJECTES/iDlG_paper/iDlG/scan_results/Chromosome_11_10000_2500_bypos_mean.parquet"
    
    import pandas as pd
    df = pd.read_parquet(input_parquet)
    self = SuggestRegions(df)

    import matplotlib.pyplot as plt

    n_samples = df.shape[1]-2
    samples = [f"S{i+1}" for i in range(n_samples)]
    positions = np.arange(self.n_positions)

    fig, axes = plt.subplots(3, 1, figsize=(12, 11), sharex=False)

    # Panel 1: original sample profiles
    for s in range(n_samples):
        axes[0].plot(positions, self.np_df[s, :], marker='', linewidth=1.3, alpha=0.85, label=samples[s])

    axes[0].set_title("Original data (10 samples across 20 positions)")
    axes[0].set_ylabel("Value")
    axes[0].set_ylim(-0.05, 2.05)
    axes[0].set_xticks(positions)
    axes[0].grid(alpha=0.25)
    axes[0].legend(ncol=5, fontsize=8, frameon=False, loc='upper center')

    # Panel 2: Approach B signal + peaks
    axes[1].plot(positions, self.b_signal, color='black', marker='o', linewidth=2, label="B = |right-left|")
    axes[1].axhline(0, color='gray', linestyle='--', linewidth=1)

    if len(self.boundaries) > 0:
        for b in self.boundaries:
            x_boundary = b + 1  # position coordinate
            axes[1].axvline(x_boundary, color='tab:red', linestyle=':', linewidth=1.2)
            axes[1].scatter(x_boundary, self.b_signal[b], color='tab:red', s=50, zorder=3)

    axes[1].set_title("Approach B (absolute difference) for boundary peak detection")
    axes[1].set_ylabel("Absolute difference")
    axes[1].set_xticks(positions)
    axes[1].grid(alpha=0.25)
    axes[1].legend(frameon=False)

    # Panel 3: Modified A on ALL between-position midpoints
    axes[2].plot(self.edge_midpoints, self.edge_scores, color='tab:blue', marker='s', linewidth=2, label="Modified A on midpoints")

    if len(self.boundaries) > 0:
        for b in self.boundaries:
            x_boundary = b + 1  # boundary at position index
            axes[2].axvline(x_boundary, color='tab:red', linestyle=':', linewidth=1.2)

    axes[2].set_title("Modified A: score on between-position midpoints (1.5, 2.5, ..., 19.5)")
    axes[2].set_xlabel("Position / midpoint")
    axes[2].set_ylabel("Clustering score")
    axes[2].set_xticks(np.arange(1, self.n_positions + 1, 1))
    axes[2].grid(alpha=0.25)
    axes[2].legend(frameon=False)

    plt.tight_layout()
    plt.show()
