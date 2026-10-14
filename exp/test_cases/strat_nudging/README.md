# Stratospheric Nudging and Free-Running MiMA Test Cases

This directory contains reference test cases for the Model of an idealized Moist Atmosphere (MiMA) in Isca, featuring realistic gravity wave drag (orographic and non-orographic), CMIP5 ozone radiative forcing, realistic boundary conditions, and wavenumber-selective stratospheric zonal wind nudging.

---

## 1. Test Cases Overview

| Test Case Script | Purpose | Key Distinguishing Features |
| :--- | :--- | :--- |
| **`strat_free_test_case.py`** | Free-running control simulation | MiMA with Ning & MG gravity wave drag, enhanced extratropical launch flux ($`B_{t,\mathrm{nh}} = 0.0010\text{ Pa}`$), CMIP5 seasonal ozone, realistic topography, and land-sea contrast. No relaxation. |
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
  * Key parameters: `gmax = 1.0`, `acoef = 1.0`, `low_lev_frac = 0.23`, `xl_mtn = 100000.0`, `source_of_sgsmtn = 'input'`, `do_conserve_energy = True`.

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

### 2.5 Prescribed Analytic Ocean Q-fluxes and Land-Sea Contrast (`qflux_nml` & `mixed_layer_nml`)

In the idealized slab ocean framework (`mixed_layer_nml`, Frierson et al., 2006), ocean dynamics are not computed prognostically. Without prescribed ocean heat transport, tropical SSTs become excessively warm, extratropical SSTs become too cold, and Northern Hemisphere stationary waves are severely underrepresented.

To produce a realistic mean climate, stationary wave field, and stratospheric polar vortex variability, the model prescribes analytic ocean heat flux convergences ($Q$-fluxes) via `src/atmos_param/qflux/qflux.f90` (`qflux_nml`) coupled to the slab mixed layer (`mixed_layer_nml`, with `do_qflux = True` and `do_warmpool = True`). This configuration follows the MiMA formulation developed across several foundational studies:

#### 1. Zonally Symmetric Meridional Heat Transport (Merlis et al., 2013; Merlis & Schneider, 2010)
Prescribes a smooth, zonally symmetric poleward ocean heat transport following Merlis et al. (2013, Part II, *J. Climate*):

$$
\mathcal{Q}_\mathrm{zonal}(\phi) = - Q_0 \left(1 - \frac{2\phi^2}{\phi_0^2}\right) \exp\left(-\frac{\phi^2}{\phi_0^2}\right) \frac{1}{\cos\phi}
$$

* **`qflux_amp = 26.0 W m^-2`** ($Q_0$): Peak amplitude of equatorial heat divergence and subtropical convergence.
* **`qflux_width = 16.0°`** ($\phi_0$): Latitudinal width parameter governing the meridional scale of tropical heat divergence.
* **Physics:** Diverts heat poleward from the deep tropics into the subtropics, preventing runaway equatorial warming and establishing realistic meridional SST gradients and Hadley circulation width.

#### 2. Zonally Asymmetric Stationary Wave Forcing (Jucker & Gerber, 2017; Garfinkel et al., 2020; Ning et al., 2026)
Planetary stationary waves in the Northern Hemisphere (particularly wavenumbers 1 and 2) are forced jointly by topography, land-sea thermal contrasts, and localized ocean heat sources. MiMA was first introduced with an idealized tropical warm pool by Jucker & Gerber (2017, *GMD*). Garfinkel et al. (2020, *JAMES*) and Ning et al. (2026, *WCD*) expanded this into a comprehensive 2D analytic $Q$-flux framework (`warmpool_localization_choice = 3`) that captures western boundary currents and localized SST dipoles:

* **Indo-Pacific Warm Pool & Cold Tongue:**
  * **`warmpool_amp = 18.0 W m^-2`**, **`warmpool_width = 35.0°`**, **`warmpool_phase = 140.0° E`**, **`warmpool_k = 1.66666`**:
  * Concentrates heat convergence in the Western Pacific warm pool region ($140^\circ\text{E}$), balanced by heat divergence in the eastern equatorial Pacific cold tongue.
* **Kuroshio Extension Current:**
  * **`kuroshio_amp = 40.0 W m^-2`**:
  * Represents localized ocean heat release by the warm Kuroshio Extension current in the northwest Pacific along $35^\circ\text{N}$, balanced by upstream and downstream cooling.
* **Gulf Stream & North Atlantic Drift:**
  * **`gulf_amp = 70.0 W m^-2`**, **`gulf_phase = 310.0° E`** ($50^\circ\text{W}$), **`gulf_k = 4`**:
  * Represents intense ocean heat convergence along the western boundary of the North Atlantic off North America and Newfoundland ($37^\circ\text{N}$), feeding the North Atlantic storm track.
