from dataclasses import dataclass, field


LANES = ["TOP", "JUNGLE", "MID", "ADC", "SUPPORT"]


@dataclass
class Player:
    id: int
    name: str
    roles: list[str]
    mmr: int


@dataclass
class Team:
    slots: dict[str, Player] = field(default_factory=dict)

    def total_mmr(self) -> int:
        return sum(player.mmr for player in self.slots.values())

    def is_complete(self) -> bool:
        return all(lane in self.slots for lane in LANES)