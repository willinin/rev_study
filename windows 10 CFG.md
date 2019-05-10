# windows 10 CFG

1.需要操作系统和编译器的支持。

2.check indirect call，在indirect call之前插入 `_guard_check_icall`函数，该函数实际的调用函数是`ntdll!LdrpValidateUserCallTarget`。

### check的方法

维护一个CFGBitmap,这个Bitmap记录有效的函数起始地址。这是基于这样的一个假设，indirect call调用的都是一个函数，而不是一段code。

```c
int Bitmap[MAX];
```

在32位下的check是这样的：

设indirect call address 是 addr，那么它应该就是检查

```c
if Bitmap[addr>>8]  >>  ((addr >> 3 & 0xfffff) &1)  &1 == 1
```

因为bitmap是int类型（4个字节32bit），所以每个元素可以记录的函数是32个（每个bit记录一个函数）。

那么上面那段话就很好理解，拿到一个地址，高3个字节24个bit做为bitmap数组的索引值。

低一个字节的高5位就是对应数组中的每个元素中的bit位置。(假设addr是0x10对齐的)

假如低字节是0x00000130，那么高5位就是110=6，`bitmap[1]|= 0x40(100 0000)`

如果addr不是0x10对齐的，假设低字节是0x31, 那么就不是第6位设为1，那么就是6 | 1 = 7，第7位设为1。

```latex
不同于linux的cfi，windows下的cfg对函数地址的检查并不精确，存在半个字节的误差。
这种误差就可以导致许多gadget的可用性。但这种方法是一种对性能和安全性矛盾性问题的折中解决方案。
```

### inplementation

vs编译器在将C/C++编译成PE文件时，维护PE头的内容。在PE头的Load Config Table里有下面内容：

- Guard CF address of check-function pointer: the address of _guard_check_icall. On the Windows 10 preview, when the PE file is loaded, _guard_check_icall will be modified and point to nt!LdrpValidateUserCallTarget.

- Guard CF function table: pointer to list of functions’ relative virtual address (RVA), which the application’s code contains. Every function RVA will be converted to a “1” bit in the CFGBitmap. In other words, the CFGBitmap’s bit information will come from the Guard CF function table.

- Guard CF function count: the list count of function’s RVA.

- CF Instrumented: indicates CFG is enabled for this application.

在OS上，在boot阶段调用`MiInitializeCfg`函数去初始化一个共享内存区域叫做`MiCfgBitMapSection`。

在较新的windows10下，它的size是0x3000000。

在每个PE第一次load的时候，会调用MiRelocateImage,MiRelocateImage会调用MiParseImageCfgBits，会将用到的函数地址（RVA，相对偏移地址）都放在PE image section's  Control_Area的结构体内。（可以理解为添加了一个section,PE文件已改变。再一次load的时候就不会再调用了（但是会update）。

Before we take a closer look at each scenario, we need to make clear some background information. In each process view, the space which contains CFGBitmap can be divided into two parts: shared and private.MiCfgBitMapSection is a shared memory section object that contains CFGBitmap’s shared bitmap content. It is shared with every process. Each process sees the same content in the shared section when it maps MiCfgBitMapSection in its process virtual memory space. The shared module (.DLL files, etc.) bitmap information will be written by the mapping method described in Section 3.a.）。

dll文件的CFG共享内存能够被所有的进程访问。

而对于private的exe文件，The mapped base address and length will be saved to a global structure which type is MI_CFG_BITMAP_INFO and address is fixed (For build 6.4.9841, the base address is 0xC0802144. For build 10.0.9926, the base address is 0xC080214C).

```c
struct MI_CFG_BITMAP_INFO
{
  void *BaseAddress ; 
  UINT32 RegionSize ;
  void * VadBaseAddress;
  _MMVAD *BitmapVad;    
}
```

Before we take a closer look at each scenario, we need to make clear some background information. In each process view, the space which contains CFGBitmap can be divided into two parts: shared and private.MiCfgBitMapSection is a shared memory section object that contains CFGBitmap’s shared bitmap content. It is shared with every process. Each process sees the same content in the shared section when it maps MiCfgBitMapSection in its process virtual memory space. The shared module (.DLL files, etc.) bitmap information will be written by the mapping method described in Section 3.a.

However, each process requires a part in the CFGBitmap that is not shared among all processes. It needs to write some of the module’s bitmap information into the CFGBitmap as private. The private part will not be shared to all processes. The EXE module’s bitmap information will be written using the mapping method in Section 3.b. The figure below shows a common scenario.

需要注意的是是CFG只有在DEP开启的情况下才有意义。

懒得写了，一个安全机制的实现总是有一堆代码。详情见文档。

### attention

Finally, Windows stores pointers to exception handling routines on the stack. Branches to those functions are not 3 protected by CFG, so an attacker can hijack them and then cause an exception to transfer control to arbitrary locations.



### 64位下的CFG

• 00 - no address in this range is a valid target; 

• 01 - this range contains an export-suppressed target; 

• 10 - the only valid target is 16-byte aligned (that is, the first address in the range); 

• 11 - all addresses in this range are valid.

64位下的情况下，每个地址占用2个bit，这2个bit所表示的情况如上所示。（在这种情况下，似乎连一小部分的gadget都没有了？继续看论文）

论文是这样解释的：

大概就是说，因为如果在一个范围内有一个未对齐的target，那么这个地址的bitmap就不得不设置为11，因此就导致了这个范围内的gadget都是可用的。



### ref

Exploring Control Flow Guard in Windows 10   -  Jack Tang, Trend Micro Threat Solution Team
