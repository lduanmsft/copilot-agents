# 如何安装和配置 EngineeringHub MCP Server (enghub-mcp)

这个指南帮助你在 Copilot CLI 中添加 [EngineeringHub MCP Server](https://github.com/azure-core/enghub-mcp-server-tools)，让 Copilot 可以直接搜索和获取 [eng.ms](https://eng.ms) 上的内容（TSGs、Onboarding 文档、Service 文档等）。

## 前提条件

- **Windows 10/11**
- **Node.js 22.12.0+** — [Download](https://nodejs.org/)
- **VPN 已连接** Microsoft corpnet
- **GitHub CLI** (`gh`) — [Download](https://cli.github.com/)（推荐安装方式需要）
- **已安装 Copilot CLI**

## 安装 enghub-mcp

有三种安装方式，推荐 Option A：

### Option A: GitHub Release（推荐，最简单）

无需 feed 认证，只需 Node.js 和 `gh`：

```powershell
gh release download --repo azure-core/enghub-mcp-server-tools --pattern "azure-core-enghub-mcp.tgz" --output enghub-mcp.tgz --clobber
npm install -g enghub-mcp.tgz
del enghub-mcp.tgz
```

> 需要先 `gh auth login` 并且账号能访问 `azure-core` EMU 组织。
> 如果你的 `gh` 只登录了 `github.com` 而非 EMU，此方式无法使用，请用 Option C。

### Option B: 从源码安装

需要 [EngineeringHub-Users](https://ms.portal.azure.com/#view/Microsoft_AAD_IAM/GroupDetailsMenuBlade/~/Overview/groupId/9513cf81-e598-4c4c-8a66-7c3fe3cd2cf5/menuId/) Azure AD 组成员身份。

```powershell
git clone https://github.com/azure-core/enghub-mcp-server-tools.git
cd enghub-mcp-server-tools
npm run auth
npm install
npm run build
npm link
```

### Option C: Azure Artifacts（Microsoft 内部 feed）

需要与 Option B 相同的组成员身份。

```powershell
# 1. 安装 vsts-npm-auth
npm install -g vsts-npm-auth

# 2. 在用户 .npmrc 中添加 scoped registry
Add-Content "$env:USERPROFILE\.npmrc" "`n@azure-core:registry=https://msazure.pkgs.visualstudio.com/One/_packaging/PIE-AECore-EngineeringHub-Consumption/npm/registry/`nalways-auth=true"

# 3. 认证（会弹出浏览器窗口）
vsts-npm-auth -config "$env:USERPROFILE\.npmrc"

# 4. 安装
npm install -g @azure-core/enghub-mcp
```

### 验证安装

```powershell
enghub-mcp --version
```

应返回版本号（如 `1.44.6`）。

## 配置 Copilot CLI

编辑 `~/.copilot/mcp-config.json`，在 `mcpServers` 中添加 `enghub`：

```json
{
  "mcpServers": {
    "enghub": {
      "type": "stdio",
      "command": "enghub-mcp",
      "args": ["start"],
      "tools": ["*"]
    }
  }
}
```

> **注意**：请与你现有的 MCP server 配置合并，不要覆盖已有的 server 条目。

### 限定搜索范围（可选）

如果你只需要搜索 eng.ms 的某个子目录，可以通过 `--search-scope` 参数或环境变量限定：

```json
{
  "enghub": {
    "type": "stdio",
    "command": "enghub-mcp",
    "args": ["start", "--search-scope", "https://eng.ms/docs/cloud-ai-platform/..."],
    "tools": ["*"]
  }
}
```

或使用环境变量：

```json
{
  "enghub": {
    "type": "stdio",
    "command": "enghub-mcp",
    "args": ["start"],
    "env": {
      "ENGHUB_SEARCH_SCOPE": "https://eng.ms/docs/cloud-ai-platform/..."
    },
    "tools": ["*"]
  }
}
```

## 认证

认证在 server 启动时自动进行：

| 平台 | 认证方式 | 说明 |
|------|---------|------|
| **Windows** | WAM (Windows Account Manager) | 自动使用你登录的 Microsoft 账号 |
| **macOS/Linux** | Azure CLI | 需运行一次：`az login --tenant 72f988bf-86f1-41af-91ab-2d7cd011db47 --scope api://engineeringhubprod.ame.gbl/.default` |
| **Headless/SSH** | Device code flow | 先在有浏览器的机器上运行 `enghub-mcp auth` |

Token 缓存在 OS keychain 中并自动刷新。清除凭据：`enghub-mcp logout`

## 重启 Copilot CLI

配置完成后，**重启 Copilot CLI 会话**。在新会话中运行 `/mcp` 或检查 MCP Server 状态，确认 `enghub` 显示为 ✓ Connected。

## 可用工具

安装成功后，Copilot CLI 将获得以下 enghub 工具：

| 工具 | 功能 |
|-----|------|
| **search** | 搜索 EngineeringHub 内容，支持按 service、tags、content types、URL path 过滤 |
| **fetch** | 获取 eng.ms URL 的完整页面内容（markdown 格式） |
| **resolve_service** | 将 service/team/org 名称解析为 ServiceTree GUID |
| **get_node_tree** | 浏览 ServiceTree 层级（Division → Organization → ServiceGroup → TeamGroup → Service） |
| **get_service_nodes** | 列出某个 ServiceTree service 下的所有内容节点（pages、TSGs、docs） |
| **get_source_link** | 获取 eng.ms 文章的源码仓库链接（用于查找/编辑底层 markdown） |

## 常用场景

### 搜索然后获取

```
User: Search EngineeringHub for "IcM endpoints"
→ 返回带 URL 的编号结果列表

User: Fetch https://eng.ms/docs/products/icm/onboarding/endpoints
→ 返回完整页面内容（markdown）
```

### 查找某个 Service 的 TSG

1. `resolve_service` → 获取 serviceId
2. `get_service_nodes` + tags=["TSGs"] → 列出 TSGs
3. `fetch` 任意 TSG URL → 读取完整内容

### 浏览 ServiceTree 层级

1. `get_node_tree`（无参数）→ 列出根级 divisions
2. `get_node_tree` + nodeId → 深入子级
3. `get_service_nodes` → 列出 service 的内容

## CLI 命令参考

| 命令 | 说明 |
|------|------|
| `enghub-mcp start` | 启动 MCP server |
| `enghub-mcp start --search-scope <url>` | 限定搜索范围启动 |
| `enghub-mcp auth` | 交互式认证（用于 headless 环境） |
| `enghub-mcp logout` | 清除缓存的 auth token |
| `enghub-mcp --version` | 显示版本 |

## 升级

重新运行你之前使用的安装命令，然后验证：

```powershell
enghub-mcp --version
```

## 故障排除

| 问题 | 解决方案 |
|------|---------|
| "Unable to connect to EngineeringHub" | 确认 VPN 已连接，尝试在浏览器打开 https://eng.ms |
| "Authentication failed" / token 错误 | **Windows**：自动使用 WAM。**macOS/Linux**：运行 `az login` 命令。尝试 `enghub-mcp logout` 清除缓存 |
| npm E404 — `@azure-core/enghub-mcp` not found | 包不在公共 npm 上，需要配置内部 registry（见 Option C） |
| npm E401 — authentication token invalid | 运行 `vsts-npm-auth -config ~/.npmrc` 重新认证 |
| MCP error -32000: Connection closed | enghub-mcp 未正确安装或启动失败，手动运行 `enghub-mcp start` 查看错误 |
| Empty search results | 检查 VPN 连接，尝试不同的搜索关键词 |
| Copilot CLI 中工具不显示 | 确认 CLI 已全局安装 (`enghub-mcp --version`)，重启 Copilot CLI 会话 |

## 参考资料

- [EngineeringHub MCP Server 仓库](https://github.com/azure-core/enghub-mcp-server-tools)
- [Architecture](https://github.com/azure-core/enghub-mcp-server-tools/blob/main/ARCHITECTURE.md)
- [MCP Server Best Practices](https://github.com/azure-core/enghub-mcp-server-tools/blob/main/MCP-SERVER-BEST-PRACTICES.md)
- [EngineeringHub](https://eng.ms)
