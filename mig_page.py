import json
import pandas as pd
import streamlit as st

from mig_core import (
    create_mig_card_row,
    build_mig_prompt,
    make_docx_bytes,
    apply_mig_output_to_csv,
)


# ==================================================
# MIG FILTER CONFIGS
# ==================================================

def get_mig_paint_filter_config() -> dict[str, list[str]]:
    return {
        "filteringProperty:Barva": [
            "Black",
            "Blue",
            "Brown",
            "Green",
            "Grey",
            "Orange",
            "Pink",
            "Purple",
            "Red",
            "Skin",
            "White",
            "Yellow",
            "Beige",
            "Rust",
        ],
        "filteringProperty:Druh barvy": [
            "Base",
            "Air",
            "Contrast",
            "Dry",
            "Layer",
            "Shade",
            "Technical",
            "Spreje",
        ],
        "filteringProperty:Příslušenství k barvám": [
            "Modelářské hmoty",
            "Ředidla & média",
            "Laky",
        ],
        "filteringProperty:Typ spreje": [
            "Primer / Základový sprej",
            "Lak / Varnish",
        ],
        "filteringProperty:Tón barvy": [
            "Dark",
            "Light",
            "Medium",
            "Fluorescent",
        ],
        "filteringProperty:Vlastnost barvy": [
            "Metallic",
            "Wash / Shade",
            "Contrast / Speedpaint",
            "Transparent / Glaze",
            "Weathering / Effects",
        ],
    }


def get_mig_brush_filter_config() -> dict[str, list[str]]:
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


def get_mig_filter_config(prompt_type: str) -> dict[str, list[str]]:
    if prompt_type == "mig_paints":
        return get_mig_paint_filter_config()

    if prompt_type == "mig_tools":
        return get_mig_brush_filter_config()

    return {}


# ==================================================
# MIG FILTER PROMPTS
# ==================================================

