import json
import pandas as pd
import streamlit as st

from mig_core import (
    create_mig_card_row,
    build_mig_prompt,
    make_docx_bytes,
    apply_mig_output_to_csv,
)


def get_mig_filter_config() -> dict[str, list[str]]:
    return {
        "filteringProperty:Použití - štětec": [
            "Base (základní nátěr)",
            "Layer (vrstvení)",
            "Detail",
            "Drybrush",
            "Wash / Shade",
            "Weathering",
            "Univerzální",
        ],
        "filteringProperty:Tvar štětce": [
            "Kulatý (Round)",
            "Plochý (Flat)",
            "Drybrush (plochý tupý)",
            "Fan (vějíř)",
            "Speciální (gumový, silikonový)",
        ],
        "filteringProperty:Typ štětin": [
            "Syntetický",
            "Přírodní (Kolinsky)",
        ],
        "filteringProperty:Velikost štětců": [
            "000",
            "00",
            "0",
            "1",
            "2",
            "3",
            "XL (drybrush velké)",
        ],
    }


def build_mig_filters_prompt_text(product_name: str, product_ean: str, product_code: str) -> str:
    config = get_mig_filter_config()

    lines = []
    lines.append("[FILTERS]")
    lines.append("")
    lines.append("Použij pouze přesné hodnoty z povoleného seznamu.")
    lines.append("Vyplň všechny filtry, které lze z produktu bezpečně určit.")
    lines.append("Pokud si nejsi jistý jen u konkrétního pole, nech prázdné pouze to pole.")
    lines.append("Nikdy nevymýšlej vlastní variantu.")
    lines.append("")
    lines.append("Pokud má filtr více hodnot, odděl je středníkem bez mezer navíc.")
    lines.append("Příklad:")
    lines.append("Base (základní nátěr);Detail")
    lines.append("")
    lines.append("Tvar štětce, Typ štětin a Velikost vracej jen pokud jsou bezpečně určitelné.")
    lines.append("")

    for key, values in config.items():
        lines.append(key)
        for value in values:
            lines.append(f"- {value}")
        lines.append("")

    lines.append("VRAŤ POUZE TENTO BLOK VE FORMÁTU key=value:")
    lines.append("")

    for key in config.keys():
        lines.append(f"{key}=")

    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("PRODUKT")
    lines.append(product_name or "")
    lines.append("")
    lines.append("EAN")
    lines.append(product_ean or "")
    lines.append("")
    lines.append("CODE")
    lines.append(product_code or "")
    lines.append("--------------------------------------------------")

    return "\n".join(lines)


