# coding:utf-8
from pwn import *
import os
import q17
import ctypes
import gmpy2
import pysnooper

# add debug location  "with pysnooper.snoop():"


def e_gcd(a, b):
    if b == 0:
        x = 1
        y = 0
        return x, y
    x, y = e_gcd(b, a % b)
    tmp = x
    x = y
    y = tmp - a/b * y
    return x, y


def signed_long(var):
    return ctypes.c_longlong(var).value


fp = open("./barely_reversible.txt.bak", "r")


def sov1(xx):
    v15 = [0, 0, 0, 0, 0, 0, 0, 0]
    for n in range(8):
        for ii in range(8):
            #xx[ii+8*(ii^n)] = (v15[n] >>(7*ii)) & 0x7F
            v15[n] = v15[n] | (xx[ii+8*(ii ^ n)] << (7*ii))
    return v15

def sign_extend(a1):
    if a1 >> 31 == 1:
        a1 += 0xFFFFFFFF00000000
    return a1

def rev_99C(a1, a2):
    tmp1 = signed_long(a1 + 0xC40BF11DDFCD22E)
    tmp2 = signed_long(0x59D39E717F7 * a2)
    tmp3 = signed_long(tmp1 - tmp2)
    x, y = e_gcd(0x35E55F10E61, 2**56)
    ans = (tmp3 * x) & 0xFFFFFFFFFFFFFF
    return ans

def rev_944(a1):
    tmp8 = a1 & 0xff
    tmp7 = (a1 >> 8) & 0xff
    tmp6 = (a1 >> 16) & 0xff
    tmp5 = (a1 >> 24) & 0xff
    tmp4 = (a1 >> 32) & 0xff
    tmp3 = (a1 >> 40) & 0xff
    tmp2 = (a1 >> 48) & 0xff
    tmp1 = (a1 >> 56) & 0xff
    x1 = tmp1
    x2 = tmp1 ^ tmp2
    x3 = tmp2 ^ tmp3
    x4 = tmp3 ^ tmp4
    x5 = tmp4 ^ tmp5
    x6 = tmp5 ^ tmp6
    x7 = tmp6 ^ tmp7
    x8 = tmp7 ^ tmp8
    outcome = (x1 << 56) ^ (x2 << 48) ^ (x3 << 40) ^ (
        x4 << 32) ^ (x5 << 24) ^ (x6 << 16) ^ (x7 << 8) ^ x8
    return outcome

def rev_A01(x, magic):
    v4 = q17.sub_7D1(magic)
    # with pysnooper.snoop():
    # x= q17.sub_99C(v5, v4)  =>v5
    v5 = rev_99C(x, v4)+ ((magic >> 56) << 56)
    # v5 = q17.sub_944(v3)    =>v3
    v3 = rev_944(v5)
    # v3 = q17.sub_9EB(v2, magic)  => v2 
    v2 = (v3 ^ magic) & ((1 << 56)-1)
    # v2 = q17.sub_99C(input_x, magic)  => input_x
    #print "rev",hex(v2),hex(v3),hex(v4),hex(v5)
    input_x = rev_99C(v2, magic)
    #print hex(input_x),hex(magic),hex(x)
    #print hex(q17.sub_A01(input_x, magic) )
    #assert q17.sub_A01(input_x, magic) == x
    return input_x


def rev_859(a1):
    ans = bytearray(8)
    tmp1 = a1 & 0x7f
    tmp2 = (a1 >> 7) & 0x7f
    tmp3 = (a1 >> 14) & 0x7f
    tmp4 = (a1 >> 21) & 0x7f
    tmp5 = (a1 >> 28) & 0x7f
    tmp6 = (a1 >> 35) & 0x7f
    tmp7 = (a1 >> 42) & 0x7f
    tmp8 = (a1 >> 49) & 0x7f
    #tmp9 = (a1 >> 56) &0x7f
    outcome1 = tmp4 | (tmp3 << 8) | (tmp2 << 16) | (tmp1 << 24)
    outcome2 = (tmp8 << 32) | (tmp7 << 40) | (tmp6 << 48) | (tmp5 << 56)
    return p64(outcome1 | outcome2)[::-1]


def get_magic1(tnum):
    v14 = u64('NeSE2018'[::-1])
    for i in range(8-tnum):
        for k in range(8):
            v14 = v14+1

        for l in range(10):
            for m in range(4):
                v14 = v14+1
        if i == 8-tnum-1:
            return v14& ((1 << 64)-1)
        v14 = v14 + q17.sub_7D1(v14)
        v14 = v14 & ((1 << 64)-1)
    return v14


def sov(ans):
    flag = bytearray(64)
    xx = bytearray(ans)
    for i in range(8):
        v15 = sov1(xx)
        v14 = get_magic1(i)

        # now we should get source v15
        for l in range(10):
            for m in range(3, -1, -1):
                v14 = v14-1
                v2 = v15[2*m]
                v3 = rev_A01(v15[2*m+1], v2)
                v15[2*m] = rev_A01(v3, v14)
                v15[2*m+1] = v2
         
        for k in range(7, -1, -1):
            v14 = v14 -1
            v15[k] = rev_A01(v15[k], v14)
        
        for j in range(8):
            xx[8*j:8*j+8] = rev_859(v15[j])
        #break
    return xx

if __name__ == "__main__":

    fp.seek(0x1da0)
    ans = fp.read(64)
    ans = bytearray(ans)

    #inp = cyclic(64)
    #inp = bytearray(inp)
    #inp = "abcd1234"*8
    #inp = cyclic(64)
    #inp = bytearray(inp)
    #print inp
    #ans = q17.sub_A83(inp)
    gg = sov(ans)
    print gg
