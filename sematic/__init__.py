"""
Sematic Public API
"""
# Standard Library
import os  # noqa: E402
import platform  # noqa: E402
import sys  # noqa: E402

# `urllib` invokes the underlying OS framework to get configured system proxies.
# On MacOS, this call causes the OS to immediately kill the `gunicorn` WSGI worker because
# it had not immediately performed `exec()` after `fork()`.
# This is a feature intended to prevent fork bombs.
#
# Setting the below sys env avoids this Mac feature by deactivating the proxy lookup.
# In order to deactivate this deactivation, set this env var: NO_PROXY=""
#
# This issue is described here: https://bugs.python.org/issue33725
if platform.system() == "Darwin" and "NO_PROXY" not in os.environ:
    os.environ["NO_PROXY"] = "*"

MIN_PYTHON_VERSION = (3, 8, 0)
_CURRENT_PYTHON_VERSION = sys.version_info[0:3]

if _CURRENT_PYTHON_VERSION < MIN_PYTHON_VERSION:
    _min_version_as_str = ".".join(str(i) for i in MIN_PYTHON_VERSION)
    _current_version_as_str = ".".join(str(i) for i in _CURRENT_PYTHON_VERSION)
    raise RuntimeError(
        f"Sematic requires python to be at {_min_version_as_str} or above, "
        f"but you are running {_current_version_as_str}. Please upgrade "
        f"to continue."
    )

# Sematic
import sematic.future_operators  # noqa: F401,E402
import sematic.types  # noqa: F401,E402
from sematic.container_images import has_container_image  # noqa: F401,E402
from sematic.function import func  # noqa: F401,E402
from sematic.future_context import SematicContext, context  # noqa: F401,E402
from sematic.plugins.external_resource.timed_message import (  # noqa: F401,E402
    TimedMessage,
)
from sematic.plugins.kuberay_wrapper.standard import (  # noqa: F401,E402
    StandardKuberayWrapper,
)
from sematic.resolver import Resolver  # noqa: F401,E402
from sematic.resolvers.cloud_resolver import CloudResolver  # noqa: F401,E402
from sematic.resolvers.local_resolver import LocalResolver  # noqa: F401,E402
from sematic.resolvers.resource_requirements import (  # noqa: F401,E402
    KubernetesCapabilities,
    KubernetesResourceRequirements,
    KubernetesSecretMount,
    KubernetesSecurityContext,
    KubernetesToleration,
    KubernetesTolerationEffect,
    KubernetesTolerationOperator,
    ResourceRequirements,
)
from sematic.resolvers.silent_resolver import SilentResolver  # noqa: F401,E402
from sematic.retry_settings import RetrySettings  # noqa: F401, E402
from sematic.runner import Runner  # noqa: F401,E402
from sematic.runners.cloud_runner import CloudRunner  # noqa: F401,E402
from sematic.runners.local_runner import LocalRunner, RerunMode  # noqa: F401,E402
from sematic.runners.silent_runner import SilentRunner  # noqa: F401,E402
from sematic.utils.exceptions import (  # noqa: F401,E402
    KubernetesError,
    PipelineRunError,
)
from sematic.versions import CURRENT_VERSION_STR as __version__  # noqa: F401,E402
