from FieldElement import FieldElemet, BitcoinFieldElement, P
import hashlib
from random import randrange
import hmac

class EllipticPoint:  #Point in book
    def __init__(self, x, y, a, b):
        '''
        x, y, a, b 分别对应椭圆曲线公式上的参数
        '''
        self.x = x
        self.y = y
        self.a = a
        self.b = b
        if x is None and y is None:
            return
        #验证x,y是否在曲线上，也就是将x,y带入公式后左右两边要想等
        if self.y ** 2 != self.x ** 3 + self.a * self.x + self.b:
            raise ValueError(f"x:{self.x}, y:{self.y} is no a elliptic point")

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y and self.a == other.a and self.b == other.b

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y or self.a != other.a or self.b != other.b

    def __repr__(self):
        return f"x:{self.x}, y:{self.y}, a:{self.a}, b:{self.b}"

    def __add__(self, other):
        #首先判断给定点在该椭圆曲线上
        if self.a != other.a or self.b != other.b:
            raise ValueError(f"given point is no on the samve elliptic curve")

        # 如果本身是零元，那么实现I + A = A
        if self.x is None and self.y is None:
            return other

        # 如果输入点是零元，那么加法结果就是本身：
        if other.x is None and other.y is None:
            return self

        # 如果输入点与当前点互为相反数，也就是关于x轴对称，那么返回无限远交点I
        if self.x == other.x and self.y != other.y: # 这里针对有限群里面的点进行了修改
            print("add to infinity!!")
            return self.__class__(None, None, self.a, self.b)

        '''
        如果当前点与给定点形成的直线与椭圆曲线有三个交点，首先我们要计算A(x1,y1),B(x2,y2)所形成直线的斜率
        s = (y2-y1)/(x2-x1), 于是A,B所形成的直线方程就是 y = s * (x-x1) + y1,
        由于椭圆曲线的方程为 y^2 = x^2 + a*x + b，由于直线与曲线相交，假设叫点的坐标为x', y'
        由于交点在直线上，因此满足 y' = s * (x' - x1) + y1, 同时又满足y' ^ 2 = x' ^ 3 + a * x' + b,
        将左边带入到右边就有：
        (s * (x' - x1)) ^ 2 = x' ^ 3 + a * x' + b
        把公式左边挪到右边然后进行化简后就有：
        x ^3 - (s^2) * (x^2) + (a + 2*(s^2)*x1 - 2*s*y1)*x + b - (s^2)*(x1^2)+2*s*x1*y1-(y1 ^2) = 0  (公式1）
        如果我们把第三个交点C的坐标设置为(x3, y3)，于是A，B,C显然能满足如下公式：
        (x-x1)*(x-x2)*(x-x3) = 0
        将其展开后为：
        x^3 - (x1 + x2 + x3) * (x^2) + (x1*x2 + x1*x3 + x2+x3)*x - x1*x2*x3 = 0  （公式2）
        我们把公式1 和公式2中对应项的系数一一对应起来，也就是两个公式中x^3的系数是1，公式1中x^2的系数是(s^2)，
        公式2中x^2的系数为(x1 + x2 + x3)，于是对应起来：
        s^2 <-> (x1 + x2 + x3)  （#1）
        公式1中x对应系数为(a + 2*(s^2)*x1 - 2*s*y1), 公式2中x对应系数为(x1*x2 + x1*x3 + x2+x3)，于是对应起来：
        (a + 2*(s^2)*x1 - 2*s*y1) <-> (x1*x2 + x1*x3 + x2+x3)
        公式1中常数项为b - (s^2)*(x1^2)+2*s*x1*y1-(y1 ^2), 公式2中常数项为 x1*x2*x3，对应起来就是：
        b - (s^2)*(x1^2)+2*s*x1*y1-(y1 ^2) <-> x1*x2*x3
        
        根据代数理论中中的Vieta定律，如果如果两个多项式的根要相同，他们对应项的系数必须相等，于是有：
        s^2 = (x1 + x2 + x3)  （#1）
        (a + 2*(s^2)*x1 - 2*s*y1) = (x1*x2 + x1*x3 + x2+x3)
        b - (s^2)*(x1^2)+2*s*x1*y1-(y1 ^2) = x1*x2*x3
        于是我们可以从(#1)中把x3 解出来：
        x3 = s^2 - x1 - x2 
        然后把x3放入直线方程将y3解出来：
        y3 = -(s(x3-x1)+y1) = s * (x1 - x3) - y1
        '''
        if self.x != other.x:
            s = (other.y - self.y) / (other.x - self.x)
            x3 = s ** 2 - self.x - other.x
            y3 = s * (self.x - x3) - self.y
            return self.__class__(x3, y3, self.a, self.b)
        '''
        如果self.x == other.x and self.y == other.y ,这种情况下对应椭圆曲线上一点的切线，这时
        我们要计算切线与曲线的另一个交点。根据微积分，函数f(x)在给定点x处的切线对应斜率就是f'(x)，
        椭圆曲线函数为y^2 = x^3 + a*x + b, 左右两步对x求导有：
        2y*(d(y)/d(x)) = 3x^2 + a, d(y)/d(x)就是f'(x),我们需要将其计算出来，也就有:
        s = d(y)/d(x) = (3*x^2+a)/(2*y),接下来的计算跟上面一样，只不过把x2换成x1,于是有：
        x3 = s^2 - 2*x1, y3 = s * (x1 - x3) - y1
        '''
        if self == other : #这里针对有限群的元素进行修改
            s = (3 * self.x ** 2 + self.a) / (2 * self.y)  #修改bug
            x3 = s ** 2 - 2 * self.x
            y3 = s * (self.x - x3) - self.y
            return self.__class__(x3, y3, self.a, self.b)

        '''
        还有最后一种情况，直线不但与y轴平行，而且还是曲线的切线，有就是一根竖直线与曲线在圆头出相切，
        这个点也是y坐标为0的点
        '''
        if self == other and 0 * self.x: #这里的修改可以应对有限群元素的情况
            return self.__class__(None, None, self.a, self.b)

    def __rmul__(self, scalar):
        result = self.__class__(None, None, self.a, self.b)
        current = self
        while scalar:
            if scalar & 1:
                result += current
            current += current
            scalar >>= 1
        return result





