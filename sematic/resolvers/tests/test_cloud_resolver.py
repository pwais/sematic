# Standard Library
from typing import Optional
from unittest import mock

# Third-party
import pytest

# Sematic
import sematic.api_client as api_client
from sematic.api.tests.fixtures import (  # noqa: F401
    mock_no_auth,
    mock_requests,
    test_client,
)
from sematic.calculator import func
from sematic.db.models.resolution import ResolutionKind, ResolutionStatus
from sematic.db.tests.fixtures import test_db  # noqa: F401
from sematic.resolvers.cloud_resolver import CloudResolver
from sematic.tests.fixtures import test_storage, valid_client_version  # noqa: F401


@func
def add(a: float, b: float) -> float:
    return a + b


# TODO: support pipeline args
@func
def pipeline() -> float:
    return add(1, 2)


@mock.patch("socketio.Client.connect")
@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
    return_value={"default": "some_image"},
)
@mock.patch("sematic.api_client.schedule_resolution")
@mock.patch("kubernetes.config.load_kube_config")
@mock_no_auth
def test_simulate_cloud_exec(
    mock_load_kube_config: mock.MagicMock,
    mock_schedule_job: mock.MagicMock,
    mock_get_image: mock.MagicMock,
    mock_socketio,
    mock_requests,  # noqa: F811
    test_db,  # noqa: F811
    test_storage,  # noqa: F811
    valid_client_version,  # noqa: F811
):
    # On the user's machine
    resolver = CloudResolver(detach=True)

    future = pipeline()

    result = future.resolve(resolver)

    assert result == future.id

    mock_schedule_job.assert_called_once_with(future.id)
    assert api_client.get_resolution(future.id).status == ResolutionStatus.CREATED.value
    resolution = api_client.get_resolution(future.id)
    resolution.status = ResolutionStatus.SCHEDULED
    api_client.save_resolution(resolution)
    # In the driver job

    runs, artifacts, edges = api_client.get_graph(future.id)

    driver_resolver = CloudResolver(detach=False, _is_running_remotely=True)

    driver_resolver.set_graph(runs=runs, artifacts=artifacts, edges=edges)
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.SCHEDULED.value
    )
    output = driver_resolver.resolve(future)

    assert output == 3
    assert (
        api_client.get_resolution(future.id).status == ResolutionStatus.COMPLETE.value
    )

    # cheap way of confirming no k8s calls were made
    mock_load_kube_config.assert_not_called()


@pytest.mark.parametrize(
    "max_parallelism, expected_validates",
    (
        (None, True),
        (0, False),
        (-1, False),
        (1, True),
        (10, True),
    ),
)
def test_max_parallelism_validation(max_parallelism, expected_validates):
    try:
        CloudResolver(max_parallelism=max_parallelism)
    except ValueError:
        assert not expected_validates
        return
    assert expected_validates


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@pytest.mark.parametrize(
    "base_image_tag, expected_image",
    (
        ("cuda", "bar"),
        (None, "foo"),
    ),
)
def test_make_run(_, base_image_tag, expected_image):
    @func(inline=False, base_image_tag=base_image_tag)
    def foo():
        pass

    future = foo()

    with mock.patch(
        "sematic.resolvers.cloud_resolver.CloudResolver._root_future",
        return_value=future,
    ):
        run = CloudResolver()._make_run(future)
        assert run.container_image_uri == expected_image


@mock.patch(
    "sematic.resolvers.cloud_resolver.get_image_uris",
    return_value={"default": "foo", "cuda": "bar"},
)
@pytest.mark.parametrize(
    "detach, expected_status, expected_kind, _base_image_tag, expected_resolution_container_image_uri",  # noqa: E501
    (
        (False, ResolutionStatus.SCHEDULED, ResolutionKind.LOCAL, "cuda", None),
        (True, ResolutionStatus.CREATED, ResolutionKind.KUBERNETES, "cuda", "bar"),
        (True, ResolutionStatus.CREATED, ResolutionKind.KUBERNETES, None, "foo"),
    ),
)
def test_make_resolution(
    _,
    detach: bool,
    expected_status: ResolutionStatus,
    expected_kind: ResolutionKind,
    _base_image_tag: Optional[str],
    expected_resolution_container_image_uri: Optional[str],
):
    @func
    def foo():
        pass

    future = foo()

    resolver = (
        CloudResolver(detach=detach, _base_image_tag=_base_image_tag)
        if _base_image_tag
        else CloudResolver(detach=detach)
    )

    resolution = resolver._make_resolution(future)

    assert resolution.status == expected_status.value
    assert resolution.kind == expected_kind.value
    assert resolution.container_image_uris == {"default": "foo", "cuda": "bar"}
    assert resolution.container_image_uri == expected_resolution_container_image_uri
