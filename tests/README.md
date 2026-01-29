# VideoVerse 测试套件

## 运行测试

### 运行所有测试

```bash
pytest
```

### 仅运行单元测试

```bash
pytest -m unit
```

### 仅运行集成测试

```bash
pytest -m integration
```

### 跳过慢速测试

```bash
pytest -m "not slow"
```

### 跳过需要 GPU 的测试

```bash
pytest -m "not gpu"
```

### 运行带覆盖率的测试

```bash
pytest --cov=core --cov-report=html
```

### 运行特定测试文件

```bash
pytest tests/unit/test_config.py -v
```

## 测试组织

```
tests/
├── unit/              # 快速、隔离的单元测试
│   ├── test_config.py
│   ├── test_paths/
│   ├── test_pipeline/
│   ├── test_utils/
│   ├── test_steps/
│   └── test_tts/
├── integration/       # 较慢的多组件测试
│   └── test_pipeline.py
├── fixtures/          # 测试数据
│   ├── audio/
│   ├── video/
│   └── models/
└── conftest.py        # 共享 pytest fixtures
```

## 测试标记

| 标记 | 描述 | 示例 |
|------|------|------|
| `unit` | 快速单元测试（每个 < 1 秒） | 配置测试、路径管理测试 |
| `integration` | 测试组件交互的集成测试 | 端到端流水线测试 |
| `slow` | 耗时 > 10 秒的测试 | 模型加载、实际处理 |
| `gpu` | 需要 CUDA GPU 的测试 | WhisperX GPU 测试 |
| `llm` | 需要真实 LLM API 密钥的测试 | 翻译步骤测试 |

## 测试数据

将测试 fixtures 放置在：

- `tests/fixtures/audio/` - 音频样本
- `tests/fixtures/video/` - 视频样本
- `tests/fixtures/models/` - 模拟模型输出

## CI/CD

在 CI 环境中，测试运行时使用：

- `-m "not gpu and not slow"` - 跳过 GPU 和慢速测试
- `--cov=core` - 生成覆盖率报告
- `--strict-markers` - 确保所有标记都已定义

## 开发工作流

### 添加新测试

1. 在相应的 `tests/unit/` 或 `tests/integration/` 目录下创建测试文件
2. 使用适当的标记装饰测试（`@pytest.mark.unit`, `@pytest.mark.slow` 等）
3. 使用 `conftest.py` 中的共享 fixtures

### 测试覆盖率目标

- 核心模块（config, paths, pipeline）: > 90%
- 工具模块（utils）: > 80%
- 步骤模块（steps）: > 70%

### 运行测试前确保

1. 虚拟环境已激活：`.venv\Scripts\activate` (Windows) 或 `source .venv/bin/activate` (Linux/Mac)
2. 依赖已安装：`uv sync`
3. 环境变量已配置（如果运行需要真实 API 的测试）
