# bin_data
import struct
class Structure():
    size: int # -1 если динамический размер и число в байтах для статического размера
    def to_bytes(self):
        raise NotImplementedError("this logic transform structure to bytes")
    def from_bytes(self, data: bytes):
        raise NotImplementedError("this logic set this structure from bytes")
    def this_size(self):
        raise NotImplementedError("this logic get dinamic size (no need if static size)")
class Number(Structure):
    respresents = int
    num: int
    signed: bool = False
    def __init__(self, num):
        self.num = num
    def to_bytes(self):
        if not self.signed:
            return int.to_bytes(self.num, self.size)
        else:
            return int.to_bytes(self.num+1<<(self.size*8-8), self.size)
    def from_bytes(self, data):
        if not self.signed:
            return int.from_bytes(data, 'big')
        else:
            return int.from_bytes(data, 'big')-2**(self.size*8-8)
    def __int__(self):
        return self.num
    
class int8(Number):
    size: int = 1
    def to_bytes(self):
        return int.to_bytes(self.num, 1)
class int16(Number):
    size: int = 2
class int32(Number):
    size: int = 4
    def to_bytes(self):
        return int.to_bytes(self.num, 4)
class int64(Number):
    size: int = 8
class int128(Number):
    size: int = 16

class signedInt8():
    size: int = 1
    signed: bool = True
class signedInt16():
    size: int = 2
    signed: bool = True
class signedInt32():
    size: int = 4
    signed: bool = True
class signedInt64():
    size: int = 8
    signed: bool = True
class signedInt128():
    size: int = 16
    signed: bool = True

class Bool(int8):
    respresents = bool
class Char(int32):
    respresents = str

class String(Structure):
    respresents = str
    size: int = -1
    def __init__(self, string=None):
        self.string = string
    def to_bytes(self):
        return int.to_bytes(len(self.string), 4)+bytes(self.string, 'utf-8')
    def from_bytes(self, data):
        sizeb = data[:4]
        size = int.from_bytes(sizeb)
        string = data[4:].decode('utf-8', errors='ignore')
        string = string[:size]
        return string
    def this_size(self):
        return 4+len(bytes(self.string, 'utf-8'))
class Bytes(Structure):
    respresents = bytes
    size: int = -1
    def __init__(self, string=None):
        self.string = string
    def to_bytes(self):
        return int.to_bytes(len(self.string), 4)+self.string
    def from_bytes(self, data):
        sizeb = data[:4]
        size = int.from_bytes(sizeb)
        string = data[4:size+4]
        return string
    def this_size(self):
        return 4+len(self.string)
import zlib
class CompBytes(Bytes):
    def __init__(self, string=None):
        super().__init__(string)
        self.comp = None
        self.bc = None
    def _comp(self):
        if self.comp is None or self.bc!=self.string:
            comp_bytes = zlib.compress(self.string, level=9)
            self.comp = comp_bytes
            self.bc = self.string
            return comp_bytes
        else:
            return self.comp
    def to_bytes(self):
        comp_bytes = self._comp()
        return int.to_bytes(len(comp_bytes), 4)+comp_bytes
    def from_bytes(self, data):
        sizeb = data[:4]
        size = int.from_bytes(sizeb)
        string = data[4:size+4]
        return zlib.decompress(string)
    def this_size(self):
        ps_string = self.string
        try:
            self.string = self._comp()
            return super().this_size()
        finally:
            self.string = ps_string
