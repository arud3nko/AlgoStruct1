import array
from ctypes import (Structure, c_int, c_void_p, c_size_t, c_double, c_long, POINTER, CDLL)
from typing import NoReturn, List, Union
import atexit


lib = CDLL("/Users/egorrudenko/CLionProjects/aads1/libtest.so")


class Element(Structure):
    """Equals C-structure Element"""

    _fields_ = [("type", c_int),
                ("data", c_void_p)]


class CArray(Structure):
    """Equals C-structure Array"""

    _fields_ = [("array", POINTER(Element)),
                ("used", c_size_t),
                ("size", c_size_t)]


class LongPopResult(Structure):
    """Equals C-structure LongPopResult"""

    _fields_ = [("resultCode", c_int),
                ("result", c_long)]


class DoublePopResult(Structure):
    """Equals C-structure DoublePopResult"""

    _fields_ = [("resultCode", c_int),
                ("result", c_double)]


class Array:
    """Класс Array позволяет работать с модулем на Си, реализующим хранение данных в массиве

    Основное применение - хранение данных в массиве и работа с этим массивом, весь функционал
    массива реализован как модуль на языке Си.

    Note:
        Реализованы структуры, позволяющие создать динамический массив с разными типами переменных,
        но ввиду сути задания полный функционал не реализован.

    Attributes:
    ----------
        typecode: str
            Код типа данных, которые будут храниться в списке. "i" - long, "d" - double, "a" - any
        initializer: List[Union[int, float]] = None
            Опциональный аттрибут, если указан то используем его значение (список int/float) в качестве
            данных для инициализации массива.

    Methods:
    ------
        __len__()
            Метод для получения длины списка, вызывает функцию в модуле Си
        __getitem__(pos: int)
            Метод для получения значения элемента списка по его индексу
        __str__()
            Метод для строкового вывода массива, переопределяет принт
        __eq__(other: array.array)
            Метод для проверки объектов на эквивалентность
        pop(pos: int = -1)
            Метод удаляет элемент из массива с возвратом
        search(arg: Union[int, float])
            Метод для бинарного поиска, массив заранее сортируется
        remove(value: Union[int, float])
            Метод для удаления элемента из списка, без возврата
        append(arg: Union[int, float])
            Метод для вставки элемента в конец списка
        insert(pos: int, arg: Union[int, float])
            Метод для вставки элемента в указанную позицию по индексу
    """

    def __init__(self, typecode: str, initializer: List[Union[int, float]] = None) -> None:

        if not (typecode in ["i", "d", "a"]):
            # i -> integer(long),
            # d -> float(double),
            # a -> multiple types (any)
            raise TypeError("[Array] Unsupported typecode")

        lib.initArray.argtypes = [POINTER(CArray), c_int]
        lib.freeArray.argtypes = [POINTER(CArray)]
        lib.insertInt.argtypes = [POINTER(CArray), c_int]
        lib.insertDouble.argtypes = [POINTER(CArray), c_double]
        lib.insertLong.argtypes = [POINTER(CArray), c_long]
        lib.printArray.argtypes = [POINTER(CArray)]
        lib.getArrayLength.argtypes = [POINTER(CArray)]
        lib.returnType.argtypes = [POINTER(CArray), c_int]
        lib.returnInt.argtypes = [POINTER(CArray), c_int]
        lib.returnDouble.argtypes = [POINTER(CArray), c_int]
        lib.returnLong.argtypes = [POINTER(CArray), c_int]
        lib.insertLongToPos.argtypes = [POINTER(CArray), c_long]
        lib.insertDoubleToPos.argtypes = [POINTER(CArray), c_double]
        lib.binarySearchLong.argtypes = [POINTER(CArray), c_long]
        lib.binarySearchDouble.argtypes = [POINTER(CArray), c_double]
        lib.removeLong.argtypes = [POINTER(CArray), POINTER(CArray), c_long]
        lib.removeDouble.argtypes = [POINTER(CArray), POINTER(CArray), c_double]
        lib.insertLongAtPos.argtypes = [POINTER(CArray), POINTER(CArray), c_long, c_int]
        lib.insertDoubleAtPos.argtypes = [POINTER(CArray), POINTER(CArray), c_double, c_int]
        lib.popLong.argtypes = [POINTER(CArray), POINTER(CArray), c_int]
        lib.popDouble.argtypes = [POINTER(CArray), POINTER(CArray), c_int]

        lib.getArrayLength.restype = c_size_t
        lib.returnInt.restype = c_int
        lib.returnDouble.restype = c_double
        lib.returnLong.restype = c_long
        lib.returnType.restype = c_int
        lib.binarySearchLong.restype = c_int
        lib.binarySearchDouble.restype = c_int
        lib.removeLong.restype = c_int
        lib.popLong.restype = LongPopResult
        lib.popDouble.restype = DoublePopResult

        self.array = CArray()
        self.typecode = typecode

        if initializer and (initializer != []):
            lib.initArray(self.array, len(initializer))
            for element in initializer:
                self.append(element)
        else:
            lib.initArray(self.array, 1)  # empty arr initialization

        atexit.register(self.__free)

    def __len__(self) -> int:
        """Метод для получения длины списка, вызывает функцию в модуле Си

            Returns:
                value: int
                    Значение длины списка
        """
        return int(lib.getArrayLength(self.array))

    def __getitem__(self, pos: int) -> Union[int, float]:
        """Метод для получения значения элемента списка по его индексу

        Parameters:
            pos: int
                Индекс элемента

        Returns:
            value: int, float
                Значение элемента int, если его тип - long | Значение элемента float,
                если его тип - double

        Raises:
            ValueError
                Если ошибка с переменной, возвращает ошибку

        """

        self.__index_error_handler(pos)
        el_type = lib.returnType(self.array, pos)
        if el_type == 0:  # et_long
            return lib.returnLong(self.array, pos)
        elif el_type == 1:  # et_dbl
            return lib.returnDouble(self.array, pos)
        else:
            raise ValueError("[Array] Unexpected error")

    def __setitem__(self, key: int, value: Union[int, float]) -> None:
        """Метод для вставки значения в позицию по индексу
            + проверка на индекс
            + проверка на перегруз

        Parameters:
            key: int
                Индекс позиции
            value: Union[int, float]
                Значение int/float
        """

        self.__index_error_handler(key)
        self.__overflow_error_handler(value)
        if self.typecode == "i":
            lib.insertLongToPos(self.array, value, key)
        elif self.typecode == "d":
            lib.insertDoubleToPos(self.array, value, key)

    def __str__(self) -> str:
        """Метод для строкового вывода массива, переопределяет принт

        Returns:
            value: str
                Строковое представление массива
        """
        return f"{[i for i in self]}"

    def __eq__(self, other: array.array) -> bool:
        """Метод для проверки объектов на эквивалентность

        Parameters:
            other: array.array
                Объект array для сравнения

        Returns:
            value: bool
                True - эквивалентны; False - разные
        """
        for i in range(len(self)):
            if self[i] != other[i]:
                return False
        return True

    def pop(self, pos: int = -1) -> Union[int, float]:
        """Метод удаляет элемент из массива с возвратом

        Создает новый массив, освобождает старый

            Parameters:
                pos: int, optional
                    Индекс элемента, если не задан: -1

            Returns:
                value: Union[int, float]
                    Возврат удаленного элемента, в зависимости от typecode: int/float

            Raises:
                IndexError
                    Если индекс выходит за пределы массива
        """

        result = None
        temp = CArray()
        lib.initArray(temp, 1)
        if self.typecode == "i":
            result = lib.popLong(self.array, temp, pos)
        elif self.typecode == "d":
            result = lib.popDouble(self.array, temp, pos)
        if result.resultCode:
            self.__free()
            self.array = temp
            return result.result
        raise IndexError(f"[Array] Index {pos} out of range")

    def search(self, arg: Union[int, float]) -> Union[int, float]:
        """Метод для бинарного поиска, массив заранее сортируется

            Parameters:
                arg: Union[int, float]
                    Значение элемента для поиска

            Returns:
                pos: Union[int, float]
                    Позиция найденного элемента в отсортированном массиве

            Raises:
                ValueError
                    Если элемент с заданным значением не найден в массиве

        """
        pos = -1
        if self.typecode == "i":
            pos = lib.binarySearchLong(self.array, arg)
        elif self.typecode == "d":
            pos = lib.binarySearchDouble(self.array, arg)
        if pos == -1:
            raise ValueError(f"[Array] Value {arg} not found")
        return pos

    def __index_error_handler(self, pos: int) -> NoReturn:
        """Приватный метод для отслеживания ошибки индексации

            Parameters:
                pos: int
                    Индекс

            Raises:
                IndexError
                    Если массив пустой
                    Если индекс выходит за пределы массива
        """

        if self.__len__() == 0:
            raise IndexError("[Array] Array is empty")
        if (pos < -self.__len__()) or (pos >= self.__len__()):
            raise IndexError(f"[Array] Index {pos} out of range")

    def remove(self, value: Union[int, float]) -> NoReturn:
        """Метод для удаления элемента из списка, без возврата

        Создает новый массив, освобождает старый

        Parameters:
            value: Union[int, float]
                Значение элемента который будет удален

        Raises:
            ValueError
                Если код ответа от функции в Си равен -1 => элемент не найден

        """

        res = 0
        temp = CArray()
        lib.initArray(temp, 1)
        if self.typecode == "i":
            res = lib.removeLong(self.array, temp, value)
        elif self.typecode == "d":
            res = lib.removeDouble(self.array, temp, value)
        if res == -1:
            raise ValueError(f"[Array] Value {value} not found")
        self.__free()
        self.array = temp

    def append(self, arg: Union[int, float]) -> NoReturn:
        """Метод для вставки элемента в конец списка

            Parameters:
                arg: Union[int, float]
                    Значение элемента (int/float)

            Note:
                Начата реализация для массива с произвольными типами, но не функционирует нормально

            Raises:
                TypeError
                    Если typecode массива не равен типу переданного значения
        """

        if self.typecode == "a":
            if isinstance(arg, int):
                self.__insert_long(arg)
            elif isinstance(arg, float):
                self.__insert_double(arg)
            elif isinstance(arg, list):
                for element in arg:
                    self.append(element)
            else:
                raise TypeError("[Array] Unexpected type")
        elif self.typecode == "i":
            if isinstance(arg, int):
                self.__insert_long(arg)
            else:
                raise TypeError(f"[Array] Expected type: int, got {arg} instead")
        elif self.typecode == "d":
            if isinstance(arg, (int, float)):
                self.__insert_double(arg)
            else:
                raise TypeError(f"[Array] Expected types: (int, float), got {arg} instead")

    def insert(self, pos: int, arg: Union[int, float]) -> NoReturn:
        """Метод для вставки элемента в указанную позицию по индексу

        Создает новый массив, освобождает старый

        Parameters:
            pos: int
                Индекс
            arg: Union[int, float]
                Значение элемента

        """

        temp = CArray()
        lib.initArray(temp, 1)

        if self.typecode == "i":
            lib.insertLongAtPos(self.array, temp, arg, pos)
        elif self.typecode == "d":
            lib.insertDoubleAtPos(self.array, temp, arg, pos)

        self.__free()
        self.array = temp

    def __insert_int(self, arg: int) -> NoReturn:
        """Метод для запуска Си-функции insertInt + проверка на перегруз

        Note:
            Реализована для массива с произвольными типами, не функционирует

        Parameters:
            arg: int
                Значение элемента
        """

        self.__overflow_error_handler(arg)
        lib.insertInt(self.array, arg)

    def __insert_double(self, arg: float) -> NoReturn:
        """Метод для запуска Си-функции insertDouble

        Parameters:
            arg: float
                Значение элемента
        """

        lib.insertDouble(self.array, arg)

    def __insert_long(self, arg: int) -> NoReturn:
        """Метод для запуска Си-функции insertLong + проверка на overflow

        Parameters:
            arg: int
                Значение элемента
        """

        self.__overflow_error_handler(arg)
        lib.insertLong(self.array, arg)

    def __free(self) -> NoReturn:
        """Метод для освобождения памяти, запускает Си-функцию free

        Note:
            С помощью atexit запускается при закрытии скрипта
        """
        lib.freeArray(self.array)

    @staticmethod
    def __overflow_error_handler(arg: int) -> NoReturn:
        """Статический метод для проверки на overflow числа типа long

        Parameters:
            arg: int
                Значение

        Raises:
            OverflowError
                Если макс значение превышено
        """
        if arg > 2147483647:
            raise OverflowError("[Array] Variable overflow")


if __name__ == '__main__':
    pass
