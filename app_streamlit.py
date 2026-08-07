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
st.markdown("Color MuseのCSVから基準色(Standard)を読み込み、基本染料のレシピを算出します。")

# --- UIレイアウト: サイドバー（チューニング） ---
with st.sidebar:
    st.header("リアルタイム調整")
    st.markdown("ガンマ値や明度係数を調整できます。")
    
    gamma = st.slider("ガンマ値 (色の変化カーブ)", min_value=0.5, max_value=1.5, value=0.85, step=0.05)
    k_white = st.slider("白 追加係数", min_value=0.1, max_value=10.0, value=4.5, step=0.1)
    k_black = st.slider("黒 追加係数", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    
    st.divider()
    st.markdown("### 単色作成用 (RGB手動入力)")
    manual_r = st.number_input("R (0-255)", min_value=0, max_value=255, value=0, step=1)
    manual_g = st.number_input("G (0-255)", min_value=0, max_value=255, value=0, step=1)
    manual_b = st.number_input("B (0-255)", min_value=0, max_value=255, value=0, step=1)
    intensity = st.slider("全体強度 (単色作成用)", min_value=0.1, max_value=3.0, value=1.0, step=0.1)
    
    manual_color_hex = f"#{manual_r:02x}{manual_g:02x}{manual_b:02x}"
    st.markdown(f'<div style="background-color: {manual_color_hex}; height: 50px; border-radius: 5px;"></div>', unsafe_allow_html=True)
    
# --- メインエリア ---
tab1, tab2 = st.tabs(["Color Muse (CSV読込)", "単色作成 (手動入力)"])

# --- 関数: CSV解析とレシピ計算 ---
def calculate_recipe_diff(std_L, std_a, std_b, sam_L, sam_a, sam_b, g, kw, kb):
    diff_L = std_L - sam_L
    diff_a = std_a - sam_a
    diff_b = std_b - sam_b

    drops = {"赤": 0, "青": 0, "黄": 0, "黒": 0, "白": 0}

    k_red = 0.1
    k_yellow = 0.2
    k_blue = 0.15

    base_intensity_a = 1.0 + (abs(sam_a) / 100.0)
    base_intensity_b = 1.0 + (abs(sam_b) / 100.0)

    if diff_a > 0:
        drops["赤"] = math.ceil(((diff_a ** g) * k_red) * base_intensity_a)
    
    if diff_b > 0:
        drops["黄"] = math.ceil(((diff_b ** g) * k_yellow) * base_intensity_b)
    elif diff_b < 0:
        drops["青"] = math.ceil(((abs(diff_b) ** g) * k_blue) * base_intensity_b)

    total_color_drops = drops["赤"] + drops["青"] + drops["黄"]

    if diff_L > 0:
        drops["白"] = math.ceil((diff_L ** g) * kw) + math.ceil(total_color_drops * 0.1)
    elif diff_L < 0:
        raw_black = math.ceil((abs(diff_L) ** g) * kb)
        drops["黒"] = max(0, raw_black - math.ceil(total_color_drops * 0.05))

    return drops

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
    uploaded_file = st.file_uploader("Color Muse の CSVファイル をアップロード", type=['csv'])
    
    if uploaded_file is not None:
        try:
            try:
                df = pd.read_csv(uploaded_file, encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(uploaded_file, encoding='shift_jis')
                
            if 'std_D65_2_L' in df.columns:
                std_hex = str(df['std_D65_2_hex'].iloc[0]).strip()
                std_L = float(df['std_D65_2_L'].iloc[0])
                std_a = float(df['std_D65_2_a'].iloc[0])
                std_b = float(df['std_D65_2_b'].iloc[0])
                sam_hex = str(df['smp_D65_2_hex'].iloc[0]).strip()
                sam_L = float(df['smp_D65_2_L'].iloc[0])
                sam_a = float(df['smp_D65_2_a'].iloc[0])
                sam_b = float(df['smp_D65_2_b'].iloc[0])
            elif 'standard-D65-2deg-hex' in df.columns:
                std_hex = str(df['standard-D65-2deg-hex'].iloc[0]).strip()
                std_L = float(df['standard-D65-2deg-L'].iloc[0])
                std_a = float(df['standard-D65-2deg-a'].iloc[0])
                std_b = float(df['standard-D65-2deg-b'].iloc[0])
                
                try:
                    sam_hex = str(df['sample-D65-2deg-b.1'].iloc[0]).strip()
                    sam_L = float(df['sample-D65-2deg-mode'].iloc[0])
                    sam_a = float(df['sample-D65-2deg-L'].iloc[0])
                    sam_b = float(df['sample-D65-2deg-a'].iloc[0])
                except:
                    sam_hex = str(df['sample-D65-2deg-hex'].iloc[0]).strip()
                    sam_L = float(df['sample-D65-2deg-L'].iloc[0])
                    sam_a = float(df['sample-D65-2deg-a'].iloc[0])
                    sam_b = float(df['sample-D65-2deg-b'].iloc[0])
            else:
                st.error("CSVからHEXデータが見つかりません。")
                st.stop()
                
            if not std_hex.startswith('#'): std_hex = '#' + std_hex
            if not sam_hex.startswith('#'): sam_hex = '#' + sam_hex
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### 基準色 (Standard)")
                st.markdown(f'<div style="background-color: {std_hex}; height: 100px; border-radius: 10px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
                st.write(f"L*: {std_L:.2f}  \n a*: {std_a:.2f}  \n b*: {std_b:.2f}")
            with col2:
                st.markdown("#### 色抜け部 (Sample)")
                st.markdown(f'<div style="background-color: {sam_hex}; height: 100px; border-radius: 10px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
                st.write(f"L*: {sam_L:.2f}  \n a*: {sam_a:.2f}  \n b*: {sam_b:.2f}")
                
            st.divider()
            
            drops = calculate_recipe_diff(std_L, std_a, std_b, sam_L, sam_a, sam_b, gamma, k_white, k_black)
            display_recipe(drops)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- Tab2: 単色作成 ---
with tab2:
    st.markdown("### 指定したRGBからレシピを算出")
    st.markdown(f"現在選択中の色: **R:{manual_r} G:{manual_g} B:{manual_b}**")
    
    drops_single = calculate_recipe_single(manual_r, manual_g, manual_b, intensity, k_white, k_black)
    display_recipe(drops_single)
