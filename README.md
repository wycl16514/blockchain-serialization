有过区块链开发相关工作经验的同学知道，要开发智能合约的应用，你首先需要通过geth同步以太坊主网，这意味着你需要从其他节点下载很多数据。另外在使用区块链技术时，例如支付，接收数字货币时，“钱包”应用需要发送一系列数据给对方，当我们需要通过网络收发数据时就需要对数据进行序列化。

前面我们了解了很多数据结构，例如有限群，椭圆曲线，公钥，私钥等，相关数据在应用时都需要通过网络进行数据传输，因此相关的数据结构需要进行序列化。对于椭圆曲线上一个点，在序列化时通常采用一种叫做非压缩SEC(standard for efficient cryptography)的数据格式，其步骤为：
1，在开头添加0x04作为标志
2，放置点的x坐标数值，它有32字节
3，放置点的y坐标数值，他有32字节。

相应的序列化代码如下：
```
    def sec(self):
        '''
        sec压缩在开头写入04,然后跟着32字节的x坐标值,最后跟着32字节的y坐标值
        '''
        return b'\x04' + self.x.num.to_bytes(32, 'big') + self.y.num.to_bytes(32, 'big')
```
既然有非压缩那就有对应的压缩形态SEC，由于椭圆曲线关于x轴对称，因此给定一个x坐标，它最多对应两个y坐标，这两个y互为相反数。但由于我们作用在椭圆曲线上的点都是有限群里面的元素，对于含有p个元素的群而言(注意到p是素数)，如果y是群里面的元素，那么"-y"就是p-y，如果y是偶数，那么p-y就是奇数，反之如果y是奇数，那么p-y就是偶数。利用这个特点我们可以压缩y坐标对应的内容。

于是给定椭圆曲线上一点(x,y),压缩形态SEC生成的步骤为：
1，如果y是奇数，那么以0x03开头，如果是偶数则以0x02开头
2，添加32字节的x坐标值
于是相应实现代码就是：
```
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
```
相对于非压缩形态，压缩形态的序列化就节省了32字节。既然节省掉y，那么接收方收到数据后就需要还原它，还记得椭圆曲线的格式为 y ^ 2 = x^3 + a * x + b，我们知道了x的值，那意味着知道了y平方的值，现在我们需要计算y的值。

假设w, v为有限群的元素，并且有w^2 = v，其中群元素总共有p个。现在我们知道v，我们需要计算w。如果p % 4 = 3，那么我们有好的算法能快速计算w。由于p % 4 = 3, 于是有(p+1) % 4 = 0。也就是(p+1) 能整除4，也就是(p+1) / 4 是一个整数。根据费马小定理 w ^ (p-1) % p = 1, 于是有w ^ 2 = w ^ 2 * 1 = w ^ 2  *  (W ^ (p-1) ) = w ^ (p + 1)，由于p是奇数，因此(p+1)就能整除2，也就是(p+1)/2 是一个整数，于是就有 w = w ^ ((p+1)/2)。