def build_mig_paint_filters_prompt_text(
    product_name: str,
    product_ean: str,
    product_code: str,
) -> str:
    config = get_mig_paint_filter_config()

    lines = []
    lines.append("[FILTERS]")
    lines.append("")
    lines.append("Použij pouze přesné hodnoty z povoleného seznamu.")
    lines.append("Vyplň všechny filtry, které lze z produktu bezpečně určit.")
    lines.append("Pokud si nejsi jistý jen u konkrétního pole, nech prázdné pouze to pole.")
    lines.append("Nikdy nevymýšlej vlastní variantu.")
    lines.append("Nikdy nepoužívej hodnotu, která není v povoleném seznamu.")
    lines.append("")
    lines.append("Pokud má filtr více hodnot, odděl je středníkem bez mezer navíc:")
    lines.append("Příklad:")
    lines.append("Metallic;Weathering / Effects")
    lines.append("")
    lines.append("Neodvozuj hodnoty agresivně.")
    lines.append("Pokud barvu, typ, tón nebo vlastnost nelze bezpečně určit z názvu produktu, popisu, kategorie nebo známého typu produktu, nech příslušné pole prázdné.")
    lines.append("")
    lines.append("POVOLENÉ HODNOTY:")
    lines.append("")

    for key, values in config.items():
        lines.append(key)
        for value in values:
            lines.append(f"- {value}")
        lines.append("")

    lines.append("--------------------------------------------------")
    lines.append("")
    lines.append("PRAVIDLA PRO URČOVÁNÍ FILTRŮ:")
    lines.append("")
    lines.append("1. filteringProperty:Barva")
    lines.append("")
    lines.append("Urči hlavní vizuální barvu produktu.")
    lines.append("Použij pouze jednu dominantní barvu, pokud jde o samostatnou barvu.")
    lines.append("Více hodnot použij pouze tehdy, pokud je produkt sada více barev nebo je z názvu bezpečně jasné, že obsahuje více barevných odstínů.")
    lines.append("")
    lines.append("Orientační mapování:")
    lines.append("- Black = černá, velmi tmavá černá barva")
    lines.append("- Blue = modrá, tyrkysově modrá, azurová, námořnická modrá")
    lines.append("- Brown = hnědá, zemité odstíny, kůže/leather, dřevo, hlína, bláto")
    lines.append("- Green = zelená, olivová, smaragdová, jedovatě zelená")
    lines.append("- Grey = šedá, popelavá, kamenná, šedomodrá")
    lines.append("- Orange = oranžová, ohnivě oranžová")
    lines.append("- Pink = růžová")
    lines.append("- Purple = fialová, purpurová")
    lines.append("- Red = červená, krvavá, karmínová")
    lines.append("- Skin = pleťové odstíny, flesh, skin, fleshtone")
    lines.append("- White = bílá")
    lines.append("- Yellow = žlutá, zlatavě žlutá, okrově žlutá")
    lines.append("- Beige = béžová, kostěná, slonová kost, krémová, písková, světlá hnědobéžová")
    lines.append("- Rust = rez, koroze, oxidace, rezavé efekty")
    lines.append("")
    lines.append("Pokud název obsahuje pouze fantasy název a z něj nelze bezpečně určit barvu, nech pole prázdné.")
    lines.append("")
    lines.append("2. filteringProperty:Druh barvy")
    lines.append("")
    lines.append("Urči druh barvy podle názvu produktu, kategorie nebo jasného označení produktu.")
    lines.append("")
    lines.append("Použij:")
    lines.append("- Base, pokud je produkt označen jako Base")
    lines.append("- Air, pokud je produkt označen jako Air nebo je určen pro airbrush")
    lines.append("- Contrast, pokud je produkt označen jako Contrast")
    lines.append("- Dry, pokud je produkt označen jako Dry")
    lines.append("- Layer, pokud je produkt označen jako Layer")
    lines.append("- Shade, pokud je produkt označen jako Shade nebo Wash")
    lines.append("- Technical, pokud je produkt označen jako Technical nebo jde o speciální efektovou/modelářskou barvu")
    lines.append("- Spreje, pokud jde o sprej, spray, aerosol, colour spray, primer spray nebo varnish spray")
    lines.append("")
    lines.append("Pokud produkt není barva, ale příslušenství k barvám, vyplň Druh barvy pouze tehdy, pokud je zároveň bezpečně určeno, že jde například o Technical, Spreje apod.")
    lines.append("Jinak nech pole prázdné.")
    lines.append("")
    lines.append("3. filteringProperty:Příslušenství k barvám")
    lines.append("")
    lines.append("Vyplň pouze u produktů, které jsou příslušenství k barvám, nikoliv běžná barva.")
    lines.append("")
    lines.append("Použij:")
    lines.append("- Modelářské hmoty = green stuff, liquid green stuff, modelovací hmota, tmel, putty")
    lines.append("- Ředidla & média = thinner, medium, glaze medium, airbrush thinner, ředidlo, médium")
    lines.append("- Laky = varnish, lak, matný lak, lesklý lak, satin varnish, gloss varnish, matte varnish")
    lines.append("")
    lines.append("Pokud jde o běžnou barvu, nech toto pole prázdné.")
    lines.append("")
    lines.append("4. filteringProperty:Typ spreje")
    lines.append("")
    lines.append("Vyplň pouze tehdy, pokud je produkt sprej.")
    lines.append("")
    lines.append("Použij:")
    lines.append("- Primer / Základový sprej = primer, undercoat, základový sprej, podkladový sprej")
    lines.append("- Lak / Varnish = varnish spray, lak ve spreji, munitorum varnish, matte varnish, gloss varnish, satin varnish")
    lines.append("")
    lines.append("Pokud je produkt sprej, ale není bezpečně jasné, zda jde o primer nebo lak, nech Typ spreje prázdný.")
    lines.append("Druh barvy v takovém případě stále může být:")
    lines.append("filteringProperty:Druh barvy=Spreje")
    lines.append("")
    lines.append("5. filteringProperty:Tón barvy")
    lines.append("")
    lines.append("Urči světlost/tón barvy pouze tehdy, pokud to lze bezpečně určit z názvu, popisu nebo běžně známého odstínu.")
    lines.append("")
    lines.append("Použij:")
    lines.append("- Dark = tmavý odstín, dark, deep, night, blackened, shadow, velmi sytá tmavá barva")
    lines.append("- Medium = střední odstín, běžná sytost bez jasného označení jako světlá nebo tmavá")
    lines.append("- Light = světlý odstín, light, pale, bright, ivory, bone, white, cream, highlight")
    lines.append("- Fluorescent = fluorescent, fluo, neon")
    lines.append("")
    lines.append("Pokud je barva fluorescent/neon, použij pouze:")
    lines.append("filteringProperty:Tón barvy=Fluorescent")
    lines.append("")
    lines.append("U příslušenství, laků, médií, tmelů nebo produktů bez jasného barevného odstínu nech pole prázdné.")
    lines.append("")
    lines.append("6. filteringProperty:Vlastnost barvy")
    lines.append("")
    lines.append("Vyplň speciální vlastnosti barvy, pokud jsou bezpečně určitelné.")
    lines.append("")
    lines.append("Použij:")
    lines.append("- Metallic = metalická barva, metallic, metal, gold, silver, bronze, brass, copper, steel, iron")
    lines.append("- Wash / Shade = shade, wash, ink wash, stínovací barva")
    lines.append("- Contrast / Speedpaint = contrast, speedpaint, xpress color, instant color, podobný typ rychlé kontrastní barvy")
    lines.append("- Transparent / Glaze = glaze, transparent, translucent, clear, ink, průhledná barva")
    lines.append("- Weathering / Effects = weathering, effects, technical effect, rust, corrosion, blood, mud, snow, crackle, texture, oxide, patina, slime, gore")
    lines.append("")
    lines.append("Pokud je produkt Contrast, automaticky nastav:")
    lines.append("filteringProperty:Vlastnost barvy=Contrast / Speedpaint")
    lines.append("")
    lines.append("Pokud je produkt Shade nebo Wash, automaticky nastav:")
    lines.append("filteringProperty:Vlastnost barvy=Wash / Shade")
    lines.append("")
    lines.append("Pokud je produkt metalická barva, automaticky nastav:")
    lines.append("filteringProperty:Vlastnost barvy=Metallic")
    lines.append("")
    lines.append("Pokud jde o efektovou barvu typu rez, krev, bahno, sníh, textura, koroze, patina nebo podobný speciální efekt, nastav:")
    lines.append("filteringProperty:Vlastnost barvy=Weathering / Effects")
    lines.append("")
    lines.append("--------------------------------------------------")
    lines.append("")
    lines.append("PRIORITA URČOVÁNÍ FILTRŮ:")
    lines.append("")
    lines.append("1. Přesný typ produktu uvedený v názvu nebo kategorii")
    lines.append("2. Druh barvy")
    lines.append("3. Příslušenství k barvám")
    lines.append("4. Typ spreje")
    lines.append("5. Vlastnost barvy")
    lines.append("6. Barva")
    lines.append("7. Tón barvy")
    lines.append("")
    lines.append("Konkrétní označení v názvu má vždy přednost před obecným odhadem.")
    lines.append("")
    lines.append("Příklady:")
    lines.append("- Produkt obsahuje \"Contrast\" → Druh barvy=Contrast a Vlastnost barvy=Contrast / Speedpaint")
    lines.append("- Produkt obsahuje \"Shade\" nebo \"Wash\" → Druh barvy=Shade a Vlastnost barvy=Wash / Shade")
    lines.append("- Produkt obsahuje \"Air\" → Druh barvy=Air")
    lines.append("- Produkt obsahuje \"Dry\" → Druh barvy=Dry")
    lines.append("- Produkt obsahuje \"Technical\" → Druh barvy=Technical")
    lines.append("- Produkt obsahuje \"Spray\" → Druh barvy=Spreje")
    lines.append("- Produkt obsahuje \"Primer\" nebo \"Undercoat\" → Typ spreje=Primer / Základový sprej")
    lines.append("- Produkt obsahuje \"Varnish\" nebo \"Lak\" → Příslušenství k barvám=Laky")
    lines.append("- Produkt obsahuje \"Medium\" nebo \"Thinner\" → Příslušenství k barvám=Ředidla & média")
    lines.append("- Produkt obsahuje \"Putty\", \"Green Stuff\" nebo \"Tmel\" → Příslušenství k barvám=Modelářské hmoty")
    lines.append("")
    lines.append("--------------------------------------------------")
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


