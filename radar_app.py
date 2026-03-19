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
    
    interval = st.number_input("单点代表角度 (度/点)", value=30, step=1, help="用于计算不良面积占比，以及判断图表连线是否需要在无数据区断开")

    st.markdown("---")
    st.header("🎨 特征区域遮罩")
    show_flats = st.checkbox("显示平面区域 (上下灰色)", value=True)
    show_pins = st.checkbox("显示顶针区域 (左右黄色)", value=True)
    
    st.markdown("---")
    st.write("💡 **使用提示**：")
    st.write("您可以直接点击表格末尾添加新行，或者从 Excel 复制完整的两列数据直接粘贴进右侧表格。")

# 核心绘图函数（已修复阴影区边界问题）
def create_radar(title, angles, values, target, upper, lower, interval, show_flats, show_pins):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

    # 🌟 核心修复：提前计算好动态图表的内外圈边界
    margin = (upper - lower) * 1.5
    r_min = lower - margin
    r_max = upper + margin

    # 1. 计算不良率
    oot_count = sum(1 for v in values if v < lower or v > upper)
    oot_area = oot_count * interval
    oot_percentage = (oot_area / 360.0) * 100

    # 2. 绘制基准线
    theta_full = np.linspace(0, 2*np.pi, 300)
    ax.plot(theta_full, np.full_like(theta_full, target), color='green', linewidth=2, label=f'Target ({target})')
    ax.plot(theta_full, np.full_like(theta_full, upper), color='red', linestyle='--', linewidth=1.5, label=f'Tolerance ({lower}-{upper})')
    ax.plot(theta_full, np.full_like(theta_full, lower), color='red', linestyle='--', linewidth=1.5)
    ax.fill_between(theta_full, lower, upper, color='green', alpha=0.1)

    # 3. 绘制区域 (使用精准的 r_min 和 r_max，确保阴影不会被隐藏)
    if show_flats:
        ax.fill_between(np.linspace(np.deg2rad(340), np.deg2rad(360+20), 50), r_min, r_max, color='gray', alpha=0.25, label='Flat Area')
        ax.fill_between(np.linspace(np.deg2rad(160), np.deg2rad(200), 50), r_min, r_max, color='gray', alpha=0.25)

    if show_pins:
        ax.fill_between(np.linspace(np.deg2rad(70), np.deg2rad(110), 50), r_min, r_max, color='gold', alpha=0.35, label='Pin Area')
        ax.fill_between(np.linspace(np.deg2rad(250), np.deg2rad(290), 50), r_min, r_max, color='gold', alpha=0.35)

    # 5. 绘制实际测量连线（带断点逻辑）
    a_plot, v_plot = [], []
    for i in range(len(angles)):
        a_plot.append(angles[i])
        v_plot.append(values[i])
        if i < len(angles) - 1 and (angles[i+1] - angles[i] > interval + 2):
            a_plot.append(angles[i] + 1)
            v_plot.append(np.nan)

    if len(angles) > 0 and (360 - angles[-1] + angles[0]) > interval + 2:
         a_plot.append(angles[-1] + 1)
         v_plot.append(np.nan)

    ax.plot(np.deg2rad(a_plot), v_plot, color='royalblue', linewidth=2.5, marker='o', markersize=6, label='Measured Data')

    # 6. 高亮超差数据并添加数值标签
    oot_points = [(a, v) for a, v in zip(angles, values) if v < lower or v > upper]
    if oot_points:
        ax.scatter([np.deg2rad(p[0]) for p in oot_points], [p[1] for p in oot_points], color='crimson', s=120, zorder=6, label='Out of Tolerance')

    for a, v in zip(angles, values):
        color = 'crimson' if (v < lower or v > upper) else 'darkblue'
        offset = (upper - lower) * 0.15 if v >= target else -(upper - lower) * 0.25
        ax.text(np.deg2rad(a), v + offset, f"{v:.2f}", ha='center', va='center', fontsize=11, color=color, fontweight='bold')

    # 7. 格式化：使用预先计算好的 r_min 和 r_max 限定视图
    ax.set_ylim(r_min, r_max)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    
    tick_step = int(interval) if interval >= 10 else 20
    ax.set_xticks(np.deg2rad(np.arange(0, 360, tick_step)))
    ax.set_xticklabels([f"{x}°" for x in np.arange(0, 360, tick_step)], fontsize=10)

    # 8. 信息框
    defect_text = f"OOT Points: {oot_count}\nOOT Area: {oot_area}°\nDefect Ratio: {oot_area}/360 = {oot_percentage:.1f}%"
    plt.figtext(0.0, 1.02, defect_text, fontsize=13, color='darkred', bbox=dict(facecolor='mistyrose', alpha=0.9, edgecolor='red'), va='bottom', ha='left')

    # 9. 题头设置
    ax.set_title(title, va='bottom', fontsize=20, fontweight='bold', pad=40)
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=10)
    
    return fig

# ----------------- 主界面布局 -----------------
col1, col2 = st.columns([1, 2])

# 默认提供 7ZL 数据
default_angles = [30, 60, 120, 150, 210, 240, 300, 330]
default_values = [39.08, 39.15, 39.13, 39.21, 39.06, 39.15, 39.17, 39.21]

df = pd.DataFrame({
    "测量角度 (°)": default_angles,
    "实测数据 (mm)": default_values
})

with col1:
    st.subheader("📝 数据录入区")
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True, hide_index=True)

with col2:
    st.subheader("📊 实时分析图表")
    valid_df = edited_df.dropna()
    current_angles = valid_df["测量角度 (°)"].tolist()
    current_values = valid_df["实测数据 (mm)"].tolist()
    
    if len(current_angles) > 0:
        fig = create_radar(report_title, current_angles, current_values, target_val, upper_limit, lower_limit, interval, show_flats, show_pins)
        
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
        buf.seek(0)
        
        st.pyplot(fig, clear_figure=True)
        st.markdown("<br>", unsafe_allow_html=True)
        
        st.download_button(
            label="⬇️ 一键下载高清分析图 (PNG)",
            data=buf,
            file_name=f"{report_title.replace(' ', '_')}_Analysis.png",
            mime="image/png",
            use_container_width=True
        )
    else:
        st.info("👈 请在左侧表格中输入测量数据以生成图表。")
