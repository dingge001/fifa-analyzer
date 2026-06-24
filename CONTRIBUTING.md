# 贡献指南

感谢你对 FIFA Analyzer 项目的关注！我们欢迎各种形式的贡献。

## 🐛 报告 Bug

如果你发现了 Bug，请通过 [GitHub Issues](https://github.com/your-username/fifa-analyzer/issues) 提交，并提供以下信息：

1. **环境信息**：Python 版本、操作系统
2. **复现步骤**：详细的操作步骤
3. **期望行为**：你认为应该发生什么
4. **实际行为**：实际发生了什么
5. **错误日志**：完整的错误信息

## 💡 功能建议

欢迎提出新功能建议！提交 Issue 时请说明：

1. 功能描述和使用场景
2. 为什么这个功能对项目有价值
3. 可能的实现思路（可选）

## 🔧 提交代码

### 开发流程

1. Fork 本仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 编写代码和测试
4. 提交更改：`git commit -m 'Add some feature'`
5. 推送分支：`git push origin feature/your-feature`
6. 提交 Pull Request

### 代码规范

- 遵循 PEP 8 编码规范
- 使用中文注释
- 函数和类添加 docstring
- 保持代码简洁，避免过度设计

### 提交信息规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type 类型**：
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 代码重构
- `test`: 测试相关
- `chore`: 构建/工具变更

**示例**：
```
feat(odds): 添加亚盘水位分析功能

- 支持从 ESPN API 获取亚盘数据
- 增加水位解读逻辑
- 更新输出模板

Closes #12
```

## 📊 添加数据源

如果你想添加新的数据源：

1. 在 `scripts/` 下创建新的 Python 脚本
2. 在 `references/data-sources.md` 中添加配置
3. 更新 `SKILL.md` 中的数据获取指南
4. 确保有缓存支持
5. 添加降级策略

## 🧠 优化分析模型

如果你想改进评分模型：

1. 修改 `references/analysis-model.md` 中的算法
2. 调整权重参数时需要说明理由
3. 添加单元测试验证结果

## 📝 文档贡献

文档同样重要！欢迎：

- 修正拼写/语法错误
- 补充使用说明
- 添加示例
- 翻译其他语言版本

## ❓ 需要帮助？

如果你有任何问题，可以：

- 查看 [README.md](README.md)
- 查看现有 Issues
- 在 Issue 中提问

## 🙏 致谢

所有贡献者都会出现在项目的 Contributors 列表中。

感谢你的贡献！🎉
