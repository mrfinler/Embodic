Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Unit U-S6, 2026-10-16.

# FEA toolchain for Phase 3: Elmer is blocked in this container, gmsh with GetDP runs

This is the evidence record for the OR-11 and OR-12 FEA toolchain (D-048e). It covers the Elmer install routes that were
tried, the mesher, two fallback solvers that install and run here, a smoke test with a closed-form check, and the
licences read from the installed files. New evidence rows EV-117 to EV-126 are in `evidence_register_phase3.md`.

## Summary

| Item | Result | Status |
|---|---|---|
| Elmer FEM | No install route reaches a package or source. Every host is refused by the network allowlist, or the repository is not enabled for the session. | verified (ran), `blocked` |
| Mesher | gmsh 4.12.1+ds1-1.1build2 from Ubuntu apt. GPL-2+ with Gmsh exception. | verified (ran, read installed file) |
| Fallback 1 (recommended) | GetDP 3.2.0+dfsg1-1.1build12 from Ubuntu apt. GPL-2+. The smoke test converges to the closed form. | verified (ran, read installed file) |
| Fallback 2 | scikit-fem 12.0.2 from PyPI in `/home/claude/fea/venv`. 3-clause BSD text. The smoke test converges to the closed form. | verified (ran, read installed file) |
| Smoke result | B_x inside the magnet is 0.621727 T from GetDP and from scikit-fem at 0.5 mm mesh size. The closed form gives 0.622222 T (−0.080 %). | verified (ran) |
| Distribution | Tools only. Nothing enters `src/`, `tests/` or the wheel. | verified (no write outside `docs/phase3/evidence/**` and `/home/claude/fea/**`) |

Fable asks the user before OR-11 and OR-12 switch from Elmer to a fallback.

## Container

Ubuntu 24.04.4 LTS, x86_64, 2 CPUs, 7 GB RAM, Python 3.11.15 (verified, `cat /etc/os-release`, `nproc`, `free -g`).
Outbound HTTPS goes through the agent proxy. `pypi.org` and `files.pythonhosted.org` bypass it (proxy status
`noProxy` list). apt reads `http://archive.ubuntu.com/ubuntu/` and `http://security.ubuntu.com/ubuntu/` (verified, apt
sources).

Every step ran through `/home/claude/fea/bin/logrun.sh`. It appends the command, the UTC time, the output and the exit
code to one log per step. Copies of the logs are in `docs/phase3/evidence/fea_smoke/logs/`.

## Elmer routes: all four are closed

The brief orders the routes. Each one stopped at the network, before any package or source was reached.

| # | Route | Command (abridged) | Output excerpt | Status |
|---|---|---|---|---|
| 0 | Ubuntu apt index | `apt-get update; apt-cache search elmer` | Only `libgeo-helmerttransform-perl - Transformations between coordinates in different datums` | verified (ran, `r0-apt.log`) |
| 1 | Elmer CSC PPA | `curl https://ppa.launchpadcontent.net/elmer-csc-ubuntu/elmer-csc-ppa/ubuntu/dists/noble/Release` and `https://api.launchpad.net/...` | `curl: (56) CONNECT tunnel failed, response 403`. Proxy note: `ppa.launchpadcontent.net:443 — connect_rejected`, `api.launchpad.net:443 — connect_rejected`. Over plain HTTP: `Could not resolve host: ppa.launchpadcontent.net` | verified (ran, `r1-ppa-probe.log`) |
| 2 | conda-forge or micromamba | `curl https://api.anaconda.org/search?name=elmer`, `https://conda.anaconda.org/conda-forge/channeldata.json`, `https://micro.mamba.pm/...`, `https://repo.prefix.dev/conda-forge/...` | `CONNECT tunnel failed, response 403` for all four hosts | verified (ran, `r2-conda-probe.log`, `r3-release-probe.log`) |
| 3 | Official release binary | `curl https://github.com/ElmerCSC/elmerfem/releases`; `gh api repos/ElmerCSC/elmerfem/releases`; `https://www.elmerfem.org/blog/binaries/`; `https://www.nic.funet.fi/pub/sci/physics/elmer/bin/` | GitHub: `"GitHub access to this repository is not enabled for this session. Use add_repo to request access."` (HTTP 403). elmerfem.org and funet.fi: `CONNECT tunnel failed, response 403` | verified (ran, `r3-release-probe.log`) |
| 4 | Source build | `curl https://codeload.github.com/ElmerCSC/elmerfem/tar.gz/refs/tags/release-9.0`; `https://sourceforge.net/projects/elmerfem/`; `https://archive.softwareheritage.org/...` | codeload: HTTP 403. SourceForge and Software Heritage: `CONNECT tunnel failed, response 403` | verified (ran, `r4-source-probe.log`) |