class ArrayType(Structure):
    respresents = tuple
    size: int = -1
    size_arr: int
    binType: Structure
    def __init__(self, data=None, binType=None):
        if data:
            self.data = data
            self.binType = binType
    def __call__(self, data, binType):
        self.data = data
        self.size_arr = len(data)
        self.binType = binType
        return self
    def __getattribute__(self, name):
        if name=="__mro__":
            return DinamicArray.__mro__
        return super().__getattribute__(name)
    def to_bytes(self):
        data = bytearray()
        if Structure in self.binType.__mro__:
            for i in range(len(self.data)):
                data.extend(self.binType(self.data[i]).to_bytes())
        else:
            for i in range(len(self.data)):
                data.extend(self.data[i].to_bytes())
        return data
    def from_bytes(self, data):
        next_id = 0
        if Structure in self.binType.__mro__:
            for i in range(self.size_arr):
                if self.binType.size!=-1:
                    self.data[i] = self.binType.from_bytes(self.binType, data[next_id:next_id+self.binType.size])
                    next_id += self.binType.size
                else:
                    val = self.binType.from_bytes(self.binType, data[next_id:])
                    if not hasattr(self.binType, "binType"):
                        next_id += self.binType(val).this_size()
                    else:
                        next_id += self.binType(val, self.binType.binType).this_size()
                    self.data[i] = val
        else:
            for i in range(self.size_arr):
                val = self.binType(new=False)
                val.from_bytes(data[next_id:])
                next_id += val.size()
                self.data[i] = val
        return self.data
    def this_size(self):
        if Structure in self.binType.__mro__:
            if self.binType.size != -1:
                return self.size_arr*self.binType.size
            else:
                n = 0
                for d in self.data:
                    n += len(self.binType(d).to_bytes())
                return n
        else:
            n = 0
            for d in self.data:
                n += d.size()
            return n
    def __str__(self):
        return str(self.data)
class DinamicArray(Structure):
    respresents = list
    size: int = -1
    binType: Structure
    def __init__(self, dat=None, binType=None):
        if binType is not None:
            self.binType = binType
        if dat is not None:
            self.data = dat
    def __call__(self, data, binType=None):
        self.data = data
        #return DinamicArray(data, self.binType)
        return self
    def __getattr__(self, name):
        if name=="__mro__":
            return DinamicArray.__mro__
        raise AttributeError(f"atribyte {name!r} not found in DinamicArray")
    def to_bytes(self):
        data = [int.to_bytes(len(self.data), 4)]
        # data = bytearray()
        # data.append(int32(len(self.data)).to_bytes())
        if Structure in self.binType.__mro__:
            if not hasattr(self.binType, 'binType'):
                if self.binType is int8:
                    data.append(struct.pack(f"{len(self.data)}B", *self.data))
                elif self.binType is int32:
                    data.append(struct.pack(f"{len(self.data)}I", *self.data))
                elif self.binType is signedInt32:
                    data.append(struct.pack(f"{len(self.data)}i", *self.data))
                elif self.binType is signedInt8:
                    data.append(struct.pack(f"{len(self.data)}b", *self.data))
                else:
                    data.extend([self.binType(self.data[i]).to_bytes() for i in range(len(self.data))])
                # for i in range(len(self.data)):
                #     data.append(self.binType(self.data[i]).to_bytes())
            else:
                data.extend([self.binType(self.data[i], self.binType.binType).to_bytes() for i in range(len(self.data))])
                # for i in range(len(self.data)):
                #     data.append(self.binType(self.data[i], self.binType.binType).to_bytes())
        else:
            data.extend([self.data[i].to_bytes() for i in range(len(self.data))])
            # for i in range(len(self.data)):
            #     data.append(self.data[i].to_bytes())
        return b''.join(data)
    def from_bytes(self, data):
        data = memoryview(data)
        size = int.from_bytes(data[0:4])
        self.data = [None for i in range(size)]
        next_id = 4
        if self.binType is int32:
            self.data = struct.unpack_from(f'{size}I', data, 4)
            return self.data
        elif self.binType is int8:
            self.data = struct.unpack_from(f'{size}B', data, 4)
            return self.data
        elif self.binType is signedInt8:
            self.data = struct.unpack_from(f'{size}b', data, 4)
            return self.data
        elif self.binType is signedInt32:
            self.data = struct.unpack_from(f'{size}i', data, 4)
            return self.data
        
        if Structure in self.binType.__mro__:
            if self.binType.size != -1:
                for i in range(size):
                    self.data[i] = self.binType.from_bytes(self.binType, data[next_id:next_id+self.binType.size])
                    next_id += self.binType.size
            elif not hasattr(self.binType, "binType"):
                for i in range(size):
                    val = self.binType.from_bytes(self.binType, data[next_id:])
                    temp_obj = self.binType(val)
                    next_id += temp_obj.this_size()
                    self.data[i] = val
            else:
                if type(self.binType) is not DinamicArray or self.binType.binType not in [int8, int32, signedInt8, signedInt32]:
                    for i in range(size):
                        val = self.binType.from_bytes(data[next_id:])
                        # temp_obj = self.binType(val, self.binType.binType)
                        next_id += self.binType.this_size()
                        self.data[i] = val
                else:
                    for i in range(size):
                        sp_dr = int.from_bytes(data[next_id:next_id+4])
                        next_id += 4
                        binType_dr = self.binType.binType
                        ss_binType_sp_dr = 1 if binType_dr in [int8, signedInt8] else 4
                        if binType_dr is int32:
                            val = struct.unpack(f'{sp_dr}I', data[next_id: next_id+ss_binType_sp_dr*sp_dr])
                        elif binType_dr is int8:
                            val = struct.unpack(f'{sp_dr}B', data[next_id: next_id+ss_binType_sp_dr*sp_dr])
                        elif binType_dr is signedInt8:
                            val = struct.unpack(f'{sp_dr}b', data[next_id: next_id+ss_binType_sp_dr*sp_dr])
                        elif binType_dr is signedInt32:
                            val = struct.unpack(f'{sp_dr}i', data[next_id: next_id+ss_binType_sp_dr*sp_dr])
                        next_id += ss_binType_sp_dr*sp_dr
                        self.data[i] = val

        else:
            for i in range(size):
                val = self.binType(new=False)
                val.from_bytes(data[next_id:])
                self.data[i] = val
                next_id += val.size()
        self._last_size = next_id
        self._last_data = self.data
        return self.data
    def this_size(self):
        n = 4  # Заголовок самого массива (int32)
        if Structure in self.binType.__mro__:
            if self.binType.size != -1:
                return n + (len(self.data) * self.binType.size)
            else:
                if hasattr(self, '_last_size') and self._last_data is self.data:
                    res = self._last_size
                    del self._last_size
                    return res
                if not hasattr(self.binType, "binType"):
                    for d in self.data:
                        n += self.binType(d).this_size()
                else:
                    for d in self.data:
                        n += self.binType(d, self.binType.binType).this_size()
                return n
        else:
            if hasattr(self, '_last_size') and self._last_data is self.data:
                res = self._last_size
                del self._last_size
                return res
            for d in self.data:
                n += d.size()
            return n
    def __str__(self):
        return str(self.data) if hasattr(self, 'data') else "not data. type:"+str(self.binType)
