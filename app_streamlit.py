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
    manual_r = st.number_input("R (0-255)", min_value=0, max_value=255, value=0, step=1)
    manual_g = st.number_input("G (0-255)", min_value=0, max_value=255, value=0, step=1)
    manual_b = st.number_input("B (0-255)", min_value=0, max_value=255, value=0, step=1)
    
    manual_color_hex = f"#{manual_r:02x}{manual_g:02x}{manual_b:02x}"
    st.markdown(f'<div style="background-color: {manual_color_hex}; height: 50px; border-radius: 5px;"></div>', unsafe_allow_html=True)

# --- メインエリア ---
tab1, tab2 = st.tabs(["Color Muse (CSV読込)", "単色作成 (手動入力)"])

# --- 関数: レシピ計算（ゼロから色を作るロジック） ---
def calculate_recipe_single(r, g, b, ints, kw, kb):
    # RGBからCMYへの簡易変換（減法混色の近似）
    c = 255 - r
    m = 255 - g
    y = 255 - b
    
    # CMYからK（黒）を抽出
    k = min(c, m, y)
    
    # 黒成分を引いて純粋なCMYを算出
    if k == 255:
        c = m = y = 0
    else:
        c = (c - k) / (255 - k) * 255
        m = (m - k) / (255 - k) * 255
        y = (y - k) / (255 - k) * 255
        
    # アプリの染料（赤、青、黄）にマッピング
    base_blue = c / 255.0
    base_red = m / 255.0
    base_yellow = y / 255.0
    base_black = k / 255.0
    
    # 明度（白の必要性）の算出
    luminance = (r + g + b) / 3.0
    base_white = luminance / 255.0

    drops = {"赤": 0, "青": 0, "黄": 0, "黒": 0, "白": 0}
    MAX_DROPS = 30.0  # 基準ドロップ数
    
    drops["赤"] = math.ceil(base_red * MAX_DROPS * ints)
    drops["青"] = math.ceil(base_blue * MAX_DROPS * ints)
    drops["黄"] = math.ceil(base_yellow * MAX_DROPS * ints)
    drops["黒"] = math.ceil(base_black * MAX_DROPS * ints * kb)
    
    # 色が薄い（白っぽい）場合は白を足す
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
                
            # HEXコードの取得ロジック
            std_hex = ""
            if 'std_D65_2_hex' in df.columns:
                std_hex = str(df['std_D65_2_hex'].iloc[0]).strip()
            elif 'standard-D65-2deg-hex' in df.columns:
                std_hex = str(df['standard-D65-2deg-hex'].iloc[0]).strip()
            else:
                st.error("CSVからHEXデータが見つかりません。")
                st.stop()
                
            if not std_hex.startswith('#'): 
                std_hex = '#' + std_hex
            
            # HEXからRGBに変換
            hex_val = std_hex.lstrip('#')
            if len(hex_val) == 6:
                r = int(hex_val[0:2], 16)
                g = int(hex_val[2:4], 16)
                b = int(hex_val[4:6], 16)
            else:
                st.error("不正なカラーコードです。")
                st.stop()
            
            st.markdown("#### 目標色 (Standard)")
            st.markdown(f'<div style="background-color: {std_hex}; height: 100px; width: 50%; border-radius: 10px; margin-bottom: 10px;"></div>', unsafe_allow_html=True)
            st.write(f"R: {r}  |  G: {g}  |  B: {b}")
            st.write(f"HEX: {std_hex}")
                
            st.divider()
            
            # ゼロから作るレシピを計算
            drops = calculate_recipe_single(r, g, b, intensity, k_white, k_black)
            display_recipe(drops)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

# --- Tab2: 単色作成 ---
with tab2:
    st.markdown("### 指定したRGBからレシピを算出")
    st.markdown(f"現在選択中の色: **R:{manual_r} G:{manual_g} B:{manual_b}**")
    
    drops_single = calculate_recipe_single(manual_r, manual_g, manual_b, intensity, k_white, k_black)
    display_recipe(drops_single)