上面我们提到(p+1)/4是一个整数，于是就有  w = w ^ ((p+1)/2) = w ^ (2 * (p+1)/2) = (w ^ 2) ^ ((p+1)/4) = v ^ ((p+1)/4)，于是如果 w ^ 2 = v, 并且有 p % 4 = 3, 那么 w = v ^ ((p+1)/4)。对于比特币使用的椭圆曲线，p值恰好能满足p % 4 = 3。这样一来，我们就将开方运算转为求指数运算，由此有限群元素开方运算的实现代码为：
```
P = 2 ** 256 - 2 ** 32 - 977
class BitcoinFieldElement(FieldElemet):  #S256Field
    def __init__(self, num, prime = None):
        super().__init__(num, P)
    def __repr__(self):
        return "{:x}".format(self.num).zfill(64)  # 填满64个数字

    def sqrt(self):
        return self ** ((P+1) // 4)
```
我们看看如何解析压缩形态的SEC格式数据，其实现方法为：
```
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
```
接下来，我们给几个私钥e，通过e * G 获得对应公钥，然后看看公钥对应的SEC压缩格式数据，代码如下：
```
'''
给定如下私钥，求它公钥的压缩sec个数：
5001， 2019 ^ 5, 0xdeadbeef54321
'''
priv = PrivateKey(5001)
print(priv.point.sec(True))

priv = PrivateKey(2019 ** 5)
print(priv.point.sec(True))

priv = PrivateKey(0xdeadbeef54321)
print(priv.point.sec(True))
```
上面代码运行后结果如下：
```
0357a4f368868a8a6d572991e484e664810ff14c05c0fa023275251151fe0e53d1
02933ec2d2b111b92737ec12f1c5d20f3233a0ad21cd8b36d0bca7a0cfa5cb8701
0296be5b1292f6c856b3c5654e886fc13511462059089cdf9c479623bfcbe77690
```
另外还需要序列化的结构就是签名。他有两个数值需要处理，分别是s和r，这两个值没有逻辑上的关联，因此不能像上面那样压缩。在区块链中用于序列化签名的格式叫DER(Distinguished Encoding sinatures)。DER格式如下：
1，以0x30字节开头
2，添加s和r的长度之和，通常情况下是(0x44和0x45)。
3，添加0x02作为分隔符
4，添加r的长度（一字节）将r转换为大端字节形式，如果它开头的字节>=0x80，那么先添加一个0x00然后添加r的内容，
5，添加s的长度（1字节），将s转为大端格式，如果它首字节>=0x80那么先添加一个0x00,后面才跟着s的内容。
由于r是256位数值，因此它最多32字节，如果它首字节>=0x80，那么我们需要在其前面添加0x00，因此r最多有33字节。s同理可以推断。我们看看代码实现：
```
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
```
我们运行上面编码试试：
```
sig = Signature(0x37206a0610995c58074999cb9767b87af4c4978db68c06e8e6e81d282047a7c6,
                0x8ca63759c1157ebeaec0d03cecca119fc9a75bf8e6d0fa65c841c8e2738cdaec)
print(f"signature der format:{sig.der().hex()}")
```
代码运行后结果如下：
```
signature der format:3048022037206a0610995c58074999cb9767b87af4c4978db68c06e8e6e81d282047a7c60224307830308ca63759c1157ebeaec0d03cecca119fc9a75bf8e6d0fa65c841c8e2738cdaec
```
由于目前所有编码都是二进制格式，这种格式有个问题就是不利于人的阅读理解。因此比特币后来采用base58来将二进制数据再次进行编码，之所以不用base64是因为后者有限字符容易令人混淆，例如数字0和字母O,小写的l和大写的I，于是使用base58能避免这些问题，我们看看base58编码实现：
```
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
```
我们试试上面代码：
```
'''
测试base58编码
'''
encode = encode_base58(bytes.fromhex('7c076ff316692a3d7eb3c3bb0f8b1488cf72e1afcd929e29307032997a838a3d'))
print(f"base58 encode:{encode}")
```
上面代码运行后得到的编码内容为：
```
9MA8fRQrT4u8Zj8ZRd6MAiiyaxb2Y1CMpvVkHQu5hVM6
```
base58编码本身有很多毛病，在市场上已经很少用，只是它某些特定特点正好能在区块链或比特币上用到。在以太坊或比特币应用上，数字货币在转账时需要有对应的接收地址，而这个地址的编码就使用到了base58，我们看看具体流程：
1，如果地址来自主网，那么以0x00开头，如果来自测试网络则以0x6f开头。
2，拿到SEC编码（可以是压缩也可以非压缩）,对其进行sha256哈希，然后把结果再次进行ripemd160哈希，这个过程叫hash160操作。
3，把第一和第二步所得结果前后连接起来
4，将第3步结果进行sha256哈希，取开头4个字节
5，将第3和第4步所得结果结合起来，进行base58编码
第5步所得结果也叫校验和，假设我们已经有了第3步的结果，然后看看如何实现第4，5两步，代码如下：
```
'''
实现地址编码的第4，5两步
'''
def encode_base58_checksum(b):
    return encode_base58(b + hashlib.sha256(b).digest()[:4])
```
上面提到的hash160操作其实可以直接调用hashlib接口来实现：
```
def hash160(s):
    return hashlib.new('ripemd160', hashlib.sha256(s).digest()).digest()
'''
在比特币应用中,哈希256都会连续执行两次以增强安全性
'''
def hash256(s):
    return hashlib.sha256(hashlib.sha256(s).digest()).digest()
```
我们把这些步骤正好到椭圆曲线的点中：
```
class BitcoinEllipticPoint(EllipticPoint):
    ....
    def hash160(self, compressed=True):
        return hash160(self.sec(compressed))

    def address(self, compressed=True, testnet=False):
        h160 = self.hash160(compressed)
        if testnet:
            prefix = b'\x6f'
        else:
            prefix = b'\x00'
        return encode_base58_checksum(prefix + h160)

```
我们运行上面实现的逻辑看看：
```
'''
测试椭圆曲线点的地址编码
'''
priv = PrivateKey(5002)
print(f"address for uncompressed SEC on testnet:{priv.point.address(compressed = False, testnet = True)}")
```
代码运行后结果如下：
```
address for uncompressed SEC on testnet:mmTPbXQFxboEtNRkwfh6K51jvdtHLxGeMA
```
还有一个数据结构需要序列化，那就是私钥。这个东西由于非常敏感，一旦你的私钥丢失，你所有的货币资产就会被别人窃取，因此我们通常不会在网络上传输私钥，但极个别时刻需要这么做，因此我们也需要对私钥进行序列化，它对应的格式叫WIF(Wallet Import Format),它的序列化步骤如下：
1，如果是主网私钥，以0x80开头，如果是测试网以0xef开头
2，将私钥转换为大端字节数组进行编码
3，如果公钥使用压缩SEC格式，那么在末尾添加0x01
4，将1，2，3三个步骤所得结果结合起来
5，将第四步进行sha256（也就是连续两轮256哈希）运算，取结果的前4个字节
6，将步骤4和5结合，使用base58进行编码
我们看看相应的代码实现：
```
class PrivateKey:
    ....
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

```
我们实验一下秘钥的序列化功能：
```
''
检验秘钥的序列化功能
'''
priv = PrivateKey(5003)
print(f"secret key wif:{priv.wif(True, True)}")
```
上面代码运行后结果为：
```
secret key wif:cMahea7zqjxrtgAbB7LSGbcQUr1uX1ojuat9jZodMN8rFTv2sfUK
```
比特币应用的代码很混乱，中本聪混淆着使用大端字节序和小端字节序，这是创始人的特权，就像鲁迅写错别字就成为了“通假字”，因此我们还需要了解小端编码的实现：
```
'''
我们使用一段文字进行256哈希形成秘钥，然后设置秘钥的地址格式
'''
secret_text = "this is my secret key"
secret = little_endian_to_int(hash256(secret_text.encode('utf-8')))
priv = PrivateKey(secret)
print(f"secret key address:{priv.point.address(testnet=True)}")
```
上面代码运行后所得结果为：
```
secret key address:mtg8uRgVQHjPiX15mmt7FVZeqSUbkUn3h3
```
我们这节内容很多，好在逻辑并不复杂，主要就是比较繁琐。



