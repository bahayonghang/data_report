import os
from pathlib import Path

# Playwright配置
config = {
    "test_dir": Path(__file__).parent / "tests",
    "timeout": 30000,
    "expect_timeout": 10000,
    "fully_parallel": True,
    "forbid_only": False,
    "retries": 2 if os.getenv("CI") else 0,
    "workers": 4,
    "reporter": [
        ["html", {"output_folder": "test-results/html-report"}],
        ["json", {"output_file": "test-results/results.json"}],
        ["junit", {"output_file": "test-results/junit.xml"}],
    ],
    "use": {
        "base_url": "http://localhost:8000",
        "trace": "on-first-retry",
        "screenshot": "only-on-failure",
        "video": "retain-on-failure",
        "viewport": {"width": 1280, "height": 720},
    },
    "projects": [
        {
            "name": "chromium",
            "use": {"browser_name": "chromium"},
        },
        {
            "name": "firefox",
            "use": {"browser_name": "firefox"},
        },
        {
            "name": "webkit",
            "use": {"browser_name": "webkit"},
        },
        {
            "name": "chromium-mobile",
            "use": {
                "browser_name": "chromium",
                "viewport": {"width": 375, "height": 667},
                "device_scale_factor": 2,
                "is_mobile": True,
                "has_touch": True,
            },
        },
    ],
}

if __name__ == "__main__":
    import json
    print(json.dumps(config, indent=2))