def parse_filters_from_text(text: str) -> dict[str, str]:
    parsed: dict[str, str] = {}

    for raw_line in str(text or "").splitlines():
        line = raw_line.strip()
        if not line.startswith("filteringProperty:"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        parsed[key.strip()] = value.strip()

    return parsed


def validate_and_normalize_mig_filters(parsed_filters: dict[str, str]) -> dict[str, str]:
    config = get_mig_filter_config()
    result = {key: "" for key in config.keys()}

    for key, value in parsed_filters.items():
        if key not in config:
            continue

        if not value:
            result[key] = ""
            continue

        values = [v.strip() for v in value.split(";") if v.strip()]
        valid_values = [v for v in values if v in config[key]]
        result[key] = ";".join(valid_values) if valid_values else ""

    return result


def enrich_mig_csv_with_filters(df: pd.DataFrame, filters_text: str, row_index: int) -> pd.DataFrame:
    df_out = df.copy()

    parsed_filters = parse_filters_from_text(filters_text)
    validated_filters = validate_and_normalize_mig_filters(parsed_filters)

    for key, value in validated_filters.items():
        if key not in df_out.columns:
            df_out[key] = ""
        df_out.at[row_index, key] = value

    return df_out


def render_mig_page():
    st.title("MIG AMMO")

    if "mig_generated_filters_prompt_text" not in st.session_state:
        st.session_state["mig_generated_filters_prompt_text"] = ""

    if "mig_generated_filters_prompt_type" not in st.session_state:
        st.session_state["mig_generated_filters_prompt_type"] = ""

    tab1, tab2 = st.tabs(["Barvy", "Štětce / Příslušenství"])

    with tab1:
        render_mig_section(
            product_type_label="MIG Barvy",
            prompt_type="mig_paints",
            item_type="product",
            show_filters=False,
        )

    with tab2:
        render_mig_section(
            product_type_label="MIG Štětce / Příslušenství",
            prompt_type="mig_tools",
            item_type="product",
            show_filters=True,
        )


def render_mig_section(
    product_type_label: str,
    prompt_type: str,
    item_type: str,
    show_filters: bool,
):
    state_key = f"{prompt_type}_export_csv_bytes"
    if state_key not in st.session_state:
        st.session_state[state_key] = None

    subtab1, subtab2 = st.tabs(["Nová karta", "Prompt + Fill"])

    with subtab1:
        st.subheader(f"{product_type_label} – vytvoření nové karty")

        st.markdown("""
        <div style="
            background:#0f172a;
            padding:16px 20px;
            border-radius:12px;
            border:1px solid #1e293b;
            margin-bottom:16px;
        ">
        <b style="font-size:16px;">🧩 Nová karta – MIG</b><br>
        <span style="color:#94a3b8;">
        Tato sekce vytvoří základní produkt pro Shoptet (CREATE CSV).<br><br>
        </span>
        </div>
        """, unsafe_allow_html=True)

        name = st.text_input("Název produktu", key=f"{prompt_type}_name")
        code = st.text_input("Code – Kód produktu - vždycky", key=f"{prompt_type}_code")
        ean = st.text_input("EAN kód - ze záložky sklad", key=f"{prompt_type}_ean")
        price = st.number_input(
            "Naše prodejní cena (s DPH)",
            min_value=0.0,
            step=1.0,
            key=f"{prompt_type}_price",
        )
        standard_price = st.number_input(
            "Doporučená cena výrobce",
            min_value=0.0,
            step=1.0,
            key=f"{prompt_type}_standard_price",
        )
        description = st.text_area("Základní popis", key=f"{prompt_type}_desc")

        if st.button("Vytvořit CREATE CSV", key=f"{prompt_type}_create_btn"):
            if not name or not code:
                st.warning("Vyplň alespoň název produktu a code.")
            else:
                df_create = create_mig_card_row(
                    name=name,
                    code=code,
                    ean=ean,
                    price=price,
                    standard_price=standard_price,
                    product_type=item_type,
                    description=description,
                )

                csv_bytes = df_create.to_csv(index=False, sep=";").encode("utf-8-sig")

                st.download_button(
                    "Stáhnout CREATE CSV",
                    data=csv_bytes,
                    file_name=f"{code}_CREATE.csv",
                    mime="text/csv",
                    key=f"{prompt_type}_download_create",
                )

    with subtab2:
        st.subheader(f"{product_type_label} – prompt + fill")

        uploaded_csv = st.file_uploader(
            "Nahraj CSV produktu",
            type=["csv"],
            key=f"{prompt_type}_uploaded_csv",
        )

        df = None
        row_index = None
        product_name = ""
        product_ean = ""
        product_code = ""

        if uploaded_csv is not None:
            try:
                df = pd.read_csv(uploaded_csv, sep=";", dtype=str).fillna("")

                name_col = None
                if "name" in df.columns:
                    name_col = "name"
                elif "name:cs" in df.columns:
                    name_col = "name:cs"

                if name_col:
                    product_options = [f"{i} | {row.get(name_col, '')}" for i, row in df.iterrows()]
                    selected = st.selectbox(
                        "Vyber produkt",
                        product_options,
                        key=f"{prompt_type}_select_product",
                    )

                    row_index = int(selected.split("|")[0].strip())
                    product_name = df.iloc[row_index].get(name_col, "")
                    product_ean = df.iloc[row_index].get("ean", "")
                    product_code = df.iloc[row_index].get("code", "")

                    st.info(f"Produkt: {product_name}")
                    st.write(f"EAN: {product_ean}")
                    st.write(f"CODE: {product_code}")
                else:
                    st.error(
                        f"CSV neobsahuje sloupec 'name' ani 'name:cs'. "
                        f"Nalezené sloupce: {list(df.columns)}"
                    )

            except Exception as e:
                st.error(f"Nepodařilo se načíst CSV: {e}")

        st.markdown("## Obsahové prompty")

        if st.button("Vygenerovat všechny prompty", key=f"{prompt_type}_generate_all_prompts"):
            if not product_name:
                st.warning("Nejdřív nahraj CSV a vyber produkt.")
            else:
                try:
                    for lang in ("cs", "en", "sk"):
                        generated_prompt = build_mig_prompt(
                            prompt_type=prompt_type,
                            product_name=product_name,
                            product_ean=product_ean,
                            product_code=product_code,
                            lang=lang,
                        )

                        st.session_state[f"mig_generated_prompt_text_{prompt_type}_{lang}"] = generated_prompt
                        st.session_state[f"{prompt_type}_prompt_preview_{lang}"] = generated_prompt

                    st.success("Prompty byly vygenerovány.")

                except Exception as e:
                    st.error(f"Nepodařilo se vygenerovat prompty: {e}")

        lang_labels = {
            "cs": "Čeština",
            "en": "English",
            "sk": "Slovenčina",
        }

        cols = st.columns(3)
        ai_outputs: dict[str, str] = {}

        for col, lang in zip(cols, ("cs", "en", "sk")):
            with col:
                st.markdown(f"### {lang_labels[lang]}")

                preview_key = f"{prompt_type}_prompt_preview_{lang}"
                generated_key = f"mig_generated_prompt_text_{prompt_type}_{lang}"

                if preview_key not in st.session_state:
                    st.session_state[preview_key] = st.session_state.get(generated_key, "")

                st.text_area(
                    f"Prompt {lang.upper()}",
                    height=260,
                    key=preview_key,
                )

                prompt_text = st.session_state.get(preview_key, "")

                if prompt_text:
                    copy_text = json.dumps(prompt_text)

                    st.components.v1.html(
                        f"""
                        <button onclick='navigator.clipboard.writeText({copy_text})'
                        style="
                            background-color:#1f77b4;
                            color:white;
                            padding:8px 16px;
                            border:none;
                            border-radius:6px;
                            cursor:pointer;
                            font-size:14px;
                            margin-top:8px;
                            width:100%;
                        ">
                        📋 Kopírovat prompt {lang.upper()}
                        </button>
                        """,
                        height=50,
                    )

                ai_outputs[lang] = st.text_area(
                    f"AI Output – {lang.upper()}",
                    height=320,
                    key=f"{prompt_type}_ai_output_{lang}",
                    placeholder="""nazev_produktu:
strucny_popis_produktu:
...""",
                )

                if ai_outputs[lang].strip():
                    prompt_docx_bytes = make_docx_bytes(ai_outputs[lang])
                    st.download_button(
                        f"Stáhnout DOCX {lang.upper()}",
                        data=prompt_docx_bytes,
                        file_name=f"vystup_prompt_{prompt_type}_{lang}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"{prompt_type}_download_docx_{lang}",
                    )

        filters_ai_output = ""

        if show_filters:
            st.markdown("---")
            st.markdown("## Filtry")

            if st.button("Vygenerovat prompt pro filtry", key=f"{prompt_type}_generate_filters_prompt"):
                if not product_name:
                    st.warning("Nejdřív nahraj CSV a vyber produkt.")
                else:
                    filters_prompt_text = build_mig_filters_prompt_text(
                        product_name=product_name,
                        product_ean=product_ean,
                        product_code=product_code,
                    )
                    st.session_state["mig_generated_filters_prompt_text"] = filters_prompt_text
                    st.session_state["mig_generated_filters_prompt_type"] = prompt_type
                    st.session_state[f"{prompt_type}_filters_prompt_preview"] = filters_prompt_text

            show_filters_prompt = (
                bool(st.session_state.get("mig_generated_filters_prompt_text", ""))
                and st.session_state.get("mig_generated_filters_prompt_type") == prompt_type
            )

            if show_filters_prompt:
                preview_filters_key = f"{prompt_type}_filters_prompt_preview"

                if preview_filters_key not in st.session_state:
                    st.session_state[preview_filters_key] = st.session_state.get(
                        "mig_generated_filters_prompt_text",
                        "",
                    )

                st.text_area(
                    "Prompt pro filtry",
                    height=300,
                    key=preview_filters_key,
                )

                filters_prompt_text = st.session_state.get(preview_filters_key, "")
                filters_copy_text = json.dumps(filters_prompt_text)

                st.components.v1.html(
                    f"""
                    <button onclick='navigator.clipboard.writeText({filters_copy_text})'
                    style="
                        background-color:#0f766e;
                        color:white;
                        padding:8px 16px;
                        border:none;
                        border-radius:6px;
                        cursor:pointer;
                        font-size:14px;
                        margin-top:8px;
                    ">
                    📋 Kopírovat prompt pro filtry
                    </button>
                    """,
                    height=50,
                )
            else:
                st.caption("Prompt pro filtry se zobrazí po kliknutí na tlačítko výše.")

            filters_ai_output = st.text_area(
                "AI Output – filtry",
                height=220,
                key=f"{prompt_type}_ai_output_filters",
                placeholder="""filteringProperty:Použití - štětec=
filteringProperty:Tvar štětce=
filteringProperty:Typ štětin=
filteringProperty:Velikost štětců=""",
            )

        st.markdown("### Odkazy na obrázky")

        img1_src = st.text_input(
            "Odkaz na obrázek 1",
            key=f"{prompt_type}_img1_src",
        )
        img2_src = st.text_input(
            "Odkaz na obrázek 2",
            key=f"{prompt_type}_img2_src",
        )
        img3_src = st.text_input(
            "Odkaz na obrázek 3",
            key=f"{prompt_type}_img3_src",
        )

        st.markdown("---")
        st.markdown("## Export do CSV")

        if st.button("Zpracovat do CSV", key=f"{prompt_type}_fill_btn_all"):
            if df is None or row_index is None:
                st.warning("Nejdřív nahraj CSV a vyber produkt.")
            else:
                try:
                    has_any_output = any(text.strip() for text in ai_outputs.values())
                    if not has_any_output:
                        st.warning("Vlož alespoň jeden AI output.")
                    else:
                        extra_values = {
                            "img1_src": img1_src.strip(),
                            "img2_src": img2_src.strip(),
                            "img3_src": img3_src.strip(),
                        }
                        extra_values = {k: v for k, v in extra_values.items() if v}

                        out_df = df.copy()

                        for lang in ("cs", "en", "sk"):
                            ai_output = ai_outputs.get(lang, "")
                            if ai_output.strip():
                                out_df = apply_mig_output_to_csv(
                                    df=out_df,
                                    row_index=row_index,
                                    ai_output=ai_output,
                                    template_kind=prompt_type,
                                    lang=lang,
                                    extra_values=extra_values,
                                )

                        if show_filters and filters_ai_output.strip():
                            out_df = enrich_mig_csv_with_filters(
                                df=out_df,
                                filters_text=filters_ai_output,
                                row_index=row_index,
                            )

                        st.session_state[state_key] = out_df.to_csv(
                            index=False,
                            sep=";",
                        ).encode("utf-8-sig")

                        st.success("CSV připraveno ke stažení.")
                except Exception as e:
                    st.error(f"Chyba při zpracování: {e}")

        if st.session_state[state_key] is not None:
            st.download_button(
                "Stáhnout FILLED CSV",
                data=st.session_state[state_key],
                file_name=f"{prompt_type}_FILLED.csv",
                mime="text/csv",
                key=f"{prompt_type}_download_filled",
            )