A = 0
B = 7
N = 0xfffffffffffffffffffffffffffffffebaaedce6af48a03bbfd25e8cd0364141


class BitcoinEllipticPoint(EllipticPoint):  #S256Point
    def __init__(self, x, y, a = None, b = None):
        a, b = BitcoinFieldElement(A), BitcoinFieldElement(B)
        if type(x) == int:
            super().__init__(x = BitcoinFieldElement(x), y = BitcoinFieldElement(y), a = a, b = b)
        else:
            super().__init__(x = x, y = y, a = a, b = b)

    def __rmul__(self, scalar):
        scalar = scalar % N
        return super().__rmul__(scalar)

    def verify(self, z, sig):
        s_invert = pow(sig.s, N- 2, N) #费马小定理计算s的逆
        u = z * s_invert % N
        v = sig.r * s_invert % N
        total = u * G + v * self
        return total.x.num == sig.r

    def sec(self, compressed = True):
        if compressed:
            if self.y.num % 2 == 0:
                return b'\x02' + self.x.num.to_bytes(32, 'big')
            else:
                return b'\x03' + self.x.num.to_bytes(32, 'big')
        '''
        sec压缩在开头写入04,然后跟着32字节的x坐标值,最后跟着32字节的y坐标值
        '''
        return b'\x04' + self.x.num.to_bytes(32, 'big') + self.y.num.to_bytes(32, 'big')

    def parse(self, sec_bin): #解析sec压缩数据
        if sec_bin[0] == 4: #非压缩sec格式
            x = int.from_bytes(sec_bin[1:33], 'big')
            y = int.from_bytes(sec_bin[33:65], 'big')
            return BitcoinEllipticPoint(x = x, y = y)

        #在压缩sec的格式下，先获取x，然后计算y的平方，最后使用开方算法获得y的值
        is_even = sec_bin[0] == 2
        x = BitcoinEllipticPoint(int.from_bytes(sec_bin[1:], 'big'))
        #y ^ 2 = x ^3 + 7
        alpha = x ** 3 + BitcoinEllipticPoint(B)
        beta = alpha.sqrt()
        '''
        在实数域中,y会对应一正一负两个值，在有限域中同理，如果y和(p-y)互为正和负.
        也就是在有限群中，如果y满足椭圆方程，那么p-y同样满足椭圆方程。由于比特币对应有限群中元素个数P为素数，
        因此如果y 是偶数，那么p-y就是奇数，如果y是奇数，那么p-y是偶数。于是在压缩SEC格式中，如果开头标志位为0x02，
        那么如果计算出来的y是奇数，那么就要采用P-y
        '''
        if beta.num % 2 == 0: #y是偶数，P-y是奇数
            even_beta = beta
            odd_beta = BitcoinFieldElement(P - beta.num)
        else: #y是奇数，P-y是偶数
            even_beta = BitcoinFieldElement(P - beta.num)
            odd_beta = beta

        if is_even:
            return BitcoinEllipticPoint(x, even_beta)
        else:
            return BitcoinEllipticPoint(x, odd_beta)

    def hash160(self, compressed=True):
        return hash160(self.sec(compressed))

    def address(self, compressed=True, testnet=False):
        h160 = self.hash160(compressed)
        if testnet:
            prefix = b'\x6f'
        else:
            prefix = b'\x00'
        return encode_base58_checksum(prefix + h160)


