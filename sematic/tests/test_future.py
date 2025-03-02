# Third-party
import pytest

# Sematic
from sematic.function import func
from sematic.resolvers.resource_requirements import (
    KubernetesResourceRequirements,
    ResourceRequirements,
)
from sematic.runners.silent_runner import SilentRunner


@func
def foo() -> str:
    return "foo"


def test_set():
    future = foo()
    f = future.set(name="some name", tags=["tag1", "tag2"])

    assert f.id == future.id
    assert f.props.name == "some name"
    assert f.props.tags == ["tag1", "tag2"]


def test_set_validate_name():
    future = foo()

    future.set(name="my_future")
    assert future.props.name == "my_future"

    with pytest.raises(ValueError, match="Invalid `name`"):
        future.set(name=123)


def test_set_validate_standalone():
    future = foo()

    assert future.props.standalone is False
    future.set(standalone=True)
    assert future.props.standalone is True

    with pytest.raises(ValueError, match="Invalid `standalone`"):
        future.set(standalone=123)


def test_set_validate_cache():
    future = foo()

    assert future.props.cache is False
    future.set(cache=True)
    assert future.props.cache is True

    with pytest.raises(ValueError, match="Invalid `cache`"):
        future.set(cache=123)


def test_set_validate_resource_requirements():
    future = foo()
    my_resource_requirements = ResourceRequirements(
        kubernetes=KubernetesResourceRequirements(node_selector={"foo": "bar"})
    )

    future.set(resource_requirements=my_resource_requirements)
    assert future.props.resource_requirements == my_resource_requirements

    with pytest.raises(ValueError, match="Invalid `resource_requirements`"):
        future.set(resource_requirements=123)


def test_set_validate_tags():
    future = foo()

    future.set(tags=["my", "tags"])
    assert future.props.tags == ["my", "tags"]

    with pytest.raises(ValueError, match="Invalid `tags`"):
        future.set(tags=123)


def test_set_validate_fields():
    future = foo()

    with pytest.raises(ValueError, match="Cannot mutate fields"):
        future.set(abc=123)


def test_no_tracking():
    assert SilentRunner().run(foo()) == "foo"


def test_bool():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        if foo():
            pass


def test_not():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        if not foo():
            pass


def test_add():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        foo() + 1


def test_iadd():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        f = foo()
        f += 1


def test_mul():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        foo() * 1


def test_imul():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        f = foo()
        f *= 1


def test_div():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        foo() / 1


def test_idiv():
    with pytest.raises(NotImplementedError, match="docs.sematic.dev"):
        f = foo()
        f /= 1
