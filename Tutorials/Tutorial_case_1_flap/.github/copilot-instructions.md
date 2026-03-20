## Quick orientation — what this repo is

This is a Kratos <-> OpenFOAM co-simulation tutorial case (FSI flap). The repo contains
- a Kratos CoSimulation driver and structural input: `MainKratosCoSim.py`, `ProjectParametersCSM.json`, `Wall_Structure.mdpa`, `StructuralMaterials.json`
- the co-simulation orchestration file: `ProjectParametersCoSim.json`
- an OpenFOAM case tree (time folders, `system/controlDict`, and `flap_fluid_mesh_kratos.gid`)
- helper scripts: `clean.sh`, `plot_displacements.py`

If you're an AI coding agent: focus on the files above to understand architecture, data mappings and run/debug flows.

## Big picture architecture & data flow (important)

1. Kratos runs the CoSimulationAnalysis driver (`MainKratosCoSim.py`) which reads `ProjectParametersCoSim.json`.
2. `ProjectParametersCoSim.json` defines two solver wrappers used by the co-simulation:
   - `structure` — a Kratos structural wrapper that reads `ProjectParametersCSM.json` (structural solver settings and `Wall_Structure.mdpa`).
   - `Openfoam_Kratos_Wrapper` — an external wrapper that communicates with the OpenFOAM case.
3. Communication between Kratos and OpenFOAM is file-based (see `io_settings.type == "kratos_co_sim_io"` and `communication_format: "file"`). The co-sim creates a directory such as `.CoSimIOComm_Openfoam_Adapter_Openfoam_Kratos_Wrapper/` (see `clean.sh` which removes it).
4. Mapping of physical fields is explicit in `ProjectParametersCoSim.json`:
   - Fluid side: `disp_interface_flap` (OpenFOAM -> Kratos) is DISPLACEMENT on model part `interface_flap`.
   - Structure side: `load_interface_flap` (Kratos -> OpenFOAM) is POINT_LOAD / FORCE on `Structure.GENERIC_FSI_Interface`.
   - The OpenFOAM function-object in `system/controlDict` uses `importDataIdentifier`/`exportDataIdentifier` names that must match the `ProjectParametersCoSim.json` data names (example: `disp_interface_flap` and `load_interface_flap`).

## Important files to read or edit when changing coupling behavior
- `ProjectParametersCoSim.json` — co-simulation sequence, mappers, solver wrappers, and operations (scaling, predictors).
- `ProjectParametersCSM.json` — structure solver settings (time stepping, tolerances, buffer, output processes).
- `MainKratosCoSim.py` — example driver showing how a custom CoSimulationAnalysis can be derived/extended.
- `system/controlDict` — OpenFOAM function object `KratosOpenfoamAdapterFunctionObject` configuration (interface patches, identifiers, dim, parameters like rho/nu).
- `system/*` and time folders — OpenFOAM case data produced/read at runtime. The adapter library path is referenced from `controlDict`.

## Project-specific conventions & gotchas (do not change lightly)
- Naming consistency matters: `model_part_name` and `interface` names must match exactly between the two sides. Example:
  - In `ProjectParametersCoSim.json` the fluid data uses `model_part_name: "interface_flap"` while the structural side uses `Structure.GENERIC_FSI_Interface`.
  - In `system/controlDict` the function-object has `name interface_flap;` and `patches (flap);` — OpenFOAM patch names must match the mesh.
- Mapper settings live under `data_transfer_operators.mapper.mapper_settings` — this case uses `nearest_neighbor` with `search_radius: 0.5`. If you change mesh scale, increase search radius.
- The coupling uses a scaling operation `scaling_loads_interface_flap` (see `coupling_operations`) with a time-expression string. These are read literally — keep the expression syntax if editing.

## Developer workflows — how to run and debug (concrete)

Assumptions: Kratos and OpenFOAM are installed and available in the environment. `controlDict` header indicates OpenFOAM v7 formatting.

Typical local run (one common approach):
1. Start OpenFOAM in the case directory (so the function object library is loaded by `controlDict`). OpenFOAM writes/reads the co-sim files and produces `logopenfoam`:

```
# (run from case directory)
pimpleFoam > logopenfoam 2>&1 &
```

2. Start the Kratos co-sim driver from the same directory (Kratos must be importable from Python):

```
python3 MainKratosCoSim.py > logkratos 2>&1
```

3. Inspect progress and troubleshooting points:
   - `.CoSimIOComm_*` directory: check exchanged files and timestamps when debugging communication.
   - `logopenfoam` and `logkratos` files for runtime messages and errors.
   - `testing_results/` and `vtk_output_structure/` for structural outputs; `postProcessing/` for OpenFOAM probes.
   - `plot_displacements.py` reads `postProcessing/probes/0/cellDisplacement` (useful quick plot).

Quick cleaning helper: `./clean.sh` — removes co-sim comm dirs, OpenFOAM case files (uses `$WM_PROJECT_DIR` so OpenFOAM env must be loaded).

## Integration & external dependencies to be aware of
- The OpenFOAM function object relies on a compiled library path referenced in `system/controlDict`: `../KratosOpenfoamAdapterFunctionObject/libKratosOpenfoamAdapterFunctionObjectFunctionObjects.so`. The adapter function-object must be built separately and placed at that path.
- Environment variables: `WM_PROJECT_DIR` (OpenFOAM) is used by `clean.sh`. Kratos must be available as a Python import (KratosMultiphysics).

## Small examples for quick edits
- To change the mapper radius: edit `ProjectParametersCoSim.json` -> `data_transfer_operators.mapper.mapper_settings.search_settings.search_radius`.
- To add a variable to structural VTK output: edit `ProjectParametersCSM.json` -> `output_processes.vtk_output[].Parameters.nodal_solution_step_data_variables`.
- To debug missing interface files: verify `system/controlDict` identifiers match the `data` keys in `ProjectParametersCoSim.json` (`disp_interface_flap` and `load_interface_flap`).

## Where to extend or add tests
- Add small smoke tests that run Kratos-only with `ProjectParametersCSM.json` to validate structural inputs (no OpenFOAM). Use `testing_results/` outputs as ground truth for automated checks.

If something in these instructions is unclear or you'd like more detail (build steps for the OpenFOAM adapter, example CLI sessions, or a quick smoke test script), tell me which piece to expand and I'll iterate.
