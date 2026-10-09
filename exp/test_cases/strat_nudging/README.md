# Stratospheric Nudging and Free-Running MiMA Test Cases

This directory contains reference test cases for the Model of an idealized Moist Atmosphere (MiMA) in Isca, featuring realistic gravity wave drag (orographic and non-orographic), CMIP5 ozone radiative forcing, realistic boundary conditions, and wavenumber-selective stratospheric zonal wind nudging.

---

## 1. Test Cases Overview

| Test Case Script | Purpose | Key Distinguishing Features |
| :--- | :--- | :--- |
| **`strat_free_test_case.py`** | Free-running control simulation | MiMA with Ning & MG gravity wave drag, enhanced extratropical launch flux ($B_{t,\mathrm{nh}} = 0.0010\text{ Pa}$), CMIP5 seasonal ozone, realistic topography, and land-sea contrast. No relaxation. |
| **`strat_nudging_test_case.py`** | Stratospheric wind nudged simulation | Identical physical configuration to the free run, with stratospheric zonal wind ($u$) relaxed towards an external NetCDF target profile (`u_target_yr23.nc`) above $90\text{ hPa}$ using real-to-complex Fourier wavenumber filtering. Defaults to zonal-mean nudging ($s=0$). |

Both test cases are configured at **T42 spectral horizontal resolution** with **40 uneven vertical sigma levels** extending from the surface up to $\sim 0.01\text{ hPa}$.

---

## 2. Important Stratospheric Physics Configuration

The model configuration incorporates key physical parameterizations developed to achieve a realistic stratospheric climate and resolve the cold polar night jet bias:

### 2.1 Vertical Resolution (`spectral_dynamics_nml`)
* **`num_levels = 40`**, **`vert_coord_option = 'uneven_sigma'`**:
  * 40 vertical sigma levels with high resolution in the upper troposphere and stratosphere.
  * Model top is at $\sigma \approx 10^{-5}$ ($\sim 0.01\text{ hPa}$ / $\sim 80\text{ km}$), fully resolving the troposphere, stratosphere, and lower mesosphere.
  * `surf_res = 0.1`, `scale_heights = 7.9`, `exponent = 1.4`.

### 2.2 Orographic Gravity Wave Drag (`mg_drag_nml`)
* **Pierrehumbert & Stern (1987) mountain drag scheme**:
  * Driven by realistic subgrid-scale mountain height standard deviation (`sgsmtn`, stored in `input/mg_drag.res.nc`), derived from high-resolution topography datasets (ERA5 / Navy).
  * Key parameters: `do_block = True` (low-level mountain blocking), `do_wave = True` (vertically propagating mountain waves), `crit_frac = 0.375`, `block_fac = 0.5`, `gflux_fac = 0.125`.

### 2.3 Non-Orographic Gravity Wave Drag (`cg_drag_nml`)
* **Alexander & Dunkerton (1999) convective wave drag scheme**:
  * Enhanced extratropical momentum flux launch in the Northern Hemisphere:
    * **`Bt_nh = 0.0010 Pa`**, launched across **`phi0n = 25.0° N`** with half-width **`dphin = 10.0°`**.
    * This enhanced extratropical wave drag exerts critical wave breaking and momentum deposition in the winter stratosphere ($50\text{--}10\text{ hPa}$), decelerating the polar night jet and mitigating the strong westerly cold-pole bias commonly found in idealized GCMs.
  * Equatorial launch (**`Bt_eq = 0.0043 Pa`**) drives a realistic quasi-biennial oscillation (QBO) in equatorial stratospheric zonal winds.
  * Wave launch spectrum: `cw = 35.0 m/s`, `Bw = 0.4`, launch level $p = 315\text{ hPa}$.

### 2.4 Ozone Radiation Coupling (`rrtm_radiation_nml`)
* **`do_read_ozone = True`**, **`ozone_file = 'ozone_1990_cmip5'`**:
  * Reads monthly-varying, zonally symmetric CMIP5 ozone volume mixing ratios (`input/ozone_1990_cmip5.nc`).
  * Captures the seasonal cycle of stratospheric radiative heating, producing a realistic stratopause temperature inversion and summer-to-winter meridional temperature gradients.

---

## 3. Stratospheric Nudging Namelist Reference

Stratospheric nudging is configured in `spectral_dynamics_nml` within the model namelist:

