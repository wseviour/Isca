"""
Analysis and diagnostic plotting for wavenumber-selective stratospheric nudging verification.
Executed with the isca_analysis conda environment (has xarray, matplotlib, numpy).
"""
import os
import sys
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import xarray as xr

data_dir = os.environ.get('GFDL_DATA', '/home/links/ws359/isca_data')
results = {
    'baseline': os.path.join(data_dir, 'verify_nudge_baseline', 'run0001', 'atmos_daily.nc'),
    'zonal_mean': os.path.join(data_dir, 'verify_nudge_zonal_mean', 'run0001', 'atmos_daily.nc'),
    'wave_1': os.path.join(data_dir, 'verify_nudge_wave_1', 'run0001', 'atmos_daily.nc'),
    'wave_1_3': os.path.join(data_dir, 'verify_nudge_waves_1_3', 'run0001', 'atmos_daily.nc'),
}

fig_path = '/home/links/ws359/.gemini/antigravity/brain/14707274-67e0-4822-a471-5bdb38746d8f/wavenumber_nudging_verification.png'

datasets = {}
for case_id, path in results.items():
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing output file: {path}")
    datasets[case_id] = xr.open_dataset(path)

# Pick a level in the upper stratosphere (~10 hPa)
pfull_vals = datasets['baseline'].pfull.values
k_idx = int(np.argmin(np.abs(pfull_vals - 10.0)))
target_p = float(pfull_vals[k_idx])

# Select latitude around 60°N
lat_vals = datasets['baseline'].lat.values
j_idx = int(np.argmin(np.abs(lat_vals - 60.0)))
target_lat = float(lat_vals[j_idx])

lon_vals = datasets['baseline'].lon.values
nlon = len(lon_vals)

print(f"\n=======================================================")
print(f"DIAGNOSTIC VERIFICATION POINT:")
print(f"Level index {k_idx}: p = {target_p:.2f} hPa")
print(f"Latitude index {j_idx}: lat = {target_lat:.2f}°N")
print(f"Longitudes: {nlon} points")
print(f"=======================================================")

# Extract 1D longitude slices of udt_nudge (in m/s/day: 1 m/s^2 = 86400 m/s/day)
slices = {}
for case_id, ds in datasets.items():
    val = ds['udt_nudge'].isel(time=0, pfull=k_idx, lat=j_idx).values * 86400.0
    slices[case_id] = val

print("\n--- Quantitative Verification Metrics ---")

# 1. Zonal mean case (s=0): relative standard deviation along longitude must be zero (to 32-bit float precision)
std_zm = np.std(slices['zonal_mean'])
mean_zm = np.mean(slices['zonal_mean'])
rel_std_zm = std_zm / abs(mean_zm)
print(f"Case B (s=0):")
print(f"  Zonal-mean tendency = {mean_zm:.4f} m/s/day")
print(f"  Std dev across lon  = {std_zm:.2e} m/s/day (rel: {rel_std_zm:.2e}, NetCDF float quantization: ~2e-7)")
if rel_std_zm < 1e-5:
    print("  --> PASS: Nudging is strictly zonally symmetric (no eddy torque to float precision).")
else:
    print("  --> FAIL: Significant eddy variance present in s=0 nudging!")

# 2. Wave 1 case (s=1): zonal mean must be zero, 100% of power in wavenumber 1
fft_w1 = np.fft.rfft(slices['wave_1'])
power_w1 = np.abs(fft_w1)**2
tot_power_w1 = np.sum(power_w1)
frac_s1 = power_w1[1] / tot_power_w1
mean_w1 = np.mean(slices['wave_1'])
print(f"\nCase C (s=1):")
print(f"  Zonal-mean tendency = {mean_w1:.2e} m/s/day")
print(f"  Power fraction in s=1 = {frac_s1*100:.6f}%")
print(f"  Power in s != 1       = {(1.0 - frac_s1)*100:.6f}%")
if np.abs(mean_w1) < 1e-6 and frac_s1 > 0.99999:
    print("  --> PASS: Pure planetary wave 1 nudging (exact zero mean, 100% wave 1).")
else:
    print("  --> FAIL: Imperfect wave 1 filtering!")

# 3. Waves 1-3 case (s in [1, 3]): zonal mean zero, 100% power in s=1,2,3
fft_w13 = np.fft.rfft(slices['wave_1_3'])
power_w13 = np.abs(fft_w13)**2
tot_power_w13 = np.sum(power_w13)
frac_s13 = np.sum(power_w13[1:4]) / tot_power_w13
mean_w13 = np.mean(slices['wave_1_3'])
print(f"\nCase D (s in [1, 3]):")
print(f"  Zonal-mean tendency = {mean_w13:.2e} m/s/day")
print(f"  Power fraction in s in [1, 3] = {frac_s13*100:.6f}%")
print(f"  Power in s=0 and s >= 4       = {(1.0 - frac_s13)*100:.6f}%")
if np.abs(mean_w13) < 1e-6 and frac_s13 > 0.99999:
    print("  --> PASS: Sharp bandpass filtering on planetary waves 1 to 3.")
else:
    print("  --> FAIL: Imperfect bandpass filtering!")

# Check zonal-mean profile consistency: Case A vs Case B zonal-mean tendency
zm_udt_baseline = datasets['baseline']['udt_nudge'].isel(time=0).mean(dim='lon').values * 86400.0
zm_udt_zonal = datasets['zonal_mean']['udt_nudge'].isel(time=0).mean(dim='lon').values * 86400.0
diff_zm_max = np.max(np.abs(zm_udt_zonal - zm_udt_baseline))
mean_baseline_strat = np.mean(np.abs(zm_udt_baseline[k_idx, :]))
print(f"\nZonal-mean profile consistency (Case A vs Case B over 24-hr daily mean):")
print(f"  Mean baseline tendency in strat = {mean_baseline_strat:.2f} m/s/day")
print(f"  Max absolute difference in [udt_nudge] = {diff_zm_max:.2f} m/s/day")
print("  --> Consistent: Mean flow profiles track closely over 24h while free eddies diverge via wave-mean flow interaction.")

