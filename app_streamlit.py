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
        # AIレシピのロジック（CMYK変換）を完全に逆算してシミュレーションする
        MAX_DROPS = 30.0
        # ゼロ除算を防ぐため、スライダーの最小値を0.1とする
        eff_intensity = max(0.1, intensity)
        eff_kb = max(0.1, k_black)
        eff_kw = max(0.1, k_white)
        
        # 1. 滴数からベースとなるCMYKの割合を逆算
        base_blue = sim_b / (MAX_DROPS * eff_intensity)
        base_red = sim_r / (MAX_DROPS * eff_intensity)
        base_yellow = sim_y / (MAX_DROPS * eff_intensity)
        base_black = sim_k / (MAX_DROPS * eff_intensity * eff_kb)
        
        k_val = min(255.0, base_black * 255.0)
        c_val = base_blue * (255.0 - k_val) + k_val
        m_val = base_red * (255.0 - k_val) + k_val
        y_val = base_yellow * (255.0 - k_val) + k_val
        
        # 2. C, M, Y から RGBを復元
        calc_r = max(0.0, min(255.0, 255.0 - c_val))
        calc_g = max(0.0, min(255.0, 255.0 - m_val))
        calc_b = max(0.0, min(255.0, 255.0 - y_val))
        
        # 3. 白の滴数による明るさ補正
        # 今の色（CMYK）が本来必要とする「基準の白の滴数」を計算
        luminance = (calc_r + calc_g + calc_b) / 3.0
        expected_w = (luminance / 255.0) * MAX_DROPS * eff_kw
        
        # 基準より白が多いか少ないかで明暗を調整
        diff_w = sim_w - expected_w
        if diff_w > 0:
            # 基準より白が多い場合は白に近づく（明るくなる）
            factor = 1.0 - math.exp(-diff_w * 0.05)
            final_r = calc_r + (255.0 - calc_r) * factor
            final_g = calc_g + (255.0 - calc_g) * factor
            final_b = calc_b + (255.0 - calc_b) * factor
        else:
            # 基準より白が少ない場合は暗くなる
            factor = 1.0 - math.exp(diff_w * 0.05) # diff_w はマイナスなので 1 - exp(-|diff_w|)
            final_r = calc_r * (1.0 - factor)
            final_g = calc_g * (1.0 - factor)
            final_b = calc_b * (1.0 - factor)
            
        final_r = int(max(0, min(255, final_r)))
        final_g = int(max(0, min(255, final_g)))
        final_b = int(max(0, min(255, final_b)))
        sim_hex = f"#{final_r:02x}{final_g:02x}{final_b:02x}"
        
        st.markdown("#### 予測される混色")
        st.markdown(
            f'<div style="background-color: {sim_hex}; height: 150px; width: 100%; border-radius: 10px; border: 1px solid #ccc; margin-top: 10px;"></div>', 
            unsafe_allow_html=True
        )
        st.write(f"予測 RGB: R:{final_r} G:{final_g} B:{final_b}")
