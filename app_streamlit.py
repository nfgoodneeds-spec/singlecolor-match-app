import streamlit as st
import pandas as pd
import math

# --- ページ設定 ---
st.set_page_config(
    page_title="Color Match AI",
    page_icon="🎨",
    layout="centered"
)

st.title("AI Color Matching System")
st.markdown("Color MuseのCSVデータを読み込み、目標色をゼロから調合するためのレシピを算出します。")

# --- UIレイアウト: サイドバー（チューニング） ---
with st.sidebar:
    st.header("リアルタイム調整")
    st.markdown("染料の全体量や、白・黒の係数を調整できます。")
    
    intensity = st.slider("全体強度 (染料の濃さ)", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
    k_white = st.slider("白 追加係数", min_value=0.1, max_value=10.0, value=2.0, step=0.1)
    k_black = st.slider("黒 追加係数", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    
    st.divider()
    st.markdown("### 単色作成用 (RGB手動入力)")
    manual_r = st.number_input("R (0-255)", min_value=0, max_value=255, value=200, step=1)
    manual_g = st.number_input("G (0-255)", min_value=0, max_value=255, value=200, step=1)
    manual_b = st.number_input("B (0-255)", min_value=0, max_value=255, value=200, step=1)
    
    manual_color_hex = f"#{manual_r:02x}{manual_g:02x}{manual_b:02x}"
    st.markdown(f'<div style="background-color: {manual_color_hex}; height: 50px; border-radius: 5px; border: 1px solid #ccc;"></div>', unsafe_allow_html=True)

# --- メインエリア ---
tab1, tab2, tab3, tab4 = st.tabs(["Color Muse (CSV読込)", "単色作成", "調合シミュレーター", "2色差分補正"])

# --- 関数: レシピ計算（ゼロから色を作るロジック） ---
def calculate_recipe_single(r, g, b, ints, kw, kb):
    c = 255 - r
    m = 255 - g
    y = 255 - b
    k = min(c, m, y)
    
    if k == 255:
        c = m = y = 0
    else:
        c = (c - k) / (255 - k) * 255
        m = (m - k) / (255 - k) * 255
        y = (y - k) / (255 - k) * 255
        
    base_blue = c / 255.0
    base_red = m / 255.0
    base_yellow = y / 255.0
    base_black = k / 255.0
    luminance = (r + g + b) / 3.0
    base_white = luminance / 255.0

    drops = {"赤": 0, "青": 0, "黄": 0, "黒": 0, "白": 0}
    MAX_DROPS = 30.0
    
    drops["赤"] = math.ceil(base_red * MAX_DROPS * ints)
    drops["青"] = math.ceil(base_blue * MAX_DROPS * ints)
    drops["黄"] = math.ceil(base_yellow * MAX_DROPS * ints)
    drops["黒"] = math.ceil(base_black * MAX_DROPS * ints * kb)
    if base_white > 0.1:
         drops["白"] = math.ceil(base_white * MAX_DROPS * kw)
    if luminance < 50:
        drops["白"] = 0

    return drops

# --- 関数: レシピ計算（2色の差分を補正するロジック） ---
def calculate_recipe_diff_rgb(curr_r, curr_g, curr_b, tgt_r, tgt_g, tgt_b, ints, kw, kb):
    cc, cm, cy = 255 - curr_r, 255 - curr_g, 255 - curr_b
    ck = min(cc, cm, cy)
    if ck != 255:
        cc, cm, cy = (cc - ck) / (255 - ck) * 255, (cm - ck) / (255 - ck) * 255, (cy - ck) / (255 - ck) * 255
    else:
        cc = cm = cy = 0

    tc, tm, ty = 255 - tgt_r, 255 - tgt_g, 255 - tgt_b
    tk = min(tc, tm, ty)
    if tk != 255:
        tc, tm, ty = (tc - tk) / (255 - tk) * 255, (tm - tk) / (255 - tk) * 255, (ty - tk) / (255 - tk) * 255
    else:
        tc = tm = ty = 0

    dc = max(0, tc - cc)
    dm = max(0, tm - cm)
    dy = max(0, ty - cy)
    dk = max(0, tk - ck)

    base_blue = dc / 255.0
    base_red = dm / 255.0
    base_yellow = dy / 255.0
    base_black = dk / 255.0

    curr_lum = (curr_r + curr_g + curr_b) / 3.0
    tgt_lum = (tgt_r + tgt_g + tgt_b) / 3.0
    diff_lum = max(0, tgt_lum - curr_lum)
    base_white = diff_lum / 255.0

    drops = {"赤": 0, "青": 0, "黄": 0, "黒": 0, "白": 0}
    MAX_DROPS = 30.0

    drops["赤"] = math.ceil(base_red * MAX_DROPS * ints)
    drops["青"] = math.ceil(base_blue * MAX_DROPS * ints)
    drops["黄"] = math.ceil(base_yellow * MAX_DROPS * ints)
    drops["黒"] = math.ceil(base_black * MAX_DROPS * ints * kb)
    if base_white > 0.05:
        drops["白"] = math.ceil(base_white * MAX_DROPS * kw)

    return drops

def display_recipe(drops):
    colors_info = {"赤": "#FF4C4C", "青": "#4C4CFF", "黄": "#FFD700", "黒": "#888888", "白": "#FFFFFF"}
    
    st.markdown("### 【 AI 調合レシピ 】")
    for name, count in drops.items():
        cc = count * 0.05
        color_code = colors_info[name]
        opacity = 1.0 if count > 0 else 0.3
        
        st.markdown(
            f'<div style="display: flex; align-items: center; margin-bottom: 10px; opacity: {opacity};">'
            f'<div style="background-color: {color_code}; width: 20px; height: 20px; border-radius: 50%; margin-right: 15px; border: 1px solid #555;"></div>'
            f'<span style="font-size: 20px; font-weight: bold; width: 80px;">{name}</span>'
            f'<span style="font-size: 20px; font-weight: bold; width: 100px;">{count:>2} 滴</span>'
            f'<span style="font-size: 18px; color: #888;">[ {cc:.2f} cc ]</span>'
            f'</div>', 
            unsafe_allow_html=True
        )

# --- Tab1: Color Muse (CSV) ---
with tab1:
    uploaded_file = st.file_uploader("Color Muse の CSVファイル をアップロード", key="tab1_csv")
    if uploaded_file is not None:
        try:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding='shift_jis')
                
            std_hex = None
            # ズレ対策：周辺の列も探しに行く強靭なロジック
            for col in ['std_D65_2_hex', 'standard-D65-2deg-hex', 'std_D65_2_b.1', 'standard-D65-2deg-b.1']:
                if col in df.columns:
                    val = str(df[col].iloc[0]).strip()
                    if val.startswith('#'):
                        std_hex = val
                        break
                        
            if not std_hex:
                st.error("CSVから目標色のHEXデータが見つかりません。")
                st.stop()
            
            hex_val = std_hex.lstrip('#')
            if len(hex_val) == 6:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
            else:
                st.error("不正なカラーコードです。")
                st.stop()
            
            st.markdown("#### 目標色 (Standard)")
            st.markdown(f'<div style="background-color: {std_hex}; height: 100px; width: 50%; border-radius: 10px; margin-bottom: 10px; border: 1px solid #ccc;"></div>', unsafe_allow_html=True)
            st.write(f"R: {r}  |  G: {g}  |  B: {b}")
            st.divider()
            
            drops = calculate_recipe_single(r, g, b, intensity, k_white, k_black)
            display_recipe(drops)
        except Exception as e:
            st.error("エラーが発生しました: ファイルの形式を確認してください。")

# --- Tab2: 単色作成 ---
with tab2:
    st.markdown("### 指定したRGBからレシピを算出")
    st.markdown(f"現在選択中の色: **R:{manual_r} G:{manual_g} B:{manual_b}**")
    st.markdown(
        f'<div style="background-color: {manual_color_hex}; height: 100px; width: 50%; border-radius: 10px; margin-bottom: 20px; border: 1px solid #ccc;"></div>', 
        unsafe_allow_html=True
    )
    drops_single = calculate_recipe_single(manual_r, manual_g, manual_b, intensity, k_white, k_black)
    display_recipe(drops_single)

# --- Tab3: 調合シミュレーター ---
with tab3:
    st.markdown("### 滴数から色をシミュレーション")
    col1, col2 = st.columns([1, 1])
    with col1:
        sim_r = st.number_input("🔴 赤 (滴)", min_value=0, max_value=500, value=0, step=1)
        sim_b = st.number_input("🔵 青 (滴)", min_value=0, max_value=500, value=0, step=1)
        sim_y = st.number_input("🟡 黄 (滴)", min_value=0, max_value=500, value=0, step=1)
        sim_k = st.number_input("⚫ 黒 (滴)", min_value=0, max_value=500, value=0, step=1)
        sim_w = st.number_input("⚪ 白 (滴)", min_value=0, max_value=500, value=0, step=1)
    with col2:
        c_rate = 1.0 - math.exp(-sim_b * 0.05)
        m_rate = 1.0 - math.exp(-sim_r * 0.05)
        y_rate = 1.0 - math.exp(-sim_y * 0.05)
        k_rate = 1.0 - math.exp(-sim_k * 0.05)
        
        calc_r = 255 * (1 - c_rate) * (1 - k_rate)
        calc_g = 255 * (1 - m_rate) * (1 - k_rate)
        calc_b = 255 * (1 - y_rate) * (1 - k_rate)
        
        w_rate = 1.0 - math.exp(-sim_w * 0.05)
        calc_r = calc_r + (255 - calc_r) * w_rate
        calc_g = calc_g + (255 - calc_g) * w_rate
        calc_b = calc_b + (255 - calc_b) * w_rate
        
        final_r = int(max(0, min(255, calc_r)))
        final_g = int(max(0, min(255, calc_g)))
        final_b = int(max(0, min(255, calc_b)))
        sim_hex = f"#{final_r:02x}{final_g:02x}{final_b:02x}"
        
        st.markdown("#### 予測される混色")
        st.markdown(
            f'<div style="background-color: {sim_hex}; height: 150px; width: 100%; border-radius: 10px; border: 1px solid #ccc; margin-top: 10px;"></div>', 
            unsafe_allow_html=True
        )
        st.write(f"予測 RGB: R:{final_r} G:{final_g} B:{final_b}")

# --- Tab4: 2色差分補正 ---
with tab4:
    st.markdown("### 今の色から目標色へ近づける補正レシピ")
    st.markdown("「現在の色」に何を足せば「目標の色」になるかを計算します。※引き算（色を抜くこと）はできないため、不足している染料のみを算出します。")
    
    diff_csv = st.file_uploader("Color Muse の CSVファイル をアップロード (2色補正用)", key="tab4_csv")
    
    is_csv_loaded = False
    curr_r, curr_g, curr_b = 200, 200, 200
    tgt_r, tgt_g, tgt_b = 150, 150, 150
    
    if diff_csv is not None:
        try:
            try:
                df = pd.read_csv(diff_csv, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(diff_csv, encoding='shift_jis')
                
            std_hex, smp_hex = None, None
            
            # ズレ対策：周辺の列も探しに行く強靭なロジック
            for col in ['std_D65_2_hex', 'standard-D65-2deg-hex', 'std_D65_2_b.1', 'standard-D65-2deg-b.1']:
                if col in df.columns:
                    val = str(df[col].iloc[0]).strip()
                    if val.startswith('#'):
                        std_hex = val
                        break
                        
            for col in ['smp_D65_2_hex', 'sample-D65-2deg-hex', 'smp_D65_2_b.1', 'sample-D65-2deg-b.1']:
                if col in df.columns:
                    val = str(df[col].iloc[0]).strip()
                    if val.startswith('#'):
                        smp_hex = val
                        break

            if not std_hex or not smp_hex:
                st.error("CSVから目標色または現在の色のHEXデータが見つかりません。")
                st.stop()

            tgt_r, tgt_g, tgt_b = int(std_hex[1:3], 16), int(std_hex[3:5], 16), int(std_hex[5:7], 16)
            curr_r, curr_g, curr_b = int(smp_hex[1:3], 16), int(smp_hex[3:5], 16), int(smp_hex[5:7], 16)
            
            is_csv_loaded = True
            st.success("CSVから「現在の色(Sample)」と「目標の色(Standard)」を読み込みました！")
        except Exception as e:
            st.error("エラーが発生しました。ファイル形式を確認してください。")

    col_c, col_t = st.columns(2)
    
    if not is_csv_loaded:
        st.info("CSVをアップロードするか、以下の数値を手動で変更してください。")
        with col_c:
            st.markdown("#### 現在の色 (色抜け部)")
            curr_r = st.number_input("現在 R", min_value=0, max_value=255, value=200, step=1, key="cr")
            curr_g = st.number_input("現在 G", min_value=0, max_value=255, value=200, step=1, key="cg")
            curr_b = st.number_input("現在 B", min_value=0, max_value=255, value=200, step=1, key="cb")
        with col_t:
            st.markdown("#### 目標の色 (基準色)")
            tgt_r = st.number_input("目標 R", min_value=0, max_value=255, value=150, step=1, key="tr")
            tgt_g = st.number_input("目標 G", min_value=0, max_value=255, value=150, step=1, key="tg")
            tgt_b = st.number_input("目標 B", min_value=0, max_value=255, value=150, step=1, key="tb")
    else:
        with col_c:
            st.markdown("#### 現在の色 (Sample)")
            st.write(f"R: {curr_r}  |  G: {curr_g}  |  B: {curr_b}")
        with col_t:
            st.markdown("#### 目標の色 (Standard)")
            st.write(f"R: {tgt_r}  |  G: {tgt_g}  |  B: {tgt_b}")

    col_c2, col_t2 = st.columns(2)
    with col_c2:
        curr_hex = f"#{curr_r:02x}{curr_g:02x}{curr_b:02x}"
        st.markdown(f'<div style="background-color: {curr_hex}; height: 80px; width: 100%; border-radius: 10px; border: 1px solid #ccc;"></div>', unsafe_allow_html=True)
    with col_t2:
        tgt_hex = f"#{tgt_r:02x}{tgt_g:02x}{tgt_b:02x}"
        st.markdown(f'<div style="background-color: {tgt_hex}; height: 80px; width: 100%; border-radius: 10px; border: 1px solid #ccc;"></div>', unsafe_allow_html=True)

    st.divider()
    diff_drops = calculate_recipe_diff_rgb(curr_r, curr_g, curr_b, tgt_r, tgt_g, tgt_b, intensity, k_white, k_black)
    display_recipe(diff_drops)
