import streamlit as st
import pandas as pd
import plotly.express as px

from prngs import REGISTRY, METADATA

st.set_page_config(page_title="PRNG Explorer", layout="wide", page_icon="🎲")

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("🎲 PRNG Explorer")
    st.subheader("Configuration")

    all_names = list(REGISTRY.keys())
    selected = st.multiselect(
        "Select algorithms",
        options=all_names,
        default=[all_names[0]],
    )

    chacha_selected = "ChaCha20 (CSPRNG)" in selected
    seed_label = "Seed ⚠️ (ignored by ChaCha20)" if chacha_selected else "Seed"
    seed = st.number_input(seed_label, value=42, step=1)

    n = st.slider("Number of values", min_value=10, max_value=10000, value=100, step=10)

    if not selected:
        st.warning("Please select at least one algorithm.")
        st.stop()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_dist, tab_range = st.tabs(["📊 Distribution Explorer", "🎯 Range Picker"])

# ===========================================================================
# TAB 1 — Distribution Explorer (original content)
# ===========================================================================
with tab_dist:
    st.title("🎲 PRNG Explorer")
    st.markdown(
        "Compare 8 pseudo-random number generation algorithms side-by-side. "
        "Pick one or more algorithms from the sidebar, optionally mix them via XOR, "
        "and inspect the resulting distribution."
    )

    # Algorithm info cards
    st.subheader("Algorithm Details")

    if chacha_selected:
        st.info(
            "**ChaCha20** is an OS-level CSPRNG (`os.urandom`). "
            "It is cryptographically secure and ignores the seed you set."
        )

    cols_per_row = 4
    rows = [selected[i : i + cols_per_row] for i in range(0, len(selected), cols_per_row)]

    for row_names in rows:
        cols = st.columns(len(row_names))
        for col, name in zip(cols, row_names):
            meta = METADATA[name]
            csprng_badge = "✅" if meta["csprng"] else "❌"
            with col:
                st.markdown(
                    f"""
<div style="
    border: 1px solid #444;
    border-radius: 8px;
    padding: 12px 16px;
    background: #1e1e2e;
    color: #cdd6f4;
    font-size: 0.85rem;
    line-height: 1.7;
">
<strong style="font-size:0.95rem; color:#89b4fa;">{name}</strong><br>
🔁 <b>Period:</b> {meta['period']}<br>
💾 <b>State:</b> {meta['state_size']}<br>
⚡ <b>Speed:</b> {meta['speed']}<br>
🔒 <b>CSPRNG:</b> {csprng_badge}
</div>
""",
                    unsafe_allow_html=True,
                )

    st.markdown("---")

    # Generate numbers
    generated: dict[str, list] = {}
    for name in selected:
        cls = REGISTRY[name]
        instance = cls(int(seed))
        values = instance.generate(n)
        values = [min(max(v, 0.0), 0.9999999999999999) for v in values]
        generated[name] = values

    mixing = len(selected) > 1

    if mixing:
        st.info(
            f"**Mixing method:** XOR of integer representations of {len(selected)} algorithms. "
            "Each float is scaled to a 32-bit integer, XOR-ed across all algorithms, "
            "then normalized back to [0, 1)."
        )
        int_lists = [[int(v * 2**32) for v in vals] for vals in generated.values()]
        mixed_ints = [0] * n
        for int_seq in int_lists:
            for i, val in enumerate(int_seq):
                mixed_ints[i] ^= val
        final_values = [v / 2**32 for v in mixed_ints]
        display_label = " ⊕ ".join(selected)
    else:
        final_values = generated[selected[0]]
        display_label = selected[0]

    st.subheader("Generated Values")
    st.caption(f"Total: {n} values  |  Showing first 20 rows")

    df = pd.DataFrame({"value": final_values})
    df.index.name = "index"
    st.dataframe(df.head(20), use_container_width=True)

    csv_data = df.to_csv(index=True)
    st.download_button(
        label="⬇️ Download all values as CSV",
        data=csv_data,
        file_name="prng_output.csv",
        mime="text/csv",
    )

    st.subheader("Distribution")

    fig = px.histogram(
        df,
        x="value",
        nbins=50,
        title=f"Distribution — {display_label}  (n={n})",
        labels={"value": "Value [0, 1)", "count": "Frequency"},
        color_discrete_sequence=["#89b4fa"],
    )
    fig.update_layout(
        bargap=0.05,
        plot_bgcolor="#1e1e2e",
        paper_bgcolor="#1e1e2e",
        font_color="#cdd6f4",
        title_font_color="#89b4fa",
    )
    fig.update_xaxes(gridcolor="#313244")
    fig.update_yaxes(gridcolor="#313244")

    st.plotly_chart(fig, use_container_width=True)

    if mixing:
        with st.expander("🔀 Mix Details"):
            st.markdown("**Algorithms mixed:**")
            for name in selected:
                meta = METADATA[name]
                csprng_badge = "✅" if meta["csprng"] else "❌"
                st.markdown(
                    f"- **{name}** — Period: `{meta['period']}`, "
                    f"State: `{meta['state_size']}`, Speed: {meta['speed']}, "
                    f"CSPRNG: {csprng_badge}"
                )
            st.markdown(
                "**Mixing method:** Each generator independently produces *n* floats from the same seed. "
                "Each float is multiplied by 2³² and truncated to an integer. "
                "Corresponding integers across all generators are XOR-ed together. "
                "The resulting integer is divided by 2³² to produce the final float in [0, 1)."
            )