```fortran
&spectral_dynamics_nml
  do_strat_nudging         = .true.,              ! Master switch to enable stratospheric nudging
  nudge_u_from_file        = .true.,              ! Read target profile from NetCDF (.true.) or use constant (.false.)
  nudge_u_file             = 'INPUT/u_target_yr23.nc', ! Path to NetCDF target file
  nudge_u_varname          = 'ucomp',             ! Variable name in NetCDF file
  nudge_u_time_offset_days = 0.0,                 ! Time offset in days between model and file calendars
  nudging_tau              = 21600.0,             ! Relaxation timescale in seconds (21600 s = 6 hours)
  nudging_p_bottom         = 90.0e2,              ! Lower transition boundary in Pa (90 hPa)
  nudging_p_top            = 50.0e2,              ! Full strength boundary in Pa (50 hPa)
  nudge_wave_min           = 0,                   ! Minimum zonal wavenumber to nudge
  nudge_wave_max           = 0,                   ! Maximum zonal wavenumber to nudge (-1 disables filtering)
  nudge_wave_list          = -1,                  ! Optional explicit array of wavenumbers to nudge
/
```

### Parameter Details:

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `do_strat_nudging` | `logical` | `.false.` | Enables stratospheric relaxation towards target $u$. |
| `nudge_u_from_file` | `logical` | `.false.` | When `.true.`, reads time-dependent 3D target wind from NetCDF. When `.false.`, nudges toward spatially uniform scalar `nudging_u_val`. |
| `nudge_u_file` | `character` | `''` | Relative path to target NetCDF file inside the run directory (e.g., `'INPUT/u_target_yr23.nc'`). |
| `nudge_u_varname` | `character` | `'ucomp'` | Variable name for zonal wind inside the NetCDF file. |
| `nudge_u_time_offset_days` | `real` | `0.0` | Calendar offset added to model time when reading target records. |
| `nudging_tau` | `real` | `21600.0` | Newtonian relaxation timescale $\tau$ in seconds ($21600\text{ s} = 6\text{ h}$, $86400\text{ s} = 24\text{ h}$). |
| `nudging_p_bottom` | `real` | `9000.0` | Lower pressure limit ($90\text{ hPa}$) below which nudging tendency is identically zero. |
| `nudging_p_top` | `real` | `5000.0` | Pressure level ($50\text{ hPa}$) above which nudging reaches $100\%$ full strength ($1/\tau$). |
| `nudge_wave_min` | `integer` | `0` | Smallest zonal wavenumber to retain in the nudging tendency. |
| `nudge_wave_max` | `integer` | `-1` | Largest zonal wavenumber to retain. When `nudge_wave_max < 0`, wavenumber filtering is disabled and all gridpoints are relaxed. |
| `nudge_wave_list` | `integer(50)` | `-1` | Explicit integer array specifying arbitrary wavenumbers to nudge (overrides min/max range when `nudge_wave_list(1) >= 0`). |

---

## 4. Wavenumber Nudging Modes

By adjusting `nudge_wave_min`, `nudge_wave_max`, and `nudge_wave_list`, users can select between four primary nudging paradigms:

