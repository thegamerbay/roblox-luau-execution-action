# Roblox Luau Execution Action 🎮

[![GitHub Release](https://img.shields.io/github/v/release/thegamerbay/roblox-luau-execution-action?style=flat-square)](https://github.com/thegamerbay/roblox-luau-execution-action/releases)
[![Lint Code and Workflows](https://github.com/thegamerbay/roblox-luau-execution-action/actions/workflows/lint.yml/badge.svg)](https://github.com/thegamerbay/roblox-luau-execution-action/actions/workflows/lint.yml)
[![codecov](https://codecov.io/gh/thegamerbay/roblox-luau-execution-action/graph/badge.svg)](https://codecov.io/gh/thegamerbay/roblox-luau-execution-action)
[![Update Major Tag](https://github.com/thegamerbay/roblox-luau-execution-action/actions/workflows/release.yml/badge.svg)](https://github.com/thegamerbay/roblox-luau-execution-action/actions/workflows/release.yml)
[![License](https://img.shields.io/github/license/thegamerbay/roblox-luau-execution-action?style=flat-square)](https://github.com/thegamerbay/roblox-luau-execution-action/blob/main/LICENSE)

A composite GitHub Action that seamlessly integrates with the **Roblox Open Cloud API**. It uploads a built `.rbxl` place file to your Universe and executes a Luau test script (like TestEZ) directly on Roblox servers.

## 🚀 Features
* **Zero Dependencies:** Runs on pure Python standard libraries, meaning execution starts instantly without waiting for `pip install`.
* **Automated Polling:** Automatically creates the task, polls the Roblox servers, and fetches the execution logs.
* **Native Integration:** Prints logs natively in GitHub Actions groups and correctly sets the exit code so your CI fails if your tests fail.

## 🛠 Usage

To use this action in your CI/CD pipeline, add the following step after building your `.rbxl` file (e.g., with Rojo).

```yaml
- name: Upload & Run Tests via Open Cloud
  uses: thegamerbay/roblox-luau-execution-action@v1
  with:
    api_key: ${{ secrets.ROBLOX_API_KEY }}
    universe_id: ${{ vars.ROBLOX_TEST_UNIVERSE_ID }}
    place_id: ${{ vars.ROBLOX_TEST_PLACE_ID }}
    place_file: 'dist.rbxl'
    script_file: 'tasks/runTests.luau'
```

## ⚡ Setup Guide

To use this action, you need to configure your Roblox experience and generate an Open Cloud API Key.

1. **Create Place:** Have a target **Test Place** ready within an Experience in Roblox Studio.
2. **Generate API Key:** Go to the [Roblox Creator Dashboard](https://create.roblox.com/docs/cloud/open-cloud/api-keys) and create a new Open Cloud API Key.
3. **Set Permissions:** Grant the API Key the following permissions for your target Experience/Place:
   * `universe.places:write`
   * `universe.place.luau-execution-session:write`
4. **Configure IP Access (Critical):** Since GitHub Actions runners use dynamic IP addresses, you **must** add `0.0.0.0/0` to the "Accepted IP Addresses" section of your API key settings.
5. **Add Repository Secrets:** In your GitHub repository, go to *Settings -> Secrets and variables -> Actions* and add the generated API Key as a Secret named `ROBLOX_API_KEY`.
6. **Add Repository Variables:** In the same GitHub settings menu, add your IDs as Variables:
   * `ROBLOX_TEST_UNIVERSE_ID` *(Note: This is your Experience ID)*
   * `ROBLOX_TEST_PLACE_ID`

> **💡 Tip: How to find your IDs**
> You can easily find both IDs in the URL of your experience on the Creator Dashboard:
> `https://create.roblox.com/dashboard/creations/experiences/[UNIVERSE_ID]/places/[PLACE_ID]/...`

## 📥 Inputs

| Input | Required | Default | Description |
| --- | --- | --- | --- |
| `api_key` | Yes |  | Your Roblox Open Cloud API Key with `universe.places:write` and `universe.place.luau-execution-session:write` permissions. |
| `universe_id` | Yes |  | Target Roblox Universe ID. |
| `place_id` | Yes |  | Target Roblox Place ID. |
| `place_file` | Yes |  | Path to your compiled place file (e.g., `dist.rbxl`). |
| `script_file` | Yes |  | Path to the Luau script to run on the server. |
| `publish` | No | `false` | Set to `true` to Publish the place instead of just Saving it. |

## 📤 Outputs

| Output | Description |
| --- | --- |
| `task_status` | The final state of the task (e.g., `COMPLETE`, `FAILED`). |
| `task_logs` | The raw string of logs returned by the execution task. |

## 📄 License

This project is licensed under the MIT License.