The PPA path, the `release-9.0` tag and the micromamba URL come from memory. They were not read in a source this session
(assumption). The result does not depend on them, because the proxy refuses the whole host before any path is sent,
and GitHub refuses the whole repository.

Two more probes looked for Elmer elsewhere.

- The PyPI project listing (`https://pypi.org/simple/`, JSON, 914,940 projects) has no Elmer solver distribution. The
  names that contain "elmer" and relate to Elmer FEM are `pyelmer` 1.2.1 ("A python interface to Elmer.") and
  `elmer-circuitbuilder` 1.0.5 ("Python module for creating the circuit simulation definitions for Elmer FEM", "GNU
  Lesser General Public License v3"). Neither ships a solver binary (inferred from the summaries). Status verified (ran,
  `r5-pypi-listing.log`, `r4-source-probe.log`).
- `docker` is installed, but `registry-1.docker.io` and `ghcr.io` are refused (`CONNECT tunnel failed, response 403`).
  Status verified (ran, `r3-release-probe.log`).

The source-build time was not estimated. The estimate needs the source tree, and no source host is reachable
(unresolved). gfortran is not installed (`which gfortran` printed nothing). The Elmer licence could not be confirmed
against an installed copy, because no copy is installed (unresolved). EV-116 still stands as a web extract.

The blocker is network access, not Elmer. To unblock Elmer, the session needs at least one of these:

- GitHub access to `ElmerCSC/elmerfem` for this session. This opens the release assets and a source build.
- `ppa.launchpadcontent.net` and the PPA signing-key host on the network allowlist.
- `conda.anaconda.org` on the allowlist. It is not known whether conda-forge carries Elmer, because the channel listing
  could not be read (unresolved).

## Meshing: gmsh 4.12.1 from apt

```
$ DEBIAN_FRONTEND=noninteractive nice -n 10 apt-get install -y --no-install-recommends gmsh getdp
Setting up libgmsh4.12t64:amd64 (4.12.1+ds1-1.1build2) ...
Setting up gmsh (4.12.1+ds1-1.1build2) ...
$ gmsh --version
4.12.1
```

`/usr/share/doc/gmsh/copyright` gives `Files: *` with `License: GPL-2+ with Gmsh exception`. The exception text says
"The copyright holders of Gmsh give you permission to combine Gmsh with code included in the standard release of TetGen
[...], Netgen [...], Chaco [...], METIS [...] and OpenCASCADE [...] under their respective licenses." Some contributed
parts carry other licences, for example `contrib/bamg/*` (`LGPL-2.1`) and `contrib/HighOrderMeshOptimizer/*`
(`Expat`). Status verified (read installed file, `c-licences.log`).

The pip route is also open. PyPI lists `gmsh` 4.15.2 with the licence field `GPLv2+` and a
`py2.py3-none-manylinux_2_24_x86_64` wheel (verified, PyPI JSON, `d0-fallback-candidates.log`). It was not installed
(not tested).

## Fallbacks that work here

