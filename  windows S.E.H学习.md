
# windows S.E.H学习
=======
<<<<<<< HEAD
# windows S.E.H学习
=======
# windows S.E.H学习
>>>>>>> origin/master
>>>>>>> Stashed changes

#### 1. 常见的异常

EXCEPTION_DATATYPE_MISALIGMENT       0x80000002

EXCEPTION_BREAKPOINT                       0x80000003

EXCEPTION_SINGLE_STEP                       0x80000004

EXCEPTION_ACCESS_VIOLATION           0xC0000005

EXCEPTION_IN_PAGE_ERROR                 0xC0000006

EXCEPTION_ILLEGAL_INSTRUCTION     0xC000001d

EXCEPTION_INT_DIVIDE_BY_ZERO         0xC0000094

详情见msdn，懒得列了。

#### 2.SEH链

seh以链表的形式存储，其一个节点的结构体如下：

```c
typedef struct _EXCEPTION_REGUSTRATION_RECORD
{
  PEXCEPTION_REGISTRATION_RECORD Next;
  PEXCEPTION_DISPOSITION Handler;
} EXCEPTION_REGUSTRATION_RECORD, *PEXCEPTION_REGUSTRATION_RECORD
```

handler的成员是异常处理函数（异常处理器）。若next成员的值为0xffffffff,则表示当前节点是链表的最后一个节点。

异常处理器或者说异常处理函数的定义如下：

```c
EXCEPTION_DISPOSITION _except_handler
(
  EXCEPTION_RECORD *pRecord,
  EXCEPTION_REGISTRATION_RECORD *pFrame,
  CONTEXT *pContext;
  PVOID pValue;
);
```

函数返回值是一个名为PEXCEPTION_DISPOSITION的枚举类型。

EXCEPTION_RECORD的结构体是异常的记录信息，如下：

```
typedef struct _EXCEPTION_RECORD {
  DWORD  ExceptionCode; //异常代码
  DWORD  ExceptionFlag;
  struct _EXCEPTION_RECORD *ExceptionRecord;
  PVOID ExceptionAdress; //异常发生地址
  DWORD NumberParameters;
  ULONG_PTR ExceptionInformation[EXCEPTION_MAXIMUM_PARAMETERS];
}EXCEPTION_RECORD *PEXCEPTION_RECORD
```

ExceptionCode用来指出异常类型。

CONTEXT结构体记录上下文信息，如下：

```
//CONTEXT _IA32
struct  CONTEXT 
{
  DWORD ContextFlags;
  DWORD Dr0;
  DWORD Dr1;
  DWORD Dr2;
  DWORD Dr3;
  DWORD Dr6;
  DWORD Dr7;
  FLOATING_SAVE_AREA FloatSave;
  DWORD SegGs;
  DWORD SegFs;
  DWORD SegEs;
  DWORD SegDs;
  DWORD Edi;
  DWORD Esi;
  DWORD Ebx;
  DWORD Edx;
  DWORD Ecx;
  DWORD Eax;
  DWORD Ebp;
  DWORD Eip;
  DWORD SegCs;
  DWORD EFlags;
  DWORD Esp;
  DWORD SegSs;
  BYTE ExtendedRegisters[MAXIMUM_SUPPORTED_EXTENSION];  
}
```

异常发生时，执行异常代码的线程会中断，转至运行SEH，此时os会把context传递给异常处理函数。在异常处理函数中将context.eip (offset = context + 0xb8) 设置为其他地址，返回时就会去运行那个函数（在我的理解来，那才是真正的异常处理函数）。

异常处理器的返回值为EXCEPTION_DISPOSITION枚举类型：

```
typedef enum _EXCEPTION_DISPOSITION 
{
  ExceptionContinueExecution =0; //继续执行异常代码
  ExceptionContinueSearch = 1; //运行下一个异常处理器
  ExceptionNestedException = 2; //在OS内部使用
  ExceptionCollidedUnwind = 3 ; //在OS内部使用
}
```

#### 3. SEH安装（链接）

要将注册一个新的异常处理器，首先考虑的问题是SEH链应该放在哪？

在TEB结构体里：

```c
TEB.NtTib.ExceptionList = FS:[0]
```

所以安装的汇编如下：

```c
PUSH MyHandler;   异常处理器
PUSH DWORD PTR FS:[0] ;   Head of SEH Linked List 
MOV DWORD PTR FS:[0],ESP
```

从这里我们可以看出   异常处理器存在栈上，SEH链放在FS上。

#### 4.删除SEH

在异常处理器中改变了context.eip之后，最后会跳转到异常处理函数上去。

所以异常处理函数有可能担负着删除异常处理器的责任。

删除的方法很简单，就是

```c
pop dword ptr FS:[0]
```

将下一个SEH的地址恢复到FS上。
