from backend.app.skills.loader import PromptAssetLoader


def test_list_skill_assets_includes_packaged_assets():
    loader = PromptAssetLoader()
    assert loader.list_skill_assets() == [
        "cxif-bmi-coach",
        "precoil-emt",
        "soc-radar",
        "testing-business-ideas",
    ]


def test_load_skill_asset_reads_frontmatter_and_body():
    loader = PromptAssetLoader()
    asset = loader.load_skill_asset("soc-radar")

    assert asset.kind == "skill"
    assert asset.name == "soc-radar"
    assert "description" in asset.metadata
    assert "# Signals of Change Radar (SOC Radar)" in asset.body


def test_load_agent_asset_supports_agent_md():
    loader = PromptAssetLoader()
    asset = loader.load_skill_asset("precoil-emt")

    assert asset.kind == "agent"
    assert "description" in asset.metadata
    assert "You are a business assumption coach." in asset.body


def test_load_step_prompt_resolves_packaged_prompt_template():
    loader = PromptAssetLoader()
    asset = loader.load_step_prompt("step2_pattern_matcher")

    assert asset.kind == "prompt"
    assert asset.name == "step2_pattern_matcher"
    assert "You are the Step 2 Pattern Reasoner" in asset.body
