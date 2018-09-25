

```c++
const void *
__VLTVerifyVtablePointer (void ** set_handle_ptr, const void * vtable_ptr)
{
  unsigned long long start = get_cycle_count ();
  int_vptr vtbl_ptr = (int_vptr) vtable_ptr;

  vtv_set_handle *handle_ptr;
  increment_num_calls (&num_calls_to_verify_vtable);
  if (!is_set_handle_handle (*set_handle_ptr))
    handle_ptr = (vtv_set_handle *) set_handle_ptr;
  else
    handle_ptr = ptr_from_set_handle_handle (*set_handle_ptr);

  if (!vtv_sets::contains (vtbl_ptr, handle_ptr))
    {
      __vtv_verify_fail ((void **) handle_ptr, vtable_ptr);
      /* Normally __vtv_verify_fail will call abort, so we won't
         execute the return below.  If we get this far, the assumption
         is that the programmer has replaced __vtv_verify_fail with
         some kind of secondary verification AND this secondary
         verification succeeded, so the vtable pointer is valid.  */
    }
  accumulate_cycle_count (&verify_vtable_cycles, start);

  return vtable_ptr;
}
```



```c
typedef uintptr_t int_vptr;

struct vptr_hash
  {
    /* Hash function, used to convert vtable pointer, V, (a memory
       address) into an index into the hash table.  */
    size_t
    operator() (int_vptr v) const
      {
	const uint32_t x = 0x7a35e4d9;
	const int shift = (sizeof (v) == 8) ? 23 : 21;
	v = x * v;
	return v ^ (v >> shift);
      }
  };

struct vptr_set_alloc
  {
    /* Memory allocator operator.  N is the number of bytes to be
       allocated.  */
    void *
    operator() (size_t n) const
      {
	return __vtv_malloc (n);
      }
  };

typedef insert_only_hash_sets<int_vptr, vptr_hash, vptr_set_alloc> vtv_sets;

template<typename Key, class HashFcn, class Alloc>
bool
insert_only_hash_sets<Key, HashFcn, Alloc>::insert_only_hash_set::contains
                                                           (key_type key) const
{
  inc (stat_contains_in_non_trivial_set);
  HashFcn hasher;
  const size_type capacity = num_buckets;
  size_type index = hasher (key) & (capacity - 1);
  key_type k = key_at_index (index);
  size_type indices_examined = 0;
  inc (stat_probes_in_non_trivial_set);
  while (k != key)
    {
      ++indices_examined;
      if (/*UNLIKELY*/(k == (key_type) illegal_key
		       || indices_examined == capacity))
	return false;

      index = next_index (index, indices_examined);
      k = key_at_index (index);
      inc (stat_probes_in_non_trivial_set);
    }
  return true;
}

key_type
    key_at_index (size_type index) const
    { return buckets[index]; }


```

```c++
const unsigned long SET_HANDLE_HANDLE_BIT = 0x2;

/* In the case where a vtable map variable is the only instance of the
   variable we have seen, it points directly to the set of valid
   vtable pointers.  All subsequent instances of the 'same' vtable map
   variable point to the first vtable map variable.  This function,
   given a vtable map variable PTR, checks a bit to see whether it's
   pointing directly to the data set or to the first vtable map
   variable.  */

static inline bool
is_set_handle_handle (void * ptr)
{
  return ((uintptr_t) ptr & SET_HANDLE_HANDLE_BIT)
                                                      == SET_HANDLE_HANDLE_BIT;
}

```

```
 /* Do not directly use insert_only_hash_set.  Instead, use the
     static methods below to create and manipulate objects of the
     following class.
  
     Implementation details: each set is represented by a pointer
     plus, perhaps, out-of-line data, which would be an object of type
     insert_only_hash_set.  For a pointer, s, the interpretation is: s
     == NULL means empty set, lsb(s) == 1 means a set with one
     element, which is (uintptr_t)s - 1, and otherwise s is a pointer
     of type insert_only_hash_set*.  So, to increase the size of a set
     we have to change s and/or *s.  To check if a set contains some
     key we have to examine s and possibly *s.  */
```














