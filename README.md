# Beat Saber PS4 Custom Song Support Project

- **[beat-saber-ps4-custom-songs/README.md](./beat-saber-ps4-custom-songs/README.md)** - Main project documentation
- **[beat-saber-ps4-custom-songs/PROGRESS.md](./beat-saber-ps4-custom-songs/PROGRESS.md)** - Development progress

## What Do?

Pipeline to convert custom Beat Saber PC songs into installable PS4 packages compatible with the PS4 Beat Saber VR game, to show up as custom playable songs in-game directly on the PS4

## Status

This is still in pre-alpha stages of development; the pipeline does not yet produce something installable. Current fpkg installs result in PS4 error dialogs.

## Getting Started

Once you have a local copy, move on to the [Quick Start](#quick-start) section below to launch the devcontainer and begin developing with an opencode agent.

Fork it, rename it, strip it down or build on top — this is your base project. Modify it to suit your needs and start building.

## Quick Start

### Prerequisites

> **Install ONE code editor** (all support Dev Containers):
> (For ease of use, VS Code is recommended. Especially in Windows; it will even automatically install docker WSL for you.)
>
> - [VS Code](https://code.visualstudio.com/) + [Dev Containers extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers) + [WSL extension (Windows)](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl) (Windows: [install WSL first](https://aka.ms/wsl), VS Code will auto-enable Docker in WSL)
> - [Cursor](https://cursor.sh/)
> - [Google Antigravity](https://antigravity.google.com/download)
> - [Zed](https://zed.dev/) (via [zed-devcontainer](https://github.com/zed-industries/zed/tree/main/crates/zed_devcontainer) extension)
> - [IntelliJ IDEA](https://www.jetbrains.com/idea/) / [PyCharm](https://www.jetbrains.com/pycharm/) (via [Dev Containers plugin](https://plugins.jetbrains.com/plugin/21962-dev-containers))
> - [GNOME Builder](https://apps.gnome.org/Builder/) (built-in)

> **Install ONE container runtime**: (only if not using VS Code with WSL on Windows)
>
> - [Docker Desktop](https://www.docker.com/products/docker-desktop/) (Windows/Mac)
> - [Docker CLI](https://docs.docker.com/engine/install/) + [Docker Compose plugin](https://docs.docker.com/compose/install/) (Linux)
> - [Rancher Desktop](https://rancherdesktop.io/) (Windows/Mac/Linux alternative)
> - [Colima](https://github.com/abiosoft/colima) (macOS/Linux alternative)
> - [WSL2 + Docker Engine](https://docs.docker.com/engine/install/) (Windows 10 LTSC — run `wsl --install`, then install Docker inside Linux)

### Steps

1. Open this folder in your editor
2. When prompted, click **Reopen in Container** (or run `Dev Containers: Reopen in Container` from the command palette)
3. The devcontainer will build and automatically launch opencode
4. If you are using Google Antigravity, it might take two launches to fully load the opencode session when building / rebuilding the devcontainer
   a. The first launch's output will create the container and end with "Container started" and just wait there.
   b. The second (and subsequent) launch(es) will pick up where that left off and actually end with opencode running.

### Persistent Data

The following folders are mounted from your host into the container and persist across rebuilds:

- **`.ai_working/opencode_data`** — opencode session data, logs, and state
- **`.ai_memory`** — AI memory/context files should be saved here if you point out the `.agent/rules.md` file to opencode.

This means your opencode sessions, conversation history, and any cached data survive container rebuilds.

## Agent Rules

This project includes a **`/workspace/.agent/rules.md`** file that defines how the AI agent should behave — memory handling, git behavior, and more.

**At the start of every conversation, point opencode to this file:**

```
Here's the rules file: /workspace/.agent/rules.md
```

This ensures the agent follows your conventions for session management, memory organization, and git behavior throughout your project.

An easy way to point to a file is to drag it from the left sidebar to the chat window. A reference to that file will be inserted where your chat cursor is, so you can insert the file into your message in the appropriate place to make sense.

## Usage

### Task: Resume Last Session

- **Command Palette**: `Tasks: Run Task` → `Opencode: Resume Last Session`
- Automatically finds the most recent session and resumes it
- Runs automatically when you open the folder in VS Code

### Task: Launch Fresh

- **Command Palette**: `Tasks: Run Task` → `Opencode: Launch Fresh`
- Starts a fresh opencode session in `/workspace`

### Manual Usage

```bash
# Start a new session
opencode /workspace

# Resume a specific session
opencode /workspace -c -s <session-id>

# List all sessions
opencode session list
```

## Project Structure

```
.devcontainer/
  ├── Dockerfile          # Container image definition
  ├── devcontainer.json  # Devcontainer config
  ├── setup_devcontainer.sh
  ├── launch_opencode.sh
  └── ...
.vscode/
  └── tasks.json         # VS Code tasks for opencode
```

## License

GNU General Public License v3 — See [LICENSE](./LICENSE) for details.
