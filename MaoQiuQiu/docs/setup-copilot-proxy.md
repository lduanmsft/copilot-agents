# 如何安装 setup-copilot-proxy Skill

这个 Claude Code skill 会自动配置 copilot-api 代理 + PM2 进程管理，让 Claude Code 通过 GitHub Copilot API 使用 Anthropic 模型（包括 1M 上下文窗口）。

## 前提条件

- Windows 10/11
- Node.js v18+
- Git Bash / MSYS2（Claude Code on Windows 的 shell 环境）
- 有效的 GitHub Copilot 许可证（individual / business / enterprise）
- 已安装 Claude Code

## 安装步骤

### 第 1 步：创建 skill 目录

```bash
mkdir -p ~/.claude/commands/setup-copilot-proxy
```

### 第 2 步：创建 SKILL.md

将下面的内容保存到 `~/.claude/commands/setup-copilot-proxy/SKILL.md`：

<details>
<summary>点击展开 SKILL.md 完整内容</summary>

```markdown
---
name: setup-copilot-proxy
description: Set up copilot-api proxy with PM2 management for Claude Code on Windows. Handles installation, PM2 config, pidusage fix for Windows 11, and Claude Code settings.
argument-hint: [account-type]
disable-model-invocation: true
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, AskUserQuestion
---

# Setup Copilot API Proxy with PM2 Management

This skill sets up the [copilot-api-js](https://github.com/puxu-msft/copilot-api-js) proxy as a PM2-managed service, enabling Claude Code to use GitHub Copilot's API with Anthropic models (including 1M context window variants).

Account type argument: `$ARGUMENTS` (defaults to `enterprise` if not provided).

## Prerequisites Check

Before starting, verify these are available:
1. **Node.js** — `node --version` (v18+ required)
2. **npm** — `npm --version`
3. **Git Bash / MSYS2** — the shell environment for Claude Code on Windows
4. **GitHub Copilot** — user must have an active Copilot license (individual, business, or enterprise)

## Step 1: Install Global Dependencies

```bash
npm install -g @hsupu/copilot-api pm2
```

Verify installation:
```bash
copilot-api --version
pm2 --version
```

## Step 2: Authenticate with GitHub

Run the auth flow (requires interactive browser login):
```bash
copilot-api auth
```

This saves the GitHub token to `~/.local/share/copilot-api/github_token`.

If the token already exists, ask the user whether to re-authenticate or skip.

## Step 3: Create PM2 Ecosystem Config

Determine the path to copilot-api's `main.mjs` entry point. The location depends on the package manager:

- **Volta**: `$LOCALAPPDATA/Volta/tools/image/packages/@hsupu/copilot-api/node_modules/@hsupu/copilot-api/dist/main.mjs`
- **Standard npm**: `$(npm root -g)/@hsupu/copilot-api/dist/main.mjs`

Verify the path exists before writing the config.

**IMPORTANT**: Do NOT use `npx` as the pm2 script on Windows — it causes `spawn EINVAL` errors. Always point pm2 directly at the `main.mjs` file.

Write `~/.local/share/copilot-api/ecosystem.config.cjs`:

```javascript
const path = require("path");
const os = require("os");

const copilotDir = path.join(os.homedir(), ".local", "share", "copilot-api");
const copilotMain = "<RESOLVED_PATH_TO_MAIN_MJS>";  // Replace with actual path

module.exports = {
  apps: [
    {
      name: "copilot-api",
      script: copilotMain,
      args: ["start", "-a", "<ACCOUNT_TYPE>"],  // enterprise, business, or individual
      cwd: copilotDir,
      autorestart: true,
      max_restarts: 10,
      restart_delay: 5000,
      log_date_format: "YYYY-MM-DD HH:mm:ss",
      merge_logs: true,
      env: {
        NODE_ENV: "production",
      },
    },
  ],
};
```

## Step 4: Fix pidusage for Windows 11

PM2's bundled `pidusage` v3.x uses `wmic` for process metrics, but `wmic` is removed in Windows 11. This causes `spawn wmic ENOENT` errors and pm2 shows `0%` CPU / `0b` memory.

**Fix**: Update `pidusage` to v4.x which falls back to PowerShell (`gwmi`) when `wmic` is unavailable.

Steps:
1. Find pm2's pidusage locations:
   ```bash
   # Main pidusage
   <PM2_INSTALL_DIR>/node_modules/pm2/node_modules/pidusage
   # pm2-sysmonit pidusage
   <PM2_INSTALL_DIR>/node_modules/pm2/node_modules/pm2-sysmonit/node_modules/pidusage
   ```
2. Download pidusage v4:
   ```bash
   npm pack pidusage@4.0.1 --pack-destination /tmp
   tar -xzf /tmp/pidusage-4.0.1.tgz -C /tmp
   ```
3. Replace both pidusage directories:
   ```bash
   rm -rf <PM2_PIDUSAGE_PATH>
   cp -r /tmp/package <PM2_PIDUSAGE_PATH>
   ```
4. Do the same for `pm2-sysmonit/node_modules/pidusage` if it exists.
5. Restart pm2 daemon: `pm2 update`

**Verify** the fix:
```bash
node -e "const p = require('<PM2_PIDUSAGE_PATH>'); p(process.pid, (err, stats) => { console.log(err, stats); });"
```
Should show memory/cpu stats, not a `wmic ENOENT` error.

**Note**: This patch is overwritten when pm2 is updated. Re-apply after `npm install -g pm2@latest`.

## Step 5: Install PM2 Log Rotation

```bash
pm2 install pm2-logrotate
pm2 set pm2-logrotate:max_size 10M
pm2 set pm2-logrotate:retain 5
pm2 set pm2-logrotate:compress true
```

## Step 6: Configure Claude Code Settings

Write `~/.claude/settings.json` (merge with existing if present):

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "http://localhost:4141",
    "ANTHROPIC_AUTH_TOKEN": "anything",
    "ANTHROPIC_MODEL": "claude-opus-4.6-1m[1m]",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "claude-haiku-4.5",
    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC": "1",
    "CLAUDE_CODE_ENABLE_TELEMETRY": "0"
  },
  "model": "opus[1m]"
}
```

