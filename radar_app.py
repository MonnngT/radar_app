import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import io

# 页面配置
st.set_page_config(page_title="扇叶外径极坐标分析系统", layout="wide")
st.title("🎯 扇叶根部外径极坐标分析系统")

# 侧边栏：参数与型号选择
with st.sidebar:
    st.header("⚙️ 参数设置")
    blade_type = st.radio("选择扇叶型号", ["4Z 系列 (4ZL / 4ZR)", "7ZL 系列"])
    # 默认英文标题
    default_title = f"{blade_type[:2]} Outer Diameter"
    report_title = st.text_input("图表标题 (Title)", default_title)
    
    st.markdown("---")
    st.header("🎨 特征区域显示")
    # 新增：自由选择是否显示平面和顶针区域
    show_flats = st.checkbox("显示平面区域 (上下灰色)", value=True)
    # 默认 7ZL 勾选顶针，4Z 不勾选，但用户可以自由修改
    default_pins = True if blade_type == "7ZL 系列" else False
    show_pins = st.checkbox("显示顶针区域 (左右黄色)", value=default_pins)
    
    st.markdown("---")
    st.write("💡 **使用提示**：")
    st.write("在右侧表格中修改数据，或从 Excel 复制一列数据粘贴到 `实测外径 (mm)` 列，图表会实时刷新。")

# 核心绘图函数（加入了 show_flats 和 show_pins 参数）
def create_radar(title, angles, values, show_flats, show_pins, interval):
    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw={'projection': 'polar'})

    # 1. 计算不良率
    oot_count = sum(1 for v in values if v < 39.1 or v > 39.3)
    oot_area = oot_count * interval
    oot_percentage = (oot_area / 360.0) * 100

    # 2. 绘制基准线
    theta_full = np.linspace(0, 2*np.pi, 300)
    ax.plot(theta_full, np.full_like(theta_full, 39.2), color='green', linewidth=2, label='Target (39.2)')
    ax.plot(theta_full, np.full_like(theta_full, 39.3), color='red', linestyle='--', linewidth=1.5, label='Tolerance (39.1-39.3)')
    ax.plot(theta_full, np.full_like(theta_full, 39.1), color='red', linestyle='--', linewidth=1.5)
    ax.fill_between(theta_full, 39.1, 39.3, color='green', alpha=0.1)

    # 3. 根据开关绘制上下灰色区域 (Flat Area)
    if show_flats:
        ax.fill_between(np.linspace(np.deg2rad(340), np.deg2rad(360+20), 50), 38.6, 39.5, color='gray', alpha=0.25, label='Flat Area')
        ax.fill_between(np.linspace(np.deg2rad(160), np.deg2rad(200), 50), 38.6, 39.5, color='gray', alpha=0.25)

    # 4. 根据开关绘制左右黄色顶针区域 (Pin Area)
    if show_pins:
        ax.fill_between(np.linspace(np.deg2rad(70), np.deg2rad(110), 50), 38.6, 39.5, color='gold', alpha=0.35, label='Pin Area')
        ax.fill_between(np.linspace(np.deg2rad(250), np.deg2rad(290), 50), 38.6, 39.5, color='gold', alpha=0.35)

    # 5. 绘制实际测量连线（带断点逻辑）
    a_plot, v_plot = [], []
    for i in range(len(angles)):
        a_plot.append(angles[i])
        v_plot.append(values[i])
        if i < len(angles) - 1 and (angles[i+1] - angles[i] > interval + 2):
            a_plot.append(angles[i] + 1)
            v_plot.append(np.nan)

    if (360 - angles[-1] + angles[0]) > interval + 2:
         a_plot.append(angles[-1] + 1)
         v_plot.append(np.nan)

    ax.plot(np.deg2rad(a_plot), v_plot, color='royalblue', linewidth=2.5, marker='o', markersize=6, label='Measured Data')

    # 6. 高亮超差数据并添加数值标签
    oot_points = [(a, v) for a, v in zip(angles, values) if v < 39.1 or v > 39.3]
    if oot_points:
        ax.scatter([np.deg2rad(p[0]) for p in oot_points], [p[1] for p in oot_points], color='crimson', s=120, zorder=6, label='Out of Tolerance')

    for a, v in zip(angles, values):
        color = 'crimson' if (v < 39.1 or v > 39.3) else 'darkblue'
        offset = 0.04 if v >= 39.15 else -0.05
        ax.text(np.deg2rad(a), v + offset, f"{v:.2f}", ha='center', va='center', fontsize=11, color=color, fontweight='bold')

    # 7. 图表格式化
    ax.set_ylim(38.6, 39.5)
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_xticks(np.deg2rad(np.arange(0, 360, 30)))
    ax.set_xticklabels([f"{x}°" for x in np.arange(0, 360, 30)], fontsize=10)

    # 8. 不良率信息框
    defect_text = f"OOT Points: {oot_count}\nOOT Area: {oot_area}°\nDefect Ratio: {oot_area}/360 = {oot_percentage:.1f}%"
    plt.figtext(0.02, 0.98, defect_text, fontsize=13, color='darkred', bbox=dict(facecolor='mistyrose', alpha=0.9, edgecolor='red'), va='top', ha='left')

    # 9. 题头设置（pad=45 解决遮挡）
    ax.set_title(title, va='bottom', fontsize=20, fontweight='bold', pad=45)
    
    # 动态调整图例位置，防止重叠
    ax.legend(loc='upper right', bbox_to_anchor=(1.35, 1.15), fontsize=10)
    
    return fig

# ----------------- 主界面布局 -----------------
col1, col2 = st.columns([1, 2])

# 根据选择初始化默认数据
if blade_type == "4Z 系列 (4ZL / 4ZR)":
    default_angles = [20, 48, 76, 104, 132, 160, 200, 228, 256, 284, 312, 340]
    default_values = [39.25, 39.24, 39.20, 39.15, 39.13, 39.08, 38.74, 38.85, 38.93, 39.06, 39.16, 39.20]
    interval = 28
else:
    default_angles = [30, 60, 120, 150, 210, 240, 300, 330]
    default_values = [39.08, 39.15, 39.13, 39.21, 39.06, 39.15, 39.17, 39.21]
    interval = 30

df = pd.DataFrame({
    "测量角度 (°)": default_angles,
    "实测外径 (mm)": default_values
})

with col1:
    st.subheader("📝 数据录入区")
    edited_df = st.data_editor(df, num_rows="fixed", use_container_width=True, hide_index=True)

with col2:
    st.subheader("📊 实时分析图表")
    current_angles = edited_df["测量角度 (°)"].tolist()
    current_values = edited_df["实测外径 (mm)"].tolist()
    
    # 生成图表 (传入开关参数)
    fig = create_radar(report_title, current_angles, current_values, show_flats, show_pins, interval)
    
    # 保存到内存用于下载
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    
    # 在网页渲染
    st.pyplot(fig, clear_figure=True)
    st.markdown("<br>", unsafe_allow_html=True)
    
    # 导出下载按钮
    st.download_button(
        label="⬇️ 一键下载高清分析图 (PNG)",
        data=buf,
        file_name=f"{report_title.replace(' ', '_')}_Analysis.png",
        mime="image/png",
        use_container_width=True
    )
