"""Provision Langfuse score configs and annotation queues for diagnostic review."""

from __future__ import annotations

import argparse
import os
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal, Protocol, cast

from dotenv import load_dotenv
from langfuse.api import LangfuseAPI
from langfuse.api.commons import ConfigCategory, ScoreConfigDataType


ScoreConfigType = Literal["BOOLEAN", "CATEGORICAL", "TEXT", "NUMERIC"]


@dataclass(frozen=True)
class ScoreConfigSpec:
    name: str
    data_type: ScoreConfigType
    description: str
    category_labels: tuple[str, ...] = ()


@dataclass(frozen=True)
class AnnotationProfile:
    key: str
    default_queue_name: str
    description: str
    score_configs: tuple[ScoreConfigSpec, ...]


@dataclass(frozen=True)
class ProvisionResult:
    profile: AnnotationProfile
    score_configs: tuple[Any, ...]
    annotation_queue: Any | None


class _ScoreConfigsClient(Protocol):
    def get(self, *, page: int | None = None, limit: int | None = None) -> Any: ...

    def create(self, **kwargs: object) -> Any: ...


class _AnnotationQueuesClient(Protocol):
    def list_queues(
        self, *, page: int | None = None, limit: int | None = None
    ) -> Any: ...

    def create_queue(self, **kwargs: object) -> Any: ...


class _LangfuseApiClient(Protocol):
    @property
    def score_configs(self) -> _ScoreConfigsClient: ...

    @property
    def annotation_queues(self) -> _AnnotationQueuesClient: ...


class ProvisioningError(RuntimeError):
    """Raised when the current Langfuse project has incompatible annotation setup."""


TRIAGE_BINARY_PROFILE = AnnotationProfile(
    key="triage_binary",
    default_queue_name="near-v1-diagnostic-triage",
    description=(
        "First-pass near-v1 diagnostic triage. Use this queue to mark whether a "
        "trace is good enough or should continue into deeper diagnostic review."
    ),
    score_configs=(
        ScoreConfigSpec(
            name="triage_outcome",
            data_type="CATEGORICAL",
            category_labels=("good", "bad"),
            description="First-pass binary quality triage: good or bad.",
        ),
    ),
)

_TRIAGE_OUTCOME_SCORE_CONFIG = TRIAGE_BINARY_PROFILE.score_configs[0]


_FAILURE_MECHANISM_LABELS = (
    "tool_routing_error",
    "evidence_synthesis_limit",
    "source_coverage_gap",
    "overreach_vs_abstain",
    "multi_entity_overload",
    "none",
)


DIAGNOSTIC_V1_PROFILE = AnnotationProfile(
    key="diagnostic_v1",
    default_queue_name="near-v1-diagnostic-review-v1",
    description=(
        "Full near-v1 diagnostic review schema. Use after triage to capture "
        "observed outcome, prompt alignment, failure mechanism, and tuning lever."
    ),
    score_configs=(
        ScoreConfigSpec(
            name="observed_outcome",
            data_type="CATEGORICAL",
            category_labels=(
                "strong_answer",
                "acceptable_answer",
                "partial_answer",
                "failed_cleanly",
                "failed_with_overreach",
            ),
            description="Reviewer-observed answer outcome.",
        ),
        ScoreConfigSpec(
            name="observed_alignment_to_prompt",
            data_type="CATEGORICAL",
            category_labels=("high", "medium", "low"),
            description="How well the answer follows the prompt and constraints.",
        ),
        ScoreConfigSpec(
            name="review_confidence",
            data_type="CATEGORICAL",
            category_labels=("high", "medium", "low"),
            description="Reviewer confidence in the diagnostic judgment.",
        ),
        ScoreConfigSpec(
            name="review_comment",
            data_type="TEXT",
            description="Short reviewer rationale for the observed outcome.",
        ),
        ScoreConfigSpec(
            name="observed_primary_failure_mechanism",
            data_type="CATEGORICAL",
            category_labels=_FAILURE_MECHANISM_LABELS,
            description="Primary reviewer-observed failure mechanism.",
        ),
        ScoreConfigSpec(
            name="obs_secondary_failure_mechanism",
            data_type="CATEGORICAL",
            category_labels=_FAILURE_MECHANISM_LABELS,
            description="Optional secondary reviewer-observed failure mechanism.",
        ),
        ScoreConfigSpec(
            name="observed_tuning_lever",
            data_type="CATEGORICAL",
            category_labels=(
                "none",
                "max_tool_calls",
                "tool_description",
                "tavily_sources",
                "prompt",
            ),
            description="Likely tuning lever suggested by the trace review.",
        ),
        ScoreConfigSpec(
            name="needs_followup",
            data_type="BOOLEAN",
            description="Whether this trace should remain on the follow-up list.",
        ),
        ScoreConfigSpec(
            name="followup_note",
            data_type="TEXT",
            description="Optional follow-up context for later analysis.",
        ),
    ),
)


