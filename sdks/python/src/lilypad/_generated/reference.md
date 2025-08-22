# Reference
## Telemetry
<details><summary><code>client.telemetry.<a href="src/lilypad/telemetry/client.py">send_traces</a>(...)</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Temporary endpoint to receive and log OpenTelemetry trace data for debugging purposes. This endpoint follows the OTLP/HTTP specification.
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from lilypad._generated import Lilypad
from lilypad._generated.telemetry import (
    TelemetrySendTracesRequestResourceSpansItem,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItem,
    TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem,
)

client = Lilypad()
client.telemetry.send_traces(
    resource_spans=[
        TelemetrySendTracesRequestResourceSpansItem(
            scope_spans=[
                TelemetrySendTracesRequestResourceSpansItemScopeSpansItem(
                    spans=[
                        TelemetrySendTracesRequestResourceSpansItemScopeSpansItemSpansItem(
                            trace_id="traceId",
                            span_id="spanId",
                            name="name",
                            start_time_unix_nano="startTimeUnixNano",
                            end_time_unix_nano="endTimeUnixNano",
                        )
                    ],
                )
            ],
        )
    ],
)

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**resource_spans:** `typing.Sequence[TelemetrySendTracesRequestResourceSpansItem]` 
    
</dd>
</dl>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

## Health
<details><summary><code>client.health.<a href="src/lilypad/health/client.py">check</a>()</code></summary>
<dl>
<dd>

#### 📝 Description

<dl>
<dd>

<dl>
<dd>

Returns the current health status of the application
</dd>
</dl>
</dd>
</dl>

#### 🔌 Usage

<dl>
<dd>

<dl>
<dd>

```python
from lilypad._generated import Lilypad

client = Lilypad()
client.health.check()

```
</dd>
</dl>
</dd>
</dl>

#### ⚙️ Parameters

<dl>
<dd>

<dl>
<dd>

**request_options:** `typing.Optional[RequestOptions]` — Request-specific configuration.
    
</dd>
</dl>
</dd>
</dl>


</dd>
</dl>
</details>

