# ============================================================================
# FILE: tests/test_com_lock.py
# ============================================================================

"""
Tests for COM call serialization via _com_lock in with_vibrationview decorator.
Verifies that concurrent requests are serialized through the lock.
"""

import threading
import time


class TestComLock:
    """Test that the COM lock serializes concurrent requests"""

    def test_concurrent_requests_are_serialized(self, client, mock_vibrationview):
        """Verify that two concurrent requests do not overlap COM calls"""
        call_log = []
        original_is_ready = mock_vibrationview.IsReady

        def slow_is_ready():
            call_log.append(("start", threading.get_ident(), time.monotonic()))
            time.sleep(0.1)
            result = original_is_ready()
            call_log.append(("end", threading.get_ident(), time.monotonic()))
            return result

        mock_vibrationview.IsReady = slow_is_ready

        results = [None, None]

        def make_request(index):
            results[index] = client.get("/api/v1/isready")

        t1 = threading.Thread(target=make_request, args=(0,))
        t2 = threading.Thread(target=make_request, args=(1,))
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)

        # Both requests should succeed
        assert results[0].status_code == 200
        assert results[1].status_code == 200

        # Verify serialization: the second call should start after the first ends
        starts = [t for tag, _, t in call_log if tag == "start"]
        ends = [t for tag, _, t in call_log if tag == "end"]
        assert len(starts) == 2
        assert len(ends) == 2

        # The later start should be after the earlier end (serialized, not overlapping)
        later_start = max(starts)
        earlier_end = min(ends)
        assert later_start >= earlier_end, (
            f"COM calls overlapped: second started at {later_start} but first ended at {earlier_end}"
        )

    def test_lock_is_released_on_error(self, client, mock_vibrationview):
        """Verify the lock is released even when a COM call raises an exception"""
        from utils.vv_manager import _com_lock

        mock_vibrationview.IsReady.side_effect = Exception("COM failure")

        response = client.get("/api/v1/isready")
        assert response.status_code == 500

        # Lock should be released — acquiring it should not block
        acquired = _com_lock.acquire(timeout=1)
        assert acquired, "COM lock was not released after exception"
        _com_lock.release()

    def test_lock_exists_at_module_level(self):
        """Verify _com_lock is a threading.Lock"""
        from utils.vv_manager import _com_lock

        assert isinstance(_com_lock, type(threading.Lock()))
