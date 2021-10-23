from abc import abstractmethod, ABC


class Blueprint(ABC):
    @abstractmethod
    def build(self):
        pass
