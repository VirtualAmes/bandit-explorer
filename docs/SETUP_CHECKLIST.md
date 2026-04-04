# Pre-Dinner Setup Checklist

Run through this on the exec's laptop BEFORE dinner. Everything should be
green before you sit down.

## Software

- [ ] **Claude Code installed and authenticated**
  ```bash
  claude --version
  # If not installed: npm install -g @anthropic-ai/claude-code
  # Then: claude (follow auth flow)
  ```

- [ ] **GitHub CLI authenticated**
  ```bash
  gh auth status
  # If not: gh auth login
  ```

- [ ] **uv installed**
  ```bash
  uv --version
  # If not: curl -LsSf https://astral.sh/uv/install.sh | sh
  ```

- [ ] **Python 3.12+ available**
  ```bash
  python3 --version
  # If not: uv python install 3.12
  ```

## Repository

- [ ] **Create the exec's repo**
  ```bash
  gh repo create <exec-name>-bandit-explorer --private --clone
  cd <exec-name>-bandit-explorer
  ```

- [ ] **Copy template files into the repo**
  ```bash
  # From your template copy:
  cp -r /path/to/bandit-explorer-template/{CLAUDE.md,README.md,pyproject.toml,.gitignore,.python-version,.github,docs,src,tests} .
  ```

- [ ] **Install dependencies**
  ```bash
  uv sync --extra dev
  ```

- [ ] **Verify quality tools work**
  ```bash
  uv run ruff --version
  uv run bandit --version
  uv run pytest --version
  ```

- [ ] **Initial commit and push**
  ```bash
  git add -A
  git commit -m "Initial project scaffold"
  git push -u origin main
  ```

- [ ] **Verify GitHub Actions triggered**
  ```bash
  gh run list
  # Should show "Code Quality" workflow, all jobs passing
  ```

- [ ] **Open Claude Code in the repo**
  ```bash
  claude
  # Accept any permission prompts
  # Type /quit to exit — just confirming it starts clean
  ```

## At the Table

- [ ] Laptop open, terminal in the repo directory
- [ ] Browser tab open to `https://github.com/<exec-name>/<repo>/actions`
- [ ] Claude Code ready to launch: just type `claude`
