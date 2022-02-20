P = 2 ** 256 - 2 ** 32 - 977

class FieldElemet:
    def __init__(self, num, prime):
        # prime 对应群的大小，也就是元素的数量, num就是元素对应数值
        if num >= prime or num < 0:
            # 群元素必须是大于等于0的整数
            error = f'field element shound be integer in range 0 to {prime-1}'
            raise ValueError(error)
        self.num = num
        self.prime = prime

    def __repr__(self):
        return f'FieldElement with value:{self.num} and order:{self.prime}'

    def __eq__(self, other):
        if other is None:
            return False
        return self.num == other.num and self.prime == other.prime

    def __add__(self, other):
        if self.prime != other.prime:
            raise TypeError('there are two different field')
        num = (self.num + other.num) % self.prime
        #新建生成一个对象
        return self.__class__(num, self.prime)
    def __sub__(self, other):
        if self.prime != other.prime:
            raise TypeError('there are two different fields')
        num = (self. num - other.num) % self.prime
        return self.__class__(num, self.prime)

    def __mul__(self, other):
        if self.prime != other.prime:
            raise TypeError('there are two different fields')
        num = (self.num * other.num) % self.prime
        return self.__class__(num, self.prime)

    def __pow__(self, num):
        num = num % self.prime
        num = pow(self.num, num, self.prime)
        return self.__class__(num, self.prime)

    def __truediv__(self, other):
        if self.prime != other.prime:
            raise TypeError('there are two different fields')
        # 使用费马小定理找到除数在有限群中的逆
        num = (self.num * pow(other.num, self.prime - 2, self.prime)) % self.prime
        return self.__class__(num, self.prime)

    def  __rmul__(self, other): #实现元素与常量相乘
        num = (self.num * other) % self.prime
        return self.__class__(num, self.prime)

    def sqrt(self):
        return self ** ((P+1) // 4)


class BitcoinFieldElement(FieldElemet):  #S256Field
    def __init__(self, num, prime = None):
        super().__init__(num, P)
    def __repr__(self):
        return "{:x}".format(self.num).zfill(64)  # 填满64个数字