class DinamicArray2D(DinamicArray):
    def __init__(self, dat=None, binType=None):
        if binType is not None:
            self.binType = binType
        if dat is not None:
            self.data = dat
            self.width = len(self.data[0])
    def to_bytes(self):
        pre_dat = self.data
        self.data = tuple(item for colect in self.data for item in colect)
        try:
            return super().to_bytes()
        finally:
            self.data = pre_dat
    def from_bytes(self):
        res = super().to_bytes()
        return [res[i:i+self.width] for i in range(0, len(res), self.width)]
    def this_size(self):
        pre_dat = self.data
        self.data = tuple(item for colect in self.data for item in colect)
        try:
            return super().this_size()
        finally:
            self.data = pre_dat
class Pointer(int64):
    NULLPTR = 0
    def __init__(self, num):
        super().__init__(num)
    def from_bytes(self, *args, **kwargs):
        return Pointer(super().from_bytes(*args, **kwargs))
    def get(self, data):
        return data[self.num+int32.size:self.num+int32.size+int.from_bytes(data[self.num: self.num+int32.size], 'big')]
    def set(self, val):
        if val<=0:
            raise ValueError("Зointer in right (not left) part regarding begin data") 
        self.num = val
    def set_nullptr(self):
        self.num = self.NULLPTR
    def __eq__(self, other):
        return self.num==other.num
class PointerData(Bytes):
    pass
class padd(Structure):
    size: int = -1
    def __init__(self, pad_size):
        self.pad = pad_size
    def to_bytes(self):
        return bytes(self.pad)
    def from_bytes(self, data):
        return bytes(self.pad)
    def this_size(self):
        return self.pad
import pickle
import io
class Any(Structure):
    size: int = -1
    represents = any
    def __init__(self, obj):
        self.obj = obj
    def to_bytes(self):
        return pickle.dumps(self.value)
    def from_bytes(self, data: bytes):
        bytes_io = io.BytesIO(data)
        unpickler = pickle.Unpickler(bytes_io)
        self.obj = unpickler.load()
        self._used_bytes_size = bytes_io.tell()
        return self.obj
    def this_size(self):
        if self.obj is not None:
            return len(self.to_bytes())
        raise ValueError("is not need")
