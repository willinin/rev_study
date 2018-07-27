# C++的异常处理

#### 异常处理过程

C++的异常处理基本语法如下：

```c++
try                //异常检测
{
  //执行代码
  throw 异常类型;   //抛出异常
}
catch(捕获异常类型)  //捕获异常
{
  //处理代码
}
catch(捕获异常类型)  //捕获异常
{
  //处理代码
}
......
```

异常的处理流程为：检测异常 -> 产生异常 -> 抛出异常 ->捕获异常。

异常处理是由编译器和操作系统共同完成。主要介绍vc++，在windows SEH的机制上使用的。

vc++的异常处理回调函数是 __CxxFrameHandler，在调用前，向eax传入了一个全局地址。说明这个函数是用寄存器传参的。eax就是参数。

eax存储的结构体是  FuncInfo 函数信息表：

```c++
struct FuncInfo    (sizeof = 0x14)
{
  DWORD magicNumber;  //编译器标识
  DWORD maxState;     //函数表最大展开数的下标值
  DWORD pUnwindMap;   //指向展开函数表的指针，指针UnwindMapEntry表结构
  DWORD dwTryCount ;  //try块数量
  DWORD pTryBlockMap; //try块列表，指向TryBlockMapEntry表结构
}
```

这里有2个表，一个是函数表，一个是try块表。

UnwindMapEntry需要配合maxState，maxState记录了异常需要展开的次数。

```c++
struct  UnwindMapEntry  (sizeof = 0x8)
{
  DWORD toState ;  //函数表展开数下标直
  DWORD lpFunAction; //析构函数的地址
}
```

需要注意的是lpFunAction记录的是析构函数地址。

然后是try块表

```c++
struct TryBlockMapEntry  (sizeof = 0x14)
{
  DWORD tryLow ;
  DWORD tryHigh;
  DWORD catchHigh;
  DWORD dwCatchCount ;  //catch 块个数
  DWORD pCatchHandlerArray ;//catch块描述，指向_msRttiDscr表结构
}
```

TryBlockMapEntry表结构用于判断异常产生在哪个try块中。tryLow项与tryHigh项用于检查产生的异常是否来源与try块中，而catchHigh块则是用与匹配catch块时的检查项。每个catch块都会对应一个_msRttiDscr表。

（特别说明：IDA7.0里识别出来叫做HandlerType）

```c++
struct _msRttiDscr   (sizeof = 0x10)
{
  DWORD nFlag ; //用于catch块的匹配检查
  DWORD pType ; //catch块要捕捉的类型，指向TypeDescriptor结构
  DWORD dispCatchObjOffset ; //用于定位异常对象在当前EBP中的偏移位置
  DWORD CatchProc ; //catch块的首地址
} 
```

nFlag的值及其含义如下：

1：常量

2：变量

4：未知

8：引用

dispCatchObjOffset用于定位try块抛出的异常对象（面向对象编程），然后和_msRttiDscr块中的pType做比较。

```c++
struct TypeDescriptor 
{ 
  DWORD hash;   //类型名称的hash值
  DWORD spare;  //保留
  DWORD name;   //类型名称  是一个字符数组
}
```

#### 抛出异常过程

 抛出异常的函数是 __CxxThrowException,它其中一个调用参数是 __TI1H，这是个全局变量，在.rdate节上。

__TI1H是一个ThrowInfo结构体：

```c++
struct ThrowInfo  (sizeof =0x10)
{
  DWORD nFlag;   //异常类型标识
  DWORD pDestructor;      //异常对象的析构函数
  DWORD pForwardCompat;   //c++逆向那本书写着未知，还行
  DWORD pCatchTableTypeArray;    //Catch块类型表，指向CatchTableTypeArray表结构;
}
```

nFlag：

1 常量  ； 2 变量

```c++
struct CatchTableTypeArray  (sizeof = 0x8)
{
  DWORD dwCount ;   //数组元素个数
  DWORD ppCatchTableType; //指针数组
}
```

ppCatchTableType是一个指针数组：

```c++
struct CatchTableType (sizeof = 0x1c)
{
  DWORD flag ; 
  DWORD pTypeInfo ;  //TypeDescription表结构
  PMD thisDisplacement ;//基类信息 （当抛出的异常是个对象时使用）
  DWORD sizeOrOffset; //类的大小
  DWORD pCopyFunction; //复制构造函数的指针
}
```

flag:

1 --简单类型复制 

2 --已被捕获

4 --有虚表基类复制

8 --指着和引用类型复制



#### 总结

感觉逆向的时候不用管那么多，windows的尿性就是100张表跳来跳去，就是找到HandlerType然后找到catch块的基地址去逆就行了。
