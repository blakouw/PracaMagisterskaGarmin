from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APP = ROOT / "pipeline/18_angular_dashboard_ui/app"


def test_required_frontend_files():
    for relative in [
        "package.json",
        "package-lock.json",
        "tsconfig.json",
        "tsconfig.node.json",
        "vite.config.ts",
        "index.html",
        "src/main.tsx",
        "src/App.tsx",
        "src/styles.css",
        "src/api/dashboardApi.ts",
        "src/api/dashboardTypes.ts",
    ]:
        assert (APP / relative).is_file(), relative

    for component in [
        "AppStatusHeader",
        "PrimaryPwsCard",
        "OptionalAssistedPwsCard",
        "ReadinessCard",
        "PwsComponentsPanel",
        "DeterministicWeightsPanel",
        "LoadMetricsPanel",
        "TimeSeriesPanel",
        "PwsModelComparisonPanel",
        "QualityCoveragePanel",
    ]:
        assert (APP / "src" / "components" / f"{component}.tsx").is_file(), component