def Array(binType, l):
    arr = ArrayType()
    def syper_fn(*args, **kwargs):
        if len(args[0]) > l:
            raise OverflowError(f"this size is big. I expected no more {l}")
        return arr(*args, binType=binType, **kwargs)
    return syper_fn
class Status(int8):
    def __init__(self, statuses):
        self.statuses = statuses
    def __call__(self, num):
        return super().__init__(num)
    def get_stat_num(self, name_stat):
        status = self.statuses.find(name_stat)
        if status == -1:
            raise ValueError(f"status {name_stat!r} is not found in statuses")
        return status
    def get_name_status(self, id_status):
        if not (0<=id_status<len(self.statuses)):
            raise IndexError(f"status id {id_status!r} not found")
        return self.statuses[id_status]
    def set(self, status):
        self.num = self.get_stat_num(status)
    def get(self):
        return self.get_name_status(self.num)

class BigStructure():
    def to_bytes(self):
        attrs = self.__annotations__
        data = [
            cls(val).to_bytes() if Structure in cls.__mro__ else val.to_bytes()
            for attr, cls in attrs.items()
            if (val := getattr(self, attr)) or True
        ]
        # for attr in attrs:
        #     val = getattr(self, attr)
        #     if Structure in attrs[attr].__mro__:
        #         bval = attrs[attr](val).to_bytes()
        #     else:
        #         bval = getattr(self, attr).to_bytes()
        #     data.append(bval)
        return b''.join(data)
    @classmethod
    def load(cls, data):
        ins = cls.__new__(cls)
        ins.from_bytes(data)
        return ins
    def from_bytes(self, data):
        attrs = self.__annotations__
        next_id = 0
        for attr in attrs:
            binType = attrs[attr]
            if Structure in binType.__mro__:
                if binType.size!=-1:
                    setattr(self, attr, binType.from_bytes(binType, data[next_id:next_id+binType.size]))
                    next_id += binType.size
                else:
                    if not hasattr(binType, "binType"):
                        val = binType.from_bytes(binType, data[next_id:])
                        next_id += binType(val).this_size()
                    else:
                        val = binType.from_bytes(data[next_id:])
                        next_id += binType(val, binType.binType).this_size()
                    setattr(self, attr, val)
            else:
                val = binType(new=False)
                val.from_bytes(data[next_id:])
                setattr(self, attr, val)
                next_id += val.size()
    def size(self):
        attrs = self.__annotations__
        n = 0
        for attr in attrs:
            binType = attrs[attr]
            if Structure in binType.__mro__:
                if binType.size!=-1:
                    n += binType.size
                else:
                    n += binType(getattr(self, attr)).this_size()
                    # n += len(binType(getattr(self, attr)).to_bytes())
            else:
                n += getattr(self, attr).size()
        return n
    def get_pos_attr(self, find_attr):
        attrs = self.__annotations__
        n = 0
        for attr in attrs:
            if attr==find_attr:
                return n
            binType = attrs[attr]
            if Structure in binType.__mro__:
                if binType.size!=-1:
                    n += binType.size
                else:
                    n += len(binType(getattr(self, attr)).to_bytes())
            else:
                n += getattr(self, attr).size()
        raise AttributeError(f"attribute {find_attr!r} is not in self")
    def __setattr__(self, name, value):
        try:
            attr_val = object.__getattribute__(self, name)
        except AttributeError:
            object.__setattr__(self, name, value)
            return
        if type(attr_val) is Pointer and (type(value) is str):
            attr_val.set(self.get_pos_attr(value))
        else:
            object.__setattr__(self, name, value)

    def set_pointer(self, pointer_attr, res_attr):
        getattr(self, pointer_attr).set(self.get_pos_attr(res_attr))
    def get_val(self, pointer_attr):
        getattr(self, pointer_attr).get(self.data)
BigStructure.respresents = BigStructure
def explanation_bytes(bStruct, depth=0):
    explation_string = f"{'  '*(depth-1)+'|--' if depth else '--'} explanation bytes of {bStruct} --\n"
    attrs = bStruct.__annotations__
    for attr in attrs:
        binStruct = attrs[attr]
        val = getattr(bStruct, attr)
        if Structure in binStruct.__mro__:
            bval = binStruct(val).to_bytes()
        else:
            bval = val.to_bytes()
        explation_string += f"{'  '*depth}{attr}: {type(binStruct).__name__} ({val.size() if Structure not in binStruct.__mro__ else binStruct.size }b) = {val} ({bval})\n"
        if Structure not in binStruct.__mro__:
            explation_string += explanation_bytes(val, depth+1)
    return explation_string

