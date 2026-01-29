"""集成测试 - 测试完整流水线的多个步骤。"""
import shutil
from pathlib import Path

import pytest

from core.pipeline.base import PipelineStep
from core.pipeline.engine import PipelineEngine
from core.pipeline.registry import StepRegistry


@pytest.fixture
def temp_workspace():
    """创建临时工作空间。"""
    temp_dir = Path(__file__).parent.parent / "fixtures" / "temp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    yield temp_dir
    # 清理
    if temp_dir.exists():
        shutil.rmtree(temp_dir)


@pytest.mark.integration
class TestPipelineIntegration:
    """完整流水线的集成测试。"""

    @pytest.mark.asyncio
    async def test_asr_to_nlp_flow_mock(self, temp_workspace):
        """测试 ASR -> NLP 流程（使用模拟）。"""
        # 创建注册表
        registry = StepRegistry()

        # 创建模拟下载步骤
        class MockDownloadStep(PipelineStep):
            @property
            def name(self):
                return "step_01_download"

            async def execute(self, context):
                video_path = temp_workspace / "test_video.mp4"
                video_path.write_text("mock video content")
                context.set("video_path", str(video_path))
                return str(video_path)

        # 创建模拟 ASR 步骤
        class MockASRStep(PipelineStep):
            @property
            def name(self):
                return "step_02_asr"

            @property
            def dependencies(self):
                return ["step_01_download"]

            async def validate(self, context):
                return context.get("video_path") is not None

            async def execute(self, context):
                # 模拟 ASR 输出
                import pandas as pd
                df = pd.DataFrame({
                    "text": ["测试句子1", "测试句子2", "测试句子3"],
                    "start": [0.0, 2.0, 4.0],
                    "end": [1.5, 3.5, 5.5],
                })
                asr_result = temp_workspace / "asr_result.xlsx"
                df.to_excel(asr_result, index=False)
                context.set("asr_result", str(asr_result))
                context.set("asr_dataframe", df)
                return str(asr_result)

        # 创建模拟 NLP 分割步骤
        class MockNLPSplitStep(PipelineStep):
            @property
            def name(self):
                return "step_03_nlp_split"

            @property
            def dependencies(self):
                return ["step_02_asr"]

            async def validate(self, context):
                return context.get("asr_dataframe") is not None

            async def execute(self, context):
                # 模拟 NLP 分割输出
                nlp_result = temp_workspace / "nlp_split.txt"
                nlp_result.write_text("分割后的文本\n测试句子1\n测试句子2\n测试句子3")
                context.set("nlp_split", str(nlp_result))
                return str(nlp_result)

        # 注册步骤
        registry.register("step_01_download", MockDownloadStep())
        registry.register("step_02_asr", MockASRStep())
        registry.register("step_03_nlp_split", MockNLPSplitStep())

        # 运行流水线
        engine = PipelineEngine(registry)
        context = await engine.run(
            steps=["step_03_nlp_split"],  # 将运行 download 和 asr 作为依赖
            video_source="test.mp4",
            source_language="zh",
            target_language="en",
        )

        # 验证
        assert context.has("video_path")
        assert context.has("asr_result")
        assert context.has("asr_dataframe")
        assert context.has("nlp_split")

        # 检查文件存在
        assert Path(context.get("video_path")).exists()
        assert Path(context.get("asr_result")).exists()
        assert Path(context.get("nlp_split")).exists()

    @pytest.mark.asyncio
    async def test_step_dependency_resolution(self):
        """测试步骤依赖解析的正确性。"""
        registry = StepRegistry()

        execution_order = []

        # 创建有复杂依赖关系的步骤
        class StepA(PipelineStep):
            @property
            def name(self):
                return "step_a"

            @property
            def dependencies(self):
                return []

            async def execute(self, context):
                execution_order.append("a")

        class StepB(PipelineStep):
            @property
            def name(self):
                return "step_b"

            @property
            def dependencies(self):
                return ["step_a"]

            async def execute(self, context):
                execution_order.append("b")

        class StepC(PipelineStep):
            @property
            def name(self):
                return "step_c"

            @property
            def dependencies(self):
                return ["step_a", "step_b"]

            async def execute(self, context):
                execution_order.append("c")

        # 注册步骤（乱序注册）
        registry.register("step_c", StepC())
        registry.register("step_a", StepA())
        registry.register("step_b", StepB())

        # 运行流水线
        engine = PipelineEngine(registry)
        await engine.run(
            steps=["step_c"],
            video_source="test.mp4",
            source_language="zh",
            target_language="en",
        )

        # 验证执行顺序：a -> b -> c
        assert execution_order == ["a", "b", "c"]

    @pytest.mark.asyncio
    async def test_error_propagation(self):
        """测试错误在流水线中的传播。"""
        registry = StepRegistry()

        class FailingStep(PipelineStep):
            @property
            def name(self):
                return "failing_step"

            async def execute(self, context):
                raise ValueError("步骤失败")

        class DependentStep(PipelineStep):
            @property
            def name(self):
                return "dependent_step"

            @property
            def dependencies(self):
                return ["failing_step"]

            async def execute(self, context):
                # 不应该到达这里
                raise AssertionError("不应该到达这里")

        registry.register("failing_step", FailingStep())
        registry.register("dependent_step", DependentStep())

        engine = PipelineEngine(registry)

        # 验证错误被传播
        with pytest.raises(ValueError, match="步骤失败"):
            await engine.run(
                steps=["dependent_step"],
                video_source="test.mp4",
                source_language="zh",
                target_language="en",
            )

    @pytest.mark.asyncio
    async def test_context_data_sharing(self):
        """测试步骤间通过 context 共享数据。"""
        registry = StepRegistry()

        class Step1(PipelineStep):
            @property
            def name(self):
                return "step_1"

            async def execute(self, context):
                context.set("shared_data", "from_step_1")
                context.set("number", 42)

        class Step2(PipelineStep):
            @property
            def name(self):
                return "step_2"

            @property
            def dependencies(self):
                return ["step_1"]

            async def execute(self, context):
                # 读取步骤 1 设置的数据
                assert context.get("shared_data") == "from_step_1"
                assert context.get("number") == 42
                # 添加新数据
                context.set("step_2_data", "success")

        class Step3(PipelineStep):
            @property
            def name(self):
                return "step_3"

            @property
            def dependencies(self):
                return ["step_2"]

            async def execute(self, context):
                # 验证所有数据都可用
                assert context.get("shared_data") == "from_step_1"
                assert context.get("number") == 42
                assert context.get("step_2_data") == "success"

        registry.register("step_1", Step1())
        registry.register("step_2", Step2())
        registry.register("step_3", Step3())

        engine = PipelineEngine(registry)
        context = await engine.run(
            steps=["step_3"],
            video_source="test.mp4",
            source_language="zh",
            target_language="en",
        )

        # 最终验证
        assert context.get("shared_data") == "from_step_1"
        assert context.get("number") == 42
        assert context.get("step_2_data") == "success"