### Fallback 1 (recommended): GetDP 3.2.0 with gmsh, from apt

GetDP installs with the same `apt-get` command as gmsh. `getdp --version` prints `3.2.0`. A run prints
`[GetDP 3.2.0, 1 node, max. 1 thread]` and solves with PETSc and MUMPS (`N: 7228 - preonly lu mumps`). Status verified
(ran, `b-gmsh-getdp-apt.log`).

`/usr/share/doc/getdp/copyright` gives `Files: *` with `License: GPL-2+`. Other files carry `GPL-2`, `GPL-3+`, `Expat`
or `Other`. Status verified (read installed file, `c-licences.log`).

GetDP is the closest match to Elmer of the tools that run here. It reads a text problem file the way Elmer reads a
`.sif` file, and it reads gmsh meshes directly. 3-D and time-harmonic runs were not tried in this unit, and the Debian
package ships empty `examples/` and `html/` folders, so those capabilities are not tested here.

### Fallback 2: scikit-fem 12.0.2, pip into `/home/claude/fea/venv`

```
$ python3 -m venv /home/claude/fea/venv && /home/claude/fea/venv/bin/pip install -q scikit-fem==12.0.2
numpy      2.4.6
scikit-fem 12.0.2
scipy      1.17.1
```

The installed `scikit_fem-12.0.2.dist-info/licenses/LICENSE` starts with "Copyright 2018-26 scikit-fem developers" and
has the three conditions of the BSD 3-clause text, including "Neither the name of the copyright holder nor the names of
its contributors". The file does not name the licence. Calling it BSD-3-Clause is inferred from the text. numpy 2.4.6
has `License-Expression: BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0`. scipy 1.17.1 has
`Classifier: License :: OSI Approved :: BSD License`. Status verified (read installed files, `c-licences.log`).

scikit-fem is a Python library. Each problem is a Python script that assembles its own weak form. It needs no input
language, but every formulation term is hand-written.

### Checked, not installed

| Tool | What was checked | Licence | Status |
|---|---|---|---|
| NGSolve 6.2.2608 with netgen-mesher 6.2.2608 | PyPI lists `ngsolve-6.2.2608-cp311-cp311-manylinux_2_28_x86_64.whl` and the matching netgen wheel | `license_expression: LGPL-2.1-only` (PyPI metadata) | verified (PyPI JSON); install not tested |
| FEMM 4.2 under wine | `wine` 9.0~repack-4build3 is an apt candidate. `https://www.femm.info/wiki/Download` is refused (`CONNECT tunnel failed, response 403`) | Aladdin Free Public License (EV-115) | verified (ran); no installer reachable, so this route does not work here |

## Smoke test: a magnet cylinder in air

### Case

A 2-D disk magnet of radius a = 10 mm sits in an air disk of radius R = 50 mm. The magnet uses the OR-11 material
values: B_r = 1.33 T along x and µ_r = 1.05 (G23, from `oracle_tests_spec.md` OR-11). The outer circle has A_z = 0, so
the normal flux density there is zero. GetDP solves H = ν(B − B_r) with ν = 1/(µ0 µ_r) in the magnet and 1/µ0 in air,
with first-order nodal A_z elements. The inputs are `fea_smoke/pm_cylinder/pm.geo` and `fea_smoke/pm_cylinder/pm.pro`.

### Closed form

The interior field of this case is uniform. The derivation below was written in this unit and was not read in an
external source (inferred).

1. Use a scalar potential φ with H = −∇φ. Inside, φ = −H_i r cos θ. In the air annulus, φ = (C/r + D r) cos θ.
2. A_z = 0 at r = R means B_r(R) = 0, which gives D = C/R².
3. Continuity of φ at r = a gives C = −H_i a² / (1 + q), with q = (a/R)².
4. Continuity of normal B at r = a gives µ0 µ_r H_i + B_r = −µ0 k H_i, with k = (1 − q)/(1 + q).
5. So B_x inside = B_r k / (µ_r + k). For R → ∞, k → 1 and this becomes B_r / (1 + µ_r).

