## Sematic decorator

### `@sematic.func`

The Sematic Function decorator.

This identifies the function as a unit of work that Sematic knows about for
tracking and scheduling. The function's execution details will be exposed
in the Sematic UI.

#### Parameters

- `func`: Optional[Callable]
    
    The `Callable` to instrument; usually the decorated function.

- `standalone`: bool
    
    When using the `CloudRunner`, whether the instrumented function should be
    executed inside its own container job (`True`) or in the same process and
    worker that is executing the `Runner` itself (`False`).

    Defaults to `False`, as most pipeline functions are expected to be
    lightweight. Set this to `True` in order to distribute its
    execution to a worker and parallelize its execution.

- `cache`: bool

    Whether to cache the function's output value under the `cache_namespace`
    configured in the `Runner`. Defaults to `False`.

    Do not activate this on a non-deterministic function!

- `resource_requirements`: Optional[ResourceRequirements]

    When using the `CloudRunner`, specifies what special execution
    resources the function requires. Defaults to `None`.

- `retry`: Optional[RetrySettings]

    Specifies in case of which Exceptions the function's execution should
    be retried, and how many times. Defaults to `None`.

- `timeout_mins`: Optional[int]

    Specifies the maximum amount of time that this function can take
    before the final result is known. Must be an integer >=1. Note that
    this time includes any time it takes to schedule the Function to
    execute and begin executing the code. Defaults to `None`.

#### Returns

Union[Calculator, Callable]

An internal instrumentation wrapper over the decorated function.

## Runners

{% hint style="info" %}
This concept used to be referred to as `Resolvers`. So don't
worry if you're familiar with that terminology! Everything
you know about Resolvers applies to Runners as well, except
that `.resolve(...)` has been renamed to `.run(...)`. 
Additionally, futures cann't call `.run(runner)` in the same
way they could call `.resolve(resolver)`. Using the
`runner.run(future)` form is now required.
{% endhint %}

### `Runner`

Abstract base class for all runners. Defines the `Runner` interfaces.

#### `Runner.run`

Abstract method. Entry-point for the pipeline execution algorithm.

##### Parameters

- `future`: AbstractFuture
    
    Root future of the graph to execute.

##### Returns

Any

output of the pipeline.

### `LocalRunner`

A runner to run a graph in-memory.

Each Future's state is tracked in the DB as a run. Each individual function's
input arguments and output value are tracked as artifacts.

#### Parameters

- `cache_namespace`: CacheNamespace

    A string or a `Callable` which takes a root `Future` and returns a string, which
    will be used as the cache key namespace in which the executed funcs' outputs will
    be cached, as long as they also have the `cache` flag activated. Defaults to
    `None`.

    The `Callable` option takes as input the `PipelineRun` root `Future`. All the other
    required variables must be enclosed in the `Callables`' context. The `Callable`
    must have a small memory footprint and must return immediately!

- `rerun_from`: Optional[str]
    
    When `None`, the pipeline is executed from scratch, as normally. When not `None`,
    must be the id of a `Run` from a previous pipeline run. Instead of running from
    scratch, parts of that previous pipeline run is cloned up until the specified `Run`,
    and only the specified `Run`, nested and downstream `Future`s are executed. This
    is meant to be used for retries or for hotfixes, without needing to re-run the
    entire pipeline again.

### `CloudRunner`

Executes a pipeline on a Kubernetes cluster.

#### Parameters

- `cache_namespace`: CacheNamespace

    A string or a `Callable` which takes a root `Future` and returns a string, which
    will be used as the cache key namespace in which the executed funcs' outputs will
    be cached, as long as they also have the `cache` flag activated. Defaults to
    `None`.

    The `Callable` option takes as input the `PipelineRun` root `Future`. All the other
    required variables must be enclosed in the `Callables`' context. The `Callable`
    must have a small memory footprint and must return immediately!

