from django.test import TestCase
from typing import NamedTuple, List
from bitarray import bitarray
import struct
import math


"""
極座標情報を 64bitにパック/アンパックするモジュール
精度は最大0.75cm
極に行くほど間隔が狭まる

"""


def fill_bits(size: int) -> int:
    b = 0
    for i in range(size):
        b = b << 1
        b = b | 1
    return b


def take_bit(V: bytes, begin: int, size: int) -> int:
    a = bitarray(endian="little")
    a.frombytes(V)
    result = 0
    for i in range(size):
        result = result << 1
        result = result | a[i+begin]

    return result


# ビット単位で上書き
def write_bits(src: bytes, begin: int, size: int, val: int) -> bytes:
    # まずsrcをbitarrayにする
    a = bitarray(endian="little")
    a.frombytes(src)
    b = bitarray(endian="little")
    b.frombytes(val.to_bytes(8, "little"))

    print(f"BEGIN {begin} size:{size} val:{val}")

    for i in range(size):
        a[begin+size-(i+1)] = b[i]

    print(f"A={a}")
    return a.tobytes()


class GeoTime(NamedTuple):
    Minute: int
    Second: int
    Millisec: int


# 最大精度3cmの点->1点当たりの容量 64bit!
class GeoPoint(NamedTuple):
    latitude: int
    lat_time: GeoTime
    longitude: int
    long_time: GeoTime

    def __str__(self):
        return f"""
LATITUDE={self.latitude},{self.lat_time.Minute},{self.lat_time.Second},{self.lat_time.Millisec}
LONGITUDE={self.longitude},{self.long_time.Minute},{self.long_time.Second},{self.long_time.Millisec}
"""

    def Pack(self) -> bytes:
        # int64にpackする
        result = bytes(8)
        EW_PM = 0b0 if self.longitude < 0 else 0b1
        NS_PM = 0b0 if self.latitude < 0 else 0b1

        result = write_bits(result, 0, 1, EW_PM)  # EW
        result = write_bits(result, 1, 8, abs(self.longitude))  # angle
        result = write_bits(result, 9, 6, self.long_time.Minute)  # minute
        result = write_bits(result, 15, 6, self.long_time.Second)  # second
        result = write_bits(result, 21, 12, self.long_time.Millisec)  # msec

        result = write_bits(result, 33, 1, NS_PM)  # NS
        result = write_bits(result, 34, 7, abs(self.latitude))  # angle
        result = write_bits(result, 41, 6, self.lat_time.Minute)  # Minute
        result = write_bits(result, 47, 6, self.lat_time.Second)  # Second
        result = write_bits(result, 53, 11, self.lat_time.Millisec)  # NS

        return result

    @staticmethod
    def From(V: bytes):
        """
EW  180 60 60 4000
    1  + 8 + 6 + 6 + 12 = 33
NS  90 60 60 2000 
    1  + 7 + 6 + 6 + 11 = 31
"""
        print(V)

        EW = take_bit(V, 0, 1)
        EW_ANGLE = take_bit(V, 1, 8)
        EW_MINUTE = take_bit(V, 9, 6)
        EW_SECOND = take_bit(V, 15, 6)
        EW_MILLISEC = take_bit(V, 21, 12)

        NS = take_bit(V, 33, 1)
        NS_ANGLE = take_bit(V, 34, 7)

        NS_MINUTE = take_bit(V, 41, 6)
        NS_SECOND = take_bit(V, 47, 6)
        NS_MILLISEC = take_bit(V, 53, 11)

        longitude = - EW_ANGLE if EW == 0 else EW_ANGLE
        latitude = - NS_ANGLE if NS == 0 else NS_ANGLE

        return GeoPoint(
            latitude=latitude,
            lat_time=GeoTime(
                Minute=NS_MINUTE,
                Second=NS_SECOND,
                Millisec=NS_MILLISEC
            ),
            longitude=longitude,
            long_time=GeoTime(
                Minute=EW_MINUTE,
                Second=EW_SECOND,
                Millisec=EW_MILLISEC
            )
        )


# 三角形領域ベースの座標(つまり三点取れる)
class GeoFlagment(NamedTuple):
    UpDown: bool
    Way5: int
    Depth: List[int]  # 三角形領域の場所リスト


if __name__ == "__main__":
    Ge = GeoPoint(
        latitude=-90,
        lat_time=GeoTime(
            Minute=20,
            Second=12,
            Millisec=211
        ),
        longitude=+100,
        long_time=GeoTime(
            Minute=20,
            Second=12,
            Millisec=211
        )
    )

    print("Pre-Pack")
    print(Ge)
    Packed = Ge.Pack()
    print(f"{Packed}")
    unpacked = GeoPoint.From(Packed)
    print("unpacked")
    print(unpacked)