### Mode 1: Zonal-Mean Nudging ($s=0$) — *Default in `strat_nudging_test_case.py`*
```python
'nudge_wave_min': 0,
'nudge_wave_max': 0,
```
* **Physics:** Relaxes only the zonal-mean wind $[u](\phi, p, t)$ towards the target profile. Non-zonal eddy departures ($u'$, $s \ge 1$) remain completely unconstrained and evolve dynamically.
* **Use case:** Benchmarking SNAPSI zonal-mean nudging protocols, studying wave-mean flow interactions and eddy feedbacks to imposed mean-state changes.

### Mode 2: Zonal-Mean + Planetary Waves 1 and 2 ($s \in [0, 2]$)
```python
'nudge_wave_min': 0,
'nudge_wave_max': 2,
```
* **Physics:** Relaxes $[u]$ and the longest planetary wave components (Wave 1 and Wave 2).
* **Use case:** Constraining large-scale planetary wave pulses and triggering vortex-split SSWs while allowing synoptic-scale eddies ($s \ge 3$) to evolve freely.

### Mode 3: Full-Field Gridpoint Nudging (All Wavenumbers)
```python
'nudge_wave_min': 0,
'nudge_wave_max': -1,
```
* **Physics:** Disables Fourier filtering and applies relaxation to the full 3D wind field $u(\lambda, \phi, p, t)$ at all gridpoints above $90\text{ hPa}$.
* **Use case:** Full reanalysis-driven nudging and deterministic forecast verification.

### Mode 4: Custom Non-Contiguous Wavenumbers
```python
'nudge_wave_list': [0, 2],  # e.g. Zonal mean and Wave 2 only
```
* **Physics:** Selectively nudges only the listed wavenumbers.

---

## 5. Fortran Implementation Details (`spectral_dynamics.F90`)

The stratospheric nudging framework is implemented in `src/atmos_spectral/model/spectral_dynamics.F90`:

### 5.1 Initialization (`strat_nudging_init`)
1. Evaluates namelist flags and determines whether Fourier filtering is active:
   ```fortran
   do_nudge_wave_filter = (nudge_wave_list(1) >= 0 .or. nudge_wave_min > 0 .or. nudge_wave_max >= 0)
   ```
2. If filtering is active, allocates work arrays:
   * `nudge_diff_u(is:ie, js:je, num_levels)`: local physical difference array.
   * `nudge_fourier_diff(0:lon_max/2, js:je, num_levels)`: complex Fourier coefficient buffer.
3. If `nudge_u_from_file = .true.`:
   * Reads the NetCDF coordinate dimensions (`lon`, `lat`, `pfull`, `time`) and verifies that spatial dimensions match the model grid.
   * Reads the time coordinate array (`nudge_u_times`).
   * Allocates local domain buffers (`u_target_m`, `u_target_p`) for holding the bounding time records.

### 5.2 Tendency Computation (`strat_nudging`)

During each dynamical timestep, before horizontal advection and spectral transforms:

#### 1. Temporal Interpolation
Model time is converted to days since origin ($t_\mathrm{eff} = \mathrm{dy} + \mathrm{sec}/86400.0 + \Delta t_\mathrm{offset}$). Bounding records $k_1, k_2$ are located and linearly interpolated:

$$
u_\mathrm{target}(t) = (1 - \alpha) u_\mathrm{target}(k_1) + \alpha u_\mathrm{target}(k_2), \quad \alpha = \frac{t_\mathrm{eff} - t_1}{t_2 - t_1}
$$

Records are cached in memory and reloaded only when the simulation steps into a new target interval.

#### 2. Wavenumber Filtering via Real-to-Complex FFT
The model computes the raw wind difference $\Delta u(\lambda, \phi, p) = u_\mathrm{model} - u_\mathrm{target}$ and executes a 1D real-to-complex FFT (`rfftf`) along each latitude circle $\phi_j$:

$$
\hat{U}(s, \phi_j, p) = \mathcal{F}\{\Delta u(\lambda, \phi_j, p)\}, \quad s = 0, 1, \dots, N_\mathrm{lon}/2
$$

Any complex Fourier coefficient $\hat{U}(s)$ outside the target wavenumber set is zeroed out:

$$
\hat{U}_\mathrm{filtered}(s) = \begin{cases}
\hat{U}(s) & \text{if } s \in [s_\mathrm{min}, s_\mathrm{max}] \text{ or } s \in \text{nudge\_wave\_list} \\
0 & \text{otherwise}
\end{cases}
$$

The inverse FFT (`rfftb`) then reconstructs the filtered physical wind difference $\Delta u_\mathrm{filtered}(\lambda, \phi, p)$.

#### 3. Vertical Hermite Transition Ramp
To prevent spurious wave reflection and Gibbs oscillations at the lower nudging boundary, the relaxation weight $w(p)$ follows a smooth cubic Hermite polynomial:

$$
w(p) = \begin{cases}
0 & p > p_\mathrm{bottom} \quad (p > 90\text{ hPa}) \\
3x^2 - 2x^3 & p_\mathrm{top} \le p \le p_\mathrm{bottom}, \quad x = \frac{p_\mathrm{bottom} - p}{p_\mathrm{bottom} - p_\mathrm{top}} \\
1 & p < p_\mathrm{top} \quad (p < 50\text{ hPa})
\end{cases}
$$

#### 4. Tendency Application & Diagnostics
The nudging tendency is applied directly to the physical zonal wind tendency:

$$
\left(\frac{\partial u}{\partial t}\right)_\mathrm{total} = \left(\frac{\partial u}{\partial t}\right)_\mathrm{dynamics} - \frac{w(p)}{\tau} \Delta u_\mathrm{filtered}
$$

The actual applied acceleration is cached in `nudging_u_dt` and exported to the diagnostic table as field `'udt_nudge'` in $\mathrm{m\ s^{-2}}$.

---

## 6. Running the Test Cases

Both scripts support command-line arguments for quick testing or full integrations:

```bash
# 1. Run free-running test case (default: 1 month, 16 cores)
python strat_free_test_case.py

# 2. Run short 2-day verification run of the free test case:
python strat_free_test_case.py --days 2 --cores 16

# 3. Run stratospheric nudging test case (default: 1 month, 16 cores):
python strat_nudging_test_case.py

# 4. Run short 2-day verification run of the nudging test case:
python strat_nudging_test_case.py --days 2 --cores 16
```

### Outputs:
* Raw model output: `isca_data/<exp_name>/run0001/atmos_monthly.nc` and `atmos_daily.nc`.
* Pressure-level interpolated output (via `isca.util.interpolate_output`):
  `isca_data/<exp_name>/run0001/plev_atmos_monthly.nc` and `plev_atmos_daily.nc` interpolated onto 25 standard pressure levels ($1000\text{ hPa}$ to $0.1\text{ hPa}$).
