//! U-D27: `embodic.physics.emf.integrate_path` ported to Rust behind a C ABI, for a measured speed and identity check.
//!
//! Every operation follows the Python and NumPy code of 0.0.4 in the same order, so that the results can be compared
//! bit for bit: `math.hypot` is CPython 3.11's `vector_norm` for two values (Modules/mathmodule.c, v3.11.9), Python's
//! `min` and `max` keep their argument order on ties, and NumPy's products run left to right as the expression parses.
//! The complex exponential is glibc's `cexp`, which NumPy 2.4.6 calls on this Linux build, or Rust's `sin` and `cos`.

use std::os::raw::c_int;

#[repr(C)]
#[derive(Clone, Copy)]
struct Complex {
    re: f64,
    im: f64,
}

extern "C" {
    fn cexp(z: Complex) -> Complex;
}

const T27: f64 = 134217729.0;

fn frexp_exponent(x: f64) -> i32 {
    let bits = x.to_bits();
    let biased = ((bits >> 52) & 0x7ff) as i32;
    if biased == 0 {
        frexp_exponent(x * f64::from_bits(0x4350000000000000)) - 54 // 2^54
    } else {
        biased - 1022
    }
}

fn pow2(e: i32) -> f64 {
    if e >= -1022 {
        f64::from_bits(((e + 1023) as u64) << 52)
    } else {
        f64::from_bits(1u64 << (52 + e + 1022))
    }
}

/// CPython 3.11 `math.hypot(x, y)`: `vector_norm` with n = 2, max = the larger magnitude.
fn py_hypot(x: f64, y: f64) -> f64 {
    let (ax, ay) = (x.abs(), y.abs());
    let max = if ay > ax { ay } else { ax };
    if max.is_infinite() {
        return max;
    }
    if ax.is_nan() || ay.is_nan() {
        return f64::NAN;
    }
    if max == 0.0 {
        return max;
    }
    let max_e = frexp_exponent(max);
    if max_e < -1023 {
        let tiny = f64::MIN_POSITIVE;
        return tiny * py_hypot(ax / tiny, ay / tiny);
    }
    let scale = pow2(-max_e);
    let (mut csum, mut frac1, mut frac2, mut frac3) = (1.0f64, 0.0f64, 0.0f64, 0.0f64);
    for v in [ax, ay] {
        let x = v * scale;
        let t = x * T27;
        let hi = t - (t - x);
        let lo = x - hi;
        let sq = hi * hi;
        let old = csum;
        csum += sq;
        frac1 += (old - csum) + sq;
        let cross = 2.0 * hi * lo;
        let old = csum;
        csum += cross;
        frac2 += (old - csum) + cross;
        frac3 += lo * lo;
    }
    let h = (csum - 1.0 + (frac1 + frac2 + frac3)).sqrt();
    let t = h * T27;
    let hi = t - (t - h);
    let lo = h - hi;
    let x = -hi * hi;
    let old = csum;
    csum += x;
    frac1 += (old - csum) + x;
    let x = -2.0 * hi * lo;
    let old = csum;
    csum += x;
    frac2 += (old - csum) + x;
    let x = -lo * lo;
    let old = csum;
    csum += x;
    frac3 += (old - csum) + x;
    let x = csum - 1.0 + (frac1 + frac2 + frac3);
    (h + x / (2.0 * h)) / scale
}

/// Python's `max(a, b)`: `a` unless `b > a`.
fn py_max(a: f64, b: f64) -> f64 {
    if b > a {
        b
    } else {
        a
    }
}

/// Python's `min(a, b)`: `a` unless `b < a`.
fn py_min(a: f64, b: f64) -> f64 {
    if b < a {
        b
    } else {
        a
    }
}

/// CPython's `math.atan2`: the special cases of `m_atan2` for a zero `y`, then libm's `atan2`.
fn py_atan2(y: f64, x: f64) -> f64 {
    if x.is_nan() || y.is_nan() {
        return f64::NAN;
    }
    if y.is_infinite() || x.is_infinite() {
        return y.atan2(x);
    }
    if y == 0.0 {
        return if x.is_sign_positive() { 0.0f64.copysign(y) } else { std::f64::consts::PI.copysign(y) };
    }
    y.atan2(x)
}

