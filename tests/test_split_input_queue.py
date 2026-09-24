#!/usr/bin/env python3
"""Exercise actual patched C with a bounded queue and notification/workqueue doubles.

Verifies overflow return/scheduling and nonblocking producer behavior, not radio
stability or Zephyr scheduling. The real firmware build validates integration.
"""
from pathlib import Path
import subprocess
import sys
import tempfile

source = (Path(sys.argv[1]) / "app/src/split/bluetooth/service.c").read_text()
start = source.index("struct input_event_notify_item {")
end = source.index("#endif /* IS_ENABLED(CONFIG_ZMK_INPUT_SPLIT) */", start)
implementation = source[start:end]

stubs = r"""
#include <assert.h>
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <string.h>
#include <errno.h>
#include <stdio.h>
#define K_NO_WAIT 0
#define CONFIG_ZMK_INPUT_SPLIT_MSG_QUEUE_SIZE 2
#define LOG_ERR(...) ((void)0)
#define LOG_WRN(...) ((void)0)
#define ZMK_SPLIT_BT_INPUT_EVENT_UUID 123
#define BT_UUID_DECLARE_128(x) (x)
struct zmk_split_input_event_payload { uint8_t type; uint16_t code; int32_t value; uint8_t sync; };
struct attribute { int uuid; void *user_data; };
struct { size_t attr_count; struct attribute attrs[3]; } split_svc = {
    3, {{123, NULL}, {0, NULL}, {0, (void *)1}}
};
static int bt_uuid_cmp(int a, int b) { return a - b; }
struct queue { size_t size, count; unsigned char data[2][64]; };
#define K_MSGQ_DEFINE(name, item_size, capacity, alignment) \
    struct queue name = {.size = item_size}; \
    _Static_assert(capacity == 2 && item_size <= 64, "test queue capacity");
static int fail_puts, submissions, notifications, notify_error;
static int notified_values[16];
static int k_msgq_put(struct queue *q, const void *item, int timeout) {
    assert(timeout == K_NO_WAIT);
    if (fail_puts) { fail_puts--; return -ENOMSG; }
    if (q->count == 2) return -ENOMSG;
    memcpy(q->data[q->count++], item, q->size);
    return 0;
}
static int k_msgq_get(struct queue *q, void *item, int timeout) {
    assert(timeout == K_NO_WAIT);
    if (!q->count) return -ENOMSG;
    memcpy(item, q->data[0], q->size);
    memmove(q->data[0], q->data[1], q->size);
    q->count--;
    return 0;
}
struct k_work { void (*handler)(struct k_work *); };
#define K_WORK_DEFINE(name, cb) struct k_work name = {.handler = cb}
static int service_work_q;
static int k_work_submit_to_queue(void *queue, struct k_work *work) {
    assert(queue == &service_work_q && work->handler);
    submissions++;
    return 1;
}
static int bt_gatt_notify(void *conn, struct attribute *attr, const void *data, size_t size) {
    assert(conn == NULL && attr == &split_svc.attrs[0]);
    assert(size == sizeof(struct zmk_split_input_event_payload));
    const struct zmk_split_input_event_payload *p = data;
    assert(p->type == 2 && p->code == 3 && p->sync == 1);
    notified_values[notifications++] = p->value;
    return notify_error;
}
"""

tests = r"""
static int report(int value) { return zmk_split_bt_report_input(1, 2, 3, value, true); }
static void drain(void) { service_input_notify_work.handler(&service_input_notify_work); }
int main(void) {
    /* Producer must never perform radio notification inline. */
    assert(report(10) == 0);
    assert(submissions == 1 && notifications == 0 && input_event_msgq.count == 1);
    drain();
    assert(notifications == 1 && notified_values[0] == 10 && input_event_msgq.count == 0);

    /* Saturation: keep newest event, return success, and still schedule work. */
    assert(report(20) == 0);
    assert(report(30) == 0);
    int before = submissions;
    assert(report(40) == 0);
    assert(submissions == before + 1 && input_event_msgq.count == 2);
    drain();
    assert(notifications == 3 && notified_values[1] == 30 && notified_values[2] == 40);

    /* A failed retry is bounded and must not claim successful delivery. */
    fail_puts = 2;
    before = submissions;
    assert(report(50) == -ENOMSG && submissions == before);
    assert(input_event_msgq.count == 0);

    /* No matching input device must not enqueue or notify anything. */
    assert(zmk_split_bt_report_input(9, 2, 3, 60, true) == -ENODEV);
    assert(submissions == before && input_event_msgq.count == 0);

    /* Disconnected radio errors must not prevent subsequent queue draining. */
    notify_error = -ENOTCONN;
    assert(report(70) == 0 && report(80) == 0);
    drain();
    assert(input_event_msgq.count == 0 && notifications == 5);
    notify_error = 0;
    assert(report(90) == 0);
    drain();
    assert(notifications == 6 && notified_values[5] == 90);
    puts("PASS: deferred send, overflow retry, retry failure, invalid device, disconnect recovery");
}
"""

with tempfile.TemporaryDirectory(prefix="split-queue-test-") as temp:
    path = Path(temp)
    (path / "test.c").write_text(stubs + implementation + tests)
    subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                    "-Wno-unused-parameter", "-Wno-pointer-to-int-cast",
                    str(path / "test.c"), "-o", str(path / "test")], check=True)
    subprocess.run([str(path / "test")], check=True)
