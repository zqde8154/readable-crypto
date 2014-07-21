#! /usr/bin/env python

# the main motivation for not using the abc module here is to maintain
# compatibility with Python 2. This might be refactored in the future.

import math

def get_bit(val, i):
    return int(val & (1 << i) != 0)


def to_blocks(val, length, N):
    result = []
    for i in range(N):
        result.append(val & int('1' * length, 2))
        val >>= length
    return reversed(result)


class QUARK_ABC(object):

    @property
    def c(self):
        raise NotImplementedError("Capacity c not specified")

    @property
    def r(self):
        raise NotImplementedError("Rate r not specified")

    @property
    def n(self):
        raise NotImplementedError("Output length n not specified")

    @property
    def IV(self):
        raise NotImplementedError("Initialisation vector not specified")

    def f(self, X):
        raise NotImplementedError("Function f not specified")

    def g(self, Y):
        raise NotImplementedError("Function g not specified")

    def h(self, X, Y, L):
        raise NotImplementedError("Function h not specified")

    def p(self, L):
        raise NotImplementedError("Function p not specified")

    def initialise(self, m, prefix_zeros=0):
        m = m << 1 | 1
        length = len(bin(m)) - 2 + prefix_zeros  # -2 for 0b prefix
        m <<= self.r - length % self.r
        N = math.ceil((prefix_zeros + length) / self.r)
        return m, N

    def P(self, s):
        b = self.r + self.c
        mask_b2 = int('1' * (b//2), 2)
        mask_log4b = int('1' * math.ceil(math.log2(4 * b)), 2)
        X = s >> (b//2)
        Y = s & mask_b2
        L = mask_log4b
        for i in range(4 * b):
            ht = self.h(X, Y, L)
            Xnew = (X << 1 | (get_bit(Y, b//2-1) ^ self.f(X) ^ ht)) & mask_b2
            Ynew = (Y << 1 | (self.g(Y) ^ ht)) & mask_b2
            Lnew = (Y << 1 | (self.p(L) ^ ht)) & mask_log4b
        return X << (b//2) | Y

    def absorb(self, m, N):
        s = self.IV
        for mblock in to_blocks(m, self.r, N):
            s = s ^ mblock
            s = self.P(s)
        return s

    def squeeze(self, s):
        result = 0x0
        for i in range(self.n // self.r - 1):
            result = result | (s & int('1' * self.r, 2))
            result <<= self.r
            s = self.P(s)
        result = result | (s & int('1' * self.r, 2))
        return result

    def hash(self, m, prefix_zeros=0):
        m, N = self.initialise(m, prefix_zeros)
        s = self.absorb(m, N)
        return self.squeeze(s)


class U_QUARK(QUARK_ABC):

    r = 8
    c = 128
    n = 136
    IV = 0xD8DACA44414A099719C80AA3AF065644DB

    def f(self, X):
        bX = lambda i: get_bit(X, 68-1 - i)
        return (bX(0) ^ bX(9) ^ bX(14) ^ bX(21) ^ bX(28) ^ bX(33) ^ bX(37) ^
                bX(45) ^ bX(50) ^ bX(52) ^ bX(55) ^ bX(55) & bX(59) ^
                (bX(33) & bX(37)) ^ (bX(9) & bX(15)) ^
                (bX(45) & bX(52) & bX(55)) ^ (bX(21) & bX(28) & bX(33)) ^
                (bX(9) & bX(28) & bX(45) & bX(59)) ^
                (bX(33) & bX(37) & bX(52) & bX(55)) ^
                (bX(15) & bX(21) & bX(55) & bX(59)) ^
                (bX(37) & bX(45) & bX(52) & bX(55) & bX(59)) ^
                (bX(9) & bX(15) & bX(21) & bX(28) & bX(33)) ^
                (bX(21) & bX(28) & bX(33) & bX(37) & bX(45) & bX(52)))

    def g(self, Y):
        bY = lambda i: get_bit(Y, 68-1 - i)
        return (bY(0) ^ bY(7) ^ bY(16) ^ bY(20) ^ bY(30) ^ bY(35) ^ bY(37) ^
                bY(42) ^ bY(49) ^ bY(51) ^ bY(54) ^
                (bY(54) & bY(58)) ^ (bY(35) & bY(37)) ^ (bY(7) & bY(15)) ^
                (bY(42) & bY(51) & bY(54)) ^ (bY(20) & bY(30) & bY(35)) ^
                (bY(7) & bY(30) & bY(42) & bY(58)) ^
                (bY(35) & bY(37) & bY(51) & bY(54)) ^
                (bY(15) & bY(20) & bY(54) & bY(58)) ^
                (bY(37) & bY(42) & bY(51) & bY(54) & bY(58)) ^
                (bY(7) & bY(15) & bY(20) & bY(30) & bY(35)) ^
                (bY(20) & bY(30) & bY(35) & bY(37) & bY(42) & bY(51)))

    def h(self, X, Y, L):
        bX = lambda i: get_bit(X, 68-1 - i)
        bY = lambda i: get_bit(Y, 68-1 - i)
        bL = lambda i: get_bit(L, 10-1 - i)
        return (bL(0) ^ bX(1) ^ bY(2) ^ bX(4) ^ bY(10) ^ bX(25) ^ bX(31) ^
                bY(43) ^ bX(56) ^ bY(59) ^
                (bY(3) & bX(55)) ^ (bX(46) & bX(55)) ^ (bX(55) & bY(59)) ^
                (bY(3) & bX(25) & bX(46)) ^ (bY(3) & bX(46) & bX(55)) ^
                (bY(3) & bX(46) & bY(59)) ^
                (bL(0) & bX(25) & bX(46) & bY(59)) ^ (bL(0) & bX(25)))

    def p(self, L):
        bL = lambda i: get_bit(L, 10-1 - i)
        return bL(0) ^ bL(3)

class D_QUARK(QUARK_ABC):

    r = 16
    c = 160
    n = 176
    IV = 0xCC6C4AB7D11FA9BDF6EEDE03D87B68F91BAA706C20E9


class S_QUARK(QUARK_ABC):

    r = 32
    c = 224
    n = 256
    IV = 0x397251CEE1DE8AA73EA26250C6D7BE128CD3E79DD718C24B8A19D09C2492DA5D