/// One path against the field table, as `integrate_path` of embodic 0.0.4.
///
/// `seg` holds `n_seg` rows `(x1, y1, x2, y2, length, width)` from `discretise_path`; `bz_t` and `bt_t` are C-ordered
/// `(n_h, n_cols)`. Writes `lam` as `n_h` interleaved (re, im) pairs, `ez` and `et` (`n_h` each) and `edge`
/// `(w, wd)`. `use_cexp` 1 takes glibc `cexp`, 0 Rust's `cos` and `sin`.
///
/// # Safety
/// Every pointer must hold the number of values given above.
#[no_mangle]
pub unsafe extern "C" fn u_d27_integrate_path(
    seg: *const f64,
    n_seg: usize,
    bz_t: *const f64,
    bt_t: *const f64,
    n_h: usize,
    n_cols: usize,
    harmonics: *const f64,
    pole_pairs: f64,
    r_a: f64,
    r_b: f64,
    radial_eps: f64,
    edge_decay: f64,
    use_cexp: c_int,
    lam: *mut f64,
    ez: *mut f64,
    et: *mut f64,
    edge: *mut f64,
) {
    let seg = std::slice::from_raw_parts(seg, n_seg * 6);
    let bz_t = std::slice::from_raw_parts(bz_t, n_h * n_cols);
    let bt_t = std::slice::from_raw_parts(bt_t, n_h * n_cols);
    let harmonics = std::slice::from_raw_parts(harmonics, n_h);
    let lam = std::slice::from_raw_parts_mut(lam, 2 * n_h);
    let ez = std::slice::from_raw_parts_mut(ez, n_h);
    let et = std::slice::from_raw_parts_mut(et, n_h);
    let edge = std::slice::from_raw_parts_mut(edge, 2);
    lam.fill(0.0);
    ez.fill(0.0);
    et.fill(0.0);
    let (mut edge_w, mut edge_wd) = (0.0f64, 0.0f64);
    let steps = (n_cols - 1) as i64;
    let theta_scale: Vec<f64> = harmonics.iter().map(|h| -h * pole_pairs).collect();
    let mut bz = vec![0.0f64; n_h];
    let mut bt = vec![0.0f64; n_h];
    for row in seg.chunks_exact(6) {
        let (x1, y1, x2, y2, length, width) = (row[0], row[1], row[2], row[3], row[4], row[5]);
        let (r1, r2) = (py_hypot(x1, y1), py_hypot(x2, y2));
        if py_max(r1, r2) <= r_a + radial_eps || py_min(r1, r2) >= r_b - radial_eps {
            continue;
        }
        let c1 = py_min(r_b, py_max(r_a, r1));
        let c2 = py_min(r_b, py_max(r_a, r2));
        let frac = if (r2 - r1).abs() >= radial_eps { (c2 - c1).abs() / (r2 - r1).abs() } else { 1.0 };
        let (a1, a2) = (py_atan2(y1, x1), py_atan2(y2, x2));
        let am = (a1 + a2) / 2.0 + (if (a2 - a1).abs() > std::f64::consts::PI { std::f64::consts::PI } else { 0.0 });
        let rm = (c1 + c2) / 2.0;
        let x = (rm - r_a) / (r_b - r_a) * (steps as f64);
        let i = 0i64.max((steps - 1).min(x.floor() as i64));
        let t = x - (i as f64);
        let (i, one_minus_t) = (i as usize, 1.0 - t);
        for k in 0..n_h {
            let row_k = k * n_cols;
            bz[k] = bz_t[row_k + i] * one_minus_t + bz_t[row_k + i + 1] * t;
            bt[k] = bt_t[row_k + i] * one_minus_t + bt_t[row_k + i + 1] * t;
        }
        let dc = c2 - c1;
        let active = length * frac;
        let w3 = width.powf(3.0); // Python's float ** 3 is C pow(w, 3.0); powi would round twice
        for k in 0..n_h {
            let theta = theta_scale[k] * am;
            let e = if use_cexp != 0 {
                cexp(Complex { re: 0.0, im: theta })
            } else {
                Complex { re: theta.cos(), im: theta.sin() }
            };
            let s = bz[k] * rm * dc;
            lam[2 * k] += s * e.re;
            lam[2 * k + 1] += s * e.im;
            ez[k] += active * bz[k] * bz[k] * w3;
            et[k] += active * bt[k] * bt[k] * width;
        }
        let w = (bz[0] * rm * dc).abs();
        edge_w += w;
        edge_wd += w * (-py_min(rm - r_a, r_b - rm) / edge_decay).exp();
    }
    edge[0] = edge_w;
    edge[1] = edge_wd;
}
