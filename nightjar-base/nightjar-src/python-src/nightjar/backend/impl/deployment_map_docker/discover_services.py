
from typing import List, Sequence, Optional
import docker  # type: ignore
from .config import DockerConfig


class ContainerPort:
    __slots__ = ('internal_port', 'public_port',)

    def __init__(self, internal_port: str, public_port: Optional[str]) -> None:
        self.internal_port = internal_port
        self.public_port = public_port


class Container:
    __slots__ = ('name', 'image', 'hash_id', 'port_map')

    def __init__(self, name: str, image: str, hash_id: str, port_map: Sequence[ContainerPort]) -> None:
        self.name = name
        self.image = image
        self.hash_id = hash_id
        self.port_map = tuple(port_map)


class AbcDiscoverServices:
    """
    ALlows for easy mocking.
    """
    def get_running_container_ports(self) -> List[Container]:
        raise NotImplementedError()


class DockerDiscoverServices(AbcDiscoverServices):
    def __init__(self, _config: DockerConfig) -> None:
        # Should allow using config...
        self.client = docker.from_env()

    def get_running_container_ports(self) -> List[Container]:
        ret: List[Container] = []
        for dc in self.client.containers.list():
            if dc.status == 'running':
                hash_id = dc.id
                image = dc.image.id
                name = dc.name
                port_map: List[ContainerPort] = [
                    ContainerPort(pub, pri)
                    for pub, pri in dc.ports.items()
                ]
                ret.append(Container(name, image, hash_id, port_map))
        return ret