* **Tropical Atlantic & Caribbean Dipoles:**
  * **`trop_atlantic_amp = 50.0 W m^-2`**:
  * Modulates heat convergence in the tropical Atlantic and Caribbean, compensating for continental boundaries.
* **Regional Modulations:**
  * **`hawaiiextra = 30.0 W m^-2`**: Modulates subtropical Pacific heat convergence and the South Pacific Convergence Zone (SPCZ).
  * `pac_itczextra = 0.0`, `north_sea_heat = 0.0`: Additional regional tuning hooks in `qflux_mod`.

#### 3. Mixed-Layer Thermal Properties (`mixed_layer_nml`)
* **`heat_capacity = 3.0e8 J m^-2 K^-1`**: Ocean slab mixed-layer heat capacity, corresponding to an effective ocean mixed-layer depth of $\sim 75\text{ m}$ ($C_w = \rho_w c_w h \approx 1000 \times 4000 \times 75$).
* **`land_capacity = 1.0e7 J m^-2 K^-1`**: Low land heat capacity ($\sim 2.5\text{ m}$ water equivalent), allowing continents to rapidly warm in summer and cool in winter, driving strong land-sea thermal contrasts.
* **`trop_capacity = 1.0e8 J m^-2 K^-1`**, **`trop_cap_limit = 20.0°`**: Reduced tropical mixed-layer depth ($\sim 25\text{ m}$) within $20^\circ$ of the equator, capturing realistic tropical seasonal SST amplitude.
* **`albedo_choice = 7`**: Surface and latitude-dependent albedo (`const_albedo = 0.23`, `higher_albedo = 0.8`, `albedo_cntrnh = 68.0° N`, `albedo_cntrsh = 64.0° S`, `albedo_wdth = 5.0°`, `lat_glacier = -70.0° S`).

---

## 3. Stratospheric Nudging Python Configuration Reference

Stratospheric nudging is configured in Python within `spectral_dynamics_nml` in the experiment file (`strat_nudging_test_case.py`):

```python
    'spectral_dynamics_nml': {
        # Standard dynamical core parameters:
        'damping_order': 4,
        'water_correction_limit': 20000.0,
        'reference_sea_level_press': 100000.0,
        'num_levels': 40,
        'valid_range_t': [100.0, 800.0],
        'initial_sphum': 2e-06,
        'vert_coord_option': 'uneven_sigma',
        'surf_res': 0.1,
        'scale_heights': 7.9,
        'exponent': 1.4,
        'vert_advect_uv': 'second_centered',
        'vert_advect_t': 'second_centered',
        'robert_coeff': 0.03,
        'ocean_topog_smoothing': 0.995,

        # =========================================================================
        # STRATOSPHERIC NUDGING CONFIGURATION (spectral_dynamics.F90)
        # =========================================================================
        # 1. Master enable switch:
        'do_strat_nudging': True,

        # 2. Variables to nudge:
        #    Accepts list containing: 'ucomp', 'vcomp', 'temp'
        #    - Default: ['ucomp'] (nudging zonal wind towards u_target_yr23.nc)
        #    - Following SNAPSI protocol (Hitchcock et al., 2022):
        #      * Zonal-mean nudging (s = 0): ['ucomp', 'temp']
        #      * Multi-wavenumber / full nudging: ['ucomp', 'vcomp', 'temp']
        'nudge_vars': ['ucomp'],

        # 3. Target forcing profile specifications:
        'nudge_u_from_file': True,
        'nudge_u_file': 'INPUT/u_target_yr23.nc',
        'nudge_u_varname': 'ucomp',
        'nudge_u_time_offset_days': 0.0,

        'nudge_v_from_file': True,                  # Optional: read target vcomp from NetCDF
        'nudge_v_file': 'INPUT/v_target_yr23.nc',
        'nudge_v_varname': 'vcomp',
        'nudge_v_time_offset_days': 0.0,

        'nudge_t_from_file': True,                  # Optional: read target temp from NetCDF
        'nudge_t_file': 'INPUT/t_target_yr23.nc',
        'nudge_t_varname': 'temp',
        'nudge_t_time_offset_days': 0.0,

        # 4. Relaxation timescale tau in seconds (e.g. 21600.0 s = 6 hours):
        'nudging_tau': 21600.0,

        # 5. Vertical transition boundaries (Pa):
        #    Nudging is zero below nudging_p_bottom, transitions smoothly via a cubic
        #    Hermite polynomial ramp between nudging_p_bottom and nudging_p_top, and
        #    reaches full strength above nudging_p_top.
        'nudging_p_bottom': 90.0e2,  # 90 hPa (lower transition boundary)
        'nudging_p_top': 50.0e2,     # 50 hPa (full strength boundary)

        # 6. Zonal Wavenumber Filtering Options:
        # Default: Zonal-Mean Nudging only (wavenumber s = 0)
        'nudge_wave_min': 0,
        'nudge_wave_max': 0,

        # Optional explicit list of wavenumbers:
        # 'nudge_wave_list': [0, 2],
    }
```

