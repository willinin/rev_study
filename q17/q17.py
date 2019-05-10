#coding:utf-8
from pwn import *
import os
import pysnooper
import ctypes

fp = open("./barely_reversible.txt.bak","r")

outcome = """0x0b755f7165164063	0x0c44641a663d516b
0x7462060b0723584e	0x624f4a5667093841
0x33503d4f3b6e447f	0x6d0b393373706f02
0x7f227d485a277b69	0x437c786417027b26""".split()

def signed_long(var):
    return ctypes.c_longlong(var).value

#base64??
def sub_80A(a1):
    return (a1[2] << 14)| a1[0]| (a1[1] << 7) | (a1[3] << 21)

def sub_859(a1):
    v1 =  (sub_80A(a1) << 28) 
    #v1 = (a1[2] << 14)| a1[0]| (a1[1] << 7) | (a1[3] << 21) | (a1[4] << 28)
    ans = v1 | sub_80A(bytearray(a1[4:]))
    #ans = bytearray(p64(ans))
    return ans 


def sub_99C(a1,a2):
    return (0x59D39E717F7 * a2 + 0x35E55F10E61 * a1 - 0xC40BF11DDFCD22E) & 0xFFFFFFFFFFFFFF

def sub_9EB(a1,a2):
    return a1 ^ a2  

def sub_650(a1,a2):
    ans = 4 * ((a2 + a1) & 0x3FF) + (a1 & 0xFFFFFFFFFFFFF000)
    #print hex(ans)
    offset = ans & 0xfff
    fp.seek(offset)
    ans = fp.read(4)
    return u32(ans)

def sign_extend(a1):
    if a1 >> 31 == 1:
        a1 += 0xFFFFFFFF00000000
    return a1

retaddr = 0x7ffff7dfb808
def sub_72D(a1):
    v1 = sub_650(retaddr, a1)
    v2 = (v1 + sub_650(retaddr, a1 + 2)) << 32
    v2 = v2 & 0xFFFFFFFFFFFFFFFF
    v3 = sub_650(retaddr, 2 * a1)
    v3 = sign_extend(v3)
    tmp = sub_650(retaddr, 3 * a1)
    tmp  = sign_extend(tmp)
    v3 = signed_long(v3)*signed_long(tmp)
    v3 = v3 & 0xFFFFFFFFFFFFFFFF
    v3 = v3^v2
    v3 = v3 & 0xFFFFFFFFFFFFFFFF
    tmp1 = sub_650(retaddr, a1 + 13)
    tmp1  = sign_extend(tmp1)
    ans = (v3 ^ tmp1)& 0xFFFFFFFFFFFFFFFF
    return ans

def sub_7D1(a1):
    return sub_72D(u32(p64(a1)[0:4]))

def sub_944(a1):
    return (a1 >> 48) ^ (a1 >> 40) ^ (a1 >> 32) ^ (a1 >> 24) ^ a1 ^ (a1 >> 8) ^ (a1 >> 16) ^ (a1 >> 56)

ggflag = 0 

#@pysnooper.snoop()  #debug the while function
def sub_A01(input_x,magic):
    v2 = sub_99C(input_x, magic)
    v3 = sub_9EB(v2, magic)
    v4 = sub_7D1(magic)
    v5 = sub_944(v3)
    #print "q17",hex(v2),hex(v3),hex(v4),hex(v5)
    
    return sub_99C(v5, v4)

def sub_A83(xx):
    v6 = xx
    #v14 = bytearray('NeSE2018'[::-1])
    v14 = u64('NeSE2018'[::-1])
    #print hex(v14)
    
    for i in range(8):
        v15 = []
        for j in range(8):
            v15.append(sub_859(bytearray(v6[8*j:8*j+8])))

       

        for k in range(8):
            v15[k] = sub_A01(v15[k],v14)
            v14 = v14 + 1 
        
    
        for l in range(10):
            for m in range(4):
                v2 = v15[2*m+1]
                v3 = sub_A01(v15[2 * m], v14)
                v15[2*m] = v2
                v15[2*m+1] = sub_A01(v3, v2)
                v14 = v14 + 1
                if m==3:
                    print 'z1', hex(v15[2*m]), 'z2', hex(v15[2*m+1])

        #for g in range(len(v15)):
        #    print hex(v15[g])  
        #return
        for n in range(8):
            for ii in range(8):
                xx[ii+8*(ii^n)] = (v15[n] >>(7*ii)) & 0x7F            
        v14 = (v14 + sub_7D1(v14)) & ((1 << 64)-1)
    return  xx
      

    

if __name__ == "__main__":
    inp = "abcd1234"*8
    #inp = cyclic(64)
    #$seed='will'
    #from hashlib import sha512
    #inp=''.join(sha512(seed).digest().encode('base64').split())[:64]
    #inp = bytearray(inp)
    #print inp
    print inp
    inp=inp[:63]+'\0'
    inp = bytearray(inp)
    xx  = sub_A83(inp)
    
    print xx
    print "test----------"
    
    