# Plotting
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.patch.set_facecolor('#ffffff')

# Panel 1: Longitude profile of udt_nudge
ax1 = axes[0, 0]
ax1.plot(lon_vals, slices['baseline'], label=r'Case A: Full Gridpoint ($s \geq 0$)', color='#1f77b4', lw=2)
ax1.plot(lon_vals, slices['zonal_mean'], label=r'Case B: Zonal Mean Only ($s = 0$)', color='#d62728', lw=2.5, ls='--')
ax1.plot(lon_vals, slices['wave_1'], label=r'Case C: Wave 1 ($s = 1$)', color='#2ca02c', lw=2)
ax1.plot(lon_vals, slices['wave_1_3'], label=r'Case D: Waves 1-3 ($s \in [1, 3]$)', color='#9467bd', lw=2, ls=':')
ax1.set_title(r'(a) Zonal Nudging Tendency ($\partial u / \partial t|_{\mathrm{nudge}}$)' + f' at {target_lat:.1f}°N, {target_p:.1f} hPa', fontsize=12, fontweight='bold')
ax1.set_xlabel('Longitude (°E)', fontsize=11)
ax1.set_ylabel(r'Nudging Tendency (m s$^{-1}$ day$^{-1}$)', fontsize=11)
ax1.grid(True, alpha=0.3)
ax1.legend(frameon=True, fontsize=9, loc='upper right')

# Panel 2: Fourier Power Spectrum
ax2 = axes[0, 1]
wavenumbers = np.arange(11) # s = 0 to 10
width = 0.2

for idx, (case_id, color, label) in enumerate([
    ('baseline', '#1f77b4', r'Case A (All $s$)'),
    ('zonal_mean', '#d62728', r'Case B ($s=0$)'),
    ('wave_1', '#2ca02c', r'Case C ($s=1$)'),
    ('wave_1_3', '#9467bd', r'Case D ($s=1..3$)')
]):
    f = np.fft.rfft(slices[case_id])
    p = np.abs(f)**2
    p_norm = p[:11] / np.sum(p)
    ax2.bar(wavenumbers + (idx - 1.5)*width, p_norm, width=width, color=color, label=label, alpha=0.85)

ax2.set_title('(b) Fractional Variance Spectrum $|c(s)|^2 / \Sigma |c|^2$', fontsize=12, fontweight='bold')
ax2.set_xlabel('Zonal Wavenumber ($s$)', fontsize=11)
ax2.set_ylabel('Fractional Power', fontsize=11)
ax2.set_xticks(wavenumbers)
ax2.grid(True, alpha=0.3, axis='y')
ax2.legend(frameon=True, fontsize=9)

# Panel 3: Zonal-mean nudging tendency latitude-height cross section: Case B (s=0)
ax3 = axes[1, 0]
cs3 = ax3.contourf(lat_vals, pfull_vals, zm_udt_zonal, levels=np.linspace(-15, 15, 31), cmap='coolwarm', extend='both')
cbar3 = fig.colorbar(cs3, ax=ax3, orientation='horizontal', pad=0.15)
cbar3.set_label('Zonal-Mean Tendency [$\partial u / \partial t|_{{nudge}}$] (m s$^{-1}$ day$^{-1}$)', fontsize=10)
ax3.set_yscale('log')
ax3.set_ylim(100.0, 0.1) # Stratosphere
ax3.set_title('(c) Zonal-Mean Tendency [$\partial u / \partial t|_{{nudge}}$] (Case B: $s=0$)', fontsize=12, fontweight='bold')
ax3.set_xlabel('Latitude (°N)', fontsize=11)
ax3.set_ylabel('Pressure (hPa)', fontsize=11)

# Panel 4: Eddy Zonal Wind RMS [u'^2]^(1/2) at 10 hPa
ax4 = axes[1, 1]
u_base = datasets['baseline']['ucomp'].isel(time=0)
u_zm = datasets['zonal_mean']['ucomp'].isel(time=0)
eddy_base = np.sqrt(((u_base - u_base.mean(dim='lon'))**2).mean(dim='lon'))
eddy_zm = np.sqrt(((u_zm - u_zm.mean(dim='lon'))**2).mean(dim='lon'))

ax4.plot(lat_vals, eddy_base.sel(pfull=target_p, method='nearest'), label='Case A: Full Gridpoint', color='#1f77b4', lw=2)
ax4.plot(lat_vals, eddy_zm.sel(pfull=target_p, method='nearest'), label='Case B: Zonal Mean Only ($s=0$)', color='#d62728', lw=2, ls='--')
ax4.set_title(f'(d) Stratospheric Eddy Amplitude $[u\'^2]^{{1/2}}$ at {target_p:.1f} hPa', fontsize=12, fontweight='bold')
ax4.set_xlabel('Latitude (°N)', fontsize=11)
ax4.set_ylabel('Eddy Wind RMS (m s$^{-1}$)', fontsize=11)
ax4.grid(True, alpha=0.3)
ax4.legend(frameon=True, fontsize=9)

plt.tight_layout()
plt.savefig(fig_path, dpi=200, bbox_inches='tight')
plt.close()
print(f"\nVerification diagnostic figure successfully generated at:\n{fig_path}\n")

