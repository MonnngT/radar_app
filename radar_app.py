import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io

# 页面配置
st.set_page_config(page_title="通用外径极坐标分析系统", layout="wide")
st.title("🎯 通用零部件外径极坐标分析系统")

# 侧边栏：全局参数设置
with st.sidebar:
    st.header("⚙️ 基础设置")
    report_title = st.text_input("图表标题 (Title)", "Outer Diameter Analysis")
    
    st.markdown("---")
    st.header("📏 尺寸标准与公差")
    target_val = st.number_input("目标尺寸 (Target)", value=39.20, step=0.01, format="%.2f")
    upper_limit = st.number_input("公差上限 (Upper Limit)", value=39.30, step=0.01, format="%.2f")
    lower_limit = st.number_input("公差下限 (Lower Limit)", value=39.10, step=0.01, format="%.2f")
    
    interval = st.number_input("单点代表角度 (度/点)", value=30, step=1)

    st.markdown("---")
    st.header("🎨 特征区域遮罩")
    show_flats = st.checkbox("显示平面区域 (上下灰色)", value=True)
    show_pins = st.checkbox("显示顶针区域 (左右黄色)", value=True)

# 核心绘图函数
def create_radar(title, angles, values, target, upper, lower, interval, show_flats, show_pins):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

    margin = max((upper - lower) * 1.5, 0.1) 
    r_min = lower - margin
    r_max = upper + margin

    oot_count = sum(1 for v in values if v < lower or v > upper)
    oot_area = oot_count * interval
    oot_percentage = (oot_area / 360.0) * 100

    theta_full = np.linspace(0, 2*np.pi, 300)
    ax.plot(theta_full, np.full_like(theta_full, target), color='green', linewidth=2, label=f'Target ({target})')
    ax.plot(theta_full, np.full_like(theta_full, upper), color='red', linestyle='--', linewidth=1.5, label=f'Tolerance ({lower}-{upper})')
    ax.plot(theta_full, np.full_like(theta_full, lower), color='red', linestyle='--', linewidth=1.5)
    ax.fill_between(theta_full, lower, upper, color='green', alpha=0.1)

    if show_flats:
        ax.fill_between(np.linspace(np.deg2rad(340), np.deg2rad(360+20), 50), r_min, r_max, color='gray', alpha=0.25, label='Flat Area')
        ax.fill_between(np.linspace(np.deg2rad(160), np.deg2rad(200), 50), r_min, r_max, color='gray', alpha=0.25)

    if show_pins:
        ax.fill_between(np.linspace(np.deg2rad(70), np.deg2rad(110), 50), r_min, r_max, color='gold', alpha=0.35, label='Pin Area')
        ax.fill_between(np.linspace(np.deg2rad(250), np.deg2rad(290), 50), r_min, r_max, color='gold', alpha=0.35)

    a_plot, v_plot = [], []
    for i in range(len(angles)):
        a_plot.append(angles[i])
        v_plot.append(values[i])
        if i < len(angles) - 1:
            diff = abs(angles[i+1] - angles[i])
            actual_gap = min(diff, 360 - diff)
            if actual_gap > interval + 2:
                a_plot.append(angles[i])
                v_plot.append(np.nan)

    if len(angles) > 0:
        diff = abs(angles[0] - angles[-1])
        actual_gap = min(diff, 360 - diff)
        if actual_gap > interval + 2:
             a_plot.append(angles[-1])
             v_plot.append(np.nan)

    ax.plot(np.deg2rad(a_plot), v_plot, color='royalblue', linewidth=2.5, marker='o', markersize=6, label='Measured Data')

    oot_points = [(a, v) for a, v in zip(angles, values) if v < lower or v > upper]
    if oot_points:
        ax.scatter([np.deg2rad(p[0]) for p in oot_points], [p[1] for p in oot_points], color='crimson', s=120, zorder=6, label='Out of Tolerance')

    for a, v in zip(angles, values):
        color = 'crimson' if (v < lower or v > upper) else 'darkblue'
        offset = (upper - lower) * 0.15 if v >= target else -(upper - lower) * 0.25
        ax.text(np.deg2rad(a), v + offset, f"{v:.2f}", ha='center', va='center', fontsize=11, color=color, fontweight='bold')

    ax.set_ylim(r_min, r_max)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    
    tick_step = int(interval) if interval >= 10 else 20
    ax.set_xticks(np.deg2rad(np.arange(0, 360, tick_step)))
    ax.set_xticklabels([f"{x}°" for x in np.arange(0, 360, tick_step)], fontsize=10)

    defect_text = f"OOT Points: {oot_count}\nOOT Area: {oot_area}°\nDefect Ratio: {oot_area}/360 = {oot_percentage:.1f}%"
    plt.figtext(0.0, 1.02, defect_text, fontsize=13, color='darkred', bbox=dict(facecolor='mistyrose', alpha=0.9, edgecolor='red'), va='bottom', ha='left')

    ax.set_title(title, va='bottom', fontsize=20, fontweight='bold', pad=40)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=10)
    
    return fig

# ----------------- 主界面布局 -----------------
col1, col2 = st.columns([1, 2])

# 初始数据
default_angles = [30.0, 60.0, 120.0, 150.0, 210.0, 240.0, 300.0, 330.0]
default_values = [39.08, 39.15, 39.13, 39.21, 39.06, 39.15, 39.17, 39.21]

# 🌟 终极防崩溃：强制声明两列都为 float64，兼容任何空白(NaN)输入 🌟
df = pd.DataFrame({
    "测量角度 (°)": pd.Series(default_angles, dtype='float64'),
    "实测数据 (mm)": pd.Series(default_values, dtype='float64')
})

with col1:
    st.subheader("📝 数据录入区")
    st.info("💡 **清空表格**：点击表格内部，按 `Ctrl+A` 全选，再按 `Delete`。\n\n💡 **全部粘贴**：单击选中下方第一列第一个单元格，按 `Ctrl+V`。")
    edited_df = st.data_editor(
        df, 
        num_rows="dynamic", 
        use_container_width=True, 
        hide_index=True
    )

with col2:
    st.subheader("📊 实时分析图表")
    
    # 清洗数据
    clean_df = edited_df.apply(pd.to_numeric, errors='coerce').dropna()

    current_angles = clean_df["测量角度 (°)"].tolist()
    current_values = clean_df["实测数据 (mm)"].tolist()
    
    if len(current_angles) > 0:
        fig = create_radar(report_title, current_angles, current_values, target_val, upper_limit, lower_limit, interval, show_flats, show_pins)
        
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        
        st.pyplot(fig, clear_figure=True)
        plt.close(fig) # 🌟 释放内存，防止长时间使用导致崩溃 🌟
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.download_button(
            label="⬇️ 一键下载高清分析图 (PNG)",
            data=buf,
            file_name=f"{report_title.replace(' ', '_')}_Analysis.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.info("👈 请在左侧输入测量数据，图表将自动生成。")
