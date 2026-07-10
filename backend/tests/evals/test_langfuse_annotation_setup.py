from __future__ import annotations

from collections.abc import Iterable
from types import SimpleNamespace
from typing import cast

import pytest

from backend.evals.diagnostic.langfuse_annotation_setup import (
    DIAGNOSTIC_TRIAGE_V1_PROFILE,
    AnnotationProfile,
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


def _existing_configs_for(profile: AnnotationProfile) -> list[SimpleNamespace]:
    configs: list[SimpleNamespace] = []
    for index, spec in enumerate(profile.score_configs, start=1):
        categories = None
        if spec.data_type == "CATEGORICAL":
            categories = [
                SimpleNamespace(label=label) for label in spec.category_labels
            ]
        configs.append(
            SimpleNamespace(
                id=f"existing-config-{index}",
                name=spec.name,
                data_type=spec.data_type,
                categories=categories,
                is_archived=False,
            )
        )
    return configs


def test_diagnostic_triage_v1_profile_flattens_triage_and_diagnostic_fields() -> None:
    assert DIAGNOSTIC_TRIAGE_V1_PROFILE.key == "diagnostic_triage_v1"
    assert DIAGNOSTIC_TRIAGE_V1_PROFILE.default_queue_name == (
        "near-v1-diagnostic-review-v1"
    )
    assert [spec.name for spec in DIAGNOSTIC_TRIAGE_V1_PROFILE.score_configs] == [
        "triage_outcome",
        "observed_outcome",
        "observed_alignment_to_prompt",
        "review_confidence",
        "review_comment",
        "observed_primary_failure_mechanism",
        "obs_secondary_failure_mechanism",
        "observed_tuning_lever",
        "needs_followup",
        "followup_note",
    ]


def test_langfuse_score_config_names_fit_platform_limit() -> None:
    for spec in DIAGNOSTIC_TRIAGE_V1_PROFILE.score_configs:
        assert len(spec.name) <= 35


def test_provision_annotation_setup_creates_configs_and_queue() -> None:
    api = _FakeLangfuseApi()

    result = provision_annotation_setup(
        client=api,
        profile=DIAGNOSTIC_TRIAGE_V1_PROFILE,
    )

    assert [config.name for config in result.score_configs] == [
        spec.name for spec in DIAGNOSTIC_TRIAGE_V1_PROFILE.score_configs
    ]
    assert result.annotation_queue is not None
    assert result.annotation_queue.name == "near-v1-diagnostic-review-v1"
    assert api.annotation_queues.created[0]["score_config_ids"] == [
        f"score-config-{index}"
        for index in range(1, len(DIAGNOSTIC_TRIAGE_V1_PROFILE.score_configs) + 1)
    ]


def test_provision_annotation_setup_omits_categories_for_non_categorical_configs() -> (
    None
):
    api = _FakeLangfuseApi()

    provision_annotation_setup(
        client=api,
        profile=DIAGNOSTIC_TRIAGE_V1_PROFILE,
        create_queue=False,
    )

    created_by_name = {config["name"]: config for config in api.score_configs.created}
    assert "categories" in created_by_name["triage_outcome"]
    assert "categories" not in created_by_name["review_comment"]
    assert "categories" not in created_by_name["needs_followup"]
    assert "categories" not in created_by_name["followup_note"]


def test_provision_annotation_setup_reuses_existing_configs_and_queue() -> None:
    existing_configs = _existing_configs_for(DIAGNOSTIC_TRIAGE_V1_PROFILE)
    existing_queue = SimpleNamespace(
        id="existing-queue",
        name="near-v1-diagnostic-review-v1",
        score_config_ids=[config.id for config in existing_configs],
    )
    api = _FakeLangfuseApi(score_configs=existing_configs, queues=[existing_queue])

    result = provision_annotation_setup(
        client=api,
        profile=DIAGNOSTIC_TRIAGE_V1_PROFILE,
    )

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
            profile=DIAGNOSTIC_TRIAGE_V1_PROFILE,
        )
