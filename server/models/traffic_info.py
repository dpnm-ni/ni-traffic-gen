# coding: utf-8

from __future__ import absolute_import
import time
from typing import List, Dict  # noqa: F401

from server.models.base_model_ import Model
from server import util


class Traffic_Gen_Info(Model):

    def __init__(self, prefix: str=None, traffic_id: str=None, src: str=None, dst: str=None, bandwidth: int=None, duration: int=None, service_type: List[str]=None):

        self.swagger_types = {
            'prefix': str,
            'traffic_id': str,
            'src': str,
            'dst': str,
            'bandwidth': int,
            'duration': int,
            'service_type': List[str]
        }

        self.attribute_map = {
            'prefix': 'prefix',
            'traffic_id': 'traffic_id',
            'src': 'src',
            'dst': 'dst',
            'bandwidth': 'bandwidth',
            'duration' : 'duration',
            'service_type' : 'service_type'
        }

        self._prefix = prefix
        self._traffic_id = traffic_id
        self._src = src
        self._dst = dst
        self._bandwidth = bandwidth
        self._duration = duration
        self._service_type = service_type

    @classmethod
    def from_dict(cls, dikt) -> 'Traffic_Gen_Info':
        return util.deserialize_model(dikt, cls)

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._prefix = prefix

    @property
    def traffic_id(self) -> str:
        return self._traffic_id

    @traffic_id.setter
    def traffic_id(self, traffic_id: str):
        self._traffic_id = traffic_id

    @property
    def src(self) -> str:
        return self._src

    @src.setter
    def src(self, src: str):
        self._src = src

    @property
    def dst(self) -> str:
        return self._dst

    @dst.setter
    def dst(self, dst: str):
        self._dst = dst

    @property
    def bandwidth(self) -> int:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, bandwidth: int):
        self._bandwidth = bandwidth

    @property
    def duration(self) -> int:
        return self._duration

    @duration.setter
    def duration(self, duration: int):
        self._duration = duration

    @property
    def service_type(self) -> List[str]:
        return self._service_type

    @service_type.setter
    def service_type(self, service_type: List[str]):
        self._service_type = service_type


class Traffic_Info(Model):

    def __init__(self, traffic_gen_info):
        self.prefix = traffic_gen_info.prefix
        self.traffic_id = traffic_gen_info.traffic_id
        self.src = traffic_gen_info.src
        self.dst = traffic_gen_info.dst
        self.bandwidth = traffic_gen_info.bandwidth
        self.duration = traffic_gen_info.duration
        self.service_type = traffic_gen_info.service_type
        self.sfcr_id = None
        self.sfc_id = None
        self.src_id = None
        self.dst_id = None
        self.process_id = None
        self.port = None
        self.start_time = time.time()

    
    def get_info(self):
        return {
            'prefix': self.prefix,
            'traffic_id': self.traffic_id,
            'src': self.src,
            'dst': self.dst,
            'bandwidth': self.bandwidth,
            'duration': self.duration,
            'service_type': self.service_type,
            'sfcr_id': self.sfcr_id,
            'sfc_id': self.sfc_id,
            'src_id': self.src_id,
            'dst_id': self.dst_id,
            'process_id': self.process_id,
            'port': self.port,
            'start_time': self.start_time
        }

    def set_prefix(self, prefix):
        self.prefix = prefix
        return

    def set_sfcr_id(self, sfcr_id):
        self.sfcr_id = sfcr_id
        return

    def set_sfc_id(self, sfc_id):
        self.sfc_id = sfc_id
        return

    def set_src_id(self, src_id):
        self.src_id = src_id
        return
   
    def set_dst_id(self, dst_id):
        self.dst_id = dst_id
        return

    def set_traffic_id(self, traffic_id):
        self.traffic_id = traffic_id
        return

    def set_duration(self, duration):
        self.duration = duration
        return

    def set_bandwidth(self, bandwidth):
        self.bandwidth = bandwidth
        return
    
    def set_process_id(self, process_id):
        self.process_id = process_id
        return

    def set_port(self, port):
        self.port = port
        return

    def set_start_time(self, start_time):
        self.start_time = start_time
        return

class Traffic_Scenario_Info(Model):

    def __init__(self, s_type: str=None, prefix: str=None, traffic_id: str=None, src: str=None, dst: str=None, bandwidth: int=None, duration: int=None, service_type: List[str]=None):

        self.swagger_types = {
            's_type' : str,
            'prefix': str,
            'traffic_id': str,
            'src': str,
            'dst': str,
            'bandwidth': int,
            'duration' : int,
            'service_type' : List[str]
        }

        self.attribute_map = {
            's_type' : 's_type',
            'prefix': 'prefix',
            'traffic_id': 'traffic_id',
            'src': 'src',
            'dst': 'dst',
            'bandwidth': 'bandwidth',
            'duration' : 'duration',
            'service_type' : 'service_type'
        }

        self._s_type = s_type
        self._prefix = prefix
        self._traffic_id = traffic_id
        self._src = src
        self._dst = dst
        self._bandwidth = bandwidth
        self._duration = duration
        self._service_type = service_type


    @classmethod
    def from_dict(cls, dikt) -> 'Traffic_Scenario_Info':
        return util.deserialize_model(dikt, cls)

    @property
    def s_type(self) -> str:
        return self._s_type

    @s_type.setter
    def s_type(self, s_type: str):
        self._s_type = s_type

    @property
    def prefix(self) -> str:
        return self._prefix

    @prefix.setter
    def prefix(self, prefix: str):
        self._prefix = prefix

    @property
    def traffic_id(self) -> str:
        return self._traffic_id

    @traffic_id.setter
    def traffic_id(self, traffic_id: str):
        self._traffic_id = traffic_id

    @property
    def src(self) -> str:
        return self._src

    @src.setter
    def src(self, src: str):
        self._src = src

    @property
    def dst(self) -> str:
        return self._dst

    @dst.setter
    def dst(self, dst: str):
        self._dst = dst

    @property
    def bandwidth(self) -> int:
        return self._bandwidth

    @bandwidth.setter
    def bandwidth(self, bandwidth: int):
        self._bandwidth = bandwidth

    @property
    def duration(self) -> int:
        return self._duration

    @duration.setter
    def duration(self, duration: int):
        self._duration = duration

    @property
    def service_type(self) -> List[str]:
        return self._service_type

    @service_type.setter
    def service_type(self, service_type: List[str]):
        self._service_type = service_type

