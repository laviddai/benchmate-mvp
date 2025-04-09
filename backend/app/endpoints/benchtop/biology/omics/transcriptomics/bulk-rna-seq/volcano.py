import streamlit as st
import pandas as pd
import numpy as np
import os
import re
from io import BytesIO
import plotly.express as px  # For interactive plot
from streamlit_app.helpers.biology.omics.transcriptomics.bulk_rna_seq.bulk_rna_seq_volcano_helpers import plot_volcano
from helpers.config_loader import load_yaml_config

# -------------------------------
# Caching Helpers
# -------------------------------

@st.cache_data
def load_data(uploaded_file, ext):
    """Load data from an uploaded file and cache the result."""
    if ext in [".xls", ".xlsx"]:
        return pd.read_excel(uploaded_file)
    else:
        return pd.read_csv(uploaded_file)

@st.cache_data
def preprocess_data(df, y_col, x_col):
    """Perform heavy computations on the data (e.g. transformations) and cache the result.
       Note: No small offset is added so that -log10 values are computed exactly.
    """
    df = df.copy()
    # Compute -log10(p-value) using actual p-values
    df["-log10_y"] = -np.log10(df[y_col])
    # Compute composite score: |fold change| * (-log10(p-value))
    if "calculated_log2FC" in df.columns:
        fc_values = df["calculated_log2FC"]
    else:
        fc_values = df[x_col]
    df["composite_score"] = np.abs(fc_values) * (-np.log10(df[y_col]))
    return df

# -------------------------------
# Dual Input Widget Helper
# -------------------------------
def dual_input_slider(label, min_value, max_value, default, step, key):
    # Initialize the session state value if not present
    if key not in st.session_state:
        st.session_state[key] = default
    col1, col2 = st.columns([3, 1])
    slider_val = col1.slider(label, min_value=min_value, max_value=max_value, 
                               value=st.session_state[key], step=step, key=key+"_slider")
    # Provide a non-empty label (" ") and hide it
    num_val = col2.number_input(" ", min_value=min_value, max_value=max_value, 
                                value=st.session_state[key], step=step, key=key+"_num", label_visibility="hidden")
    new_val = num_val if num_val != st.session_state[key] else slider_val
    st.session_state[key] = new_val
    return new_val

