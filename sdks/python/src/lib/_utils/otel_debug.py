import logging

from opentelemetry.sdk.trace.export import ReadableSpan, BatchSpanProcessor

log = logging.getLogger("lilypad.otel-debug")
log.setLevel(logging.DEBUG)
if not log.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s  %(levelname)s  %(message)s", "%H:%M:%S"))
    log.addHandler(handler)


def wrap_batch_processor(processor: BatchSpanProcessor) -> None:
    """Monkey-patch BatchSpanProcessor to log enqueue / flush activity."""

    origin_on_end = processor.on_end
    origin_flush = processor.force_flush

    def on_end(span: ReadableSpan) -> None:
        qsize = len(processor.queue)
        log.debug("[on_end ] enqueue span=%s  queue=%d→%d", span.name, qsize, qsize + 1)
        origin_on_end(span)

    def force_flush(timeout_millis: int = 5_000):  # noqa: D401
        qsize_before = len(processor.queue)
        log.debug("[flush   ] called  queue=%d", qsize_before)
        result = origin_flush(timeout_millis)
        log.debug("[flush   ] done    queue=%d  result=%s", len(processor.queue), result)
        return result

    processor.on_end = on_end  # type: ignore
    processor.force_flush = force_flush  # type: ignore
