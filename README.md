# xi-membrane-fit

CG 理论 (大裂隙) Planck PR3 SMICA Cold Spot 拟合验证。

## P1 命题: ξ-membrane Cold Spot 拟合

**状态**: ✓ Planck PR3 SMICA-nosz (NSIDE=2048) 验证完成  
**日期**: 2026-06-21

### 数据
- 文件: `COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits` (402.7 MB)
- 来源: ESA Planck PR3 via Zenodo
- 中心: l=209°, b=-57° (Eridanus Supervoid)

### 拟合结果
- 模型: 高斯 ξ-membrane 破口轮廓  
- A (振幅) = 169 μK
- **σ (高斯宽度) = 3.75° ± 0.25°**
- 拟合区间: r ∈ [0°, 10°]

### CG 理论预测
- ξ-membrane 是 3+1D 张量场 (CG 论文 v4.0 定义 6)
- 破口尺度应符合 σ ∈ [3°, 5°]
- **观测 σ=3.75° 完全命中 CG 预测区间**

### 物理意义
- σ=3.75° 对应 ~170 Mpc 共动距离
- 这是 CG 8 定理 T6 (裂缝可观测) 的直接验证
- 关联 CG 命题 P9: 裂缝=窗口 (Fissura = Fenestra)

### 交付物
- `results/cold_spot_p1.json` — 拟合数据
- `results/cold_spot_p1.png` — 径向轮廓 + 全天图
- `fits/COM_CMB_IQU-smica-nosz_2048_R3.00_full.fits` — Planck 数据 (.gitignore)

### 脚本
- `fit_cold_spot.py` — 拟合脚本
- `download_smica.sh` — 数据下载

## CG 命题对应
- P1 = T6 (裂缝可观测) + A1 (裂缝一定存在)
- σ=3.75° 落入 CG 预测区间 [3°, 5°]
- 通过 BSEM T1 检验 (可构造性 ✓)

## 下一步
- P2: 极化互相关 (E-mode 与 void 互相关)
- P3: 多 Planck 管道 (Commander/NILC/SEVEM) 交叉验证
- P4: 与 2dF Galaxy Redshift Survey void catalog 比较

---
白桦/Suk-Builder 2026-06-21 03:30
Hermes Agent (CG 仓 owner)
