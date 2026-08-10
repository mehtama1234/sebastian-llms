from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from arch_adv_2026.decision_stack_validate import validate_decision_stack_artifacts


def test_validate_decision_stack_artifacts_accepts_consistent_mismatch_state() -> None:
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": ["kv_sharing"],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {
                "variant": "kv_sharing",
                "priority": 2,
            },
            {
                "variant": "compressed_attention",
                "priority": 0,
            },
            {
                "variant": "history_compression",
                "priority": 0,
            },
            {
                "variant": "attention_budgeting",
                "priority": 0,
            },
        ],
    }
    final_memo = {
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": ["kv_sharing"],
        "exploratory_variants": ["history_compression"],
        "drop_for_now_variants": ["attention_budgeting"],
        "summary_lines": [
            "Focused follow-up review priority variants: `kv_sharing`.",
        ],
        "evidence_matrix": [
            {"variant": "compressed_attention"},
            {"variant": "kv_sharing"},
            {"variant": "history_compression"},
            {"variant": "attention_budgeting"},
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": ["kv_sharing"],
                "raw_mismatch_variants": ["attention_budgeting"],
                "resolved_mismatch_variants": ["attention_budgeting"],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    assert validate_decision_stack_artifacts(audit, review_plan, final_memo) == []


def test_validate_decision_stack_artifacts_flags_missing_unresolved_summary_line() -> None:
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": ["attention_budgeting"],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        }
    }
    final_memo = {
        "summary_lines": [
            "Focused follow-up review priority variants: `attention_budgeting`.",
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": ["attention_budgeting"],
                "raw_mismatch_variants": ["attention_budgeting"],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": ["attention_budgeting"],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "final memo summary is missing the active unresolved mismatch line" in errors


def test_decision_stack_validate_cli_writes_failures_to_stderr(tmp_path: Path) -> None:
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": ["attention_budgeting"],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        }
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": ["attention_budgeting"],
                "raw_mismatch_variants": ["attention_budgeting"],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": ["attention_budgeting"],
            }
        },
    }

    audit_path = tmp_path / "audit.json"
    review_path = tmp_path / "review.json"
    memo_path = tmp_path / "memo.json"
    audit_path.write_text(json.dumps(audit), encoding="utf-8")
    review_path.write_text(json.dumps(review_plan), encoding="utf-8")
    memo_path.write_text(json.dumps(final_memo), encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "arch_adv_2026.decision_stack_validate",
            "--audit",
            str(audit_path),
            "--review-plan",
            str(review_path),
            "--final-memo",
            str(memo_path),
        ],
        cwd=tmp_path.parent,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    assert "missing the active unresolved mismatch line" in result.stderr
    assert result.stdout == ""


def test_validate_decision_stack_artifacts_flags_bad_mismatch_partition() -> None:
    audit = {
        "summary": {
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": ["attention_budgeting"],
            "unresolved_mismatch_variants": ["attention_budgeting"],
        },
        "rows": [],
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": ["attention_budgeting"],
                "resolved_mismatch_variants": ["attention_budgeting"],
                "unresolved_mismatch_variants": ["attention_budgeting"],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "audit resolved and unresolved mismatches must be disjoint" in errors


def test_validate_decision_stack_artifacts_flags_priority_summary_drift() -> None:
    audit = {
        "summary": {
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {
                "variant": "kv_sharing",
                "priority": 2,
            }
        ],
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "review plan priority variants do not match the rows marked priority >= 2" in errors


def test_validate_decision_stack_artifacts_flags_bad_audit_counts() -> None:
    audit = {
        "summary": {
            "variant_count": 2,
            "mismatch_count": 2,
            "mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_count": 0,
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_count": 2,
            "unresolved_mismatch_variants": ["attention_budgeting"],
        },
        "rows": [{"variant": "attention_budgeting"}],
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": ["attention_budgeting"],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": ["attention_budgeting"],
            "review_count": 0,
        },
        "rows": [],
    }
    final_memo = {
        "summary_lines": [
            "Active unresolved decision mismatches still needing review: `attention_budgeting`.",
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": ["attention_budgeting"],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": ["attention_budgeting"],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "audit variant_count does not match the number of audit rows" in errors
    assert "audit mismatch_count does not match mismatch_variants" in errors
    assert "audit unresolved_mismatch_count does not match unresolved_mismatch_variants" in errors


def test_validate_decision_stack_artifacts_flags_bad_review_count() -> None:
    audit = {
        "summary": {
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 0,
        },
        "rows": [
            {
                "variant": "compressed_attention",
                "priority": 0,
            }
        ],
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "review plan review_count does not match the number of review rows" in errors


def test_validate_decision_stack_artifacts_flags_duplicate_audit_rows() -> None:
    audit = {
        "summary": {
            "variant_count": 2,
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {"variant": "compressed_attention"},
            {"variant": "compressed_attention"},
        ],
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 0,
        },
        "rows": [],
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "audit rows contain duplicate variant entries" in errors


def test_validate_decision_stack_artifacts_flags_duplicate_review_rows() -> None:
    audit = {
        "summary": {
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 2,
        },
        "rows": [
            {"variant": "kv_sharing", "priority": 1},
            {"variant": "kv_sharing", "priority": 1},
        ],
    }
    final_memo = {
        "summary_lines": [],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "review plan rows contain duplicate variant entries" in errors


def test_validate_decision_stack_artifacts_flags_duplicate_final_memo_matrix_rows() -> None:
    audit = {
        "summary": {
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 0,
        },
        "rows": [],
    }
    final_memo = {
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": [],
        "exploratory_variants": [],
        "drop_for_now_variants": [],
        "summary_lines": [],
        "evidence_matrix": [
            {"variant": "compressed_attention"},
            {"variant": "compressed_attention"},
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "final memo evidence_matrix contains duplicate variant entries" in errors


def test_validate_decision_stack_artifacts_flags_final_memo_partition_drift() -> None:
    audit = {
        "summary": {
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        }
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 0,
        },
        "rows": [],
    }
    final_memo = {
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": ["kv_sharing"],
        "exploratory_variants": [],
        "drop_for_now_variants": [],
        "summary_lines": [],
        "evidence_matrix": [
            {"variant": "compressed_attention"},
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "final memo evidence_matrix variants do not match the carry-forward partition" in errors


def test_validate_decision_stack_artifacts_flags_final_memo_variant_universe_drift() -> None:
    audit = {
        "summary": {
            "variant_count": 2,
            "mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
        },
        "rows": [
            {"variant": "compressed_attention"},
            {"variant": "kv_sharing"},
        ],
    }
    review_plan = {
        "summary": {
            "priority_variants": [],
            "raw_mismatch_variants": [],
            "resolved_mismatch_variants": [],
            "unresolved_mismatch_variants": [],
            "review_count": 2,
        },
        "rows": [
            {"variant": "compressed_attention", "priority": 0},
            {"variant": "kv_sharing", "priority": 0},
        ],
    }
    final_memo = {
        "default_carry_forward_variant": "compressed_attention",
        "secondary_variants": [],
        "exploratory_variants": [],
        "drop_for_now_variants": [],
        "summary_lines": [],
        "evidence_matrix": [
            {"variant": "compressed_attention"},
        ],
        "evidence": {
            "review_summary": {
                "priority_variants": [],
                "raw_mismatch_variants": [],
                "resolved_mismatch_variants": [],
                "unresolved_mismatch_variants": [],
            }
        },
    }

    errors = validate_decision_stack_artifacts(audit, review_plan, final_memo)
    assert "final memo variants do not match the audit row variants" in errors
    assert "final memo variants do not match the review-plan row variants" in errors