DIAGNOSTIC_TRIAGE_V1_PROFILE = AnnotationProfile(
    key="diagnostic_triage_v1",
    default_queue_name="near-v1-diagnostic-review-v1",
    description=(
        "Single-queue near-v1 diagnostic review schema. Start with "
        "triage_outcome=good/bad, then fill the full diagnostic fields only for "
        "traces that need deeper review."
    ),
    score_configs=(
        _TRIAGE_OUTCOME_SCORE_CONFIG,
        *DIAGNOSTIC_V1_PROFILE.score_configs,
    ),
)


PROFILES = {
    DIAGNOSTIC_TRIAGE_V1_PROFILE.key: DIAGNOSTIC_TRIAGE_V1_PROFILE,
    TRIAGE_BINARY_PROFILE.key: TRIAGE_BINARY_PROFILE,
    DIAGNOSTIC_V1_PROFILE.key: DIAGNOSTIC_V1_PROFILE,
}


def provision_annotation_setup(
    *,
    client: _LangfuseApiClient,
    profile: AnnotationProfile,
    queue_name: str | None = None,
    create_queue: bool = True,
) -> ProvisionResult:
    existing_configs = _list_score_configs(client)
    provisioned_configs = tuple(
        _get_or_create_score_config(
            client=client,
            existing_configs=existing_configs,
            spec=spec,
        )
        for spec in profile.score_configs
    )

    annotation_queue = None
    if create_queue:
        annotation_queue = _get_or_create_annotation_queue(
            client=client,
            queue_name=queue_name or profile.default_queue_name,
            description=profile.description,
            score_config_ids=[config.id for config in provisioned_configs],
        )

    return ProvisionResult(
        profile=profile,
        score_configs=provisioned_configs,
        annotation_queue=annotation_queue,
    )


def build_langfuse_api_from_env() -> LangfuseAPI:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    base_url = (
        os.environ.get("LANGFUSE_BASE_URL")
        or os.environ.get("LANGFUSE_HOST")
        or "https://cloud.langfuse.com"
    )
    if not public_key or not secret_key:
        raise ProvisioningError(
            "LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY must be set in backend/.env"
        )

    return LangfuseAPI(
        base_url=base_url,
        x_langfuse_public_key=public_key,
        x_langfuse_sdk_name="finlab-x-diagnostic-setup",
        username=public_key,
        password=secret_key,
    )


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Provision Langfuse score configs and annotation queues"
    )
    parser.add_argument(
        "--profile",
        choices=[*PROFILES.keys(), "all"],
        default=DIAGNOSTIC_TRIAGE_V1_PROFILE.key,
        help="Annotation profile to provision",
    )
    parser.add_argument(
        "--queue-name",
        help="Queue name override. Only valid when provisioning a single profile.",
    )
    parser.add_argument(
        "--score-configs-only",
        action="store_true",
        help="Create/reuse score configs but skip annotation queue creation.",
    )
    args = parser.parse_args(argv)

    if args.profile == "all" and args.queue_name:
        parser.error("--queue-name can only be used with a single --profile")

    client = cast(_LangfuseApiClient, build_langfuse_api_from_env())
    selected_profiles = _select_profiles(args.profile)

    for profile in selected_profiles:
        result = provision_annotation_setup(
            client=client,
            profile=profile,
            queue_name=args.queue_name,
            create_queue=not args.score_configs_only,
        )
        print(f"Profile: {result.profile.key}")
        for config in result.score_configs:
            print(f"  score_config: {config.name} ({config.data_type}) id={config.id}")
        if result.annotation_queue is not None:
            print(
                "  annotation_queue: "
                f"{result.annotation_queue.name} id={result.annotation_queue.id}"
            )