### Parameter Details:

| Parameter | Type | Default | Description |
| :--- | :---: | :---: | :--- |
| `do_strat_nudging` | `bool` | `False` | Enables stratospheric relaxation towards target fields. |
| `nudge_vars` | `list[str]` | `['ucomp']` | List of variables to nudge: `'ucomp'`, `'vcomp'`, `'temp'`. Following SNAPSI, zonal-mean nudging typically uses `['ucomp', 'temp']`, while multi-wavenumber or full nudging uses `['ucomp', 'vcomp', 'temp']`. |
| `nudge_u_from_file` | `bool` | `False` | When `True`, reads time-dependent 3D target wind from NetCDF. When `False`, nudges toward spatially uniform scalar `nudging_u_val`. |
| `nudge_u_file` | `str` | `'INPUT/u_target.nc'` | Relative path to target NetCDF file inside the run directory. |
| `nudge_u_varname` | `str` | `'ucomp'` | Variable name for zonal wind inside the NetCDF file. |
| `nudge_v_file` | `str` | `''` | NetCDF file for `vcomp`. If empty, defaults to `nudge_u_file`. |
| `nudge_v_varname` | `str` | `'vcomp'` | Variable name for meridional wind inside the NetCDF file. |
| `nudge_t_file` | `str` | `''` | NetCDF file for `temp`. If empty, defaults to `nudge_u_file`. |
| `nudge_t_varname` | `str` | `'temp'` | Variable name for temperature inside the NetCDF file. |
| `nudging_tau` | `float` | `21600.0` | Newtonian relaxation timescale $\tau$ in seconds ($21600\text{ s} = 6\text{ h}$, $86400\text{ s} = 24\text{ h}$). |
| `nudging_p_bottom` | `float` | `9000.0` | Lower pressure limit ($90\text{ hPa}$) below which nudging tendency is identically zero. |
| `nudging_p_top` | `float` | `5000.0` | Pressure level ($50\text{ hPa}$) above which nudging reaches $100\%$ full strength ($1/\tau$). |
| `nudge_wave_min` | `int` | `0` | Smallest zonal wavenumber to retain in the nudging tendency. |
| `nudge_wave_max` | `int` | `-1` | Largest zonal wavenumber to retain. When `nudge_wave_max < 0`, wavenumber filtering is disabled and all gridpoints are relaxed. |
| `nudge_wave_list` | `list[int]` | `[-1]` | Explicit integer array specifying arbitrary wavenumbers to nudge (overrides min/max range when `nudge_wave_list[0] >= 0`). |

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
Model time is converted to days since origin ($`t_\mathrm{eff} = \mathrm{dy} + \mathrm{sec}/86400.0 + \Delta t_\mathrm{offset}`$). Bounding records $`k_1, k_2`$ are located and linearly interpolated:

$$
u_\mathrm{target}(t) = (1 - \alpha) u_\mathrm{target}(k_1) + \alpha u_\mathrm{target}(k_2), \quad \alpha = \frac{t_\mathrm{eff} - t_1}{t_2 - t_1}
$$

Records are cached in memory and reloaded only when the simulation steps into a new target interval.

#### 2. Wavenumber Filtering via Real-to-Complex FFT
The model computes the raw wind difference $`\Delta u(\lambda, \phi, p) = u_\mathrm{model} - u_\mathrm{target}`$ and executes a 1D real-to-complex FFT (`rfftf`) along each latitude circle $`\phi_j`$:

$$
\hat{U}(s, \phi_j, p) = \mathcal{F}\{\Delta u(\lambda, \phi_j, p)\}, \quad s = 0, 1, \dots, N_\mathrm{lon}/2
$$

Any complex Fourier coefficient $\hat{U}(s)$ outside the target wavenumber set is zeroed out:

$$
\hat{U}_\mathrm{filtered}(s) = \begin{cases}
\hat{U}(s) & \text{if } s \in [s_\mathrm{min}, s_\mathrm{max}] \text{ or } s \in \mathcal{S}_\mathrm{list} \\
0 & \text{otherwise}
\end{cases}
$$

where $`\mathcal{S}_\mathrm{list}`$ denotes the optional explicit wavenumber set defined in `nudge_wave_list`. The inverse FFT (`rfftb`) then reconstructs the filtered physical wind difference $`\Delta u_\mathrm{filtered}(\lambda, \phi, p)`$.

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
