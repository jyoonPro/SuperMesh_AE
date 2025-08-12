from dataclasses import dataclass
from typing import List


@dataclass
class ChunkInfo:
    chunk_id: int
    src_id: int
    dest_id: int
    current_src_node: int
    current_dest_node: int
    messages: int
    timestep: int
    dependency: int
    alpha:int


@dataclass
class LoggerInfo:
    chunk_id_list: List[int]
    link_src: int
    link_end: int
    start_cycle: int
    end_cycle: int
    alpha_cost: int
    per_chunk_cycle: int