# ===========================================================================
# TAB 2 — Range Picker
# ===========================================================================
with tab_range:
    st.title("🎯 Range Picker")
    st.markdown(
        "Pick a numeric range, choose an algorithm, and generate a single random value "
        "— or a batch — mapped into that range."
    )

    st.markdown("---")

    # Controls laid out in two columns
    ctrl_left, ctrl_right = st.columns(2)

    with ctrl_left:
        st.subheader("Range")
        use_float = st.toggle("Use decimal (float) range", value=False)

        if use_float:
            low = st.number_input("Low", value=0.0, step=0.1, format="%.6f", key="rp_low_f")
            high = st.number_input("High", value=1.0, step=0.1, format="%.6f", key="rp_high_f")
        else:
            low = st.number_input("Low", value=1, step=1, key="rp_low_i")
            high = st.number_input("High", value=100, step=1, key="rp_high_i")

        if high <= low:
            st.error("High must be greater than Low.")

    with ctrl_right:
        st.subheader("Generator")
        rp_algorithms = st.multiselect(
            "Algorithms (select one or more to XOR-mix)",
            options=all_names,
            default=[all_names[0]],
            key="rp_algo",
        )
        if not rp_algorithms:
            st.error("Select at least one algorithm.")

        rp_chacha = "ChaCha20 (CSPRNG)" in rp_algorithms
        rp_seed = st.number_input(
            "Seed ⚠️ (ignored by ChaCha20)" if rp_chacha else "Seed",
            value=42,
            step=1,
            key="rp_seed",
        )
        rp_count = st.number_input(
            "How many values to generate",
            min_value=1,
            max_value=10000,
            value=1,
            step=1,
            key="rp_count",
        )

    st.markdown("---")

    # Generate button
    generate_clicked = st.button("⚡ Generate", type="primary", use_container_width=False)

    if generate_clicked and high > low and rp_algorithms:
        n_rp = int(rp_count)

        # --- Generate raw [0,1) floats from each selected algorithm ---
        rp_generated: dict[str, list] = {}
        for name in rp_algorithms:
            cls = REGISTRY[name]
            rp_generated[name] = cls(int(rp_seed)).generate(n_rp)

        # --- XOR-mix if more than one algorithm ---
        rp_mixing = len(rp_algorithms) > 1
        if rp_mixing:
            int_lists = [[int(v * 2**32) for v in vals] for vals in rp_generated.values()]
            mixed_ints = [0] * n_rp
            for int_seq in int_lists:
                for i, val in enumerate(int_seq):
                    mixed_ints[i] ^= val
            raw = [v / 2**32 for v in mixed_ints]
            mix_label = " ⊕ ".join(rp_algorithms)
            st.info(f"**Mixing:** XOR of {len(rp_algorithms)} algorithms → {mix_label}")
        else:
            raw = rp_generated[rp_algorithms[0]]
            mix_label = rp_algorithms[0]

        spread = high - low

        if use_float:
            results = [low + v * spread for v in raw]
            result_label = "float"
        else:
            low_i, high_i = int(low), int(high)
            int_spread = high_i - low_i + 1
            results = [low_i + int(v * int_spread) for v in raw]
            result_label = "integer"

        # --------------- Single value: big display ---------------
        if rp_count == 1:
            value = results[0]
            formatted_value = f"{value:,.6f}" if use_float else f"{int(value):,}"
            st.markdown("### Result")
            st.markdown(
                f"""
<div style="
    border: 2px solid #89b4fa;
    border-radius: 12px;
    padding: 32px;
    text-align: center;
    background: #1e1e2e;
    color: #cdd6f4;
    margin: 16px 0;
">
    <div style="font-size: 3.5rem; font-weight: 800; color: #89b4fa; letter-spacing: 2px;">
        {formatted_value}
    </div>
    <div style="font-size: 0.95rem; margin-top: 8px; color: #a6adc8;">
        {result_label} in [{low}, {high}]
        &nbsp;·&nbsp; algorithm: <strong>{mix_label}</strong>
    </div>
</div>
""",
                unsafe_allow_html=True,
            )
            st.metric(
                label=f"{mix_label} → [{low}, {high}]",
                value=formatted_value,
            )

        # --------------- Multiple values: table + histogram ------
        else:
            st.markdown(f"### {n_rp} values in [{low}, {high}]")

            df_rp = pd.DataFrame({"value": results})

            col_tbl, col_stats = st.columns([2, 1])

            with col_tbl:
                st.caption(f"Showing first 20 of {n_rp}")
                st.dataframe(df_rp.head(20), use_container_width=True)
                csv_rp = df_rp.to_csv(index=True)
                st.download_button(
                    label="⬇️ Download as CSV",
                    data=csv_rp,
                    file_name="range_output.csv",
                    mime="text/csv",
                    key="rp_download",
                )

            with col_stats:
                st.markdown("**Statistics**")
                vals = df_rp["value"]
                st.metric("Min", f"{vals.min():,.4f}" if use_float else f"{int(vals.min()):,}")
                st.metric("Max", f"{vals.max():,.4f}" if use_float else f"{int(vals.max()):,}")
                st.metric("Mean", f"{vals.mean():,.4f}" if use_float else f"{vals.mean():,.2f}")
                st.metric("Std dev", f"{vals.std():,.4f}" if use_float else f"{vals.std():,.2f}")

            fig_rp = px.histogram(
                df_rp,
                x="value",
                nbins=min(50, n_rp // 2 + 1),
                title=f"{mix_label} · {n_rp} values in [{low}, {high}]",
                labels={"value": f"Value [{low}, {high}]", "count": "Frequency"},
                color_discrete_sequence=["#a6e3a1"],
            )
            fig_rp.update_layout(
                bargap=0.05,
                plot_bgcolor="#1e1e2e",
                paper_bgcolor="#1e1e2e",
                font_color="#cdd6f4",
                title_font_color="#a6e3a1",
            )
            fig_rp.update_xaxes(gridcolor="#313244")
            fig_rp.update_yaxes(gridcolor="#313244")
            st.plotly_chart(fig_rp, use_container_width=True)

        # Mix details expander (when multiple selected)
        if rp_mixing:
            with st.expander("🔀 Mix Details"):
                st.markdown("**Algorithms mixed:**")
                for name in rp_algorithms:
                    meta = METADATA[name]
                    csprng_badge = "✅" if meta["csprng"] else "❌"
                    st.markdown(
                        f"- **{name}** — Period: `{meta['period']}`, "
                        f"State: `{meta['state_size']}`, Speed: {meta['speed']}, "
                        f"CSPRNG: {csprng_badge}"
                    )
                st.markdown(
                    "Each generator independently produces floats from the same seed. "
                    "Floats are scaled to 32-bit integers, XOR-ed element-wise across all generators, "
                    "then divided by 2³² to get the final value in [0, 1) before range mapping."
                )

        # ChaCha20 seed warning
        if rp_chacha:
            st.caption("ℹ️ ChaCha20 uses OS-level randomness and ignores the seed.")
