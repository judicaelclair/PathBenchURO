
from structures import DynamicColour, Colour, TRANSPARENT
from simulator.services.service import Service
from simulator.services.services import Services
from simulator.services.event_manager.events.colour_update_event import ColourUpdateEvent
from simulator.services.event_manager.events.new_colour_event import NewColourEvent
from simulator.services.debug import DebugLevel
from utility.utils import exclude_from_dict

from typing import Dict, Final, Any, List, Optional
import json
import os

class PersistentStateView():
    __services: Services
    state: 'PersistentState'
    index: int
    colours: Dict[str, DynamicColour]

    EFFECTIVE_VIEW: Final[int] = -1

    def __init__(self, services: Services, state: 'PersistentState', index: int) -> None:
        self.__services = services
        self.state = state
        self.index = index

        self.colours = {}

    def __colour_callback(self, colour: DynamicColour) -> None:
        if self.index == self.state.view_idx:
            self.state.effective_view.colours[colour.name].set_all(colour.colour, colour.visible)
        self.__services.ev_manager.post(ColourUpdateEvent(colour, self))

    def _add_colour(self, name: str, colour: Colour, visible: bool) -> DynamicColour:
        if name in self.colours:
            return self.colours[name]
        dc = self.colours[name] = DynamicColour(colour, name, self.__colour_callback, visible)
        self.__colour_callback(dc)
        return dc

    def _from_view(self, other: 'PersistentStateView') -> None:
        self.colours = {k: v for k, v in self.colours.items() if k in other.colours}
        for n, c in other.colours.items():
            if n not in self.colours:
                self._add_colour(n, c.colour, c.visible)
            else:
                self.colours[n].set_all(c.colour, c.visible)

    def _from_json(self, data: Dict[str, Any]) -> None:
        for n, c in data["colours"].items():
            colour = Colour(*c["colour"])
            visible = bool(c["visible"])
            self.colours[n] = DynamicColour(colour, n, self.__colour_callback, visible)

    def _to_json(self) -> Dict[str, Any]:
        data = {}
        dc = data["colours"] = {}
        for n, c in self.colours.items():
            dc[n] = {}
            dc[n]["colour"] = tuple(c.colour)
            dc[n]["visible"] = c.visible
        return data

    def is_effective(self) -> bool:
        return self.index == PersistentStateView.EFFECTIVE_VIEW

class PersistentState(Service):
    file_name: str

    MAX_VIEWS: Final[int] = 6
    effective_view: PersistentStateView
    views: List[PersistentStateView]
    __view_idx: int

    _save_task: Optional['Task']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **exclude_from_dict(kwargs, ["file_name"]))
        self.file_name = kwargs["file_name"] if "file_name" in kwargs else ".pathbench.json"

        self._save_task = None

        self.reset(False)
        self.load()
        self.save()

    def reset(self, save: bool = True) -> None:
        self.effective_view = PersistentStateView(self._services, self, PersistentStateView.EFFECTIVE_VIEW)
        self.views = [PersistentStateView(self._services, self, i) for i in range(self.MAX_VIEWS)]
        self.__view_idx = 0
        if save:
            self.save()

    def load(self) -> None:
        def check(req: bool) -> None:
            if not req:
                raise RuntimeError

        if os.path.isfile(self.file_name):
            self._services.debug.write("Loading state from '{}'".format(self.file_name), DebugLevel.BASIC)
            with open(self.file_name, 'r') as f:
                try:
                    jdata = json.load(f)
                    jidx = jdata["view_index"]
                    check(jidx >= 0 and jidx < self.MAX_VIEWS)
                    jviews = jdata["views"]
                    for v in range(self.MAX_VIEWS):
                        self.views[v]._from_json(jviews[v])
                    self.view_idx = jidx
                except Exception:
                    print("{} is corrupted".format(self.file_name))
                    self.reset()
        else:
            self._services.debug.write("'{}' not found, falling back to default state data".format(self.file_name), DebugLevel.BASIC)

    def save(self) -> None:
        self._services.debug.write("Saving state to '{}'".format(self.file_name), DebugLevel.BASIC)
        data = {}
        data["view_index"] = self.view_idx
        data["views"] = [self.views[v]._to_json() for v in range(self.MAX_VIEWS)]
        with open(self.file_name, 'w') as f:
            json.dump(data, f, sort_keys=True, indent=4)

        if self._save_task is not None:
            self._services.graphics.window.taskMgr.remove(self._save_task)
            self._save_task = None

    def schedule_save(self, delay: float = 0) -> None:
        if delay < 0:
            return

        if delay > 0 and self._services.graphics is not None:
            tm = self._services.graphics.window.taskMgr
            if self._save_task is None:
                self._services.debug.write("Scheduling state save to be executed {} seconds from now".format(delay), DebugLevel.BASIC)
                self._save_task = tm.doMethodLater(delay, lambda _: self.save(), "save_persistent_state")
        else:
            self.save()

    def add_colour(self, name: str, default_colour: Colour, default_visible: bool = True, save_delay: float = 0) -> DynamicColour:
        if name in self.effective_view.colours:
            return self.effective_view.colours[name]

        dc = self.effective_view._add_colour(name, default_colour, default_visible)
        for v in range(self.MAX_VIEWS):
            self.views[v]._add_colour(name, default_colour, default_visible)
        self._services.ev_manager.post(NewColourEvent(dc))
        self.schedule_save(save_delay)
        return dc

    def restore_effective_view(self):
        self.effective_view._from_view(self.view)

    def apply_effective_view(self, save_delay: float = 0):
        self.view._from_view(self.effective_view)
        self.schedule_save(save_delay)

    @property
    def view_idx(self) -> str:
        return 'view_idx'

    @view_idx.getter
    def view_idx(self) -> int:
        return self.__view_idx

    @view_idx.setter
    def view_idx(self, value: Any) -> None:
        idx, save_delay = (value, 4.0) if isinstance(value, int) else value
        self.__view_idx = idx
        self.effective_view._from_view(self.views[idx])
        self.schedule_save(save_delay)

    @property
    def view(self) -> str:
        return 'view'

    @view.getter
    def view(self) -> PersistentStateView:
        return self.views[self.view_idx]

    @view.setter
    def view(self, v: PersistentStateView) -> None:
        assert v == self.views[v.index], "PersistentStateView is not owned by this PersistentState"
        self.view_idx = v.index