- `max_parallelism`: Optional[int]

    The maximum number of [Standalone
    Runs](./glossary.md#standalone-inline-function) that this runner will
    allow to be in the `SCHEDULED` state at any one time. Must be a positive
    integer, or `None` for unlimited runs. Defaults to `None`.

    This is intended as a simple mechanism to limit the amount of computing resources
    consumed by one pipeline execution for pipelines with a high degree of
    parallelism. Note that if other runners are active, runs from them will not be
    considered in this parallelism limit. Note also that runs that are in the RAN
    state do not contribute to the limit, since they do not consume computing
    resources.

- `rerun_from`: Optional[str]

    When `None`, the pipeline is executed from scratch, as normally. When not `None`,
    must be the id of a `Run` from a previous pipeline run. Instead of running from
    scratch, parts of that previous pipeline run is cloned up until the specified `Run`,
    and only the specified `Run`, nested and downstream `Future`s are executed. This
    is meant to be used for retries or for hotfixes, without needing to re-run the
    entire pipeline again.

### `SilentRunner`

A runner to execute a DAG in memory, without tracking to the DB.

## Resource requirements

### `ResourceRequirements`

#### Parameters

- `kubernetes`: KubernetesResourceRequirements

    Kubernetes resource requirements.

### `KubernetesResourceRequirements`

Information on the Kubernetes resources required.

#### Parameters

- `node_selector`: Dict[str, str]

    The kind of Kubernetes node that the job must run on. More details can be
    found here:
    https://kubernetes.io/docs/concepts/scheduling-eviction/assign-pod-node/ The
    value of this field will be used as the nodeSelector described there.

- `requests`: Dict[str, str]

    Requests for resources on a kubernetes pod. More details can be found here:
    https://kubernetes.io/docs/concepts/configuration/manage-resources-containers/
    The values used here will apply to both the "requests" and the "limits" of
    the job.

- `secret_mounts`: KubernetesSecretMount

    Requests to take the contents of Kubernetes secrets and expose them as
    environment variables or files on disk when running in the cloud.

- `tolerations`: List[KubernetesToleration]

    If your Kubernetes configuration uses node taints to control which workloads
    get scheduled on which nodes, this enables control over how your workload
    interacts with these node taints. More information can be found here:
    https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

- `mount_expanded_shared_memory`: bool

    By default, Docker uses a 64MB /dev/shm partition. If this flag is set, a
    memory-backed tmpfs that expands up to half of the available memory file is used
    instead. Defaults to False. If that file is expanded to more than that limit
    (through external action), then the pod will be terminated.

- `security_context`: KubernetesSecurityContext

    Custom security context for your container to run in. Can ONLY be set
    if your Sematic administrator has enabled the
    `ALLOW_CUSTOM_SECURITY_CONTEXTS` server setting.

### `KubernetesSecretMount`

Information about how to expose Kubernetes secrets when running a Sematic func.

This can be used to mount credentials that the func may need to execute. To use it
in this manner:

1. Create a Kubernetes secret containing the credentials you need. The secret MUST be
    named "sematic-func-secrets" Instructions for this can be found here:
    https://kubernetes.io/docs/concepts/configuration/secret/
    In the "data" field of the secret, you should have key value pairs for every
    secret value you wish to expose for Sematic functions. For example, you might
    have the key `my-api-key` and the value `mYSu93Rs3cretKey`

2. For the Sematic func that requires access to the secret, list it either as an
    environment secret (the secret's value will be stored in an environment variable)
    or as a file secret (the secret's value will be stored in a file).

Before using Kubernetes secrets to give this kind of credential access, be aware that
using them will allow anybody who can execute Sematic funcs in your cluster access to
the secrets.

#### Parameters

- `environment_secrets`: Dict[str, str]

    A dict whose keys are the same as the subset of keys from the
    "sematic-func-secret" that you want mounted for the func, and whose values are
    the name of the environment variable where it should be exposed

- `file_secrets`: Dict[str, str]

    A dict whose keys are the same as the subset of keys from the
    "sematic-func-secret" that you want mounted for the func, and whose values are
    the path to the file within the container where the secret should be exposed.
    These file paths should be RELATIVE paths, they will be taken as relative to
    file_secret_root_path.

- `file_secret_root_path`: str

    File secrets must all be stored in the same directory. This gives the directory
    where they will be stored. The directory must be a new directory, or the contents
    of the existing directory will be overwritten.

### `KubernetesToleration`

Toleration for a node taint, enabling the pod for the function to run on the node

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Parameters

- `key`: Optional[str]

    The key for the node taint intended to be tolerated. If empty, means
    to match all keys AND all values

- `operator`: KubernetesTolerationOperator

    The way to compare the key/value pair to the node taint's key/value pair
    to see if the toleration applies

- `effect`: KubernetesTolerationEffect

    The effect of the node taint the toleration is intended to tolerate.
    Leaving it empty means to tolerate all effects.

- `value`: Optional[str]

    If the operator is Equals, this value will be compared to the value
    on the node taint to see if this toleration applies.

- `toleration_seconds`: Optional[int]

    Only specified when effect is NoExecute (otherwise is an error). It
    specifies the amount of time the pod can continue executing on a node
    with a NoExecute taint

### `KubernetesTolerationEffect`

The effect that the toleration is meant to tolerate

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Values

- `KubernetesTolerationEffect.NoSchedule`
    The toleration indicates that the pod can run on the node even
    if it has specified a NoSchedule taint, assuming the rest of
    the toleration matches the taint.

- `KubernetesTolerationEffect.PreferNoSchedule`

    The toleration indicates that the pod can run on the node even
    if it has specified a PreferNoSchedule taint, assuming the rest
    of the toleration matches the taint.

- `KubernetesTolerationEffect.NoExecute`

    The pod will not be evicted from the node even if the node has
    specified a NoExecute taint, assuming the rest of the toleration
    matches the taint.

- `KubernetesTolerationEffect.All`

    The pod will not be evicted from the node even if the node has
    any kind of taint, assuming the rest of the toleration
    matches the taint.

### `KubernetesTolerationOperator`

The way that a toleration should be checked to see if it applies.

See Kubernetes documentation for more:
https://kubernetes.io/docs/concepts/scheduling-eviction/taint-and-toleration/

#### Values

- `KubernetesTolerationOperator.Equal`

    value must be specified, and must be equal for the toleration and the taint
    for the toleration to be considered to apply. In addition to this condition,
    the "effect" must be equal for the toleration and the taint for the toleration
    to be considered to apply.

- `KubernetesTolerationOperator.Exists`

    value is not required. If a taint with the given key exists on the node,
    the toleration is considered to apply. In addition to this condition,
    the "effect" must be equal for the toleration and the taint for the toleration
    to be considered to apply.

### `KubernetesSecurityContext`

A custom security context for your Sematic job to run in. The
following docs are sourced from the
[Kubernetes docs](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#securitycontext-v1-core).
For more up-to-date documentation, please refer to those docs.

#### Parameters

- `allow_privilege_escalation`: bool

    AllowPrivilegeEscalation controls whether a process can gain more privileges
    than its parent process. This bool directly controls if the no_new_privs
    flag will be set on the container process. AllowPrivilegeEscalation is true
    always when the container is: 1) run as Privileged 2) has CAP_SYS_ADMIN Note
    that this field cannot be set when spec.os.name is windows.

- `privileged`: bool

    Run container in privileged mode. Processes in privileged containers are
    essentially equivalent to root on the host. Defaults to false. Note that
    this field cannot be set when spec.os.name is windows.

- `capabilities`: KubernetesCapabilities

    The capabilities to add/drop when running containers. Defaults to the default
    set of capabilities granted by the container runtime. Note that this field
    cannot be set when spec.os.name is windows.

### `KubernetesCapabilities`

Capabilities for a custom security context. The
following docs are sourced from the
[Kubernetes docs](https://kubernetes.io/docs/reference/generated/kubernetes-api/v1.27/#capabilities-v1-core).
For more up-to-date documentation, please refer to those docs.

#### Parameters

- `add`: List[str]

    Capabilities to add (e.g. `["SYS_ADMIN"]`).

- `drop`: List[str]

    The capabilities to drop.

## Fault tolerance

### `RetrySettings`

Configuration object to pass to `@sematic.func` to activate retries.

#### Parameters

- `exceptions`: Tuple[Type[Exception]]

    A tuple of exception types to retry for.

- `retries`: int

    How may times to retry.

## Context

### `SematicContext`

Contextual information about the execution of the current Sematic function

#### Attributes

- `run_id`: str

    The id of the future for the current execution. For cloud executions, this
    is equivalent to the id for the existing run.

- `root_id`: str

    The id of the root future for a pipeline run. For cloud executions, this is
    equivalent to the id for the root run.

### `context`

Get the current run context, including the active run id and root run id.

This can be used if you wish to track information about a Sematic execution
in an external system, and store it by an id that can link you back to the
Sematic run. It should not be used to interact with the Sematic API directly.

#### Returns

`SematicContext`

The active context, if a Sematic function is currently executing. Otherwise
it will raise an error.

#### Raises

- `NotInSematicFuncError`

    If this function is called outside the execution of a Sematic function.

## Types

### `Link`

Link lets users return a URL from a Sematic function which will render as a
button in the UI.

#### Parameters

- `label`: str

    The label of the button that will be displayed in the UI

- `url`: str

    The URL to link to

#### Raises

- `ValueError`

    In case of missing URL scheme and netloc as extracted by `urllib.parse.urlparse`.


### `SnowflakeTable`

A class to easily access Snowflake tables.

The following user settings need to be set:

```shell
$ sematic settings set SNOWFLAKE_USER <george>
$ sematic settings set SNOWFLAKE_PASSWORD <across-the-universe>
$ sematic settings set SNOWFLAKE_ACCOUNT <the-beatles>
```

#### Parameters

- `database`: str

    Name of Snowflake database

- `table`: str

    Name of Snowflake table

#### `Snowflake.to_df`

Output content of the table to a `pandas.DataFrame`.

##### Parameters

- `limit`: Optional[int]
    
    Maximum number of rows to return. Defaults to -1, i.e. all.


## Custom metrics

{% hint style="info" %}

Custom metrics are an Enteprise feature. Get in touch at
[support@sematic.dev](mailto:support@sematic.dev) to learn more.

{% endhint %}

### `sematic.ee.metrics.log_metric`

Logs a timeseries metric value.

#### Parameters

- `name`: str

    Name of metric to log.

- `value`: float

    Metric value to log.

- `metric_type`: `MetricType`

    Defaults to `MetricType.GAUGE`. Specifies how a particular metric is
    aggregated. `MetricType.GAUGE` will average values within a given
    aggregation bucket while `MetricType.COUNT` will sum values within a given
    aggregation bucket.