# GitHub / Azure deployment

Public repository: https://github.com/aserdargun/cpu-aserdargun-com

Production URL: https://cpu.aserdargun.com

Azure-generated URL: https://happy-field-0e86cdc03.1.azurestaticapps.net

Target: `aserdargun subscription 4` (`a78f5745-b16b-415a-aaf9-9cfd5d19c6a3`), resource group `rg-cpu-aserdargun-com`, Static Web App `swa-cpu-aserdargun-com`, West Europe, Free. The existing `cpu.aserdargun.com` custom domain serves the same app; publishing content reuses this binding.

The authoritative `.github/workflows/deploy-swa-cpu-aserdargun-com.yml` runs on `main` or manual dispatch, serializes production uploads and uses immutable official action SHAs. It installs locked dependencies, verifies the stored engineering evidence against current source hashes, runs 55 assembler/RTL-WASM/mapped-gate tests and three DEF parser tests, builds the static site, checks every copied public artifact and uploads prebuilt `dist/`. Native Spike, formal and physical design runs remain distinct local engineering evidence; see TOOLCHAIN.md to reproduce them.

The deployment token is a scoped GitHub Actions secret named `AZURE_STATIC_WEB_APPS_API_TOKEN_SWA_CPU_ASERDARGUN_COM`; it is not stored in the repository. `/release.json` records the deployed commit, Actions run ID and SHA-256 hashes of all deployment assets. The workflow's `cpu-release-evidence` artifact retains its test report and release manifest.

To check a live release from the development host:

```sh
CPU_LAB_BASE_URL=https://happy-field-0e86cdc03.1.azurestaticapps.net npx playwright test
```

The existing CPU physical boundaries are unchanged by publication: router DRC is zero, antenna violations remain, and RV32IM does not meet the 100 ns STA target. The published web app is CPU Atlas, an educational guide to processor architecture with interactive RISC-V examples. Its engineering artifacts do not establish fabrication signoff.