G = BitcoinEllipticPoint(0x79be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798,
                         0x483ada7726a3c4655da4fbfc0e1108a8fd17b448a68554199c47d08ffb10d4b8)


def verify_signature(r, s, z, P):
    s_invert = pow(s, N - 2, N)  # 使用费马小定理直接找到s的逆元素
    u = z * s_invert % N  # u = z / s
    v = r * s_invert % N # v = r / s
    return (u * G + v * P).x.num == r # 检验x坐标对应数值是否等于 r


class Signature:
    def __init__(self, r, s):
        self.r = r
        self.s = s

    def __repr__(self):
        return f"Signature({hex(self.r)}, {hex(self.s)})"

    def der(self):
        #现将r转换为大端格式
        rbin = self.r.to_bytes(32, byteorder='big')
        #去掉开始的0x00内容
        rbin = rbin.lstrip(b'\0x00')
        if rbin[0] & 0x80: # 如果头字节>=0x80，在前头添加0x00
            rbin = '\0x00' + rbin
        #以0x2开头，接着是r的长度，最后是r的内容
        result = bytes([2, len(rbin)]) + rbin

        sbin = self.s.to_bytes(32, byteorder='big')
        sbin.lstrip(b'\0x00')
        if sbin[0] & 0x80:
            sbin = b'0x00' + sbin
        result += bytes([2, len(sbin)]) + sbin
        '''
        以0x30开头，跟着是r和s的总长度，然后是r和s的编码
        '''
        print(f"der total bytes:{len(result)}")
        return bytes([0x30, len(result)]) + result


