from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import cast

import pytest

from backend.evals.diagnostic.langfuse_annotation_setup import (
    DIAGNOSTIC_V1_PROFILE,
    TRIAGE_BINARY_PROFILE,
    ProvisioningError,
    provision_annotation_setup,
)


class _FakeScoreConfigsClient:
    def __init__(self, existing: list[SimpleNamespace] | None = None) -> None:
        self.existing = existing or []
        self.created: list[dict[str, object]] = []

    def get(
        self, *, page: int | None = None, limit: int | None = None
    ) -> SimpleNamespace:
        return SimpleNamespace(data=self.existing)

    def create(self, **kwargs: object) -> SimpleNamespace:
        created = SimpleNamespace(
            id=f"score-config-{len(self.created) + 1}",
            name=kwargs["name"],
            data_type=kwargs["data_type"],
            categories=kwargs.get("categories"),
            min_value=kwargs.get("min_value"),
            max_value=kwargs.get("max_value"),
            is_archived=False,
        )
        self.created.append(kwargs)
        self.existing.append(created)
        return created


class _FakeAnnotationQueuesClient:
    def __init__(self, existing: list[SimpleNamespace] | None = None) -> None:
        self.existing = existing or []
        self.created: list[dict[str, object]] = []

    def list_queues(
        self, *, page: int | None = None, limit: int | None = None
    ) -> SimpleNamespace:
        return SimpleNamespace(data=self.existing)

    def create_queue(self, **kwargs: object) -> SimpleNamespace:
        created = SimpleNamespace(
            id=f"queue-{len(self.created) + 1}",
            name=kwargs["name"],
            score_config_ids=list(cast(Iterable[str], kwargs["score_config_ids"])),
            description=kwargs.get("description"),
        )
        self.created.append(kwargs)
        self.existing.append(created)
        return created


class _FakeLangfuseApi:
    def __init__(
        self,
        *,
        score_configs: list[SimpleNamespace] | None = None,
        queues: list[SimpleNamespace] | None = None,
    ) -> None:
        self.score_configs = _FakeScoreConfigsClient(score_configs)
        self.annotation_queues = _FakeAnnotationQueuesClient(queues)


def test_triage_binary_profile_is_single_good_bad_score() -> None:
    assert TRIAGE_BINARY_PROFILE.key == "triage_binary"
    assert [spec.name for spec in TRIAGE_BINARY_PROFILE.score_configs] == [
        "triage_outcome"
    ]
    assert TRIAGE_BINARY_PROFILE.score_configs[0].data_type == "CATEGORICAL"
    assert TRIAGE_BINARY_PROFILE.score_configs[0].category_labels == ("good", "bad")


def test_diagnostic_v1_profile_matches_joiner_columns() -> None:
    assert [spec.name for spec in DIAGNOSTIC_V1_PROFILE.score_configs] == [
        "observed_outcome",
        "observed_alignment_to_prompt",
        "review_confidence",
        "review_comment",
        "observed_primary_failure_mechanism",
        "observed_secondary_failure_mechanism",
        "observed_tuning_lever",
        "needs_followup",
        "followup_note",
    ]


def test_provision_annotation_setup_creates_configs_and_queue() -> None:
    api = _FakeLangfuseApi()

    result = provision_annotation_setup(
        client=api,
        profile=TRIAGE_BINARY_PROFILE,
        queue_name="near-v1-triage",
    )

    assert [config.name for config in result.score_configs] == ["triage_outcome"]
    assert result.annotation_queue is not None
    assert result.annotation_queue.name == "near-v1-triage"
    assert api.annotation_queues.created[0]["score_config_ids"] == ["score-config-1"]


def test_provision_annotation_setup_reuses_existing_configs_and_queue() -> None:
    existing_config = SimpleNamespace(
        id="existing-config",
        name="triage_outcome",
        data_type="CATEGORICAL",
        categories=[
            SimpleNamespace(label="good", value=1.0),
            SimpleNamespace(label="bad", value=0.0),
        ],
        is_archived=False,
    )
    existing_queue = SimpleNamespace(
        id="existing-queue",
        name="near-v1-triage",
        score_config_ids=["existing-config"],
    )
    api = _FakeLangfuseApi(score_configs=[existing_config], queues=[existing_queue])

    result = provision_annotation_setup(
        client=api,
        profile=TRIAGE_BINARY_PROFILE,
        queue_name="near-v1-triage",
    )

    assert result.score_configs[0].id == "existing-config"
    assert result.annotation_queue is not None
    assert result.annotation_queue.id == "existing-queue"
    assert api.score_configs.created == []
    assert api.annotation_queues.created == []


def test_provision_annotation_setup_rejects_mismatched_existing_config() -> None:
    existing_config = SimpleNamespace(
        id="bad-config",
        name="triage_outcome",
        data_type="BOOLEAN",
        categories=None,
        is_archived=False,
    )
    api = _FakeLangfuseApi(score_configs=[existing_config])

    with pytest.raises(
        ProvisioningError, match="already exists with incompatible schema"
    ):
        provision_annotation_setup(
            client=api,
            profile=TRIAGE_BINARY_PROFILE,
            queue_name="near-v1-triage",
        )
