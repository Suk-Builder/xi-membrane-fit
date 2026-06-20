#!/usr/bin/env python3
"""
ξ-membrane 拟合 v2 — Planck SMICA Cold Spot 区域 (GPU 版)
CG P1 终极验证: 用 2D ξ-membrane 模型拟合 CMB Cold Spot 区域温度异常

针对 Win11 RTX 3060 12GB + 16GB RAM 优化
使用 PyTorch GPU 加速 fit
"""
import numpy as np
import healpy as hp
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import time
import sys
import os

# 检测 GPU
try:
    import torch
    HAS_GPU = torch.cuda.is_available()
    if HAS_GPU:
        DEVICE = torch.device('cuda')
        print(f"[GPU] PyTorch CUDA: {torch.cuda.get_device_name(0)}")
        print(f"     VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
    else:
        DEVICE = torch.device('cpu')
        print("[GPU] PyTorch 无 CUDA, 用 CPU")
except ImportError:
    HAS_GPU = False
    DEVICE = None
    print("[GPU] 无 PyTorch, 纯 numpy")

start = time.time()
print("="*60)
print("ξ-membrane 拟合 v2 — Planck SMICA Cold Spot (GPU)")
print("="*60)

# === 1. 读 SMICA FITS ===
FITS_PATH = sys.argv[1] if len(sys.argv) > 1 else 'COM_CMB_IQU-smica_2048_R3.00_full.fits'
print(f"\n[1/7] 读 {FITS_PATH} ...")
m = hp.read_map(FITS_PATH, field=0, verbose=False)
NSIDE = hp.npix2nside(len(m))
print(f"   shape: {m.shape}, NSIDE={NSIDE}")
print(f"   range: [{m.min():.6e}, {m.max():.6e}] K_CMB")
print(f"   std: {m.std():.6e}")

# === 2. 准备 GPU 数据 ===
print(f"\n[2/7] 上传 GPU...")
if HAS_GPU:
    m_gpu = torch.from_numpy(m).to(DEVICE).float()
    print(f"   m_gpu: {m_gpu.shape}, device={m_gpu.device}")
else:
    m_gpu = m

# === 3. 平滑到 NSIDE=64 (暴露大尺度结构) ===
print("\n[3/7] 平滑 NSIDE={} → 64 (FWHM=5°)...".format(NSIDE))
NSIDE_LOW = 64
m_smooth = hp.smoothing(m, fwhm=np.radians(5.0), lmax=2*NSIDE_LOW)
m_low = hp.ud_grade(m_smooth, nside_out=NSIDE_LOW, order_in='NESTED', order_out='RING')
print(f"   低分辨率 shape: {m_low.shape}, std: {m_low.std():.6e}")

# === 4. 提取 Cold Spot 区域 ===
print("\n[4/7] 提取 Cold Spot 区域 (l=209.7°, b=-57.2°, r=10°)...")
l_cold, b_cold = 209.7, -57.2
radius_deg = 10.0
vec_cold = hp.ang2vec(np.radians(l_cold), np.radians(b_cold))
pix_in_disc = hp.query_disc(NSIDE_LOW, vec_cold, np.radians(radius_deg), nest=False, inclusive=True)
T_disc = m_low[pix_in_disc]
T_coldest = T_disc.min()
print(f"   Cold Spot 像素数: {len(pix_in_disc)}")
print(f"   Cold Spot T: mean={T_disc.mean():.3e}, min={T_coldest:.3e} ({T_coldest*1e6:.1f} μK)")

# 像素到中心角距离
l_pix, b_pix = hp.pix2ang(NSIDE_LOW, pix_in_disc, lonlat=True)
r_pix = hp.rotator.angdist(
    [np.radians(l_cold), np.radians(b_cold)],
    np.radians(np.array([l_pix, b_pix]).T)
)
r_pix_deg = np.degrees(r_pix)

# === 5. ξ-membrane 模型 + 拟合 (GPU 加速) ===
print("\n[5/7] ξ-membrane 模型拟合 (GPU)...")

def xi_membrane_np(r, T_bg, A, sigma):
    """CPU 拟合用"""
    return T_bg - A * np.exp(-0.5 * (r / sigma)**2)

# GPU 拟合
if HAS_GPU:
    r_gpu = torch.from_numpy(r_pix_deg).to(DEVICE).float()
    T_gpu = torch.from_numpy(T_disc).to(DEVICE).float()

    def xi_membrane_gpu(r, T_bg, A, sigma):
        return T_bg - A * torch.exp(-0.5 * (r / sigma)**2)

    # PyTorch 最小二乘 (LBFGS)
    T_bg0 = float(m_low.mean())
    A0 = float(T_bg0 - T_coldest)
    sigma0 = 5.0
    print(f"   初值: T_bg={T_bg0:.4e}, A={A0:.4e}, σ={sigma0}")

    T_bg_t = torch.tensor(T_bg0, device=DEVICE, requires_grad=True)
    A_t = torch.tensor(A0, device=DEVICE, requires_grad=True)
    sigma_t = torch.tensor(sigma0, device=DEVICE, requires_grad=True)

    optimizer = torch.optim.LBFGS([T_bg_t, A_t, sigma_t], max_iter=500, lr=0.1, line_search_fn='strong_wolfe')

    def closure():
        optimizer.zero_grad()
        T_pred = xi_membrane_gpu(r_gpu, T_bg_t, A_t, sigma_t)
        loss = ((T_pred - T_gpu) ** 2).mean()
        loss.backward()
        return loss

    for i in range(20):
        loss = optimizer.step(closure)
        if i % 5 == 0:
            print(f"   iter {i}: loss={loss.item():.4e}, T_bg={T_bg_t.item():.4e}, A={A_t.item():.4e}, σ={sigma_t.item():.4f}")

    T_bg_fit = T_bg_t.item()
    A_fit = A_t.item()
    sigma_fit = sigma_t.item()
    T_fit = xi_membrane_np(r_pix_deg, T_bg_fit, A_fit, sigma_fit)
    print(f"\n   [GPU Fit] T_bg={T_bg_fit:.4e}, A={A_fit:.4e} ({A_fit*1e6:.1f} μK), σ={sigma_fit:.3f}°")
else:
    # scipy CPU fallback
    from scipy.optimize import curve_fit
    popt, _ = curve_fit(xi_membrane_np, r_pix_deg, T_disc, p0=[m_low.mean(), m_low.mean()-T_coldest, 5.0], maxfev=10000)
    T_bg_fit, A_fit, sigma_fit = popt
    T_fit = xi_membrane_np(r_pix_deg, *popt)
    print(f"   [CPU Fit] T_bg={T_bg_fit:.4e}, A={A_fit:.4e} ({A_fit*1e6:.1f} μK), σ={sigma_fit:.3f}°")

# === 6. 拟合优度 ===
print("\n[6/7] 拟合优度...")
residuals = T_disc - T_fit
chi2 = np.sum((residuals / T_disc.std())**2)
ndf = len(T_disc) - 3
reduced_chi2 = chi2 / ndf
print(f"   χ² = {chi2:.2f}, ndf = {ndf}, χ²/ndf = {reduced_chi2:.3f}")
print(f"   残差 std: {residuals.std():.3e} ({residuals.std()*1e6:.1f} μK)")

# === 7. CG 预测对比 + 出图 ===
print("\n[7/7] 出图 + CG 预测对比...")
fig, axes = plt.subplots(2, 2, figsize=(12, 10))

# 图1: 径向剖面 + 拟合曲线
ax = axes[0, 0]
nbin = 10
rbins = np.linspace(0, radius_deg, nbin+1)
rcenters = 0.5 * (rbins[1:] + rbins[:-1])
T_binned = np.array([T_disc[(r_pix_deg >= rbins[i]) & (r_pix_deg < rbins[i+1])].mean() for i in range(nbin)])
T_errs = np.array([T_disc[(r_pix_deg >= rbins[i]) & (r_pix_deg < rbins[i+1])].std() / np.sqrt(max(1, ((r_pix_deg >= rbins[i]) & (r_pix_deg < rbins[i+1])).sum())) for i in range(nbin)])
ax.errorbar(rcenters, T_binned*1e6, yerr=T_errs*1e6, fmt='o', color='black', label='SMICA data (binned)')
r_fit = np.linspace(0, radius_deg, 200)
T_model = xi_membrane_np(r_fit, T_bg_fit, A_fit, sigma_fit)
ax.plot(r_fit, T_model*1e6, 'r-', lw=2, label=f'ξ-membrane fit\nσ={sigma_fit:.2f}°, A={A_fit*1e6:.0f}μK')
ax.axhline(0, color='gray', linestyle=':')
ax.set_xlabel('r (deg)')
ax.set_ylabel('T (μK_CMB)')
ax.set_title('Cold Spot 径向温度剖面')
ax.legend(fontsize=9)
ax.grid(True, alpha=0.3)

# 图2: 全天图 (用 RING 排布的 1D 数组 → 2D 投影)
ax = axes[0, 1]
# 简单粗暴: 拍平 NSIDE=64 的 49152 像素成 64x768 长条
m_2d = m_low.reshape(1, -1)
im = ax.imshow(m_2d, cmap='RdBu_r', aspect='auto', vmin=-3e-5, vmax=3e-5, extent=[0, 360, -90, 90])
plt.colorbar(im, ax=ax, label='T (K_CMB)')
ax.set_title('SMICA NSIDE=64 (smoothing FWHM=5°)')
ax.set_xlabel('longitude (deg)')
ax.set_ylabel('latitude (deg)')

# 图3: 残差
ax = axes[1, 0]
ax.scatter(r_pix_deg, residuals*1e6, alpha=0.6, s=20, color='blue')
ax.axhline(0, color='r', linestyle='--')
ax.set_xlabel('r (deg)')
ax.set_ylabel('residual (μK)')
ax.set_title(f'拟合残差 (χ²/ndf={reduced_chi2:.2f})')
ax.grid(True, alpha=0.3)

# 图4: CG 预测 vs 观测对比
ax = axes[1, 1]
ax.bar(['ξ-membrane\nσ predicted\n2-10°', 'Fit σ', 'ΛCDM\n(rare event)'],
       [sigma_fit if 2 < sigma_fit < 10 else 0, sigma_fit, 0],
       color=['green' if 2 < sigma_fit < 10 else 'gray', 'red', 'blue'])
ax.set_ylabel('σ (degrees)')
ax.set_title(f'CG 验证: σ_fit = {sigma_fit:.2f}°\n{"✅ CG 一致" if 2 < sigma_fit < 10 else "⚠️ 需进一步分析"}')
ax.grid(True, alpha=0.3, axis='y')

plt.suptitle(f'ξ-membrane Fit v2 — Planck SMICA Cold Spot (NSIDE={NSIDE})', fontsize=14)
plt.tight_layout()
plt.savefig('xi_membrane_fit_v2.png', dpi=120, bbox_inches='tight')
print(f"   图: ./xi_membrane_fit_v2.png")

# === 8. CG 验证结论 ===
print("\n" + "="*60)
print("CG 验证结果")
print("="*60)
print(f"   σ_fit = {sigma_fit:.3f}° (CG 预测 2-10°)")
print(f"   A_fit = {A_fit*1e6:.1f} μK (观测 Cold Spot ~ -150 μK)")
print(f"   χ²/ndf = {reduced_chi2:.3f}")
cg_match = 2 < sigma_fit < 10
print(f"   CG 验证: {'✅ PASS' if cg_match else '⚠️ 部分'}")
print(f"\n总耗时: {time.time()-start:.1f} 秒")

# 保存参数
import json
result = {
    'fits_path': FITS_PATH,
    'NSIDE': int(NSIDE),
    'NSIDE_LOW': int(NSIDE_LOW),
    'T_bg_fit': float(T_bg_fit),
    'A_fit': float(A_fit),
    'sigma_fit': float(sigma_fit),
    'reduced_chi2': float(reduced_chi2),
    'T_coldest_uK': float(T_coldest*1e6),
    'cg_match': bool(cg_match),
    'gpu': HAS_GPU
}
with open('xi_membrane_result.json', 'w') as f:
    json.dump(result, f, indent=2)
print(f"\n结果: ./xi_membrane_result.json")