def build_mig_brush_filters_prompt_text(
    product_name: str,
    product_ean: str,
    product_code: str,
) -> str:
    config = get_mig_brush_filter_config()

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
    lines.append("Při určování filtrů hledej co nejvíce informací na oficiálním webu MIG.")
    lines.append("Preferuj oficiální zdroj před jinými e-shopy nebo katalogy.")
    lines.append("Oficiální web:")
    lines.append("https://www.migjimenez.com/en/")
    lines.append("")
    lines.append("Zkus dohledat oficiální produktovou stránku, oficiální kategorii nebo oficiální popis produktu podle názvu, EAN nebo CODE.")
    lines.append("Pokud oficiální zdroj jasně potvrzuje typ štětin, tvar nebo velikost, vyplň je.")
    lines.append("Pokud to oficiální zdroj nepotvrdí dostatečně jasně, nech pole prázdné.")
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


def build_mig_filters_prompt_text(
    prompt_type: str,
    product_name: str,
    product_ean: str,
    product_code: str,
) -> str:
    if prompt_type == "mig_paints":
        return build_mig_paint_filters_prompt_text(
            product_name=product_name,
            product_ean=product_ean,
            product_code=product_code,
        )

    if prompt_type == "mig_tools":
        return build_mig_brush_filters_prompt_text(
            product_name=product_name,
            product_ean=product_ean,
            product_code=product_code,
        )

    return ""


