import bf


class TestWrappingInt:
    def test_new(self):
        assert isinstance(bf.WrappingInt(1), bf.WrappingInt)
        assert bf.WrappingInt(3, 0, 4) == 3
        assert bf.WrappingInt(3, 0, 2) == 0
        assert bf.WrappingInt(3, 1, 2) == 1
        assert bf.WrappingInt(-1, 0, 2) == 2
        assert bf.WrappingInt(1, 2, 3) == 3
        assert bf.WrappingInt(1, 4, 7) == 5
        assert bf.WrappingInt(2, 3, 4) == 4
        assert bf.WrappingInt(1) == 1
        assert bf.WrappingInt(-1, -3, -2) == -3
        assert bf.WrappingInt(3, -1, 2) == -1

    def test_addition_subtraction(self):
        x = bf.WrappingInt(0) + bf.WrappingInt(1)
        assert isinstance(x, bf.WrappingInt)
        assert x == 1
        x = bf.WrappingInt(0) + 1
        assert x == 1
        assert isinstance(x, bf.WrappingInt)
        x = bf.WrappingInt(1) + 1
        assert x == 0
        assert isinstance(x, bf.WrappingInt)