With q = 0.04, k = 0.923077 and B_x = 0.622222 T.

### Command and result

```
$ bash docs/phase3/evidence/fea_smoke/setup_fea.sh
closed form B_x inside magnet = 0.622222 T
lc_m      nodes  getdp_Bx_T   err_%    skfem_Bx_T  err_%
0.002        513    0.614750  -1.201    0.614762  -1.199
0.001       1889    0.620246  -0.318    0.620246  -0.318
0.0005      7388    0.621727  -0.080    0.621727  -0.080
--- GetDP log, last 6 lines of the finest run ---
Info    : ...done: 20x20x1
Info    : PostOperation 2/2
          > 'b_inside.txt'
Info    : (Wall = 0.593435s, CPU = 0.18402s, Mem = 68.3516Mb)
E n d   P o s t - P r o c e s s i n g
Info    : Stopped (Fri Oct 16 13:13:41 2026, Wall = 0.594331s, CPU = 0.184903s, Mem = 68.4766Mb)
```

The run in `a-smoke-getdp-skfem.log` and the rerun in `e-rerun-setup.log` print the same table (verified). `lc_m` is
the gmsh mesh size inside the magnet. The air mesh is 4 times coarser at r = R.

What the numbers show:

- GetDP converges to the closed form. The error falls by a factor of 3.8 and then 4.0 for each halving of the mesh size
  (verified, ratio of the printed errors). That is the second-order rate expected from first-order elements and a
  polygonal circle (inferred).
- scikit-fem assembles the same weak form with independent code and agrees with GetDP to six digits on the two finer
  meshes (verified). The agreement checks the sign and scale of the magnet term in `pm.pro`. The 1.2e-5 T gap on the
  coarse mesh comes from the evaluation point. GetDP reads one element at (0, 0), and the script averages the elements
  around the centre node (inferred).
- The run proves the tools solve a linear magnet problem with OR-11 material values. It does not validate any OR-11 or
  OR-12 band, and it does not exercise periodic boundaries, 3-D or time-harmonic solves (not tested).

## Licences and the tools-only boundary

gmsh (GPL-2+ with Gmsh exception), GetDP (GPL-2+), scikit-fem (3-clause BSD text), numpy and scipy are tools on the
cloud container. They are installed under apt and `/home/claude/fea/` only. Nothing was written to `src/`, `tests/`,
the project venv or the wheel (verified, `find -newermt` on the worktree lists only files under
`docs/phase3/evidence/`). Agent 4 commits only problem inputs and results, as `oracle_tests_spec.md` requires.
D-048c records embodic as a personal project used at the office. The tools stay on the cloud container and are never
distributed (assumption, from the U-S6 brief). The GPL obligations attach to distributing the tools, so none arise
here (inferred, not legal advice).

## How to reproduce

Run this from the worktree root. The script is safe to rerun. apt and pip skip what is already installed.

```
bash docs/phase3/evidence/fea_smoke/setup_fea.sh
```

The script writes meshes and results to `/home/claude/fea/smoke/run`. Pass another folder as the first argument to
change it. It never writes into `docs/`.

## Open questions

- Q1 (user, through Fable). Switch OR-11 and OR-12 to GetDP with gmsh, or enable a route for Elmer (GitHub access to
  `ElmerCSC/elmerfem`, or the Launchpad PPA hosts)?
- Q2 (Agent 4). If GetDP is chosen, the first OR-12 run should include a closed-form time-harmonic check (for example a
  conducting slab), because time-harmonic GetDP runs are not tested here.
- Q3 (Fable). OR-11's 3-D edge-leakage case was the reason to prefer Elmer. GetDP 3-D and NGSolve 3-D are both
  not tested here.
