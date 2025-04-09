import matplotlib.pyplot as plt

def plot_volcano(
    df,
    label_genes=None,
    title="Volcano Plot",
    xlabel="log2 Fold Change",
    ylabel="-log10(p-value)",
    x_col="log2FoldChange",
    y_col="pvalue",
    gene_col="gene",
    footer_text=None,
    fc_thresh=1.0,
    pval_thresh=0.05,
    legend_title="Regulation",
    colors={"up": "red", "down": "blue", "neutral": "gray"},
    legend_labels={"up": "Up", "down": "Down", "neutral": "Neutral"},
    show_grid=True,
    legend_position="best",
    figsize=(8, 6),
    show_borders=True,
    xlim=(-5, 5),
    ylim=(0, 10),
    log_scale_y=False,
    show_threshold_line=False
):
    import numpy as np

    # Classify regulation
    df["regulation"] = "neutral"
    df.loc[(df[x_col] >= fc_thresh) & (df[y_col] <= pval_thresh), "regulation"] = "up"
    df.loc[(df[x_col] <= -fc_thresh) & (df[y_col] <= pval_thresh), "regulation"] = "down"
    df["-log10_y"] = -np.log10(df[y_col])

    fig, ax = plt.subplots(figsize=figsize)

    for group in df["regulation"].unique():
        group_data = df[df["regulation"] == group]
        ax.scatter(group_data[x_col], group_data["-log10_y"],
                   label=legend_labels.get(group, group),
                   color=colors.get(group, "gray"), alpha=0.7)

    # Label selected genes
    if label_genes:
        for _, row in df[df[gene_col].isin(label_genes)].iterrows():
            ax.text(row[x_col], row["-log10_y"], row[gene_col],
                    fontsize=8, alpha=0.8)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_xlim(xlim)
    ax.set_ylim(ylim)

    if log_scale_y:
        ax.set_yscale("log")
    else:
        ax.set_yscale("linear")

    ax.grid(show_grid)

    if not show_borders:
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    else:
        ax.spines["top"].set_visible(True)
        ax.spines["right"].set_visible(True)

    if legend_position == "outside right":
        ax.legend(title=legend_title, loc="center left", bbox_to_anchor=(1, 0.5))
    else:
        ax.legend(title=legend_title, loc=legend_position)
        
    if show_threshold_line:
        threshold_line = -np.log10(pval_thresh)
        ax.axhline(y=threshold_line, linestyle="--", color="black", linewidth=1)
    
    if footer_text:
        ax.text(
            0.5, -0.15, footer_text,
            transform=ax.transAxes,
            ha='center', va='top',
            fontsize=8, color='gray'
        )

    return fig