def _select_profiles(profile_key: str) -> tuple[AnnotationProfile, ...]:
    if profile_key == "all":
        return (DIAGNOSTIC_TRIAGE_V1_PROFILE,)
    return (PROFILES[profile_key],)


def _list_score_configs(client: _LangfuseApiClient) -> list[Any]:
    response = client.score_configs.get(limit=100)
    return list(getattr(response, "data", []))


def _get_or_create_score_config(
    *,
    client: _LangfuseApiClient,
    existing_configs: list[Any],
    spec: ScoreConfigSpec,
) -> Any:
    existing = _find_score_config_by_name(existing_configs, spec.name)
    if existing is not None:
        _validate_existing_score_config(existing, spec)
        return existing

    create_kwargs: dict[str, object] = {
        "name": spec.name,
        "data_type": ScoreConfigDataType(spec.data_type),
        "description": spec.description,
    }
    if spec.data_type == "CATEGORICAL":
        create_kwargs["categories"] = _build_categories(spec.category_labels)

    created = client.score_configs.create(**create_kwargs)
    existing_configs.append(created)
    return created


def _get_or_create_annotation_queue(
    *,
    client: _LangfuseApiClient,
    queue_name: str,
    description: str,
    score_config_ids: list[str],
) -> Any:
    existing = _find_annotation_queue_by_name(client, queue_name)
    if existing is not None:
        existing_ids = set(
            cast(Iterable[str], getattr(existing, "score_config_ids", []))
        )
        missing_ids = [
            config_id for config_id in score_config_ids if config_id not in existing_ids
        ]
        if missing_ids:
            raise ProvisioningError(
                f"Annotation queue '{queue_name}' already exists but is missing "
                f"score config ids: {', '.join(missing_ids)}"
            )
        return existing

    return client.annotation_queues.create_queue(
        name=queue_name,
        description=description,
        score_config_ids=score_config_ids,
    )


def _find_score_config_by_name(existing_configs: list[Any], name: str) -> Any | None:
    for config in existing_configs:
        if getattr(config, "name", None) == name:
            return config
    return None


def _find_annotation_queue_by_name(client: _LangfuseApiClient, name: str) -> Any | None:
    response = client.annotation_queues.list_queues(limit=100)
    for queue in getattr(response, "data", []):
        if getattr(queue, "name", None) == name:
            return queue
    return None


def _validate_existing_score_config(config: Any, spec: ScoreConfigSpec) -> None:
    if getattr(config, "is_archived", False):
        raise ProvisioningError(
            f"Score config '{spec.name}' already exists but is archived"
        )
    actual_type = _normalize_data_type(getattr(config, "data_type", None))
    if actual_type != spec.data_type:
        raise ProvisioningError(
            f"Score config '{spec.name}' already exists with incompatible schema: "
            f"data_type={actual_type}, expected={spec.data_type}"
        )
    if spec.data_type == "CATEGORICAL":
        actual_labels = _category_labels(getattr(config, "categories", None))
        if actual_labels != spec.category_labels:
            raise ProvisioningError(
                f"Score config '{spec.name}' already exists with incompatible schema: "
                f"categories={actual_labels}, expected={spec.category_labels}"
            )


def _normalize_data_type(data_type: object) -> str:
    return str(getattr(data_type, "value", data_type))


def _build_categories(labels: tuple[str, ...]) -> list[ConfigCategory]:
    return [
        ConfigCategory(value=float(len(labels) - index - 1), label=label)
        for index, label in enumerate(labels)
    ]


def _category_labels(categories: object) -> tuple[str, ...]:
    if not categories:
        return ()
    return tuple(
        str(getattr(category, "label", ""))
        for category in cast(Iterable[object], categories)
    )


if __name__ == "__main__":
    main()
