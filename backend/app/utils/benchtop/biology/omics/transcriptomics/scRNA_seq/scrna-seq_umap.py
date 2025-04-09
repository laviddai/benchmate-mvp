def run_umap_tool(uploaded_file):
    import streamlit as st
    import scanpy as sc
    import anndata
    import matplotlib.pyplot as plt
    from streamlit_app.helpers.biology.omics.transcriptomics.scrna_seq.scrna_seq_umap_helpers import plot_umap

    st.title("🧬 UMAP Explorer")

    st.markdown("""
    Upload a `.h5ad` file (AnnData format) to visualize single-cell data using **UMAP** or **PCA**.  
    Use the sidebar to control clustering, color, and layout.
    """)

    if uploaded_file is not None:
        try:
            adata = sc.read_h5ad(uploaded_file)

            st.success("✅ File loaded!")
            st.markdown(f"**Shape**: {adata.shape[0]} cells × {adata.shape[1]} genes")

            available_keys = list(adata.obs.columns)
            if not available_keys:
                st.warning("This .h5ad file has no metadata (obs). Cannot color by anything.")
            else:
                st.sidebar.header("🧪 Plot Settings")

                # Embedding Method
                method = st.sidebar.selectbox("Embedding method", ["UMAP", "PCA"])

                # Coloring group
                color_by = st.sidebar.selectbox("Color cells by", available_keys)

                # Appearance
                st.sidebar.markdown("### 🧭 Axis & Appearance")
                title = st.sidebar.text_input("Plot Title", f"{method.upper()} Plot")
                xlabel = st.sidebar.text_input("X-axis Label", f"{method.upper()} 1")
                ylabel = st.sidebar.text_input("Y-axis Label", f"{method.upper()} 2")

                legend_loc = st.sidebar.selectbox("Legend location", ["right margin", "on data", "none"])
                point_size = st.sidebar.slider("Point size", 10, 100, 30)
                font_size = st.sidebar.slider("Font size", 8, 24, 14)

                show_frame = st.sidebar.checkbox("Show plot frame", False)
                show_grid = st.sidebar.checkbox("Show gridlines", True)
                show_top_right_border = st.sidebar.checkbox("Show top/right border", False)

                # Axis Range Control
                st.sidebar.markdown("### 📏 Axis Range")
                set_manual_range = st.sidebar.checkbox("Set axis limits manually", False)
                x_range = st.sidebar.slider("X-axis Range", -20.0, 20.0, (-10.0, 10.0)) if set_manual_range else None
                y_range = st.sidebar.slider("Y-axis Range", -20.0, 20.0, (-10.0, 10.0)) if set_manual_range else None

                # Color Map
                st.sidebar.markdown("### 🎨 Colors")
                color_map = st.sidebar.selectbox("Colormap", ["viridis", "plasma", "inferno", "magma", "cividis", "coolwarm", "bwr", "Spectral", "Set1", "Set2"])

                st.markdown("### 📊 UMAP Visualization")
                fig = plot_umap(
                    adata,
                    method=method,
                    color=color_by,
                    legend_loc=legend_loc,
                    point_size=point_size,
                    frameon=show_frame,
                    title=title,
                    xlabel=xlabel,
                    ylabel=ylabel,
                    font_size=font_size,
                    show_grid=show_grid,
                    show_top_right_border=show_top_right_border,
                    x_range=x_range,
                    y_range=y_range,
                    cmap=color_map
                )
                st.pyplot(fig)

                # Download
                import io
                buf = io.BytesIO()
                fig.savefig(buf, format="png")
                st.download_button(
                    label="📥 Download plot as PNG",
                    data=buf.getvalue(),
                    file_name="umap_plot.png",
                    mime="image/png"
                )
                # --------------------
                # 🧬 Gene Expression Overlay
                # --------------------
                st.subheader("🎯 Gene Expression Overlay")

                all_genes = adata.var_names.tolist()
                selected_gene = st.selectbox("Select a gene to visualize", all_genes)

                if selected_gene:
                    st.markdown(f"Showing expression of **{selected_gene}** on {method.upper()}")

                    fig2 = plot_umap(
                        adata,
                        method=method,
                        color=selected_gene,
                        legend_loc=legend_loc,
                        point_size=point_size,
                        frameon=show_frame,
                        title=title,
                        xlabel=xlabel,
                        ylabel=ylabel,
                        font_size=font_size,
                        show_grid=show_grid,
                        show_top_right_border=show_top_right_border,
                        x_range=x_range,
                        y_range=y_range,
                        cmap=color_map
                    )
                    st.pyplot(fig2)

                    buf2 = io.BytesIO()
                    fig2.savefig(buf2, format="png")
                    st.download_button(
                        label=f"📥 Download {selected_gene} UMAP as PNG",
                        data=buf2.getvalue(),
                        file_name=f"{selected_gene}_expression_umap.png",
                        mime="image/png"
                    )


        except Exception as e:
            st.error(f"❌ Could not load .h5ad file: {e}")