# ==================================================
# FILTER PARSE + VALIDATION
# ==================================================

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


def validate_and_normalize_mig_filters(
    parsed_filters: dict[str, str],
    prompt_type: str,
) -> dict[str, str]:
    config = get_mig_filter_config(prompt_type)
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


def enrich_mig_csv_with_filters(
    df: pd.DataFrame,
    filters_text: str,
    row_index: int,
    prompt_type: str,
) -> pd.DataFrame:
    df_out = df.copy()

    parsed_filters = parse_filters_from_text(filters_text)
    validated_filters = validate_and_normalize_mig_filters(
        parsed_filters=parsed_filters,
        prompt_type=prompt_type,
    )

    for key, value in validated_filters.items():
        if key not in df_out.columns:
            df_out[key] = ""
        df_out.at[row_index, key] = value

    return df_out


def get_filters_placeholder(prompt_type: str) -> str:
    config = get_mig_filter_config(prompt_type)
    return "\n".join(f"{key}=" for key in config.keys())


# ==================================================
# PAGE
# ==================================================

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
            show_filters=True,
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
                    product_options = [
                        f"{i} | {row.get(name_col, '')}"
                        for i, row in df.iterrows()
                    ]

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

            if prompt_type == "mig_paints":
                st.caption("Tato sekce používá filtry pro MIG / AMMO barvy.")
            elif prompt_type == "mig_tools":
                st.caption("Tato sekce používá filtry pro MIG / AMMO štětce.")

            if st.button("Vygenerovat prompt pro filtry", key=f"{prompt_type}_generate_filters_prompt"):
                if not product_name:
                    st.warning("Nejdřív nahraj CSV a vyber produkt.")
                else:
                    filters_prompt_text = build_mig_filters_prompt_text(
                        prompt_type=prompt_type,
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
                placeholder=get_filters_placeholder(prompt_type),
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

                        extra_values = {
                            k: v
                            for k, v in extra_values.items()
                            if v
                        }

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
                                prompt_type=prompt_type,
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