**Key settings explained**:
- `ANTHROPIC_BASE_URL`: Points to the local proxy
- `ANTHROPIC_AUTH_TOKEN`: Any non-empty string (proxy handles real auth)
- `ANTHROPIC_MODEL`: The 1M context window Opus model
- `model`: Short model selector name with 1M context bracket notation

**IMPORTANT**: Preserve any existing settings (permissions, plugins, etc.) when merging.

## Step 7: Start the Service

If port 4141 is already in use (from a manual copilot-api process), the user must stop it first.

```bash
pm2 start ~/.local/share/copilot-api/ecosystem.config.cjs
pm2 save
```

Verify:
```bash
pm2 status
curl -s http://localhost:4141/health
```

Health check should return: `{"status":"healthy","checks":{"copilotToken":true,"githubToken":true,"models":true}}`

## Step 8: Verify End-to-End

1. `pm2 status` — copilot-api shows `online` with memory stats
2. `curl http://localhost:4141/health` — returns healthy
3. `pm2 logs copilot-api --lines 5 --nostream` — shows startup logs with model list

## PM2 Quick Reference

| Command | Description |
|---|---|
| `pm2 start copilot-api` | Start (after first registration) |
| `pm2 stop copilot-api` | Stop |
| `pm2 restart copilot-api` | Restart |
| `pm2 status` | Show status with CPU/memory |
| `pm2 logs copilot-api` | Tail logs |
| `pm2 logs copilot-api --lines N --nostream` | Show last N log lines |
| `pm2 reset copilot-api` | Reset restart counter |
| `pm2 save` | Save process list for resurrection |
| `pm2 update` | Restart pm2 daemon |
| `copilot-api auth` | Re-authenticate GitHub token |
| `copilot-api check-usage -a enterprise` | Check Copilot quota |

## Model Name Mapping Reference

The proxy normalizes model names as follows:

| Input (from Claude Code) | Proxy resolves to | Sent to Copilot API |
|---|---|---|
| `opus` | `claude-opus-4.6` | `claude-opus-4.6` |
| `opus[1m]` | `claude-opus-4.6-1m` | `claude-opus-4.6-1m` |
| `claude-opus-4-6` | `claude-opus-4.6` | `claude-opus-4.6` |
| `claude-opus-4-6[1m]` | `claude-opus-4.6-1m` | `claude-opus-4.6-1m` |
| `sonnet` | `claude-sonnet-4.6` | `claude-sonnet-4.6` |
| `haiku` | `claude-haiku-4.5` | `claude-haiku-4.5` |

Custom overrides can be configured in `~/.local/share/copilot-api/config.yaml` under `model_overrides`.

## Troubleshooting

- **`EADDRINUSE`**: Port 4141 already in use. Kill the existing process first.
- **`spawn wmic ENOENT`**: pidusage fix not applied. Re-run Step 4.
- **pm2 shows 0% CPU / 0b memory**: Same as above — pidusage needs updating.
- **Health check fails**: Check `pm2 logs copilot-api` for errors. Common: expired GitHub token (re-run `copilot-api auth` then `pm2 restart copilot-api`).
- **pm2 update resets pidusage**: Re-apply Step 4 after any pm2 upgrade.
```

</details>

### 第 3 步：验证 skill 已注册

重启 Claude Code，然后输入：

```
/setup-copilot-proxy
```

或带参数：

```
/setup-copilot-proxy enterprise
```

Claude Code 会自动识别 `~/.claude/commands/` 下的 skill 并执行。

## 工作原理

```
Claude Code
  → localhost:4141 (copilot-api 代理, PM2 管理)
    → GitHub Copilot API
      → Anthropic 模型 (Opus/Sonnet/Haiku, 支持 1M 上下文)
```

## 注意事项

- 此 skill 仅适用于 **Windows** 环境（含 Windows 11 的 pidusage 修复）
- 需要有效的 **GitHub Copilot 许可证**
- Step 2 中的 GitHub 认证需要**浏览器交互**，无法全自动完成
- Windows 11 上 PM2 的 pidusage 补丁在 `npm install -g pm2@latest` 后需要重新应用
- `settings.json` 修改会与现有配置合并，不会覆盖已有的 permissions 等设置