# -------------------------------
# Main Function
# -------------------------------
def run_volcano_tool(uploaded_file):
    # Load configuration from YAML
    config = load_yaml_config("config/biology/omics/transcriptomics/bulk_rna_seq/bulk_rna_seq_volcano.yaml")

    # Set default values from the configuration
    default_gene = config["expected_columns"]["gene_name"]
    default_x_col_name = config["expected_columns"]["log2fc"]
    default_y_col_name = config["expected_columns"]["pvalue"]

    default_threshold_x = config["thresholds"]["log2fc"]
    default_threshold_y = config["thresholds"]["pvalue"]

    default_colors = config["colors"]
    default_legend = config["legend"]
    default_axis = config["axis"]
    default_layout = config["layout"]
    default_auto_label = config["auto_label"]
    default_graph_title = config["graph"]["title"]

    # Title and intro markdown
    st.title("🧠 Volcano Plot Explorer")
    st.markdown("""
    Upload your **bulk RNA-seq results** and generate a customizable volcano plot.
    This app supports full customization for data manipulation and visualization.
    """)

    # Option to use interactive plot (Plotly)
    interactive_plot = st.checkbox("Use interactive plot (with hover tooltips)", value=False)

    if uploaded_file is not None:
        try:
            # -------------------------------
            # Data Loading with Caching
            # -------------------------------
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            # Load data via caching function
            df = load_data(uploaded_file, ext)
            st.session_state.df = df

            # -------------------------------
            # Group Detection
            # -------------------------------
            filename = uploaded_file.name
            match = re.search(r"(.+)_v_(.+)\.", filename)
            if match:
                default_group_a = match.group(1).replace(".", " ").strip()
                default_group_b = match.group(2).replace(".", " ").strip()
            else:
                default_group_a = "Group A"
                default_group_b = "Group B"

            st.success(f"✅ File uploaded: {uploaded_file.name}")
            st.subheader("Dataset Preview")
            with st.expander("View full dataset", expanded=False):
                st.dataframe(st.session_state.df)

            # -------------------------------
            # Identify Columns
            # -------------------------------
            numeric_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
            text_cols = df.select_dtypes(include=["object"]).columns.tolist()

            # -------------------------------
            # Sidebar: Data Columns
            # -------------------------------
            with st.sidebar.expander("1) Data Columns", expanded=False):
                st.markdown("<h3>🧠 Assign Data Columns <span title='Select columns representing gene names, fold changes, and p-values.'>ℹ️</span></h3>", unsafe_allow_html=True)
                st.markdown("Choose a gene name column, a column for log2 fold changes (if available), and a column for p-values (or FDR).")
                gene_col = st.selectbox("Gene Name Column", options=text_cols, index=text_cols.index(default_gene) if default_gene in text_cols else 0)
                x_col = st.selectbox("X-axis Column (e.g., log2 fold change)", options=numeric_cols, index=numeric_cols.index(default_x_col_name) if default_x_col_name in numeric_cols else 0)
                y_col = st.selectbox("Y-axis Column (e.g., p-value or FDR)", options=numeric_cols, index=numeric_cols.index(default_y_col_name) if default_y_col_name in numeric_cols else 0)

            # -------------------------------
            # Sidebar: Comparison Mode
            # -------------------------------
            with st.sidebar.expander("2) Mode / Comparison", expanded=False):
                st.markdown("<h3>⚙️ Mode <span title='Use Single Group Mode for one condition; for comparisons, enter group labels.'>ℹ️</span></h3>", unsafe_allow_html=True)
                st.markdown("Select 'Single Group Mode' if no comparison is needed; otherwise, enter group labels.")
                single_group_mode = st.checkbox("Single Group Mode (no comparison labels)", value=False)
                if not single_group_mode:
                    group_a_label = st.text_input("Group A Label", default_group_a, help="Label for first group (e.g., 'Treatment').")
                    group_b_label = st.text_input("Group B Label", default_group_b, help="Label for second group (e.g., 'Control').")
                else:
                    group_a_label = default_group_a
                    group_b_label = default_group_b

            # -------------------------------
            # Sidebar: Derive Columns From Existing Data
            # -------------------------------
            with st.sidebar.expander("3) Derive Columns From Existing Data", expanded=False):
                st.markdown("""
                    <h3>Derive Columns From Existing Data 
                    <span title="Compute new values for your dataset. For example, derive Log2 Fold Change if it is not present.">ℹ️</span></h3>
                    """, unsafe_allow_html=True)
                st.markdown("""
                    **Purpose:** Compute additional values if they are not already present:
                    - **Log2 Fold Change:** log₂(Column A / Column B). Use this if your dataset does not include it.
                    - **-log10(p-value):** Although the plot automatically transforms your p-values, you can calculate this column to export or inspect the data.
                    """)
                # -------------------------------
                # Log2 Fold Change
                # -------------------------------
                if len(numeric_cols) >= 2:
                    col1 = st.selectbox("Column A (for fold change)", numeric_cols, key="calc_col1")
                    col2 = st.selectbox("Column B (for fold change)", numeric_cols, key="calc_col2")
                    derived_fc_col = "calculated_log2FC"
                    if derived_fc_col in df.columns:
                        st.info(f"Column '{derived_fc_col}' already exists. You can use it for plotting.")
                    else:
                        if st.button("Calculate log2(Column A / Column B)"):
                            try:
                                st.session_state.df[derived_fc_col] = np.log2(df[col1] / df[col2])
                                df = st.session_state.df
                                st.success(f"✅ New column added: {derived_fc_col}")
                            except Exception as e:
                                st.error(f"❌ Could not calculate log2 Fold Change: {e}")
                # -------------------------------
                # -log10(p-value) Transformation
                # -------------------------------
                if y_col:
                    derived_pval_col = f"calculated_neglog10_{y_col}"
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        if derived_pval_col in df.columns:
                            st.info(f"Column '{derived_pval_col}' already exists. You can use it for plotting.")
                        else:
                            if st.button(f"Calculate -log10(p-value) from {y_col}"):
                                try:
                                    st.session_state.df[derived_pval_col] = -np.log10(df[y_col])
                                    df = st.session_state.df
                                    st.success(f"✅ New column added: {derived_pval_col}")
                                except Exception as e:
                                    st.error(f"❌ Could not calculate -log10(p-value): {e}")
                    with col2:
                        st.markdown('<span title="This transformation is used in the plot. If you already see the correct y-axis in the plot, you may not need to derive this column.">ℹ️</span>', unsafe_allow_html=True)

            # -------------------------------
            # Sidebar: Axis Settings
            # -------------------------------
            with st.sidebar.expander("4) Axis Settings", expanded=False):
                st.markdown("<h3>🧭 Axis Settings <span title='Set the min/max values for the axes. These values will influence the filtering thresholds.'>ℹ️</span></h3>", unsafe_allow_html=True)
                user_x_min = st.number_input("X-axis min", value=default_axis["x_min"])
                user_x_max = st.number_input("X-axis max", value=default_axis["x_max"])
                user_y_min = st.number_input("Y-axis min", value=default_axis["y_min"])
                user_y_max = st.number_input("Y-axis max", value=default_axis["y_max"])
                log_scale_y = st.checkbox("Use log scale for Y-axis", value=default_axis["log_scale_y"])
                st.session_state["user_y_min"] = user_y_min
                st.session_state["user_y_max"] = user_y_max

            # -------------------------------
            # Sidebar: Filtering Thresholds
            # -------------------------------
            with st.sidebar.expander("5) Filtering Thresholds", expanded=False):
                st.markdown("<h3>🧮 Gene Filtering Thresholds <span title='Set thresholds for fold change and -log10(p-value). The Y-axis is automatically transformed using -log10().' >ℹ️</span></h3>", unsafe_allow_html=True)
                st.markdown("Adjust thresholds for fold change (x-axis) and significance on the y-axis. (Note: The y-axis threshold is in –log₁₀(p-value); e.g., a value of 2 means p-value ≤ 0.01.)")
                # Compute transformed y-values for filtering (using the actual p-values)
                trans_y = -np.log10(df[y_col])
                # Determine slider limits for x-axis as before
                x_min_val = round(float(df[x_col].min()), 2)
                x_max_val = round(float(df[x_col].max()), 2)
                slider_x_max = max(x_max_val, default_axis["x_max"])
                slider_x_min = min(x_min_val, default_axis["x_min"])
                if x_col == default_x_col_name:
                    x_default = tuple(default_threshold_x)
                else:
                    x_default = (slider_x_min, slider_x_max)
                # For y-axis, use user-defined axis limits from Axis Settings (transformed values)
                slider_y_min = st.session_state["user_y_min"]
                slider_y_max = st.session_state["user_y_max"]
                if y_col == default_y_col_name:
                    y_default = -np.log10(default_threshold_y)
                else:
                    y_default = slider_y_max

                fc_range = st.slider(f"{x_col} Range", min_value=slider_x_min, max_value=slider_x_max, value=x_default, step=0.1, key="fc_slider")
                # Use dual input for y-axis threshold
                threshold_y = dual_input_slider(f"Min -log10({y_col})", slider_y_min, slider_y_max, y_default, 0.001, key="mp_slider")
                # Checkbox to toggle the Y-axis threshold line
                show_threshold_line = st.checkbox("Show Y-Axis Threshold Line", value=False)
                
                if st.button("🔄 Reset Thresholds to Default", key="reset_thresholds_button"):
                    fc_range = x_default
                    threshold_y = y_default
                    st.success("Thresholds have been reset to default.")

            # -------------------------------
            # Sidebar: Colors & Legend
            # -------------------------------
            with st.sidebar.expander("6) Colors & Legend", expanded=False):
                st.markdown("<h3>🎨 Colors & Legend <span title='Customize colors for gene regulation and legend settings.'>ℹ️</span></h3>", unsafe_allow_html=True)
                color_up = st.color_picker("Upregulated", default_colors["up"])
                color_down = st.color_picker("Downregulated", default_colors["down"])
                color_neutral = st.color_picker("Neutral", default_colors["neutral"])
                st.markdown("Customize legend labels and title:")
                label_up = st.text_input("Label for Upregulated Genes", default_legend["labels"]["up"])
                label_down = st.text_input("Label for Downregulated Genes", default_legend["labels"]["down"])
                label_neutral = st.text_input("Label for Neutral Genes", default_legend["labels"]["neutral"])
                legend_title = st.text_input("Legend Title", default_legend["title"])
                legend_position = st.selectbox("Legend Position", options=["best", "upper right", "upper left", "outside right"],
                                               index=["best", "upper right", "upper left", "outside right"].index(default_legend["position"]))

            # -------------------------------
            # Sidebar: Auto-Labeling & Gene Search
            # -------------------------------
            with st.sidebar.expander("7) Auto-Labeling & Gene Search", expanded=False):
                st.markdown("<h3>🔍 Auto-Labeling & Gene Search <span title='Automatically label top genes based on a composite metric that combines fold change and significance. Hover on points in the interactive plot for details.'>ℹ️</span></h3>", unsafe_allow_html=True)
                st.markdown("**Composite Metric:** |log₂ Fold Change| × (-log₁₀(p-value)). This is used to select top genes.")
                top_n_up = st.number_input("Auto-label Top N Upregulated Genes", min_value=0, value=default_auto_label["top_n_up"], step=1)
                top_n_down = st.number_input("Auto-label Top N Downregulated Genes", min_value=0, value=default_auto_label["top_n_down"], step=1)
                search_gene = st.text_input("Go to Gene (search & highlight)", value="")

            # -------------------------------
            # Sidebar: Layout & Misc
            # -------------------------------
            with st.sidebar.expander("8) Layout & Misc", expanded=False):
                st.markdown("<h3>📐 Layout & Misc <span title='Adjust overall plot layout, grid, dimensions, borders, etc.'>ℹ️</span></h3>", unsafe_allow_html=True)
                add_footer = st.checkbox("Add footer with group + threshold info", value=default_layout["add_footer"])
                show_grid = st.checkbox("Show grid", value=default_layout["show_grid"])
                plot_width = st.slider("Plot Width", 4, 12, value=default_layout["plot_width"])
                plot_height = st.slider("Plot Height", 4, 12, value=default_layout["plot_height"])
                show_borders = st.checkbox("Show top/right plot borders", value=default_layout["show_borders"])
            
            # -------------------------------
            # Dataset Preview
            # -------------------------------
            # Display a preview of the updated dataset (using st.session_state.df to include derived columns)
            st.dataframe(st.session_state.df.head())
            
            # -------------------------------
            # Graph Title and Axis Labels
            # -------------------------------
            custom_title = st.text_input("Graph Title", default_graph_title)
            x_axis_label = st.text_input("X-axis Label", x_col)
            y_axis_label = st.text_input("Y-axis Label", f"-log10({y_col})" if not log_scale_y else y_col)

            # -------------------------------
            # Main Content: Filtering, Plotting, etc.
            # -------------------------------
            # Use a copy of the original data for filtering
            filtered_df = df.copy()
            # Calculate transformed y-values without an offset
            trans_y = -np.log10(df[y_col])
            filtered_df["regulation"] = "neutral"
            filtered_df.loc[(df[x_col] >= fc_range[1]) & (trans_y >= threshold_y), "regulation"] = "up"
            filtered_df.loc[(df[x_col] <= fc_range[0]) & (trans_y >= threshold_y), "regulation"] = "down"

            # Compute composite score for filtered data
            if "calculated_log2FC" in df.columns:
                fc_values = df["calculated_log2FC"]
            else:
                fc_values = df[x_col]
            composite_score = np.abs(fc_values) * (-np.log10(df[y_col]))
            filtered_df["composite_score"] = composite_score

            # Manual gene labeling selection
            label_genes = st.multiselect("Label specific genes", df[gene_col].unique().tolist())

            # Auto-label top N genes using composite score
            auto_labels = set()
            if top_n_up > 0:
                up_genes = filtered_df[filtered_df["regulation"] == "up"].copy()
                up_genes = up_genes.sort_values(by="composite_score", ascending=False)
                auto_labels.update(up_genes[gene_col].head(top_n_up).tolist())
            if top_n_down > 0:
                down_genes = filtered_df[filtered_df["regulation"] == "down"].copy()
                down_genes = down_genes.sort_values(by="composite_score", ascending=False)
                auto_labels.update(down_genes[gene_col].head(top_n_down).tolist())
            if search_gene and search_gene in df[gene_col].unique():
                auto_labels.add(search_gene)
            combined_labels = list(set(label_genes) | auto_labels)

            total_genes = len(df)
            filtered_genes = len(filtered_df[filtered_df["regulation"].isin(["up", "down"])])
            labeled_genes = len(combined_labels)

            st.subheader("📊 Summary Statistics")
            st.markdown(f"""
            - **Total genes in file:** {total_genes}  
            - **Genes passing filters:** {filtered_genes}  
            - **Genes labeled:** {labeled_genes}
                    """)

            reg_counts = filtered_df["regulation"].value_counts().to_dict()
            up_count = reg_counts.get("up", 0)
            down_count = reg_counts.get("down", 0)
            neutral_count = reg_counts.get("neutral", 0)

            st.markdown("### 🧬 Gene Regulation Summary")
            if not single_group_mode and group_a_label and group_b_label:
                st.markdown(f"🧪 **Comparison:** {group_a_label} vs {group_b_label}")
            st.markdown(f"""
            - 🔺 **Upregulated** ({x_axis_label} ≥ {fc_range[1]}, {y_axis_label} ≥ {threshold_y}): {up_count} genes  
            - 🔻 **Downregulated** ({x_axis_label} ≤ {fc_range[0]}, {y_axis_label} ≥ {threshold_y}): {down_count} genes  
            - ⚪ **Neutral**: {neutral_count} genes
                    """)

            with st.expander("Download Options", expanded=False):
                summary_text = f"""🧠 Volcano Plot Summary
            Comparison: {group_a_label} vs {group_b_label}
            X-axis: {x_axis_label} | Y-axis: {y_axis_label}
            Thresholds: {x_axis_label} ≥ {fc_range[1]}, {y_axis_label} ≥ {threshold_y}

            Total genes: {total_genes}
            Passing filters: {filtered_genes}
            Upregulated: {filtered_df[filtered_df["regulation"]=="up"].shape[0]}
            Downregulated: {filtered_df[filtered_df["regulation"]=="down"].shape[0]}
            Neutral: {filtered_df[filtered_df["regulation"]=="neutral"].shape[0]}
            """
                st.download_button(
                    label="📄 Download Summary (.txt)",
                    data=summary_text,
                    file_name=("summary.txt" if single_group_mode 
                            else f"summary_{group_a_label}_vs_{group_b_label}.txt".replace(" ", "_")),
                    mime="text/plain"
                )

                csv_data = filtered_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    label="📥 Download filtered data as CSV",
                    data=csv_data,
                    file_name=("filtered_genes.csv" if single_group_mode 
                            else f"filtered_genes_{group_a_label}_vs_{group_b_label}.csv".replace(" ", "_")),
                    mime="text/csv"
                )
                
                excel_buffer = BytesIO()
                with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                    filtered_df.to_excel(writer, index=False, sheet_name='Filtered Data')
                st.download_button(
                    label="📥 Download filtered data as Excel",
                    data=excel_buffer.getvalue(),
                    file_name=("filtered_genes.xlsx" if single_group_mode 
                            else f"filtered_genes_{group_a_label}_vs_{group_b_label}.xlsx".replace(" ", "_")),
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
                
                up_genes_list = filtered_df[filtered_df["regulation"]=="up"][gene_col]
                down_genes_list = filtered_df[filtered_df["regulation"]=="down"][gene_col]
                neutral_genes_list = filtered_df[filtered_df["regulation"]=="neutral"][gene_col]
                st.download_button(
                    label="📥 Download Upregulated Genes",
                    data=up_genes_list.to_csv(index=False).encode("utf-8"),
                    file_name="upregulated_genes.csv",
                    mime="text/csv"
                )
                st.download_button(
                    label="📥 Download Downregulated Genes",
                    data=down_genes_list.to_csv(index=False).encode("utf-8"),
                    file_name="downregulated_genes.csv",
                    mime="text/csv"
                )
                st.download_button(
                    label="📥 Download Neutral Genes",
                    data=neutral_genes_list.to_csv(index=False).encode("utf-8"),
                    file_name="neutral_genes.csv",
                    mime="text/csv"
                )

            # -------------------------------
            # Plotting Section
            # -------------------------------
            if interactive_plot:
                # Use the cached preprocessed data if available
                if "processed_df" not in st.session_state:
                    processed_df = preprocess_data(df, y_col, x_col)
                    st.session_state.processed_df = processed_df
                else:
                    processed_df = st.session_state.processed_df

                # For interactive plot, we use the processed_df (which already has -log10_y and composite_score computed)
                df_plot = processed_df.copy()

                # Reclassify regulation based on current thresholds (using actual p-values)
                df_plot["regulation"] = "neutral"
                df_plot.loc[(df_plot[x_col] >= fc_range[1]) & (-np.log10(df_plot[y_col]) >= threshold_y), "regulation"] = "up"
                df_plot.loc[(df_plot[x_col] <= fc_range[0]) & (-np.log10(df_plot[y_col]) >= threshold_y), "regulation"] = "down"

                # Create the interactive scatter plot
                fig = px.scatter(
                    df_plot,
                    x=x_col,
                    y="-log10_y",
                    color="regulation",
                    color_discrete_map={"up": color_up, "down": color_down, "neutral": color_neutral},
                    hover_data=[gene_col, x_col, y_col, "composite_score"],
                    title=custom_title,
                    labels={x_col: x_axis_label, "-log10_y": y_axis_label}
                )
                
                # Compute the maximum y-value from the data
                computed_y_max = df_plot["-log10_y"].max()
                effective_y_max = max(user_y_max, computed_y_max * 1.05)
                
                st.write("Computed y_max:", computed_y_max, "Effective y_max:", effective_y_max)
                
                # Update axis ranges using effective_y_max and force a linear scale
                fig.update_layout(
                    xaxis=dict(range=[user_x_min, user_x_max]),
                    yaxis=dict(range=[user_y_min, effective_y_max], type='linear'),
                    title=custom_title,
                    margin=dict(l=50, r=50, t=50, b=150)
                )
                fig.update_xaxes(title=x_axis_label, showgrid=show_grid)
                fig.update_yaxes(title=y_axis_label, showgrid=show_grid, automargin=True, fixedrange=True)
                
                legend_position_mapping = {
                    "best": dict(x=0.95, y=0.95, xanchor="right", yanchor="top"),
                    "upper right": dict(x=1, y=1, xanchor="right", yanchor="top"),
                    "upper left": dict(x=0, y=1, xanchor="left", yanchor="top"),
                    "outside right": dict(x=1.02, y=1, xanchor="left", yanchor="top"),
                }
                legend_pos = legend_position_mapping.get(legend_position, dict(x=0.95, y=0.95, xanchor="right", yanchor="top"))
                fig.update_layout(legend=dict(title=legend_title, **legend_pos))
                
                if show_borders:
                    fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
                    fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
                else:
                    fig.update_xaxes(showline=False)
                    fig.update_yaxes(showline=False)
                
                if show_threshold_line:
                    fig.add_hline(y=threshold_y, line_dash="dash", line_color="black")
                
                footer_text = (f"{group_a_label} vs {group_b_label} • {x_axis_label} ≥ {fc_range[1]} • {y_axis_label} ≥ {threshold_y}") if add_footer else None
                if footer_text:
                    fig.add_annotation(
                        text=footer_text,
                        xref="paper", yref="paper",
                        x=0.5, y=-0.25,
                        showarrow=False,
                        font=dict(size=8, color="gray")
                    )
                st.plotly_chart(fig, use_container_width=True)
            else:
                raw_pval_threshold = 10 ** (-threshold_y)
                fig = plot_volcano(
                    filtered_df,
                    label_genes=combined_labels,
                    title=custom_title,
                    xlabel=x_axis_label,
                    ylabel=y_axis_label,
                    fc_thresh=abs(fc_range[1]) if 'fc' in x_col.lower() else 1.0,
                    pval_thresh=raw_pval_threshold,
                    colors={"up": color_up, "down": color_down, "neutral": color_neutral},
                    legend_title=legend_title,
                    legend_labels={"up": label_up, "down": label_down, "neutral": label_neutral},
                    show_grid=show_grid,
                    legend_position=legend_position,
                    figsize=(plot_width, plot_height),
                    show_borders=show_borders,
                    xlim=(user_x_min, user_x_max),
                    ylim=(user_y_min, user_y_max),
                    log_scale_y=log_scale_y,
                    x_col=x_col,
                    y_col=y_col,
                    gene_col=gene_col,
                    show_threshold_line=show_threshold_line,
                    footer_text=(f"{group_a_label} vs {group_b_label} • {x_axis_label} ≥ {fc_range[1]} • {y_axis_label} ≥ {threshold_y}") if add_footer else None
                )
                st.pyplot(fig)
                buf = BytesIO()
                fig.savefig(buf, format="png")
                image_name = ("volcano_plot.png" if single_group_mode 
                            else f"volcano_{group_a_label}_vs_{group_b_label}.png".replace(" ", "_"))
                st.download_button("📥 Download PNG", buf.getvalue(), image_name, "image/png")

        except Exception as e:
            st.error(f"❌ Could not process file: {e}")