class PrivateKey:
    def __init__(self, secret):
        self.secret = secret
        self.point = secret * G

    def hex(self):
        return "{:x}".format(self.secret).zfill(64)

    def sign(self, z):
        k = randrange(N)
        r = (k * G).x.num
        k_invert = pow(k, N - 2, N)
        s = (z + r * self.secret) * k_invert % N
        if s > N / 2:
            s = N - s
        return Signature(r, s)

    def deterministic_k(self, z):
        k = b'\x00' * 32
        v = b'\x01' * 32
        if z > N:
            z -= N
        z_bytes = z.to_bytes(32, 'big')
        secret_bytes = self.secret.to_bytes(32, 'big')
        s256 = hashlib.sha256
        k = hmac.new(k, v + b'\x00' + secret_bytes + z_bytes, s256).hexdigest()
        v = hmac.new(k, v, s256).digest()
        k = hmac.new(k, v + b'\0x1' + secret_bytes + z_bytes, s256).digest()
        v = hmac.new(k, v, s256).digest()
        while True:
            v = hmac.new(k, v, s256).digest()
            candidate = int.from_bytes(v, 'big')
            if candidate >= 1 and candidate < N:
                return candidate
            k = hmac.new(k ,v + b'\x00', s256).digest()
            v = hmac.new(k, v, s256).digest()

    def wif(self, compressed = True, testnet = False):
        #先将秘钥转换为大端字节序
        secret_bytes = self.secret.to_bytes(32, 'big')
        if testnet: #根据主网还是测试网添加前缀
            prefix = b'\xef'
        else:
            prefix = b'\x80'

        if compressed: # 根据压缩形态添加后缀
            suffix = b'\x01'
        else:
            suffix = b'\01'

        return encode_base58_checksum(prefix + secret_bytes + suffix)



'''
给定如下私钥，求它公钥的压缩sec个数：
5001， 2019 ^ 5, 0xdeadbeef54321
'''
priv = PrivateKey(5001)
print(priv.point.sec(True).hex())

priv = PrivateKey(2019 ** 5)
print(priv.point.sec(True).hex())

priv = PrivateKey(0xdeadbeef54321)
print(priv.point.sec(True).hex())

'''
r =  0x37206a0610995c58074999cb9767b87af4c4978db68c06e8e6e81d282047a7c6
s =  0x8ca63759c1157ebeaec0d03cecca119fc9a75bf8e6d0fa65c841c8e2738cdaec
获取der编码
'''
sig = Signature(0x37206a0610995c58074999cb9767b87af4c4978db68c06e8e6e81d282047a7c6,
                0x8ca63759c1157ebeaec0d03cecca119fc9a75bf8e6d0fa65c841c8e2738cdaec)
print(f"signature der format:{sig.der().hex()}")

'''
base58 的编码字符没有小写的l和大写的I,以及大写的字母O
'''
BASE58_ALPHABET = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz'
def encode_base58(s):
    '''
    先统计要编码的数据以多少个0开头
    '''
    count = 0
    for c in s:
        if c == 0:
            count += 1
        else:
            break

    num = int.from_bytes(s, 'big')
    prefix = '1' * count
    result = ''
    while num > 0:
        num, mod = divmod(num, 58)
        result = BASE58_ALPHABET[mod] + result

    return prefix + result




'''
测试base58编码
'''
encode = encode_base58(bytes.fromhex('7c076ff316692a3d7eb3c3bb0f8b1488cf72e1afcd929e29307032997a838a3d'))
print(f"base58 encode:{encode}")


def encode_base58_checksum(b):
    '''
    实现地址编码的第4，5两步
    '''
    return encode_base58(b + hash256(b)[:4])


def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()

'''
在比特币应用中,哈希256都会连续执行两次以增强安全性
'''
def hash256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()

'''
实现整形与小端编码的相互转换
'''
def little_endian_to_int(b):
    return int.from_bytes(b, 'little')


def int_to_little_endian(n, length):
    return n.to_bytes(length, 'little')

'''
我们使用一段文字进行256哈希形成秘钥，然后设置秘钥的地址格式
'''
secret_text = "this is my secret key"
secret = little_endian_to_int(hash256(secret_text.encode('utf-8')))
priv = PrivateKey(secret)
print(f"secret key address:{priv.point.address(testnet=True)}")

'''
测试椭圆曲线点的地址编码
'''
priv = PrivateKey(5002)
print(f"address for uncompressed SEC on testnet:{priv.point.address(compressed = False, testnet = True)}")

'''
检验秘钥的序列化功能
'''
priv = PrivateKey(5003)
print(f"secret key wif:{priv.wif(True, True)}")