class TextView():
    def __repr__(self):
        return f"{type(self).__name__}({', '.join(f'{attr}={repr(getattr(self, attr))}' for attr in self.__annotations__)})"
class AutoCreate():
    def __init__(self, *args, **kwargs):
        attrs = self.__annotations__
        for i, val in enumerate(args):
            name = list(attrs.items())[i][0]
            if isinstance(val, attrs[name].respresents):
                setattr(self, name, val)
            else:
                raise ValueError(f"excepted {attrs[name].respresents.__name__}")
        for attr in kwargs:
            val = kwargs[attr]
            if attr=='new':
                return
            if isinstance(val, attrs[attr].respresents):
                setattr(self, attr, val)
            else:
                raise ValueError(f"excepted {attrs[attr].respresents.__name__}")
if __name__ == "__main__":
    from contextlib import contextmanager
    import time
    @contextmanager
    def timeit(testname):
        print("["+("-"*(11+len(testname))+("-"*10)+"]"))
        print("|"+"-"*9, testname, "-"*10+"|")
        print("["+("-"*(11+len(testname))+("-"*10)+"]"))
        t = time.time()
        try:
            yield
        finally:
            print("timeit:", time.time()-t, "seconds")
    class User(BigStructure, TextView):
        name: String
        id: int64
        def __init__(self, name=None, id=None, new=True):
            if new:
                self.name = name
                self.id = id
        def __str__(self):
            return repr(self)
    class GroupUsers(BigStructure, TextView):
        first: User
        second: User
        def __init__(self, first=None, second=None, new=True):
            if new:
                self.first = first
                self.second = second
    user = User("hello", 5)
    print(user)
    buser = user.to_bytes()
    print(buser)
    print(explanation_bytes(user))
    luser = User(new=False)
    luser.from_bytes(buser)
    print(luser)
    luser.id = 1
    g = GroupUsers(luser, user)
    print(repr(g))
    print(explanation_bytes(g))
    bg = g.to_bytes()
    print(bg)
    lg = GroupUsers.load(bg)
    # lg.from_bytes(bg)
    print(repr(lg))
    with timeit("array test"):
        size_arr = 2
        arr = Array(String, size_arr)(["Hello", "World"])
        barr = arr.to_bytes()
        print(barr)
        larr = Array(String, size_arr)(["", ""])
        larr.from_bytes(barr)
        print(larr)
    with timeit("dinamic array test"):
        darr = DinamicArray([User("peple", 1), User("peple", 5)], User)
        bdarr = darr.to_bytes()
        print(bdarr)
        ldarr = DinamicArray(None, User)
        ldarr.from_bytes(bdarr)
        print(ldarr)
    with timeit("dinamic array test 2D struct"):
        darr = DinamicArray([[User("peple", 1), User("peple", 5)]], DinamicArray([], User))
        bdarr = darr.to_bytes()
        print(bdarr)
        ldarr = DinamicArray(None, DinamicArray([], User))
        ldarr.from_bytes(bdarr)
        print(ldarr)
    # class Molecule(TextView, AutoCreate, BigStructure):
    #     x: int64
    #     y: int64
    #     size: int64 = 5
    #     sx: int64 = 0
    #     sy: int64 = 0
    #     en: Bool = True
    # from random import randint
    # with timeit("dinamic array test"):
    #     molecs = [Molecule(randint(0,100), randint(0,100)) for i in range(100)]
    #     byte_molecs = DinamicArray(molecs, Molecule).to_bytes()
    #     print(byte_molecs)
    import random
    with timeit("test compress"):
        for_bdata = bytes(' '.join(['hello world', 'this is good', 'error of '+str(random.randint(0,5))+" line", " is super error\n", *(' '.join(["this", "good", "no", "err", "line", "syper fn", "func", "was good no", "goodly", "no good this m", "press f", "hw work"][random.randint(0,7)] for i in range(20)) for i in range(10))][random.randint(0,3)] for i in range(100)), 'utf-8')
        bcdata = CompBytes(for_bdata)
        bdatabytes = bcdata.to_bytes()
        print(repr(bdatabytes))
        bcdata = CompBytes()
        res = bcdata.from_bytes(bdatabytes)
        print(res)
