# pylint: disable=no-self-use

import random
from typing import Generator

import pytest

from sdcm.sct_events.base import ContinuousEventsRegistry, ContinuousEventRegistryException, EventPeriod
from sdcm.sct_events.database import FullScanEvent
from sdcm.sct_events.loaders import GeminiStressEvent
from sdcm.sct_events.nodetool import NodetoolEvent


class TestContinuousEventsRegistry:
    @pytest.fixture(scope="function")
    def registry(self):
        yield ContinuousEventsRegistry()

    @pytest.fixture(scope="function")
    def nodetool_stress_event(self) -> Generator[NodetoolEvent, None, None]:
        yield NodetoolEvent(nodetool_command="mock_cmd", publish_event=False)

    @pytest.fixture(scope="function")
    def gemini_stress_event(self) -> Generator[GeminiStressEvent, None, None]:
        yield GeminiStressEvent(node="mock_node", cmd="gemini mock cmd", publish_event=False)

    @pytest.fixture(scope="function")
    def full_scan_event(self) -> Generator[FullScanEvent, None, None]:
        full_scan_event = FullScanEvent
        yield full_scan_event.start(db_node_ip="124.5.2.1", ks_cf="mock_cf")

    @pytest.fixture(scope="function")
    def populated_registry(self,
                           registry: ContinuousEventsRegistry) -> Generator[ContinuousEventsRegistry, None, None]:
        for _ in range(100):
            new_nodetool_event = NodetoolEvent(nodetool_command="mock cmd", publish_event=False)
            new_gemini_event = GeminiStressEvent(node="2323432", cmd="gemini hello", publish_event=False)
            registry.add_event(random.choice([new_gemini_event, new_nodetool_event]))

        yield registry

    def test_add_event(self,
                       registry: ContinuousEventsRegistry,
                       nodetool_stress_event: NodetoolEvent):
        registry.add_event(nodetool_stress_event)

        assert nodetool_stress_event in registry.continuous_events

    def test_add_multiple_events(self,
                                 registry: ContinuousEventsRegistry):
        number_of_insertions = 10
        for _ in range(number_of_insertions - 1):
            new_nodetool_event = NodetoolEvent(nodetool_command="mock cmd", publish_event=False)
            new_gemini_event = GeminiStressEvent(node="2323432", cmd="gemini hello", publish_event=False)
            registry.add_event(random.choice([new_nodetool_event, new_gemini_event]))

        assert len(registry.continuous_events) == number_of_insertions

    def test_adding_a_non_continuous_event_raises_error(self,
                                                        registry: ContinuousEventsRegistry,
                                                        full_scan_event: FullScanEvent):
        with pytest.raises(ContinuousEventRegistryException):
            registry.add_event(full_scan_event)

    def test_get_event_by_id(self,
                             populated_registry: ContinuousEventsRegistry):
        some_event = random.choice(populated_registry.continuous_events)
        some_event_id = some_event.event_id
        found_event = populated_registry.get_event_by_id(some_event_id)

        assert found_event.event_id == some_event.event_id

    def test_get_events_by_type(self,
                                populated_registry: ContinuousEventsRegistry):
        gemini_events_in_registry_count = len([e for e in populated_registry.continuous_events
                                               if isinstance(e, GeminiStressEvent)])
        found_gemini_events = populated_registry.get_events_by_type(event_type=GeminiStressEvent)

        assert len(found_gemini_events) == gemini_events_in_registry_count
        for event in found_gemini_events:
            assert isinstance(event, GeminiStressEvent)

    def test_get_events_by_period_type(self,
                                       populated_registry: ContinuousEventsRegistry,
                                       nodetool_stress_event: NodetoolEvent):
        populated_registry.add_event(nodetool_stress_event)
        nodetool_stress_event.begin_event()
        found_events = populated_registry.get_events_by_period(period_type=EventPeriod.Begin)

        assert len(found_events) == 1
